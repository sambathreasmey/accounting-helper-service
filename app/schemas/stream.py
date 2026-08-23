from pydantic import BaseModel

from app.db.models import StreamStatus


class StreamStatusUpdateRequest(BaseModel):
    status: StreamStatus


class StreamCallbackStream(BaseModel):
    label: str
    resolution: str
    width: int
    height: int
    raw_tag: str
    source_url: str | None = None


class StreamCallbackRequest(BaseModel):
    request_id: str
    page_url: str
    success: bool
    streams: list[StreamCallbackStream] = []
    error: str | None = None
