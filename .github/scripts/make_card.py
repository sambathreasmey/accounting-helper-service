import os
import re
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------- ENVIRONMENT VARIABLES ----------
overall_ok = os.environ.get("OVERALL_OK", "true").lower() == "true"
project = os.environ.get("PROJECT", "accounting-helper-service")
environment = os.environ.get("ENVIRONMENT", "Production")
branch = os.environ.get("BRANCH", "main")
short_sha = os.environ.get("SHORT_SHA", "9cae8ad")
author = os.environ.get("AUTHOR", "sambathreasmey")
commit_msg = os.environ.get("COMMIT_MSG", "cicd update")
lint_result = os.environ.get("LINT_RESULT", "success")
lint_duration = os.environ.get("LINT_DURATION", "4s")
deploy_result = os.environ.get("DEPLOY_RESULT", "success")
deploy_duration = os.environ.get("DEPLOY_DURATION", "18s")
timestamp = os.environ.get("TIMESTAMP", "23-Jul-2026 | 03:21 PM UTC")
avatar_path = os.environ.get("AVATAR_PATH", "")

# ---------- MODERN PALETTE ----------
bg_top, bg_bottom = (18, 16, 28), (10, 8, 18)
card_bg = (28, 24, 43)
card_bg_hi = (38, 33, 58)
card_border = (58, 50, 85)
text_bright = (255, 255, 255)
text_muted = (160, 150, 190)
divider = (48, 41, 72)

mint = (52, 211, 153)  # Success Accent
coral = (248, 113, 113)  # Failure Accent
gray_skip = (107, 114, 128)
sun = (251, 191, 36)  # Total Time / Accent
sky = (56, 189, 248)  # Clock / Accent
lilac = (192, 132, 252)

if overall_ok:
    accent, accent_glow = mint, mint
    banner_text, banner_icon = "ALL GOOD", "check"
else:
    accent, accent_glow = coral, coral
    banner_text, banner_icon = "NEEDS ATTENTION", "cross"


# ---------- HELPER FUNCTIONS ----------
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


lint_s = parse_seconds(lint_duration)
deploy_s = parse_seconds(deploy_duration)
total_s = (
    (lint_s or 0) + (deploy_s or 0)
    if (lint_s is not None or deploy_s is not None)
    else None
)

W, H = 1000, 640

# Base canvas & vertical background gradient
img = Image.new("RGBA", (W, H))
draw_grad = ImageDraw.Draw(img)
for yy in range(H):
    t = yy / H
    r = int(bg_top[0] + (bg_bottom[0] - bg_top[0]) * t)
    g = int(bg_top[1] + (bg_bottom[1] - bg_top[1]) * t)
    b = int(bg_top[2] + (bg_bottom[2] - bg_top[2]) * t)
    draw_grad.line([(0, yy), (W, yy)], fill=(r, g, b, 255))

# Soft ambient background glows
blob_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bd = ImageDraw.Draw(blob_layer)
bd.ellipse([-100, -100, 300, 300], fill=lilac + (35,))
bd.ellipse([700, -80, 1100, 320], fill=sky + (30,))
bd.ellipse([-80, 400, 300, 750], fill=accent_glow + (35,))
blob_layer = blob_layer.filter(ImageFilter.GaussianBlur(80))
img.paste(blob_layer, (0, 0), blob_layer)

# ---------- FONTS ----------
FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def get_font(path, size):
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, path), size)
    except Exception:
        return ImageFont.load_default()


f_title = get_font("DejaVuSans-Bold.ttf", 36)
f_sub = get_font("DejaVuSans-Bold.ttf", 20)
f_body = get_font("DejaVuSans.ttf", 22)
f_body_bold = get_font("DejaVuSans-Bold.ttf", 22)
f_small = get_font("DejaVuSans.ttf", 18)
f_label = get_font("DejaVuSans-Bold.ttf", 18)
f_banner = get_font("DejaVuSans-Bold.ttf", 24)
f_avatar = get_font("DejaVuSans-Bold.ttf", 28)
f_footer = get_font("DejaVuSans-Bold.ttf", 18)

# ---------- MAIN CARD CONTAINER ----------
pad = 50
card_box = [pad, pad, W - pad, H - pad]

# Card shadow & ambient glow ring
shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow)
sd.rounded_rectangle(
    [pad, pad + 6, W - pad, H - pad + 6], radius=28, fill=(0, 0, 0, 160)
)
shadow = shadow.filter(ImageFilter.GaussianBlur(20))
img.paste(shadow, (0, 0), shadow)

# Card Background
draw = ImageDraw.Draw(img, "RGBA")
draw.rounded_rectangle(card_box, radius=28, fill=card_bg, outline=card_border, width=2)


# ---------- VECTOR DRAWING HELPERS ----------
def draw_check(d, cx, cy, r, color, weight=3):
    d.line(
        [
            (cx - r * 0.5, cy),
            (cx - r * 0.1, cy + r * 0.4),
            (cx + r * 0.5, cy - r * 0.4),
        ],
        fill=color,
        width=weight,
        joint="bevel",
    )


def draw_cross(d, cx, cy, r, color, weight=3):
    d.line(
        [(cx - r * 0.4, cy - r * 0.4), (cx + r * 0.4, cy + r * 0.4)],
        fill=color,
        width=weight,
    )
    d.line(
        [(cx - r * 0.4, cy + r * 0.4), (cx + r * 0.4, cy - r * 0.4)],
        fill=color,
        width=weight,
    )


def draw_dash(d, cx, cy, r, color, weight=3):
    d.line([(cx - r * 0.4, cy), (cx + r * 0.4, cy)], fill=color, width=weight)


def draw_branch_icon(d, x, y, size, color):
    cx = x + size * 0.3
    d.line([(cx, y + size * 0.15), (cx, y + size * 0.85)], fill=color, width=3)
    d.ellipse([cx - 4, y + size * 0.1, cx + 4, y + size * 0.3], outline=color, width=2)
    d.ellipse([cx - 4, y + size * 0.7, cx + 4, y + size * 0.9], outline=color, width=2)
    d.ellipse(
        [
            x + size * 0.7 - 4,
            y + size * 0.4 - 4,
            x + size * 0.7 + 4,
            y + size * 0.4 + 4,
        ],
        outline=color,
        width=2,
    )
    d.line(
        [(cx, y + size * 0.5), (x + size * 0.7, y + size * 0.4)], fill=color, width=2
    )


def draw_person_icon(d, x, y, size, color):
    d.ellipse(
        [x + size * 0.3, y + size * 0.1, x + size * 0.7, y + size * 0.5],
        outline=color,
        width=2,
    )
    d.arc(
        [x + size * 0.15, y + size * 0.45, x + size * 0.85, y + size * 1.05],
        200,
        340,
        fill=color,
        width=2,
    )


def draw_message_icon(d, x, y, size, color):
    d.rounded_rectangle(
        [x + size * 0.1, y + size * 0.15, x + size * 0.9, y + size * 0.75],
        radius=4,
        outline=color,
        width=2,
    )
    d.polygon(
        [
            (x + size * 0.25, y + size * 0.75),
            (x + size * 0.15, y + size * 0.95),
            (x + size * 0.45, y + size * 0.75),
        ],
        fill=color,
    )


def draw_clock_icon(d, x, y, size, color):
    d.ellipse([x, y, x + size, y + size], outline=color, width=2)
    cx, cy = x + size / 2, y + size / 2
    d.line([(cx, cy), (cx, cy - size * 0.3)], fill=color, width=2)
    d.line([(cx, cy), (cx + size * 0.25, cy)], fill=color, width=2)


def draw_bolt_icon(d, x, y, size, color):
    pts = [
        (x + size * 0.55, y),
        (x + size * 0.15, y + size * 0.55),
        (x + size * 0.45, y + size * 0.55),
        (x + size * 0.4, y + size),
        (x + size * 0.85, y + size * 0.4),
        (x + size * 0.55, y + size * 0.4),
    ]
    d.polygon(pts, fill=color)


# ---------- STATUS BANNER (TOP-LEFT) ----------
bbox = draw.textbbox((0, 0), banner_text, font=f_banner)
text_w = bbox[2] - bbox[0]
banner_h = 48
banner_w = text_w + 70
banner_x, banner_y = pad + 24, pad + 24

draw.rounded_rectangle(
    [banner_x, banner_y, banner_x + banner_w, banner_y + banner_h],
    radius=banner_h // 2,
    fill=accent,
)
icon_cx = banner_x + 26
icon_cy = banner_y + banner_h / 2
if banner_icon == "check":
    draw_check(draw, icon_cx, icon_cy, 12, card_bg, weight=4)
else:
    draw_cross(draw, icon_cx, icon_cy, 10, card_bg, weight=4)

draw.text(
    (banner_x + 48, banner_y + (banner_h - (bbox[3] - bbox[1])) / 2 - bbox[1]),
    banner_text,
    font=f_banner,
    fill=card_bg,
)

# ---------- AVATAR (TOP-RIGHT) ----------
avatar_d = 72
avatar_x = W - pad - 24 - avatar_d
avatar_y = pad + 18

avatar_drawn = False
if avatar_path and os.path.exists(avatar_path):
    try:
        av = Image.open(avatar_path).convert("RGB").resize((avatar_d, avatar_d))
        mask = Image.new("L", (avatar_d, avatar_d), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, avatar_d, avatar_d], fill=255)
        img.paste(av, (avatar_x, avatar_y), mask)
        avatar_drawn = True
    except Exception:
        avatar_drawn = False

if not avatar_drawn:
    initials = (author[:2] if len(author) <= 2 else author[0] + author[-1]).upper()
    draw.ellipse(
        [avatar_x, avatar_y, avatar_x + avatar_d, avatar_y + avatar_d],
        fill=card_bg_hi,
        outline=accent,
        width=2,
    )
    ibbox = draw.textbbox((0, 0), initials, font=f_avatar)
    tw, th = ibbox[2] - ibbox[0], ibbox[3] - ibbox[1]
    draw.text(
        (avatar_x + (avatar_d - tw) / 2, avatar_y + (avatar_d - th) / 2 - ibbox[1]),
        initials,
        font=f_avatar,
        fill=text_bright,
    )

# ---------- PROJECT & ENVIRONMENT ----------
y_curr = pad + 90
draw.text((pad + 24, y_curr), project, font=f_title, fill=text_bright)
y_curr += 46

draw.text((pad + 24, y_curr), f"● {environment}", font=f_sub, fill=accent)
y_curr += 40

draw.line([pad + 24, y_curr, W - pad - 24, y_curr], fill=divider, width=1)
y_curr += 24

# ---------- METADATA BLOCK ----------
row_h = 36
meta_rows = [
    ("Branch", f"{branch}  ·  {short_sha}", draw_branch_icon),
    ("Author", author, draw_person_icon),
    (
        "Message",
        f"“{commit_msg[:42] + '...' if len(commit_msg) > 45 else commit_msg}”",
        draw_message_icon,
    ),
]

for label, val, icon_fn in meta_rows:
    icon_fn(draw, pad + 24, y_curr, 20, text_muted)
    draw.text((pad + 56, y_curr), label, font=f_label, fill=text_muted)
    draw.text((pad + 180, y_curr - 2), val, font=f_body, fill=text_bright)
    y_curr += row_h

y_curr += 12
draw.line([pad + 24, y_curr, W - pad - 24, y_curr], fill=divider, width=1)
y_curr += 24


# ---------- JOB PILLS ----------
def draw_job_pill(x, y, w, h, label, result, duration):
    ok = result == "success"
    color = mint if ok else coral if result == "failure" else gray_skip

    draw.rounded_rectangle(
        [x, y, x + w, y + h], radius=16, fill=card_bg_hi, outline=card_border, width=1
    )

    # Status Circle
    cx, cy = x + 32, y + h / 2
    draw.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=color)
    if ok:
        draw_check(draw, cx, cy, 8, card_bg, weight=3)
    elif result == "failure":
        draw_cross(draw, cx, cy, 7, card_bg, weight=3)
    else:
        draw_dash(draw, cx, cy, 7, card_bg, weight=3)

    draw.text((x + 60, y + 14), label, font=f_body_bold, fill=text_bright)
    status_text = duration if ok else result.capitalize()
    draw.text((x + 60, y + 40), status_text, font=f_small, fill=text_muted)


pill_w = (W - (pad * 2) - 48 - 20) // 2
draw_job_pill(pad + 24, y_curr, pill_w, 72, "Lint", lint_result, lint_duration)
draw_job_pill(
    pad + 24 + pill_w + 20, y_curr, pill_w, 72, "Deploy", deploy_result, deploy_duration
)

y_curr += 72 + 24

# ---------- FOOTER (TIMESTAMP & TOTAL TIME) ----------
footer_h = 38

# Timestamp Pill
ts_bbox = draw.textbbox((0, 0), timestamp, font=f_footer)
ts_w = ts_bbox[2] - ts_bbox[0] + 56
draw.rounded_rectangle(
    [pad + 24, y_curr, pad + 24 + ts_w, y_curr + footer_h],
    radius=footer_h // 2,
    fill=card_bg_hi,
)
draw_clock_icon(draw, pad + 36, y_curr + 10, 18, sky)
draw.text(
    (pad + 62, y_curr + (footer_h - (ts_bbox[3] - ts_bbox[1])) / 2 - ts_bbox[1]),
    timestamp,
    font=f_footer,
    fill=text_bright,
)

# Duration Pill
if total_s is not None:
    dur_str = f"{format_seconds(total_s)} total"
    dur_bbox = draw.textbbox((0, 0), dur_str, font=f_footer)
    dur_w = dur_bbox[2] - dur_bbox[0] + 56
    dur_x = pad + 24 + ts_w + 12
    draw.rounded_rectangle(
        [dur_x, y_curr, dur_x + dur_w, y_curr + footer_h],
        radius=footer_h // 2,
        fill=card_bg_hi,
    )
    draw_bolt_icon(draw, dur_x + 14, y_curr + 10, 18, sun)
    draw.text(
        (
            dur_x + 40,
            y_curr + (footer_h - (dur_bbox[3] - dur_bbox[1])) / 2 - dur_bbox[1],
        ),
        dur_str,
        font=f_footer,
        fill=text_bright,
    )

# Save Image Output
img.save("card.png")
