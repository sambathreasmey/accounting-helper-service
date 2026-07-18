import logging

from app.core.config import settings
from app.db.crud import get_po, set_status
from app.db.models import POStatus
from app.services.github_client import GitHubDispatchError, trigger_po_generate_workflow
from app.services.redis_client import cache_invalidate_chat
from app.services.telegram_client import telegram_client

logger = logging.getLogger("bot.po_dispatch")


async def dispatch_po_generation(
    session, po_db_id, chat_id: int, po_id: str, data: list[dict]
) -> None:
    """
    Triggers the GitHub workflow that generates the PO file, updating
    status/cache and notifying the user (and the alert chat) on failure.

    Shared between the typed-PO flow (auto-dispatched on creation) and the
    forwarded-PO flow (only dispatched once the user taps "Confirm").
    """
    try:
        await trigger_po_generate_workflow(chat_id, data, str(po_db_id))
        po = await get_po(session, po_db_id)
        await set_status(session, po, POStatus.DISPATCHED)
        await cache_invalidate_chat(chat_id)
    except GitHubDispatchError as exc:
        logger.exception("PO generation dispatch failed for chat_id=%s", chat_id)
        po = await get_po(session, po_db_id)
        await set_status(session, po, POStatus.FAILED, error_message=str(exc))
        await cache_invalidate_chat(chat_id)
        await telegram_client.send_message(
            chat_id,
            f"❌ Something went wrong triggering PO generation for {po_id}. "
            "Please try again shortly, or regenerate it from the dashboard.",
        )
        if settings.ALERT_CHAT_ID:
            await telegram_client.send_message(
                settings.ALERT_CHAT_ID,
                f"🚨 GitHub dispatch failed for chat_id={chat_id} po={po_id}: {exc}",
            )
