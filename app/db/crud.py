import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import POSource, POStatus, PurchaseOrder, Supplier, User


async def upsert_user_profile(
    session: AsyncSession,
    *,
    chat_id: int,
    first_name: str,
    last_name: str | None = None,
    username: str | None = None,
    photo_url: str | None = None,
) -> User:
    """Saves or updates profile details received from Telegram Mini App auth."""
    query = select(User).where(User.chat_id == chat_id)
    result = await session.execute(query)
    user = result.scalars().first()

    if user:
        # Update existing records to capture profile updates or changed photo URLs
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.photo_url = photo_url
    else:
        # Create user record if accessing for the first time
        user = User(
            chat_id=chat_id,
            first_name=first_name,
            last_name=last_name,
            username=username,
            photo_url=photo_url,
        )
        session.add(user)

    await session.commit()
    await session.refresh(user)
    return user


async def get_user_profile(session: AsyncSession, chat_id: int) -> User | None:
    """Fetches a user profile by their Telegram chat id."""
    query = select(User).where(User.chat_id == chat_id)
    result = await session.execute(query)
    return result.scalars().first()


async def create_supplier(
    session: AsyncSession,
    *,
    chat_id: int,
    name: str,
) -> Supplier:
    normalized_name = " ".join(name.split()).strip()
    if not normalized_name:
        raise ValueError("Supplier name cannot be empty")

    query = select(Supplier).where(
        Supplier.chat_id == chat_id, Supplier.name == normalized_name
    )
    result = await session.execute(query)
    existing = result.scalars().first()
    if existing:
        return existing

    supplier = Supplier(chat_id=chat_id, name=normalized_name)
    session.add(supplier)
    await session.commit()
    await session.refresh(supplier)
    return supplier


async def get_supplier(
    session: AsyncSession, supplier_id: uuid.UUID
) -> Supplier | None:
    return await session.get(Supplier, supplier_id)


async def list_suppliers(
    session: AsyncSession,
    *,
    chat_id: int,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Supplier], int]:
    query = (
        select(Supplier)
        .where(Supplier.chat_id == chat_id)
        .order_by(Supplier.name.asc())
        .limit(limit)
        .offset(offset)
    )
    count_query = (
        select(func.count()).select_from(Supplier).where(Supplier.chat_id == chat_id)
    )

    total = (await session.execute(count_query)).scalar_one()
    rows = (await session.execute(query)).scalars().all()
    return list(rows), total


async def delete_supplier(session: AsyncSession, supplier: Supplier) -> None:
    await session.delete(supplier)
    await session.commit()


async def create_po(
    session: AsyncSession,
    *,
    chat_id: int,
    po_id: str,
    supplier_name: str,
    items: list[dict],
    source: POSource = POSource.TELEGRAM,
    raw_text: str | None = None,
    regenerated_from_id: uuid.UUID | None = None,
) -> PurchaseOrder:
    supplier = await create_supplier(session, chat_id=chat_id, name=supplier_name)
    po = PurchaseOrder(
        chat_id=chat_id,
        po_id=po_id,
        supplier_id=supplier.id,
        items=items,
        source=source,
        raw_text=raw_text,
        regenerated_from_id=regenerated_from_id,
        status=POStatus.PENDING,
    )
    session.add(po)
    await session.commit()
    await session.refresh(po)
    return po


async def set_status(
    session: AsyncSession,
    po: PurchaseOrder,
    status: POStatus,
    *,
    error_message: str | None = None,
    file_url: str | None = None,
    github_run_id: str | None = None,
) -> PurchaseOrder:
    po.status = status
    if error_message is not None:
        po.error_message = error_message
    if file_url is not None:
        po.file_url = file_url
    if github_run_id is not None:
        po.github_run_id = github_run_id
    await session.commit()
    await session.refresh(po)
    return po


async def get_po(session: AsyncSession, po_uuid: uuid.UUID) -> PurchaseOrder | None:
    return await session.get(PurchaseOrder, po_uuid)


async def delete_po(session: AsyncSession, po: PurchaseOrder) -> None:
    await session.delete(po)
    await session.commit()


async def list_pos(
    session: AsyncSession,
    *,
    chat_id: int,
    status: POStatus | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[PurchaseOrder], int]:
    query = select(PurchaseOrder).where(PurchaseOrder.chat_id == chat_id)
    count_query = (
        select(func.count())
        .select_from(PurchaseOrder)
        .where(PurchaseOrder.chat_id == chat_id)
    )

    if status is not None:
        query = query.where(PurchaseOrder.status == status)
        count_query = count_query.where(PurchaseOrder.status == status)

    query = query.order_by(PurchaseOrder.created_at.desc()).limit(limit).offset(offset)

    total = (await session.execute(count_query)).scalar_one()
    rows = (await session.execute(query)).scalars().all()
    return list(rows), total


async def dashboard_stats(session: AsyncSession, *, chat_id: int) -> dict:
    query = (
        select(PurchaseOrder.status, func.count())
        .where(PurchaseOrder.chat_id == chat_id)
        .group_by(PurchaseOrder.status)
    )
    rows = (await session.execute(query)).all()
    counts = {status.value: 0 for status in POStatus}
    for status, count in rows:
        counts[status.value] = count

    recent, _ = await list_pos(session, chat_id=chat_id, limit=5)
    return {
        "counts": counts,
        "total": sum(counts.values()),
        "recent": [po.to_dict() for po in recent],
    }


async def update_po_content(
    session: AsyncSession,
    po: PurchaseOrder,
    *,
    items: list[dict],
    raw_text: str | None = None,
) -> PurchaseOrder:
    po.items = items
    if raw_text is not None:
        po.raw_text = raw_text
    po.status = POStatus.PENDING
    po.error_message = None
    await session.commit()
    await session.refresh(po)
    return po
