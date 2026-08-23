def build_stream_quality_keyboard(
    streams: list[dict[str, str]], user_msg_id: int
) -> dict:
    """Generates inline buttons containing label, resolution, and user_msg_id.

    Format: "stream_select:<label>:<resolution>:<user_message_id>"
    """
    inline_keyboard = []

    for stream in streams:
        label = stream["label"]  # e.g., "FHD"
        res = stream["resolution"]  # e.g., "1920x1080"

        button_text = f"🎬 {label} ({res})"
        callback_data = f"stream_select:{label}:{res}:{user_msg_id}"

        inline_keyboard.append([{"text": button_text, "callback_data": callback_data}])

    return {"inline_keyboard": inline_keyboard}
