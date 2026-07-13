from app.core.config import settings
from app.services.telegram_client import telegram_client


def _webapp_kwargs() -> dict:
    if not settings.MINI_APP_URL:
        return {}
    return {
        "reply_markup": {
            "inline_keyboard": [
                [
                    {
                        "text": "📊 Open Dashboard",
                        "web_app": {"url": settings.MINI_APP_URL},
                    }
                ]
            ]
        }
    }


async def handle_default_message(chat_id: int, text: str) -> None:
    if text == "/start":
        await telegram_client.send_message(
            chat_id,
            "👋 Welcome! Send me a purchase order like:\n"
            "Thai Hout PO-00001\n- Noodle 5kg 2.50$\n\n"
            "Open the dashboard below to see your PO history, track status, "
            "and regenerate orders with edits.",
            **_webapp_kwargs(),
        )
        return

    if text == "/dashboard":
        if not settings.MINI_APP_URL:
            await telegram_client.send_message(
                chat_id, "The dashboard isn't configured yet."
            )
            return
        await telegram_client.send_message(
            chat_id, "📊 Your dashboard:", **_webapp_kwargs()
        )
        return

    await telegram_client.send_message(chat_id, f"You said: {text}")
