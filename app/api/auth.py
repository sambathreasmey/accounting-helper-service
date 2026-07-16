from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.core.security import (
    InvalidInitData,
    InvalidToken,
    create_access_token,
    create_refresh_token,
    decode_token,
    validate_init_data,
)

router = APIRouter(prefix="/api/webapp/auth", tags=["Auth"])


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/telegram", response_model=TokenResponse)
async def auth_telegram(x_telegram_init_data: str | None = Header(default=None)):
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Missing X-Telegram-Init-Data")
    try:
        user = validate_init_data(x_telegram_init_data)
    except InvalidInitData as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    chat_id = int(user["id"])
    return TokenResponse(
        access_token=create_access_token(chat_id),
        refresh_token=create_refresh_token(chat_id),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    try:
        chat_id = decode_token(body.refresh_token, expected_type="refresh")
    except InvalidToken as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    return TokenResponse(
        access_token=create_access_token(chat_id),
        refresh_token=create_refresh_token(chat_id),
    )