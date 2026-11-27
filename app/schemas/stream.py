from pydantic import BaseModel, ConfigDict, Field

from app.db.models import StreamStatus


class StreamStatusUpdateRequest(BaseModel):
    status: StreamStatus


class StreamSegments(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    segment_url: str = Field(alias="segmentUrl")
    segments_url: list[str] = Field(alias="segmentsUrl")


class StreamSegmentsUpdateRequest(BaseModel):
    segments: StreamSegments


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
