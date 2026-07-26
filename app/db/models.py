import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Enum, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class POStatus(str, enum.Enum):
    PENDING = "pending"  # parsed, not yet dispatched to GitHub
    DISPATCHED = "dispatched"  # sent to GitHub Actions, waiting on it
    COMPLETED = "completed"  # workflow finished, document generated
    FAILED = "failed"  # dispatch or generation failed


class POSource(str, enum.Enum):
    TELEGRAM = "telegram"  # created from a raw Telegram message
    WEBAPP_REGENERATE = "webapp_regenerate"  # re-triggered from the Mini App


class User(Base):
    __tablename__ = "users"

    # Telegram user ID / chat ID is used as the primary identifier
    chat_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, index=True, autoincrement=False
    )

    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    username: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.chat_id,  # Scopes directly to frontend's expected me.id field
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "photo_url": self.photo_url,
            "created_at": self.created_at.isoformat(),
        }


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("chat_id", "name", name="uq_supplier_chat_name"),
    )

    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship(
        back_populates="supplier"
    )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "chat_id": self.chat_id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
        }


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Telegram private-chat id == user id for DMs, which is what both the
    # bot handler and the Mini App auth use to scope history per user.
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)

    po_id: Mapped[str] = mapped_column(Text, index=True, nullable=False)

    # NOTE: legacy denormalized column, kept only so existing rows created
    # before the supplier relationship existed still resolve a name via the
    # fallback in `supplier_name` below. No code path writes to this anymore.
    # Safe to drop once historical data has been backfilled with supplier_id,
    # at which point this mapped_column AND the fallback line in the
    # `supplier_name` property must be removed together.
    supplier_name_text: Mapped[str | None] = mapped_column(
        "supplier_name", Text, nullable=True, index=True
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("suppliers.id"), nullable=True, index=True
    )
    items: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)

    supplier: Mapped["Supplier | None"] = relationship(
        back_populates="purchase_orders", lazy="selectin"
    )

    status: Mapped[POStatus] = mapped_column(
        Enum(POStatus, name="po_status", native_enum=True),
        default=POStatus.PENDING,
        nullable=False,
        index=True,
    )
    source: Mapped[POSource] = mapped_column(
        Enum(POSource, name="po_source", native_enum=True),
        default=POSource.TELEGRAM,
        nullable=False,
    )

    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    github_run_id: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Lets a "regenerate" flow keep a lineage back to the record it replaced.
    regenerated_from_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    @property
    def supplier_name(self) -> str:
        # Always prefer the live relationship so edits to a supplier's name
        # show up immediately on every PO that references it.
        supplier_obj = self.__dict__.get("supplier")
        if isinstance(supplier_obj, Supplier):
            return supplier_obj.name
        # Fallback only for legacy rows with no supplier_id link.
        return self.supplier_name_text or ""

    def to_dict(self) -> dict:
        created_at = self.created_at
        updated_at = self.updated_at
        status_value = self.status.value if self.status else None
        source_value = self.source.value if self.source else None

        return {
            "id": str(self.id),
            "chat_id": self.chat_id,
            "po_id": self.po_id,
            "supplier_id": str(self.supplier_id) if self.supplier_id else None,
            "supplier_name": self.supplier_name,
            "items": self.items,
            "status": status_value,
            "source": source_value,
            "error_message": self.error_message,
            "file_url": self.file_url,
            "created_at": created_at.isoformat() if created_at else None,
            "updated_at": updated_at.isoformat() if updated_at else None,
        }
