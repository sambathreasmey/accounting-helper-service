import logging
import uuid

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
    chat_id = callback_query["message"]["chat"]["id"]

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
            await _handle_forward(callback_id, po)
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


async def _handle_forward(callback_id: str, po) -> None:
    """
    Fastest path for the user: Telegram's own native forward action
    (long-press the message, or tap the ⋮ menu, then choose "Forward")
    already lets them send this PO to any chat or group -- no extra
    typing, no custom chat picker needed.
    """
    await telegram_client.answer_callback_query(
        callback_id,
        text="Long-press the message above (or tap ⋮) and choose 'Forward' to send it anywhere.",
        show_alert=True,
    )
