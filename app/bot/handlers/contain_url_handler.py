import logging
import re

import httpx
from bs4 import BeautifulSoup

from app.bot.keyboards.stream_keyboard import build_stream_quality_keyboard
from app.services.edit_state import set_pending_stream_url
from app.services.telegram_client import telegram_client

logger = logging.getLogger("bot.contain_link_handler")

URL_REGEX = re.compile(r"https?://\S+")


def is_contain_link_message(text: str) -> bool:
    return bool(URL_REGEX.search(text))


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


async def get_streams(page_url: str) -> list[dict[str, str]]:
    async with httpx.AsyncClient(
        timeout=20.0,
        follow_redirects=True,
        headers=HEADERS,
    ) as client:
        response = await client.get(page_url)

    print("STATUS:", response.status_code)
    print("FINAL URL:", response.url)
    print("CONTENT TYPE:", response.headers.get("content-type"))
    print("CONTENT LENGTH:", len(response.text))

    soup = BeautifulSoup(response.text, "html.parser")

    # Look at every preload
    for link in soup.find_all("link", rel="preload"):
        print(
            "PRELOAD:",
            link.get("as"),
            link.get("type"),
            link.get("href"),
        )

    # Search directly for m3u8
    if ".m3u8" in response.text:
        print("✅ m3u8 exists in raw HTML")
    else:
        print("❌ No m3u8 in raw HTML")

    return []


def parse_m3u8_resolutions(url: str) -> list[dict[str, str]]:
    multi_match = re.search(r"multi=([^/]+)", url)
    if not multi_match:
        return []

    raw_multi = multi_match.group(1)
    matches = re.findall(r"(\d+)x(\d+):([^:]+):", raw_multi)

    results = []
    for width_str, height_str, raw_label in matches:
        width = int(width_str)
        height = int(height_str)

        if height >= 2160:
            quality_label = "4K"
        elif height >= 1440:
            quality_label = "2K"
        elif height >= 1080:
            quality_label = "FHD"
        elif height >= 720:
            quality_label = "HD"
        else:
            quality_label = "SD"

        results.append(
            {
                "label": quality_label,
                "resolution": f"{width}x{height}",
                "width": width,
                "height": height,
                "raw_tag": raw_label,
            }
        )

    return results


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
    streams = await get_streams(target_url)

    if not streams:
        await telegram_client.send_message(
            chat_id, "⚠️ No playable resolutions found in the provided link."
        )
        return

    await _send_stream_quality_picker(chat_id, user_msg_id, streams, target_url)


async def _send_stream_quality_picker(
    chat_id: int, user_msg_id: int, streams: list[dict[str, str]], target_url: str
) -> None:
    for stream in streams:
        set_pending_stream_url(user_msg_id, stream["resolution"], target_url)

    keyboard = build_stream_quality_keyboard(streams, user_msg_id)
    await telegram_client.send_message(
        chat_id=chat_id,
        text="🎥 <b>Available Stream Qualities:</b>\nPlease select a resolution below:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
