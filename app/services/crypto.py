from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

_fernet = Fernet(settings.STREAM_URL_ENCRYPTION_KEY.encode())


def encrypt_url(url: str) -> str:
    return _fernet.encrypt(url.encode()).decode()


def decrypt_url(token: str) -> str | None:
    try:
        return _fernet.decrypt(token.encode()).decode()
    except InvalidToken:
        return None
