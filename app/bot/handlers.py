import logging

from app.services.telegram_client import telegram_client

logger = logging.getLogger("telegram.bot")


async def handle_update(update: dict) -> None:
    message = update.get("message")
    if not message:
        return

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    try:
        if text == "/start":
            await telegram_client.send_message(
                chat_id, "👋 Welcome! I'm up and running."
            )
        else:
            await telegram_client.send_message(chat_id, f"You said: {text}")
    except Exception:
        logger.exception("Failed to handle update %s", update.get("update_id"))
