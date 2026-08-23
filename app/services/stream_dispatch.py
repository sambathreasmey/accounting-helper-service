import logging

import httpx

from app.core.config import settings
from app.services.edit_state import create_pending_stream_request

logger = logging.getLogger("services.stream_dispatch")


async def dispatch_get_streams(chat_id: int, user_msg_id: int, target_url: str) -> str:
    """
    Creates a pending-request record, then fires a repository_dispatch event
    that triggers the get-streams GitHub Action. Returns the request_id.
    """
    request_id = create_pending_stream_request(chat_id, user_msg_id, target_url)

    url = f"https://api.github.com/repos/{settings.GITHUB_REPO}/dispatches"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {
        "event_type": "get-streams",
        "client_payload": {
            "page_url": target_url,
            "request_id": request_id,
            "callback_url": f"{settings.PUBLIC_BASE_URL}/api/external/streams/callback",
        },
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, json=payload, headers=headers)

    if resp.status_code != 204:
        logger.error("repository_dispatch failed: %s %s", resp.status_code, resp.text)
        raise RuntimeError(f"Failed to dispatch GitHub Action: {resp.status_code}")

    return request_id
