from app.core.config import settings
from app.db.crud import list_suppliers
from app.db.database import async_session_maker
from app.services.telegram_client import telegram_client


def _webapp_kwargs() -> dict:
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


async def _send_supplier_picker(chat_id: int, page: int = 1) -> None:
    async with async_session_maker() as session:
        suppliers, total = await list_suppliers(
            session, chat_id=chat_id, limit=6, offset=(page - 1) * 6
        )

    if not suppliers:
        await telegram_client.send_message(
            chat_id,
            "No suppliers saved yet. Open the dashboard in Telegram to add and manage them, then choose one here.",
        )
        return

    keyboard = []
    for supplier in suppliers:
        keyboard.append(
            [
                {
                    "text": supplier.name,
                    "callback_data": f"supplier_select:{supplier.name}",
                }
            ]
        )

    nav_row = []
    if page > 1:
        nav_row.append({"text": "◀️ Prev", "callback_data": f"supplier_page:{page - 1}"})
    if (page * 6) < total:
        nav_row.append({"text": "Next ▶️", "callback_data": f"supplier_page:{page + 1}"})
    if nav_row:
        keyboard.append(nav_row)

    await telegram_client.send_message(
        chat_id,
        f"Choose a supplier for your next PO ({page}/{max(1, (total + 5) // 6)}):",
        markup={"inline_keyboard": keyboard},
    )


async def handle_default_message(chat_id: int, text: str) -> None:
    if text == "/start":
        await telegram_client.send_message(
            chat_id,
            "👋 Welcome! Send me a purchase order like:\n"
            "Thai Hout PO-00001\n- Noodle 5kg 2.50$\n\n"
            "Open the dashboard below to see your PO history, track status, "
            "and regenerate orders with edits.",
            **_webapp_kwargs(),
        )
        return

    if text == "/dashboard":
        if not settings.MINI_APP_URL:
            await telegram_client.send_message(
                chat_id, "The dashboard isn't configured yet."
            )
            return
        await telegram_client.send_message(
            chat_id, "📊 Your dashboard:", **_webapp_kwargs()
        )
        return

    if text == "/suppliers":
        await _send_supplier_picker(chat_id, page=1)
        return

    await telegram_client.send_message(chat_id, f"You said: {text}")
