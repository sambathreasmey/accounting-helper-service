from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException  # Added Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession  # Added AsyncSession

from app.core.security import (
    InvalidInitData,
    InvalidToken,
    create_access_token,
    create_refresh_token,
    decode_token,
    validate_init_data,
)
from app.db.crud import upsert_user_profile
from app.db.database import get_session

router = APIRouter(prefix="/api/webapp/auth", tags=["Auth"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/telegram", response_model=TokenResponse)
async def auth_telegram(
    session: SessionDep,
    x_telegram_init_data: Annotated[str | None, Header()] = None,
):
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Missing X-Telegram-Init-Data")

    try:
        user_data = validate_init_data(x_telegram_init_data)
    except InvalidInitData as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    chat_id = int(user_data["id"])

    # 2. Extract and save/update the user's latest Telegram profile data
    await upsert_user_profile(
        session,
        chat_id=chat_id,
        first_name=user_data.get("first_name", ""),
        last_name=user_data.get("last_name"),
        username=user_data.get("username"),
        photo_url=user_data.get("photo_url"),
    )

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
