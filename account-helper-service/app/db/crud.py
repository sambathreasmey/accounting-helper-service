import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import POSource, POStatus, PurchaseOrder


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
    po = PurchaseOrder(
        chat_id=chat_id,
        po_id=po_id,
        supplier_name=supplier_name,
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
