import logging
import re
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.stream_keyboard import build_stream_quality_keyboard
from app.db.crud import get_all_streams_validate_name
from app.services.crypto import decrypt_url
from app.services.edit_state import set_pending_stream_url
from app.services.stream_dispatch import dispatch_get_streams
from app.services.telegram_client import telegram_client

logger = logging.getLogger("bot.contain_link_handler")

URL_REGEX = re.compile(r"https?://\S+")


def is_contain_link_message(text: str) -> bool:
    return bool(URL_REGEX.search(text))


async def handle_contain_link_message(
    session: AsyncSession, chat_id: int, message: dict
) -> None:
    text = message.get("text", "")
    user_msg_id = message["message_id"]
    match = URL_REGEX.search(text)

    if not match:
        return

    target_url = match.group(0)

    decripted_whitelist_domain = decrypt_url(
        "gAAAAABqv6WEWClIXY5yTr5XQ16rYNHA16IxxB0CrgzT-F1zEg7lUjlFknaW_pCIIgdvNvSspD_tF8cUHx64JeJ3DHwZpuRrVA=="
    )
    parsed_url = urlparse(target_url)
    if (
        parsed_url.netloc != decripted_whitelist_domain
        and not parsed_url.netloc.endswith("." + decripted_whitelist_domain)
    ):
        return
    await telegram_client.delete_message(chat_id=chat_id, message_id=user_msg_id)

    # 2. Extract video name from URL
    new_video_name = extract_video_name(target_url)

    # 3. Fetch all streams ONLY for the current chat_id to check duplicates
    existing_streams = await get_all_streams_validate_name(session, limit=None)
    existing_filenames = [
        decrypt_url((s.url or "").strip())
        for s in existing_streams
        if s.url is not None
    ]

    # 4. Check for duplication
    if is_video_duplicate(new_video_name, existing_filenames):
        await telegram_client.send_message(
            chat_id,
            "⚠️ This video link has already been added. Please send a different link.",
        )
        return

    # 5. Dispatch stream task
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


def extract_video_name(url_or_name: str) -> str:
    """Helper function to cleanly extract and normalize a video identifier/name."""
    url_or_name = url_or_name.strip().lower()

    # If it's a full URL, extract the video segment
    if url_or_name.startswith(("http://", "https://")):
        path = urlparse(url_or_name).path
        segments = [s for s in path.split("/") if s]
        if segments:
            # Take the last segment of the URL path
            url_or_name = segments[-1]

    # Clean file extensions if present (e.g., .mp4, .mkv)
    url_or_name = re.sub(r"\.(mp4|mkv|avi|mov|flv|webm)$", "", url_or_name)

    # Standardize whitespace and hyphens
    url_or_name = re.sub(r"[\s_]+", "-", url_or_name)

    return url_or_name


def is_video_duplicate(new_video: str, existing_videos: list[str]) -> bool:
    """
    Safely checks if a video name or URL is a duplicate against an existing list.

    :param new_video: The new video URL or name to check.
    :param existing_videos: List of existing video URLs or names.
    :return: True if duplicate, False otherwise.
    """
    if not new_video or not isinstance(new_video, str):
        return False

    target_name = extract_video_name(new_video)

    # Fast set lookup on normalized names
    normalized_existing = {
        extract_video_name(vid) for vid in existing_videos if isinstance(vid, str)
    }

    return target_name in normalized_existing


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
