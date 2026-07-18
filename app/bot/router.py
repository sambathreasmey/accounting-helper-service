import logging

from app.bot.handlers.callback_handler import handle_callback_query
from app.bot.handlers.default_handler import handle_default_message
from app.bot.handlers.forward_handler import (
    handle_forward_message,
    is_forwarded_message,
)
from app.bot.handlers.po_handler import handle_po_message, looks_like_po_message

logger = logging.getLogger("bot.router")


async def handle_update(update: dict) -> None:
    try:
        callback_query = update.get("callback_query")
        if callback_query:
            await handle_callback_query(callback_query)
            return

        message = update.get("message")
        if not message:
            return

        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        if is_forwarded_message(message):
            await handle_forward_message(chat_id, message)
        elif looks_like_po_message(text):
            await handle_po_message(chat_id, text)
        else:
            await handle_default_message(chat_id, text)
    except Exception:
        logger.exception(
            "Unhandled error processing update %s", update.get("update_id")
        )
