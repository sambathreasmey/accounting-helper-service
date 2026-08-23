import logging
import re

from app.bot.keyboards.stream_keyboard import build_stream_quality_keyboard
from app.services.edit_state import set_pending_stream_url
from app.services.stream_dispatch import dispatch_get_streams
from app.services.telegram_client import telegram_client

logger = logging.getLogger("bot.contain_link_handler")

URL_REGEX = re.compile(r"https?://\S+")


def is_contain_link_message(text: str) -> bool:
    return bool(URL_REGEX.search(text))


async def handle_contain_link_message(chat_id: int, message: dict) -> None:
    text = message.get("text", "")
    user_msg_id = message["message_id"]
    match = URL_REGEX.search(text)

    if not match:
        await telegram_client.send_message(
            chat_id, "Please send a valid link (starting with http:// or https://)."
        )
        return

    target_url = match.group(0)

    try:
        await dispatch_get_streams(chat_id, user_msg_id, target_url)
    except Exception:
        logger.exception("Failed to dispatch stream fetch for %s", target_url)
        await telegram_client.send_message(
            chat_id, "⚠️ Couldn't start fetching stream qualities. Please try again."
        )
        return

    await telegram_client.send_message(
        chat_id, "🔎 Fetching available stream qualities, one moment…"
    )


async def send_stream_quality_picker(
    chat_id: int, user_msg_id: int, streams: list[dict[str, str]], target_url: str
) -> None:
    """Called from the /streams/callback endpoint once the GitHub Action reports back."""
    for stream in streams:
        set_pending_stream_url(user_msg_id, stream["resolution"], target_url)

    keyboard = build_stream_quality_keyboard(streams, user_msg_id)
    await telegram_client.send_message(
        chat_id=chat_id,
        text="🎥 <b>Available Stream Qualities:</b>\nPlease select a resolution below:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
