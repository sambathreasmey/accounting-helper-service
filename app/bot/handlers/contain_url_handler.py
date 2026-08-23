import logging
import re
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.bot.keyboards.stream_keyboard import build_stream_quality_keyboard
from app.services.edit_state import set_pending_stream_url
from app.services.telegram_client import telegram_client

logger = logging.getLogger("bot.contain_link_handler")

URL_REGEX = re.compile(r"https?://\S+")


def is_contain_link_message(text: str) -> bool:
    return bool(URL_REGEX.search(text))


async def get_streams(page_url: str) -> list[dict[str, str]]:

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/151.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": page_url,
    }

    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers=headers,
    ) as client:
        response = await client.get(page_url)
        response.raise_for_status()

    print("STATUS:", response.status_code)
    print("FINAL URL:", response.url)
    print("CONTENT TYPE:", response.headers.get("content-type"))
    print("CONTENT LENGTH:", len(response.text))

    soup = BeautifulSoup(response.text, "html.parser")

    # Find ALL preload links
    preload_links = soup.find_all(
        "link",
        rel=lambda value: value and "preload" in value,
        href=True,
    )

    print("PRELOAD LINKS:", len(preload_links))

    for index, link in enumerate(preload_links):
        href = str(link.get("href"))

        print(f"\n--- PRELOAD {index} ---")
        print("RAW HREF:", href)

        full_url = urljoin(str(response.url), href)

        print("FULL URL:", full_url)

        # Look for m3u8
        if ".m3u8" in full_url.lower():
            print("✅ M3U8 FOUND")

            streams = parse_m3u8_resolutions(full_url)

            if streams:
                return streams

    print("❌ No usable m3u8 preload found")

    # Extra debugging:
    # Search the entire HTML for m3u8
    m3u8_matches = re.findall(
        r'https?[^"\'<>\s]+\.m3u8[^"\'<>\s]*',
        response.text,
        re.IGNORECASE,
    )

    print("\nM3U8 URLs found directly in HTML:", len(m3u8_matches))

    for url in m3u8_matches[:10]:
        print(url)

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
