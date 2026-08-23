import logging
import uuid

from app.core.config import settings
from app.db.crud import (
    build_po_id_for_supplier,
    create_stream_request,
    finalize_po,
    get_po,
)
from app.db.database import async_session_maker
from app.db.models import POStatus
from app.services.edit_state import (
    pop_pending_stream_url,
    set_pending_edit,
    set_pending_supplier,
)
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

    action = data.split(":", 1)[0]
    if action not in {
        "po_confirm",
        "po_edit",
        "po_forward",
        "supplier_select",
        "supplier_page",
        "stream_select",
    }:
        logger.warning("Malformed callback_data: %r", data)
        await telegram_client.answer_callback_query(
            callback_id, text="Invalid action.", show_alert=True
        )
        return

    if action == "stream_select":
        await _handle_stream_select(callback_id, callback_query, data)
        return

    if action in {"supplier_select", "supplier_page"}:
        if action == "supplier_select":
            await _handle_supplier_select(callback_id, chat_id, data)
        else:
            await _handle_supplier_page(callback_id, chat_id, data)
        return

    try:
        _, po_id_str = data.split(":", 1)
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
        elif action == "supplier_select":
            await _handle_supplier_select(callback_id, chat_id, data)
        elif action == "supplier_page":
            await _handle_supplier_page(callback_id, chat_id, data)
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

    await telegram_client.answer_callback_query(callback_id, text="Choose a supplier…")

    from app.bot.handlers.default_handler import _send_supplier_picker

    await _send_supplier_picker(chat_id, page=1, po_db_id=str(po.id))


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


async def _handle_supplier_select(callback_id: str, chat_id: int, data: str) -> None:
    parts = data.split(":", 2)
    if len(parts) >= 2:
        _, supplier_name = parts[0], parts[1]
    else:
        await telegram_client.answer_callback_query(
            callback_id, text="Invalid supplier selection."
        )
        return

    if len(parts) == 3:
        po_id_str = parts[2]
        try:
            po_db_id = uuid.UUID(po_id_str)
        except ValueError:
            await telegram_client.answer_callback_query(
                callback_id, text="Invalid PO reference."
            )
            return

        async with async_session_maker() as session:
            po = await get_po(session, po_db_id)
            if po is None:
                await telegram_client.answer_callback_query(
                    callback_id, text="PO not found."
                )
                return

            po_code = await build_po_id_for_supplier(
                session, chat_id=chat_id, supplier_name=supplier_name
            )
            po = await finalize_po(
                session,
                po,
                chat_id=chat_id,
                supplier_name=supplier_name,
                po_id=po_code,
            )
            data_payload = [
                {
                    "supplier_name": po.supplier_name,
                    "po_id": po.po_id,
                    "items": po.items,
                }
            ]
            await dispatch_po_generation(
                session, po.id, chat_id, po.po_id, data_payload
            )

        await telegram_client.answer_callback_query(
            callback_id, text=f"PO finalized for {supplier_name}."
        )
        return

    set_pending_supplier(chat_id, supplier_name)
    await telegram_client.answer_callback_query(
        callback_id,
        text=f"Supplier set to {supplier_name}. Send your next PO and I’ll use it.",
    )


async def _handle_supplier_page(callback_id: str, chat_id: int, data: str) -> None:
    parts = data.split(":", 2)
    if len(parts) < 2:
        await telegram_client.answer_callback_query(callback_id, text="Invalid page.")
        return

    try:
        page = int(parts[1])
    except ValueError:
        await telegram_client.answer_callback_query(callback_id, text="Invalid page.")
        return

    po_db_id = parts[2] if len(parts) == 3 else None

    from app.bot.handlers.default_handler import _send_supplier_picker

    await _send_supplier_picker(chat_id, page=page, po_db_id=po_db_id)
    await telegram_client.answer_callback_query(callback_id, text="Loading suppliers…")


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


async def _handle_stream_select(
    callback_id: str, callback_query: dict, data: str
) -> None:
    """Persists the stream selection (url + resolution), then deletes both
    the original link message and the button keyboard message."""
    parts = data.split(":", 3)
    if len(parts) < 4:
        await telegram_client.answer_callback_query(
            callback_id, text="Invalid selection format.", show_alert=True
        )
        return

    selected_label = parts[1]  # e.g., "FHD"
    selected_resolution = parts[2]  # e.g., "1920x1080"
    user_msg_id = int(parts[3])  # Original user message ID

    message = callback_query["message"]
    chat_id = message["chat"]["id"]
    bot_msg_id = message["message_id"]  # Bot message ID (with buttons)

    # 1. Answer callback popup
    await telegram_client.answer_callback_query(
        callback_id, text=f"Selected quality: {selected_label} ({selected_resolution})"
    )

    # 2. Recover the URL stashed for this user_msg_id + resolution
    url = pop_pending_stream_url(user_msg_id, selected_resolution)
    if not url:
        logger.warning(
            "No pending URL found for user_msg_id %s, resolution %s",
            user_msg_id,
            selected_resolution,
        )
        await telegram_client.answer_callback_query(
            callback_id,
            text="This request expired. Please resend the link.",
            show_alert=True,
        )
        return

    # 3. Persist the selection
    async with async_session_maker() as session:
        stream = await create_stream_request(
            session,
            chat_id=chat_id,
            url=url,
            label=selected_label,
            resolution=selected_resolution,
            user_msg_id=user_msg_id,
            bot_msg_id=bot_msg_id,
        )

    # 4. Delete the user's original message (with link)
    try:
        await telegram_client.delete_message(chat_id=chat_id, message_id=user_msg_id)
    except Exception as exc:
        logger.warning("Could not delete user message %s: %s", user_msg_id, exc)

    # 5. Delete the bot's message (containing buttons)
    try:
        await telegram_client.delete_message(chat_id=chat_id, message_id=bot_msg_id)
    except Exception as exc:
        logger.warning("Could not delete bot message %s: %s", bot_msg_id, exc)

    # 6. Proceed with application logic (e.g. notify or start streaming task)
    await telegram_client.send_message(
        chat_id=chat_id,
        text=f"✅ Processing <b>{selected_label} ({selected_resolution})</b> stream (ref: {stream.id})...",
        parse_mode="HTML",
    )
