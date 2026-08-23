import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import get_all_streams, get_stream, update_stream_status
from app.db.database import get_session
from app.db.models import StreamStatus
from app.schemas.stream import StreamStatusUpdateRequest

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
