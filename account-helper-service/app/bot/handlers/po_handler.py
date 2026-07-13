import logging

from app.bot.parsers.po_parser import POParseError, parse_po_message
from app.core.config import settings
from app.db.crud import create_po, get_po, set_status
from app.db.database import async_session_maker
from app.db.models import POStatus
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
        "I'll message you again once it's done. You can also track progress "
        "and browse past orders in the dashboard.",
        **_dashboard_kwargs(),
    )

    async with async_session_maker() as session:
        for order in orders:
            po_record = await create_po(
                session,
                chat_id=chat_id,
                po_id=order.po_id,
                supplier_name=order.supplier_name,
                items=[item.to_dict() for item in order.items],
                raw_text=text,
            )
            await _dispatch(session, po_record.id, chat_id, order)


async def _dispatch(session, po_db_id, chat_id: int, order) -> None:
    data = [order.to_dict()]
    try:
        await trigger_po_generate_workflow(chat_id, data, str(po_db_id))
        po = await get_po(session, po_db_id)
        await set_status(session, po, POStatus.DISPATCHED)
    except GitHubDispatchError as exc:
        logger.exception("PO generation dispatch failed for chat_id=%s", chat_id)
        po = await get_po(session, po_db_id)
        await set_status(session, po, POStatus.FAILED, error_message=str(exc))
        await telegram_client.send_message(
            chat_id,
            f"❌ Something went wrong triggering PO generation for {order.po_id}. "
            "Please try again shortly, or regenerate it from the dashboard.",
            **_dashboard_kwargs(),
        )
        if settings.ALERT_CHAT_ID:
            await telegram_client.send_message(
                settings.ALERT_CHAT_ID,
                f"🚨 GitHub dispatch failed for chat_id={chat_id} po={order.po_id}: {exc}",
            )


def _dashboard_kwargs() -> dict:
    """reply_markup kwarg for a 'Open Dashboard' button, or {} if no Mini App is configured."""
    if not settings.MINI_APP_URL:
        return {}
    return {
        "reply_markup": {
            "inline_keyboard": [
                [
                    {
                        "text": "📊 Open Dashboard",
                        "web_app": {"url": settings.MINI_APP_URL},
                    }
                ]
            ]
        }
    }
