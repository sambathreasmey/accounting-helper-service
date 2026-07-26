import pytest
from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

if not hasattr(SQLiteTypeCompiler, "visit_JSONB"):

    def _visit_jsonb(self, type_, **kw):
        return self.visit_JSON(type_, **kw)

    SQLiteTypeCompiler.visit_JSONB = _visit_jsonb


@pytest.mark.asyncio
async def test_create_and_list_suppliers_for_chat(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "secret")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://example.test")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setenv("PO_CALLBACK_SECRET", "secret")
    monkeypatch.setenv("JWT_SECRET", "secret")
    monkeypatch.setenv("ALERT_CHAT_ID", "0")

    import importlib

    import app.core.config as config_module

    importlib.reload(config_module)

    from app.db.crud import create_po, create_supplier, list_suppliers
    from app.db.database import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        supplier = await create_supplier(session, chat_id=123, name="Thai Hout")
        assert supplier.name == "Thai Hout"

        rows, total = await list_suppliers(session, chat_id=123)
        assert total == 1
        assert [row.name for row in rows] == ["Thai Hout"]

        po = await create_po(
            session,
            chat_id=123,
            po_id="PO-100",
            supplier_name="Thai Hout",
            items=[{"name": "Pens", "qty": 2, "price": 10.0}],
        )
        assert po.supplier_id == supplier.id
        assert po.supplier_name == "Thai Hout"

    await engine.dispose()
