import httpx

from app.core.config import settings

TELEGRAM_API_BASE = "https://api.telegram.org"


class TelegramClient:
    def __init__(self, token: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=f"{TELEGRAM_API_BASE}/bot{token}",
            timeout=10.0,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def set_webhook(self, url: str, secret_token: str) -> dict:
        response = await self._client.post(
            "/setWebhook",
            json={
                "url": url,
                "secret_token": secret_token,
                "drop_pending_updates": True,
                "allowed_updates": ["message", "callback_query"],
            },
        )
        response.raise_for_status()
        return response.json()

    async def send_message(self, chat_id: int, text: str, **kwargs) -> dict:
        response = await self._client.post(
            "/sendMessage", json={"chat_id": chat_id, "text": text, **kwargs}
        )
        response.raise_for_status()
        return response.json()


telegram_client = TelegramClient(settings.TELEGRAM_BOT_TOKEN)
