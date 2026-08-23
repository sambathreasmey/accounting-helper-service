from pydantic import BaseModel

from app.db.models import StreamStatus


class StreamStatusUpdateRequest(BaseModel):
    status: StreamStatus
