import logging
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.crud import get_po, set_status
from app.db.database import get_session
from app.db.models import POStatus
from app.schemas.po import POCallbackRequest
from app.services.telegram_client import telegram_client

logger = logging.getLogger("po.callback")
router = APIRouter(prefix="/api/po", tags=["PO Callback"])


@router.post("/callback", status_code=status.HTTP_200_OK)
async def po_generation_callback(
    body: POCallbackRequest,
    session: AsyncSession = Depends(get_session),
    x_callback_secret: str | None = Header(default=None),
):
    """
    Called by the po-generate-automation GitHub Actions workflow once a
    document has been generated (or generation failed), so history reflects
    the final state instead of sitting at "dispatched" forever.
    """
    if x_callback_secret != settings.PO_CALLBACK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid secret"
        )

    try:
        po_uuid = uuid.UUID(body.po_db_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid po_db_id"
        )

    po = await get_po(session, po_uuid)
    if po is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PO not found"
        )

    if body.status not in (POStatus.COMPLETED.value, POStatus.FAILED.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status"
        )

    new_status = POStatus(body.status)
    await set_status(
        session,
        po,
        new_status,
        error_message=body.error_message,
        file_url=body.file_url,
        github_run_id=body.github_run_id,
    )

    if new_status is POStatus.COMPLETED:
        text = f"✅ {po.po_id} ({po.supplier_name}) is ready!"
        kwargs = {}
        if body.file_url:
            kwargs["reply_markup"] = {
                "inline_keyboard": [
                    [{"text": "📄 Open Document", "url": body.file_url}]
                ]
            }
        await telegram_client.send_message(po.chat_id, text, **kwargs)
    else:
        await telegram_client.send_message(
            po.chat_id,
            f"❌ Generation failed for {po.po_id} ({po.supplier_name}).\n"
            f"{body.error_message or 'Unknown error.'}\n"
            "You can edit and regenerate it from the dashboard.",
        )

    return {"ok": True}
