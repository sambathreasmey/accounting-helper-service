import time

_TTL_SECONDS = 600  # 10 minutes to reply with the correction before it expires

# chat_id -> (po_id, expires_at)
_pending: dict[int, tuple[str, float]] = {}


def set_pending_edit(chat_id: int, po_id: str) -> None:
    _pending[chat_id] = (po_id, time.monotonic() + _TTL_SECONDS)


def pop_pending_edit(chat_id: int) -> str | None:
    """
    Returns and clears the pending po_id for this chat, if any and not expired.
    Returns None if there's no pending edit (or it expired), so callers can
    fall through to normal message routing.
    """
    entry = _pending.pop(chat_id, None)
    if entry is None:
        return None
    po_id, expires_at = entry
    if time.monotonic() > expires_at:
        return None
    return po_id
