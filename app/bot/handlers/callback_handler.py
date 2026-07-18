import logging
import uuid

from app.core.config import settings
from app.db.crud import get_po
from app.db.database import async_session_maker
from app.db.models import POStatus
from app.services.edit_state import set_pending_edit
from app.services.po_dispatch import dispatch_po_generation
from app.services.telegram_client import telegram_client

logger = logging.getLogger("bot.callback_handler")


async def handle_callback_query(callback_query: dict) -> None:
    """
    Handles taps on the inline keyboard attached to a PO message
    (see app/bot/keyboards/po_keyboard.py). callback_data is formatted
    as "<action>:<po_id>", e.g. "po_confirm:3fa85f64-....".
    """
    callback_id = callback_query["id"]
    data = callback_query.get("data", "")
    message = callback_query["message"]
    chat_id = message["chat"]["id"]

    try:
        action, po_id_str = data.split(":", 1)
        po_db_id = uuid.UUID(po_id_str)
    except (ValueError, KeyError):
        logger.warning("Malformed callback_data: %r", data)
        await telegram_client.answer_callback_query(
            callback_id, text="Invalid action.", show_alert=True
        )
        return

    async with async_session_maker() as session:
        po = await get_po(session, po_db_id)
        if po is None:
            await telegram_client.answer_callback_query(
                callback_id, text="PO not found.", show_alert=True
            )
            return

        if action == "po_confirm":
            await _handle_confirm(callback_id, session, po, chat_id)
        elif action == "po_edit":
            await _handle_edit(callback_id, po, chat_id)
        elif action == "po_forward":
            await _handle_forward(callback_id, po, message)
        else:
            logger.warning("Unknown callback action: %r", action)
            await telegram_client.answer_callback_query(
                callback_id, text="Unknown action.", show_alert=True
            )


async def _handle_confirm(callback_id: str, session, po, chat_id: int) -> None:
    if po.status != POStatus.PENDING:
        await telegram_client.answer_callback_query(
            callback_id, text=f"This PO is already {po.status.value}."
        )
        return

    await telegram_client.answer_callback_query(
        callback_id, text="Dispatching PO generation…"
    )

    data_payload = [
        {"supplier_name": po.supplier_name, "po_id": po.po_id, "items": po.items}
    ]
    await dispatch_po_generation(session, po.id, chat_id, po.po_id, data_payload)


async def _handle_edit(callback_id: str, po, chat_id: int) -> None:
    """
    Marks this chat as "mid-edit" for this PO. The next plain-text message
    the user sends in this chat is picked up by the router (before normal
    routing) and passed to app/bot/handlers/edit_handler.py.
    """
    set_pending_edit(chat_id, str(po.id))
    await telegram_client.answer_callback_query(
        callback_id, text="Reply with the corrected PO text to edit it."
    )


async def _handle_forward(callback_id: str, po, message: dict) -> None:
    """
    One-tap forward: sends this PO message straight to a fixed configured
    chat (settings.FORWARD_CHAT_ID), e.g. a warehouse/supplier group --
    no manual long-press or chat picker needed from the user.
    """
    if not settings.FORWARD_CHAT_ID:
        await telegram_client.answer_callback_query(
            callback_id,
            text="No forward destination is configured yet (settings.FORWARD_CHAT_ID).",
            show_alert=True,
        )
        return

    from_chat_id = message["chat"]["id"]
    message_id = message["message_id"]

    try:
        await telegram_client.forward_message(
            chat_id=settings.FORWARD_CHAT_ID,
            from_chat_id=from_chat_id,
            message_id=message_id,
        )
    except Exception:
        logger.exception("Failed to forward PO %s to FORWARD_CHAT_ID", po.po_id)
        await telegram_client.answer_callback_query(
            callback_id,
            text="Couldn't forward this PO. Please try again.",
            show_alert=True,
        )
        return

    await telegram_client.answer_callback_query(callback_id, text="Forwarded ✅")
