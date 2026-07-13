import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import InvalidInitData, validate_init_data
from app.db.crud import create_po, dashboard_stats, get_po, list_pos, set_status
from app.db.database import get_session
from app.db.models import POSource, POStatus
from app.schemas.po import RegeneratePORequest
from app.services.github_client import GitHubDispatchError, trigger_po_generate_workflow

router = APIRouter(prefix="/api/webapp", tags=["Mini App"])


async def get_chat_id(x_telegram_init_data: str | None = Header(default=None)) -> int:
    """
    Validates the Telegram WebApp `initData` sent by the Mini App on every
    request and returns the user's id, which doubles as the chat_id for
    the private chat between the user and the bot.
    """
    if not x_telegram_init_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Telegram-Init-Data",
        )
    try:
        user = validate_init_data(x_telegram_init_data)
    except InvalidInitData as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
    return int(user["id"])


@router.get("/dashboard")
async def get_dashboard(
    chat_id: int = Depends(get_chat_id),
    session: AsyncSession = Depends(get_session),
):
    return await dashboard_stats(session, chat_id=chat_id)


@router.get("/history")
async def get_history(
    chat_id: int = Depends(get_chat_id),
    session: AsyncSession = Depends(get_session),
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    status_enum = None
    if status_filter:
        try:
            status_enum = POStatus(status_filter)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status filter")

    rows, total = await list_pos(
        session,
        chat_id=chat_id,
        status=status_enum,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    return {
        "items": [po.to_dict() for po in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/po/{po_id}")
async def get_po_detail(
    po_id: uuid.UUID,
    chat_id: int = Depends(get_chat_id),
    session: AsyncSession = Depends(get_session),
):
    po = await get_po(session, po_id)
    if po is None or po.chat_id != chat_id:
        raise HTTPException(status_code=404, detail="Not found")
    return po.to_dict()


@router.post("/po/{po_id}/regenerate")
async def regenerate_po(
    po_id: uuid.UUID,
    body: RegeneratePORequest,
    chat_id: int = Depends(get_chat_id),
    session: AsyncSession = Depends(get_session),
):
    """
    Creates a fresh history record from edited items and re-dispatches the
    generation workflow. The original record is left untouched for audit
    history; the new one links back via `regenerated_from_id`.
    """
    original = await get_po(session, po_id)
    if original is None or original.chat_id != chat_id:
        raise HTTPException(status_code=404, detail="Not found")

    items = [item.model_dump() for item in body.items]
    new_po = await create_po(
        session,
        chat_id=chat_id,
        po_id=original.po_id,
        supplier_name=body.supplier_name,
        items=items,
        source=POSource.WEBAPP_REGENERATE,
        regenerated_from_id=original.id,
    )

    order_payload = {
        "supplier_name": new_po.supplier_name,
        "po_id": new_po.po_id,
        "items": items,
    }

    try:
        await trigger_po_generate_workflow(chat_id, [order_payload], str(new_po.id))
        await set_status(session, new_po, POStatus.DISPATCHED)
    except GitHubDispatchError as exc:
        await set_status(session, new_po, POStatus.FAILED, error_message=str(exc))
        raise HTTPException(status_code=502, detail=f"Dispatch failed: {exc}") from exc

    return new_po.to_dict()
