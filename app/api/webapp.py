from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import InvalidToken, decode_token
# ...your other existing imports stay as-is

bearer_scheme = HTTPBearer(auto_error=False)


async def get_chat_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> int:
    """Resolves chat_id from a JWT access token (Authorization: Bearer ...)."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        return decode_token(credentials.credentials, expected_type="access")
    except InvalidToken as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
