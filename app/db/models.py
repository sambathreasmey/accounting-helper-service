import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Enum, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

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


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Telegram private-chat id == user id for DMs, which is what both the
    # bot handler and the Mini App auth use to scope history per user.
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)

    po_id: Mapped[str] = mapped_column(Text, index=True, nullable=False)
    supplier_name: Mapped[str] = mapped_column(Text, nullable=False)
    items: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)

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

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "chat_id": self.chat_id,
            "po_id": self.po_id,
            "supplier_name": self.supplier_name,
            "items": self.items,
            "status": self.status.value,
            "source": self.source.value,
            "error_message": self.error_message,
            "file_url": self.file_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
