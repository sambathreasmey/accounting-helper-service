import logging

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status

from app.bot.handlers import handle_update
from app.core.config import settings
from app.services.redis_client import is_duplicate_update

logger = logging.getLogger("telegram.webhook")
router = APIRouter(prefix="/telegram", tags=["Telegram"])


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid secret token")

    update = await request.json()
    update_id = update.get("update_id")

    if update_id is not None and await is_duplicate_update(update_id):
        logger.info("Duplicate update %s ignored", update_id)
        return {"ok": True}

    # Ack Telegram immediately — do real work after the response is sent.
    background_tasks.add_task(handle_update, update)
    return {"ok": True}