import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from app.core.config import settings
from datetime import datetime, timedelta, timezone
import uuid
import jwt
from jwt import PyJWTError

INIT_DATA_MAX_AGE_SECONDS = 24 * 60 * 60  # Telegram WebApp sessions are short-lived


class InvalidInitData(Exception):
    """Raised when Telegram WebApp initData fails validation."""


def validate_init_data(init_data: str) -> dict:
    """
    Validates the `initData` string a Telegram Mini App sends on every
    request, per https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

    Returns the parsed Telegram user dict on success.
    """
    if not init_data:
        raise InvalidInitData("Missing initData")

    parsed = dict(parse_qsl(init_data, strict_parsing=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise InvalidInitData("initData missing hash")

    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(parsed.items())
    )

    secret_key = hmac.new(
        b"WebAppData", settings.TELEGRAM_BOT_TOKEN.encode(), hashlib.sha256
    ).digest()
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise InvalidInitData("initData hash mismatch")

    auth_date = int(parsed.get("auth_date", 0))
    if time.time() - auth_date > INIT_DATA_MAX_AGE_SECONDS:
        raise InvalidInitData("initData expired")

    user_raw = parsed.get("user")
    if not user_raw:
        raise InvalidInitData("initData missing user")

    return json.loads(user_raw)


class InvalidToken(Exception):
    pass


def create_access_token(chat_id: int) -> str:
    now = datetime.now(time.timezone.utc)
    payload = {
        "sub": str(chat_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES),
        "type": "access",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(chat_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(chat_id),
        "iat": now,
        "exp": now + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, expected_type: str = "access") -> int:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except PyJWTError as exc:
        raise InvalidToken(str(exc)) from exc
    if payload.get("type") != expected_type:
        raise InvalidToken("Wrong token type")
    try:
        return int(payload["sub"])
    except (KeyError, ValueError) as exc:
        raise InvalidToken("Malformed subject") from exc