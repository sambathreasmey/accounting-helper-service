import time

_TTL_SECONDS = 600  # 10 minutes to reply with the correction before it expires

# chat_id -> (po_id, expires_at)
_pending: dict[int, tuple[str, float]] = {}
_pending_supplier: dict[int, tuple[str, float]] = {}


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


def set_pending_supplier(chat_id: int, supplier_name: str) -> None:
    _pending_supplier[chat_id] = (supplier_name, time.monotonic() + _TTL_SECONDS)


def pop_pending_supplier(chat_id: int) -> str | None:
    entry = _pending_supplier.pop(chat_id, None)
    if entry is None:
        return None
    supplier_name, expires_at = entry
    if time.monotonic() > expires_at:
        return None
    return supplier_name


_pending_stream_urls: dict[tuple[int, str], str] = {}


def set_pending_stream_url(user_msg_id: int, resolution: str, url: str) -> None:
    _pending_stream_urls[(user_msg_id, resolution)] = url


def pop_pending_stream_url(user_msg_id: int, resolution: str) -> str | None:
    return _pending_stream_urls.pop((user_msg_id, resolution), None)
