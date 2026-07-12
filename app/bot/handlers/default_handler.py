from app.services.telegram_client import telegram_client


async def handle_default_message(chat_id: int, text: str) -> None:
    if text == "/start":
        await telegram_client.send_message(
            chat_id,
            "👋 Welcome! Send me a purchase order like:\n"
            "Thai Hout PO-00001\n- Noodle 5kg 2.50$",
        )
        return
    await telegram_client.send_message(chat_id, f"You said: {text}")