import asyncio
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger("github.dispatch")

GITHUB_API_BASE = "https://api.github.com"
MAX_RETRIES = 180
RETRY_DELAY_SECONDS = 10


class GitHubDispatchError(Exception):
    """Raised when a repository_dispatch event could not be delivered."""


async def trigger_po_generate_workflow(chat_id: int, data: list[dict]) -> None:
    url = (
        f"{GITHUB_API_BASE}/repos/{settings.GITHUB_REPO_OWNER}/"
        f"{settings.GITHUB_REPO_NAME}/dispatches"
    )
    headers = {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    payload = {
        "event_type": "po-generate-trigger",
        "client_payload": {"chat_id": chat_id, "invitation_data": data},
    }

    last_error: str | None = None

    async with httpx.AsyncClient(timeout=15.0) as client:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code == 204:
                    logger.info("Workflow triggered for chat_id=%s", chat_id)
                    return

                last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                logger.warning("Attempt %s/%s failed: %s", attempt, MAX_RETRIES, last_error)

                if 400 <= response.status_code < 500:
                    break  # Client error — retrying won't help.

            except httpx.HTTPError as exc:
                last_error = str(exc)
                logger.warning("Attempt %s/%s error: %s", attempt, MAX_RETRIES, last_error)

            if attempt < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY_SECONDS)

    raise GitHubDispatchError(
        f"Failed to trigger po-generate-trigger after retries. Last error: {last_error}"
    )