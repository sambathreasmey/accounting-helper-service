import logging

from app.bot.keyboards.po_keyboard import forward_message
from app.bot.parsers.po_parser import POParseError, parse_po_message
from app.db.crud import create_po
from app.db.database import async_session_maker
from app.services.llm_client import call_llama
from app.services.telegram_client import telegram_client
from app.utils.otp import generate_otp

logger = logging.getLogger("bot.forward_handler")

DEFAULT_SUPPLIER_NAME = "Thai Hout"


def is_forwarded_message(message: dict) -> bool:
    """
    Detects whether an incoming Telegram message was forwarded.
    Covers both the new `forward_origin` (Bot API 7.0+) and the
    legacy forward_date / forward_from / forward_from_chat fields.
    """
    return any(
        key in message
        for key in (
            "forward_origin",
            "forward_date",
            "forward_from",
            "forward_from_chat",
        )
    )


def generate_clean_po(supplier_name: str, invoice_id: str, raw_items: str) -> str:
    """
    Formats the PO with a clean header (no brackets) and a bulleted list,
    ensuring the price is always at the end of the line and formatted as amount$.
    """
    system_message = (
        "You are a strict data entry assistant. "
        "Output the raw items into a structured list based on these rules:\n\n"
        f"1. HEADER RULE: Write the header exactly as '{supplier_name} {invoice_id}' (NO BRACKETS).\n"
        "2. FORMAT RULE: Every single item must follow this exact structure: '- [Item Name] [Quantity] [Price]'.\n"
        "3. ORDERING RULE: The Price MUST ALWAYS be at the very end of the line. If the raw text has the price "
        "before the quantity, you MUST rearrange the words.\n"
        "4. CURRENCY RULE: The price must ALWAYS be formatted as the number followed by the '$' symbol "
        "(e.g., '3.5$'). If the raw text says '$3.5', you MUST rewrite it as '3.5$'.\n"
        "5. PRESERVATION: Keep original spelling and units for everything else, just fix the order and "
        "currency format."
    )
    return call_llama(
        user_prompt=raw_items, system_prompt=system_message, temperature=0.1
    )


async def handle_forward_message(chat_id: int, message: dict) -> None:
    """
    Handles a forwarded message: builds a clean PO from the raw text via LLM,
    parses it into structured items (same parser the typed-PO flow uses),
    saves it to the DB as PENDING, and sends it back with a confirm/edit/forward
    keyboard. PO generation is NOT dispatched here -- that only happens once the
    user taps "Confirm" (see app/bot/handlers/callback_handler.py).
    """
    text = message.get("text") or message.get("caption") or ""
    if not text.strip():
        await telegram_client.send_message(
            chat_id,
            "⚠️ That forwarded message doesn't have any text I can turn into a PO.",
        )
        return

    supplier_name = DEFAULT_SUPPLIER_NAME
    invoice_id = generate_otp()

    po_data = generate_clean_po(supplier_name, invoice_id, text)

    try:
        orders = parse_po_message(po_data)
    except POParseError:
        logger.exception(
            "LLM-generated PO text failed to parse for chat_id=%s invoice_id=%s",
            chat_id,
            invoice_id,
        )
        await telegram_client.send_message(
            chat_id,
            "⚠️ I cleaned up the forwarded message but couldn't parse it into items. "
            "Please check the formatting and try forwarding it again, or type the PO manually.",
        )
        return

    # generate_clean_po is prompted to produce exactly one supplier/PO block,
    # so this should always be a single order.
    order = orders[0]
    items = [item.to_dict() for item in order.items]

    async with async_session_maker() as session:
        po_record = await create_po(
            session,
            chat_id=chat_id,
            po_id=invoice_id,
            supplier_name=supplier_name,
            items=items,
            raw_text=text,
        )

    res_msg = await telegram_client.send_message(
        chat_id,
        po_data,
        reply_markup=forward_message(str(po_record.id), po_data),
    )

    if not res_msg.get("ok"):
        logger.error(
            "Failed to send forwarded PO message for chat_id=%s: %s", chat_id, res_msg
        )
