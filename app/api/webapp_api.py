import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import InvalidToken, decode_token
from app.db.crud import (
    create_po,
    dashboard_stats,
    delete_po,
    get_po,
    get_user_profile,
    list_pos,
    set_status,
)
from app.db.database import get_session
from app.db.models import POSource, POStatus
from app.schemas.po import RegeneratePORequest
from app.services.github_client import GitHubDispatchError, trigger_po_generate_workflow
from app.services.redis_client import cache_get, cache_invalidate_chat, cache_set

router = APIRouter(prefix="/api/webapp", tags=["Mini App"])

DASHBOARD_CACHE_TTL = 40
HISTORY_CACHE_TTL = 40

bearer_scheme = HTTPBearer(auto_error=False)
BearerToken = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_chat_id(
    credentials: BearerToken = None,
) -> int:
    """Resolves chat_id from a JWT access token (Authorization: Bearer ...)."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        return decode_token(credentials.credentials, expected_type="access")
    except InvalidToken as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/me")
async def get_me(
    session: SessionDep,
    chat_id: int = Depends(get_chat_id),
):
    """Fetches full authenticated Telegram profile information for the UI header."""
    user = await get_user_profile(session, chat_id=chat_id)

    if not user:
        return {
            "id": chat_id,
            "first_name": "",
            "last_name": None,
            "username": None,
            "photo_url": None,
        }

    return user.to_dict()


@router.get("/dashboard")
async def get_dashboard(
    session: SessionDep,
    chat_id: int = Depends(get_chat_id),
):
    cache_key = f"webapp:{chat_id}:dashboard"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    data = await dashboard_stats(session, chat_id=chat_id)
    await cache_set(cache_key, data, ex=DASHBOARD_CACHE_TTL)
    return data


@router.get("/history")
async def get_history(
    session: SessionDep,
    chat_id: int = Depends(get_chat_id),
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

    cache_key = f"webapp:{chat_id}:history:{status_filter or 'all'}:{page}:{page_size}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    rows, total = await list_pos(
        session,
        chat_id=chat_id,
        status=status_enum,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    result = {
        "items": [po.to_dict() for po in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
    await cache_set(cache_key, result, ex=HISTORY_CACHE_TTL)
    return result


@router.get("/po/{po_id}")
async def get_po_detail(
    po_id: uuid.UUID,
    session: SessionDep,
    chat_id: int = Depends(get_chat_id),
):
    po = await get_po(session, po_id)
    if po is None or po.chat_id != chat_id:
        raise HTTPException(status_code=404, detail="Not found")
    return po.to_dict()


@router.delete("/po/{po_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_po_detail(
    po_id: uuid.UUID,
    session: SessionDep,
    chat_id: int = Depends(get_chat_id),
):
    po = await get_po(session, po_id)
    if po is None or po.chat_id != chat_id:
        raise HTTPException(status_code=404, detail="Not found")

    await delete_po(session, po)
    await cache_invalidate_chat(chat_id)


@router.post("/po/{po_id}/regenerate")
async def regenerate_po(
    po_id: uuid.UUID,
    body: RegeneratePORequest,
    session: SessionDep,
    chat_id: int = Depends(get_chat_id),
):
    original = await get_po(session, po_id)
    if original is None or original.chat_id != chat_id:
        raise HTTPException(status_code=404, detail="Not found")

    items = [item.model_dump() for item in body.items]
    new_po = await create_po(
        session,
        chat_id=chat_id,
        po_id=body.po_id.strip(),
        supplier_name=body.supplier_name,
        items=items,
        source=POSource.WEBAPP_REGENERATE,
        regenerated_from_id=original.id,
    )
    await cache_invalidate_chat(chat_id)

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
        await cache_invalidate_chat(chat_id)
        raise HTTPException(status_code=502, detail=f"Dispatch failed: {exc}") from exc

    await cache_invalidate_chat(chat_id)
    return new_po.to_dict()
