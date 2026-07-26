import logging

from app.bot.parsers.po_parser import POParseError, parse_po_message
from app.db.crud import create_po
from app.db.database import async_session_maker
from app.bot.keyboards.po_keyboard import forward_message
from app.services.telegram_client import telegram_client

logger = logging.getLogger("bot.po_handler")


def looks_like_po_message(text: str) -> bool:
    """
    Cheap heuristic to route a message to the PO handler: any line starting
    with '-' looks like an item line ('- Description Qty Price$'), which
    only ever shows up in PO messages. Doesn't require a literal 'PO-'
    prefix, since PO codes can be arbitrary (e.g. '07', 'INV-42').
    """
    return any(line.strip().startswith("-") for line in text.strip().splitlines())


async def handle_po_message(
    chat_id: int, text: str, default_supplier_name: str | None = None
) -> None:
    try:
        orders = parse_po_message(text, default_supplier_name=default_supplier_name)
    except POParseError as exc:
        await telegram_client.send_message(
            chat_id,
            f"⚠️ Couldn't read that purchase order:\n{exc}\n\n"
            "Format:\n<Supplier Name> <PO-ID>\n- <Description> <Qty><Unit> <Price>$",
        )
        return

    async with async_session_maker() as session:
        for order in orders:
            supplier_name = order.supplier_name.strip() or default_supplier_name or ""
            po_record = await create_po(
                session,
                chat_id=chat_id,
                po_id="",
                supplier_name=supplier_name,
                items=[item.to_dict() for item in order.items],
                raw_text=text,
            )
            await telegram_client.send_message(
                chat_id,
                "✅ Drafted purchase order. Tap Confirm to choose a supplier and finish it.",
                reply_markup=forward_message(str(po_record.id), text),
            )
