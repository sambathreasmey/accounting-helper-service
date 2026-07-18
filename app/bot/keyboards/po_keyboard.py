def forward_message(po_id: str, po_data: str) -> dict:
    """
    Builds the Telegram inline keyboard (reply_markup) attached to a
    generated PO message, allowing the user to confirm/forward/edit it.

    `po_id` is the PurchaseOrder's own primary key (as a string), not the
    chat id — the callback handler needs to look up *this* PO specifically,
    and a chat can have multiple pending POs at once.
    """
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Confirm", "callback_data": f"po_confirm:{po_id}"},
                {"text": "✏️ Edit", "callback_data": f"po_edit:{po_id}"},
            ],
            [
                {"text": "📤 Forward", "callback_data": f"po_forward:{po_id}"},
            ],
        ]
    }
