import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.contain_url_handler import send_stream_quality_picker
from app.core.config import settings
from app.db.crud import (
    get_all_streams,
    get_stream,
    get_stream_by_id,
    update_stream_status,
)
from app.db.database import get_session
from app.db.models import StreamStatus
from app.schemas.stream import StreamCallbackRequest, StreamStatusUpdateRequest
from app.services.edit_state import pop_pending_stream_request

router = APIRouter(prefix="/api/external", tags=["External"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/streams")
async def get_streams_list(
    session: SessionDep,
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    status_enum = None
    if status_filter:
        try:
            status_enum = StreamStatus(status_filter)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status filter")

    rows = await get_all_streams(
        session,
        status=status_enum,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    return {
        "items": [stream.to_dict() for stream in rows],
        "page": page,
        "page_size": page_size,
    }


@router.get("/streams/{stream_id}")
async def get_stream_by_id_endpoint(
    stream_id: int,
    session: SessionDep,
):
    stream = await get_stream_by_id(session, stream_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")

    return stream.to_dict()


@router.patch("/streams/{stream_id}/status")
async def update_stream_status_entry(
    stream_id: uuid.UUID,
    body: StreamStatusUpdateRequest,
    session: SessionDep,
):
    stream = await get_stream(session, stream_id)
    if stream is None:
        raise HTTPException(status_code=404, detail="Not found")

    stream = await update_stream_status(session, stream_id, body.status)
    return stream.to_dict()


@router.post("/streams/callback")
async def streams_callback(
    body: StreamCallbackRequest,
    authorization: Annotated[str | None, Header()] = None,
):
    expected = f"Bearer {settings.STREAM_CALLBACK_TOKEN}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid callback token")

    pending = pop_pending_stream_request(body.request_id)
    if pending is None:
        # Either already handled, or an unrecognized/expired request_id
        raise HTTPException(status_code=404, detail="Unknown or expired request_id")

    from app.services.telegram_client import telegram_client

    chat_id = pending["chat_id"]
    user_msg_id = pending["user_msg_id"]
    target_url = pending["target_url"]

    if not body.success or not body.streams:
        await telegram_client.send_message(
            chat_id,
            "⚠️ No playable resolutions found in the provided link."
            if not body.error
            else f"⚠️ Couldn't fetch stream qualities: {body.error}",
        )
        return {"received": True, "forwarded": False}

    streams_dicts = [s.model_dump() for s in body.streams]
    await send_stream_quality_picker(chat_id, user_msg_id, streams_dicts, target_url)

    return {"received": True, "forwarded": True}
