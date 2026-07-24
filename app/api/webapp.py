from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import InvalidToken, decode_token

bearer_scheme = HTTPBearer(auto_error=False)
BearerToken = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


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
