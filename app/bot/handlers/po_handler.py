import logging

from app.bot.parsers.po_parser import POParseError, parse_po_message
from app.core.config import settings
from app.services.github_client import GitHubDispatchError, trigger_po_generate_workflow
from app.services.telegram_client import telegram_client

logger = logging.getLogger("bot.po_handler")


def looks_like_po_message(text: str) -> bool:
    """Cheap heuristic to route a message to the PO handler."""
    return "PO-" in text.upper()


async def handle_po_message(chat_id: int, text: str) -> None:
    try:
        orders = parse_po_message(text)
    except POParseError as exc:
        await telegram_client.send_message(
            chat_id,
            f"⚠️ Couldn't read that purchase order:\n{exc}\n\n"
            "Format:\n<Supplier Name> <PO-ID>\n- <Description> <Qty><Unit> <Price>$",
        )
        return

    summary = "\n".join(f"• {o.po_id} ({o.supplier_name})" for o in orders)
    await telegram_client.send_message(
        chat_id,
        f"✅ Got it! Generating {len(orders)} purchase order(s):\n{summary}\n\n"
        "I'll message you again once it's done.",
    )

    data = [order.to_dict() for order in orders]

    try:
        await trigger_po_generate_workflow(chat_id, data)
    except GitHubDispatchError as exc:
        logger.exception("PO generation dispatch failed for chat_id=%s", chat_id)
        await telegram_client.send_message(
            chat_id,
            "❌ Something went wrong triggering PO generation. Please try again shortly.",
        )
        if settings.ALERT_CHAT_ID:
            await telegram_client.send_message(
                settings.ALERT_CHAT_ID,
                f"🚨 GitHub dispatch failed for chat_id={chat_id}: {exc}",
            )