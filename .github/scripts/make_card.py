import os
import re
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------- ENVIRONMENT VARIABLES ----------
overall_ok = os.environ.get("OVERALL_OK", "true").lower() == "true"
project = os.environ.get("PROJECT", "accounting-helper-service")
environment = os.environ.get("ENVIRONMENT", "Production")
branch = os.environ.get("BRANCH", "main")
short_sha = os.environ.get("SHORT_SHA", "9cae8ad")
author = os.environ.get("AUTHOR", "Sambath Reasmey")
commit_msg = os.environ.get("COMMIT_MSG", "cicd update")
lint_result = os.environ.get("LINT_RESULT", "success")
lint_duration = os.environ.get("LINT_DURATION", "4s")
deploy_result = os.environ.get("DEPLOY_RESULT", "success")
deploy_duration = os.environ.get("DEPLOY_DURATION", "18s")
timestamp = os.environ.get("TIMESTAMP", "23-Jul-2026 | 03:21 PM UTC")
avatar_path = os.environ.get("AVATAR_PATH", "")

# ---------- SCALING ----------
# Design is authored in logical "base" pixels (as if the card were 1000x640).
# SS = internal supersample factor used only for crisp anti-aliasing while drawing.
# FINAL_SCALE = the actual output multiplier requested (2x normal resolution).
# Every literal pixel value below is wrapped in S() so proportions stay correct
# regardless of how big the internal canvas is -- this is what was missing before.
BASE_W, BASE_H = 1000, 640
SS = 4
FINAL_SCALE = 2


def S(v):
    return int(round(v * SS))


W, H = BASE_W * SS, BASE_H * SS

# ---------- MODERN PALETTE ----------
bg_top, bg_bottom = (18, 16, 28), (10, 8, 18)
card_bg = (28, 24, 43)
card_bg_hi = (38, 33, 58)
card_border = (58, 50, 85)
text_bright = (255, 255, 255)
text_muted = (162, 152, 190)
divider = (48, 41, 72)

mint = (52, 211, 153)
coral = (248, 113, 113)
gray_skip = (130, 125, 140)
sun = (251, 191, 36)
sky = (56, 189, 248)
lilac = (192, 132, 252)

if overall_ok:
    accent = mint
    banner_text, banner_icon = "ALL GOOD", "check"
else:
    accent = coral
    banner_text, banner_icon = "NEEDS ATTENTION", "cross"


# ---------- HELPERS ----------
def parse_seconds(dur):
    if not dur:
        return None
    m = re.match(r"(?:(\d+)m)?(?:(\d+)s)?", dur.strip())
    if not m or (not m.group(1) and not m.group(2)):
        return None
    minutes = int(m.group(1)) if m.group(1) else 0
    seconds = int(m.group(2)) if m.group(2) else 0
    return minutes * 60 + seconds


def format_seconds(total):
    m, s = divmod(total, 60)
    return f"{m}m {s}s" if m else f"{s}s"


def truncate_to_width(draw, text, font, max_width):
    if draw.textlength(text, font=font) <= max_width:
        return text
    ellipsis = "..."
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        candidate = text[:mid] + ellipsis
        if draw.textlength(candidate, font=font) <= max_width:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo] + ellipsis


lint_s = parse_seconds(lint_duration)
deploy_s = parse_seconds(deploy_duration)
total_s = (
    (lint_s or 0) + (deploy_s or 0)
    if (lint_s is not None or deploy_s is not None)
    else None
)

# ---------- BASE CANVAS + GRADIENT ----------
img = Image.new("RGBA", (W, H))
draw_grad = ImageDraw.Draw(img)
for yy in range(H):
    t = yy / H
    r = int(bg_top[0] + (bg_bottom[0] - bg_top[0]) * t)
    g = int(bg_top[1] + (bg_bottom[1] - bg_top[1]) * t)
    b = int(bg_top[2] + (bg_bottom[2] - bg_top[2]) * t)
    draw_grad.line([(0, yy), (W, yy)], fill=(r, g, b, 255))

# ambient glow blobs, positioned proportionally to canvas size
blob_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bd = ImageDraw.Draw(blob_layer)
bd.ellipse([S(-100), S(-100), S(300), S(300)], fill=lilac + (35,))
bd.ellipse([W - S(300), S(-80), W - S(-100), S(320)], fill=sky + (28,))
bd.ellipse([S(-80), H - S(240), S(300), H + S(110)], fill=accent + (32,))
blob_layer = blob_layer.filter(ImageFilter.GaussianBlur(S(28)))
img.paste(blob_layer, (0, 0), blob_layer)

# ---------- FONTS ----------
FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def get_font(path, size):
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, path), S(size))
    except Exception:
        return ImageFont.load_default()


f_title = get_font("DejaVuSans-Bold.ttf", 38)
f_sub = get_font("DejaVuSans-Bold.ttf", 21)
f_body = get_font("DejaVuSans.ttf", 23)
f_body_bold = get_font("DejaVuSans-Bold.ttf", 23)
f_small = get_font("DejaVuSans.ttf", 18)
f_label = get_font("DejaVuSans-Bold.ttf", 16)
f_banner = get_font("DejaVuSans-Bold.ttf", 23)
f_avatar = get_font("DejaVuSans-Bold.ttf", 27)
f_footer = get_font("DejaVuSans-Bold.ttf", 17)

# ---------- CARD CONTAINER ----------
pad = S(50)
card_box = [pad, pad, W - pad, H - pad]

shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow)
sd.rounded_rectangle([pad, pad + S(8), W - pad, H - pad + S(8)], radius=S(28), fill=(0, 0, 0, 150))
shadow = shadow.filter(ImageFilter.GaussianBlur(S(16)))
img.paste(shadow, (0, 0), shadow)

draw = ImageDraw.Draw(img, "RGBA")
draw.rounded_rectangle(card_box, radius=S(28), fill=card_bg, outline=card_border, width=S(2))


# ---------- VECTOR ICONS ----------
def draw_check(d, cx, cy, r, color, weight):
    d.line(
        [(cx - r * 0.5, cy), (cx - r * 0.1, cy + r * 0.4), (cx + r * 0.5, cy - r * 0.4)],
        fill=color, width=weight, joint="curve",
    )


def draw_cross(d, cx, cy, r, color, weight):
    d.line([(cx - r * 0.4, cy - r * 0.4), (cx + r * 0.4, cy + r * 0.4)], fill=color, width=weight)
    d.line([(cx - r * 0.4, cy + r * 0.4), (cx + r * 0.4, cy - r * 0.4)], fill=color, width=weight)


def draw_dash(d, cx, cy, r, color, weight):
    d.line([(cx - r * 0.4, cy), (cx + r * 0.4, cy)], fill=color, width=weight)


def draw_branch_icon(d, x, y, size, color):
    w = max(2, S(2))
    dot_r = max(2, size * 0.09)
    cx = x + size * 0.3
    d.line([(cx, y + size * 0.15), (cx, y + size * 0.85)], fill=color, width=w)
    d.ellipse([cx - dot_r, y + size * 0.08, cx + dot_r, y + size * 0.08 + dot_r * 2], outline=color, width=w)
    d.ellipse([cx - dot_r, y + size * 0.78, cx + dot_r, y + size * 0.78 + dot_r * 2], outline=color, width=w)
    bx = x + size * 0.72
    by = y + size * 0.4
    d.ellipse([bx - dot_r, by - dot_r, bx + dot_r, by + dot_r], outline=color, width=w)
    d.line([(cx, y + size * 0.5), (bx, by)], fill=color, width=w)


def draw_person_icon(d, x, y, size, color):
    w = max(2, S(2))
    d.ellipse([x + size * 0.3, y + size * 0.08, x + size * 0.7, y + size * 0.48], outline=color, width=w)
    d.arc([x + size * 0.12, y + size * 0.42, x + size * 0.88, y + size * 1.02], 200, 340, fill=color, width=w)


def draw_message_icon(d, x, y, size, color):
    w = max(2, S(2))
    d.rounded_rectangle(
        [x + size * 0.08, y + size * 0.14, x + size * 0.92, y + size * 0.72],
        radius=size * 0.08, outline=color, width=w,
    )
    d.polygon(
        [(x + size * 0.26, y + size * 0.72), (x + size * 0.16, y + size * 0.94), (x + size * 0.46, y + size * 0.72)],
        fill=color,
    )


def draw_clock_icon(d, x, y, size, color):
    w = max(2, S(2))
    d.ellipse([x, y, x + size, y + size], outline=color, width=w)
    cx, cy = x + size / 2, y + size / 2
    d.line([(cx, cy), (cx, cy - size * 0.3)], fill=color, width=w)
    d.line([(cx, cy), (cx + size * 0.25, cy)], fill=color, width=w)


def draw_bolt_icon(d, x, y, size, color):
    pts = [
        (x + size * 0.55, y), (x + size * 0.15, y + size * 0.55), (x + size * 0.45, y + size * 0.55),
        (x + size * 0.4, y + size), (x + size * 0.85, y + size * 0.4), (x + size * 0.55, y + size * 0.4),
    ]
    d.polygon(pts, fill=color)


# ---------- STATUS BANNER ----------
bbox = draw.textbbox((0, 0), banner_text, font=f_banner)
text_w = bbox[2] - bbox[0]
banner_h = S(46)
banner_w = text_w + S(66)
banner_x, banner_y = pad + S(24), pad + S(24)

draw.rounded_rectangle([banner_x, banner_y, banner_x + banner_w, banner_y + banner_h], radius=banner_h // 2, fill=accent)
icon_cx = banner_x + S(26)
icon_cy = banner_y + banner_h / 2
if banner_icon == "check":
    draw_check(draw, icon_cx, icon_cy, S(11), card_bg, weight=S(4))
else:
    draw_cross(draw, icon_cx, icon_cy, S(9), card_bg, weight=S(4))

draw.text(
    (banner_x + S(46), banner_y + (banner_h - (bbox[3] - bbox[1])) / 2 - bbox[1]),
    banner_text, font=f_banner, fill=card_bg,
)

# ---------- AVATAR (top right, with colored status ring) ----------
avatar_d = S(70)
avatar_x = W - pad - S(24) - avatar_d
avatar_y = pad + S(20)
ring_pad = S(4)

draw.ellipse(
    [avatar_x - ring_pad, avatar_y - ring_pad, avatar_x + avatar_d + ring_pad, avatar_y + avatar_d + ring_pad],
    fill=accent,
)

avatar_drawn = False
if avatar_path and os.path.exists(avatar_path):
    try:
        av = Image.open(avatar_path).convert("RGB").resize((avatar_d, avatar_d), Image.LANCZOS)
        mask = Image.new("L", (avatar_d, avatar_d), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, avatar_d, avatar_d], fill=255)
        img.paste(av, (avatar_x, avatar_y), mask)
        avatar_drawn = True
    except Exception:
        avatar_drawn = False

if not avatar_drawn:
    initials = (author[:2] if len(author) <= 2 else author[0] + author.split()[-1][0]).upper()
    draw.ellipse([avatar_x, avatar_y, avatar_x + avatar_d, avatar_y + avatar_d], fill=card_bg_hi)
    ibbox = draw.textbbox((0, 0), initials, font=f_avatar)
    tw, th = ibbox[2] - ibbox[0], ibbox[3] - ibbox[1]
    draw.text(
        (avatar_x + (avatar_d - tw) / 2, avatar_y + (avatar_d - th) / 2 - ibbox[1]),
        initials, font=f_avatar, fill=text_bright,
    )

# ---------- PROJECT & ENVIRONMENT ----------
y_curr = pad + S(88)
draw.text((pad + S(24), y_curr), project, font=f_title, fill=text_bright)
y_curr += S(48)

env_dot_r = S(5)
draw.ellipse([pad + S(24), y_curr + S(9), pad + S(24) + env_dot_r * 2, y_curr + S(9) + env_dot_r * 2], fill=accent)
draw.text((pad + S(24) + env_dot_r * 2 + S(10), y_curr), environment, font=f_sub, fill=accent)
y_curr += S(42)

draw.line([pad + S(24), y_curr, W - pad - S(24), y_curr], fill=divider, width=max(1, S(1)))
y_curr += S(26)

# ---------- METADATA ----------
row_h = S(38)
label_col_w = S(150)
value_max_w = W - pad - S(24) - (pad + S(24) + label_col_w) - S(24)

meta_rows = [
    ("Branch", f"{branch}  \u00b7  {short_sha}", draw_branch_icon),
    ("Author", author, draw_person_icon),
    ("Message", f"\u201c{commit_msg}\u201d", draw_message_icon),
]

for label, val, icon_fn in meta_rows:
    icon_fn(draw, pad + S(24), y_curr, S(20), text_muted)
    draw.text((pad + S(58), y_curr + S(1)), label, font=f_label, fill=text_muted)
    display_val = truncate_to_width(draw, val, f_body, value_max_w)
    draw.text((pad + S(24) + label_col_w, y_curr - S(2)), display_val, font=f_body, fill=text_bright)
    y_curr += row_h

y_curr += S(10)
draw.line([pad + S(24), y_curr, W - pad - S(24), y_curr], fill=divider, width=max(1, S(1)))
y_curr += S(26)


# ---------- JOB PILLS ----------
def draw_job_pill(x, y, w, h, label, result, duration):
    ok = result == "success"
    color = mint if ok else coral if result == "failure" else gray_skip

    draw.rounded_rectangle([x, y, x + w, y + h], radius=S(16), fill=card_bg_hi, outline=card_border, width=max(1, S(1)))

    circle_d = S(28)
    cx, cy = x + S(32), y + h / 2
    draw.ellipse([cx - circle_d / 2, cy - circle_d / 2, cx + circle_d / 2, cy + circle_d / 2], fill=color)
    if ok:
        draw_check(draw, cx, cy, S(8), card_bg, weight=S(3))
    elif result == "failure":
        draw_cross(draw, cx, cy, S(7), card_bg, weight=S(3))
    else:
        draw_dash(draw, cx, cy, S(7), card_bg, weight=S(3))

    text_x = x + S(60)
    draw.text((text_x, y + S(13)), label, font=f_body_bold, fill=text_bright)
    status_text = duration if ok else result.capitalize()
    draw.text((text_x, y + S(41)), status_text, font=f_small, fill=text_muted)


pill_gap = S(18)
pill_h = S(70)
pill_w = (W - pad * 2 - S(48) - pill_gap) // 2
draw_job_pill(pad + S(24), y_curr, pill_w, pill_h, "Lint", lint_result, lint_duration)
draw_job_pill(pad + S(24) + pill_w + pill_gap, y_curr, pill_w, pill_h, "Deploy", deploy_result, deploy_duration)

y_curr += pill_h + S(26)

# ---------- FOOTER ----------
footer_h = S(36)

ts_bbox = draw.textbbox((0, 0), timestamp, font=f_footer)
ts_w = (ts_bbox[2] - ts_bbox[0]) + S(52)
draw.rounded_rectangle(
    [pad + S(24), y_curr, pad + S(24) + ts_w, y_curr + footer_h], radius=footer_h // 2, fill=card_bg_hi,
)
draw_clock_icon(draw, pad + S(36), y_curr + S(9), S(17), sky)
draw.text(
    (pad + S(60), y_curr + (footer_h - (ts_bbox[3] - ts_bbox[1])) / 2 - ts_bbox[1]),
    timestamp, font=f_footer, fill=text_bright,
)

if total_s is not None:
    dur_str = f"{format_seconds(total_s)} total"
    dur_bbox = draw.textbbox((0, 0), dur_str, font=f_footer)
    dur_w = (dur_bbox[2] - dur_bbox[0]) + S(52)
    dur_x = pad + S(24) + ts_w + S(12)
    draw.rounded_rectangle([dur_x, y_curr, dur_x + dur_w, y_curr + footer_h], radius=footer_h // 2, fill=card_bg_hi)
    draw_bolt_icon(draw, dur_x + S(13), y_curr + S(9), S(17), sun)
    draw.text(
        (dur_x + S(38), y_curr + (footer_h - (dur_bbox[3] - dur_bbox[1])) / 2 - dur_bbox[1]),
        dur_str, font=f_footer, fill=text_bright,
    )

# ---------- DOWNSAMPLE FOR CRISP FINAL OUTPUT AT REQUESTED 2x RESOLUTION ----------
final_w, final_h = BASE_W * FINAL_SCALE, BASE_H * FINAL_SCALE
img = img.convert("RGB").resize((final_w, final_h), Image.LANCZOS)
img.save("card.png")
