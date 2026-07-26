from collections.abc import AsyncGenerator

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


# Neon (and most managed Postgres) are reached over a pooled connection
# already, and serverless-style deployments open/close often — so we keep
# our own pool small and recycle connections defensively rather than
# holding long-lived ones that Neon's proxy might have already dropped.
engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    pool_recycle=300,
    connect_args={"ssl": "require"} if "neon.tech" in settings.DATABASE_URL else {},
)

async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False, autoflush=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a scoped DB session per request."""
    async with async_session_maker() as session:
        yield session


async def ensure_schema_columns() -> None:
    """Backfill missing columns on existing databases without forcing a full reset."""

    async with engine.begin() as conn:
        await conn.run_sync(_ensure_schema_columns)


def _ensure_schema_columns(conn) -> None:
    inspector = inspect(conn)
    if not inspector.has_table("purchase_orders"):
        return

    purchase_orders_columns = {
        column["name"] for column in inspector.get_columns("purchase_orders")
    }
    if "supplier_name" not in purchase_orders_columns:
        conn.execute(
            text(
                "ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS supplier_name TEXT"
            )
        )

    if "supplier_id" not in purchase_orders_columns:
        conn.execute(
            text(
                "ALTER TABLE purchase_orders ADD COLUMN IF NOT EXISTS supplier_id UUID"
            )
        )

    conn.execute(
        text(
            "UPDATE purchase_orders "
            "SET supplier_name = (SELECT name FROM suppliers WHERE suppliers.id = purchase_orders.supplier_id) "
            "WHERE supplier_name IS NULL AND supplier_id IS NOT NULL"
        )
    )


async def init_models() -> None:
    """Create tables on startup if they don't exist yet.

    Fine for this project's scale. If the schema grows non-trivially,
    switch to Alembic migrations instead of relying on create_all.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await ensure_schema_columns()


async def dispose_engine() -> None:
    await engine.dispose()
