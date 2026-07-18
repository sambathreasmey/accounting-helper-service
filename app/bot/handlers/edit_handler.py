import logging
import uuid

from app.bot.handlers.forward_handler import generate_clean_po
from app.bot.keyboards.po_keyboard import forward_message
from app.bot.parsers.po_parser import POParseError, parse_po_message
from app.db.crud import get_po, update_po_content
from app.db.database import async_session_maker
from app.services.telegram_client import telegram_client

logger = logging.getLogger("bot.edit_handler")


async def handle_po_edit_reply(chat_id: int, po_id: str, raw_text: str) -> None:
    """
    Called when a user replies with corrected text after tapping "Edit" on
    a PO. Regenerates the PO from the corrected text (same LLM cleanup +
    parser as the initial forward flow), updates the existing DB record,
    and sends a fresh confirm/edit/forward message.
    """
    try:
        po_db_id = uuid.UUID(po_id)
    except ValueError:
        logger.warning("Malformed pending-edit po_id: %r", po_id)
        return

    if not raw_text.strip():
        await telegram_client.send_message(
            chat_id, "⚠️ That message was empty — nothing to edit."
        )
        return

    async with async_session_maker() as session:
        po = await get_po(session, po_db_id)
        if po is None:
            await telegram_client.send_message(
                chat_id, "⚠️ Couldn't find the PO to edit anymore."
            )
            return

        po_data = generate_clean_po(po.supplier_name, po.po_id, raw_text)

        try:
            orders = parse_po_message(po_data)
        except POParseError:
            logger.error(
                "Edited PO text failed to parse for chat_id=%s po_id=%s.\n"
                "--- LLM output start ---\n%s\n--- LLM output end ---",
                chat_id,
                po.po_id,
                po_data,
            )
            await telegram_client.send_message(
                chat_id,
                "⚠️ I cleaned up your correction but couldn't parse it into items. "
                "Please check the formatting and try again.",
            )
            return

        order = orders[0]
        items = [item.to_dict() for item in order.items]

        po = await update_po_content(session, po, items=items, raw_text=raw_text)
        po_uuid_str = str(po.id)

    res_msg = await telegram_client.send_message(
        chat_id,
        po_data,
        reply_markup=forward_message(po_uuid_str, po_data),
    )
    if not res_msg.get("ok"):
        logger.error(
            "Failed to send updated PO message for chat_id=%s: %s", chat_id, res_msg
        )
