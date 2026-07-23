import os
import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter

overall_ok = os.environ.get("OVERALL_OK", "true") == "true"
project = os.environ["PROJECT"]
environment = os.environ["ENVIRONMENT"]
branch = os.environ["BRANCH"]
short_sha = os.environ["SHORT_SHA"]
author = os.environ.get("AUTHOR", "unknown")
commit_msg = os.environ.get("COMMIT_MSG", "")
lint_result = os.environ["LINT_RESULT"]
lint_duration = os.environ.get("LINT_DURATION", "")
deploy_result = os.environ["DEPLOY_RESULT"]
deploy_duration = os.environ.get("DEPLOY_DURATION", "")
timestamp = os.environ["TIMESTAMP"]
avatar_path = os.environ.get("AVATAR_PATH", "")

# ---------- cute dark palette ----------
bg_top, bg_bottom = (26, 22, 46), (18, 15, 33)          # deep indigo -> near-black
card_bg = (34, 29, 56)                                    # soft plum
card_bg_hi = (41, 35, 66)
text_bright = (245, 242, 255)
text_muted = (154, 146, 186)
divider = (55, 48, 84)

mint = (110, 231, 183)      # success
coral = (255, 128, 149)     # failure
gray_skip = (99, 91, 128)
sun = (255, 209, 102)       # decorative yellow
sky = (125, 211, 252)       # decorative blue
lilac = (196, 167, 255)     # decorative purple

if overall_ok:
    accent, accent_glow = mint, mint
    banner_text, banner_icon = "ALL GOOD", "check"
else:
    accent, accent_glow = coral, coral
    banner_text, banner_icon = "NEEDS ATTENTION", "cross"


def parse_seconds(dur):
    """Parse strings like '12s', '1m5s', '' into total seconds. Returns None if unparsable."""
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
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


lint_s = parse_seconds(lint_duration)
deploy_s = parse_seconds(deploy_duration)
total_s = (lint_s or 0) + (deploy_s or 0) if (lint_s is not None or deploy_s is not None) else None

W, H = 1000, 640

# vertical gradient background
grad = Image.new("RGB", (1, H), color=0)
for yy in range(H):
    t = yy / H
    r = int(bg_top[0] + (bg_bottom[0] - bg_top[0]) * t)
    g = int(bg_top[1] + (bg_bottom[1] - bg_top[1]) * t)
    b = int(bg_top[2] + (bg_bottom[2] - bg_top[2]) * t)
    grad.putpixel((0, yy), (r, g, b))
img = grad.resize((W, H))

# soft colorful blurred blobs for a "cute" glow backdrop
blob_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bd = ImageDraw.Draw(blob_layer)
bd.ellipse([-120, -140, 260, 200], fill=lilac + (70,))
bd.ellipse([760, -100, 1120, 260], fill=sky + (60,))
bd.ellipse([680, 460, 1060, 780], fill=sun + (45,))
bd.ellipse([-100, 440, 220, 740], fill=accent_glow + (55,))
blob_layer = blob_layer.filter(ImageFilter.GaussianBlur(70))
img.paste(blob_layer, (0, 0), blob_layer)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def font(path, size):
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, path), size)
    except Exception:
        return ImageFont.load_default()


f_title = font("DejaVuSans-Bold.ttf", 40)
f_sub = font("DejaVuSans-Bold.ttf", 22)
f_body = font("DejaVuSans.ttf", 26)
f_body_bold = font("DejaVuSans-Bold.ttf", 26)
f_small = font("DejaVuSans.ttf", 20)
f_label = font("DejaVuSans-Bold.ttf", 18)
f_banner = font("DejaVuSans-Bold.ttf", 28)
f_avatar = font("DejaVuSans-Bold.ttf", 30)
f_footer = font("DejaVuSans-Bold.ttf", 20)

# card drop shadow
shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow)
sd.rounded_rectangle([40, 46, W - 40, H - 34], radius=36, fill=(0, 0, 0, 120))
shadow = shadow.filter(ImageFilter.GaussianBlur(18))
img.paste(shadow, (0, 0), shadow)

# faint accent glow ring around the card edge
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.rounded_rectangle([40, 40, W - 40, H - 40], radius=36, outline=accent_glow + (140,), width=3)
glow = glow.filter(ImageFilter.GaussianBlur(6))
img.paste(glow, (0, 0), glow)

draw = ImageDraw.Draw(img, "RGBA")
draw.rounded_rectangle([40, 40, W - 40, H - 40], radius=36, fill=card_bg)
draw.rounded_rectangle([40, 40, W - 40, 140], radius=36, fill=card_bg_hi)
draw.rectangle([40, 110, W - 40, 140], fill=card_bg_hi)

pad = 64


# ---------- vector icon helpers ----------
def draw_check(d, cx, cy, r, color, weight=4):
    d.line(
        [(cx - r * 0.55, cy), (cx - r * 0.15, cy + r * 0.45), (cx + r * 0.6, cy - r * 0.45)],
        fill=color, width=weight, joint="curve",
    )


def draw_cross(d, cx, cy, r, color, weight=4):
    d.line([(cx - r * 0.5, cy - r * 0.5), (cx + r * 0.5, cy + r * 0.5)], fill=color, width=weight)
    d.line([(cx - r * 0.5, cy + r * 0.5), (cx + r * 0.5, cy - r * 0.5)], fill=color, width=weight)


def draw_dash(d, cx, cy, r, color, weight=4):
    d.line([(cx - r * 0.5, cy), (cx + r * 0.5, cy)], fill=color, width=weight)


def draw_leaf_icon(d, x, y, size, color):
    d.pieslice([x, y, x + size, y + size], 200, 20, fill=color)
    d.line([(x + size * 0.15, y + size * 0.85), (x + size * 0.85, y + size * 0.15)], fill=color, width=3)


def draw_branch_icon(d, x, y, size, color):
    cx = x + size * 0.25
    d.line([(cx, y + size * 0.1), (cx, y + size * 0.9)], fill=color, width=4)
    d.ellipse([cx - 5, y + size * 0.05, cx + 5, y + size * 0.15], outline=color, width=3)
    d.ellipse([cx - 5, y + size * 0.75, cx + 5, y + size * 0.95], outline=color, width=3)
    d.ellipse([x + size * 0.65, y + size * 0.35, x + size * 0.75, y + size * 0.55], outline=color, width=3)
    d.line([(cx, y + size * 0.5), (x + size * 0.7, y + size * 0.45)], fill=color, width=3)


def draw_person_icon(d, x, y, size, color):
    d.ellipse([x + size * 0.32, y + size * 0.05, x + size * 0.68, y + size * 0.42], outline=color, width=3)
    d.arc([x + size * 0.15, y + size * 0.45, x + size * 0.85, y + size * 1.15], 200, 340, fill=color, width=3)


def draw_message_icon(d, x, y, size, color):
    d.rounded_rectangle([x + size * 0.05, y + size * 0.15, x + size * 0.95, y + size * 0.75], radius=6, outline=color, width=3)
    d.line([(x + size * 0.25, y + size * 0.75), (x + size * 0.15, y + size * 0.95)], fill=color, width=3)
    d.line([(x + size * 0.15, y + size * 0.95), (x + size * 0.4, y + size * 0.75)], fill=color, width=3)


def draw_clock_icon(d, x, y, size, color, weight=3):
    d.ellipse([x, y, x + size, y + size], outline=color, width=weight)
    cx, cy = x + size / 2, y + size / 2
    d.line([(cx, cy), (cx, cy - size * 0.3)], fill=color, width=weight)
    d.line([(cx, cy), (cx + size * 0.22, cy + size * 0.1)], fill=color, width=weight)


def draw_broom_icon(d, x, y, size, color):
    d.line([(x + size * 0.2, y), (x + size * 0.8, y + size * 0.8)], fill=color, width=4)
    d.polygon(
        [(x + size * 0.65, y + size * 0.6), (x + size * 1.0, y + size * 0.75),
         (x + size * 0.9, y + size * 1.0), (x + size * 0.55, y + size * 0.85)],
        fill=color,
    )


def draw_rocket_icon(d, x, y, size, color):
    cx = x + size / 2
    d.polygon([(cx, y), (x + size * 0.75, y + size * 0.65), (x + size * 0.25, y + size * 0.65)], fill=color)
    d.polygon([(x + size * 0.25, y + size * 0.65), (x + size * 0.1, y + size), (x + size * 0.35, y + size * 0.8)], fill=color)
    d.polygon([(x + size * 0.75, y + size * 0.65), (x + size * 0.9, y + size), (x + size * 0.65, y + size * 0.8)], fill=color)


def draw_bolt_icon(d, x, y, size, color):
    d.polygon(
        [
            (x + size * 0.58, y),
            (x + size * 0.18, y + size * 0.58),
            (x + size * 0.46, y + size * 0.58),
            (x + size * 0.4, y + size),
            (x + size * 0.85, y + size * 0.4),
            (x + size * 0.54, y + size * 0.4),
        ],
        fill=color,
    )


def draw_star(d, cx, cy, r, color):
    import math
    pts = []
    for i in range(10):
        ang = math.pi / 2 + i * math.pi / 5
        rad = r if i % 2 == 0 else r * 0.42
        pts.append((cx + rad * math.cos(ang), cy - rad * math.sin(ang)))
    d.polygon(pts, fill=color)


# ---------- decorative cute sparkles ----------
draw_star(draw, W - 150, 190, 8, sun)
draw_star(draw, W - 100, 250, 5, lilac)
draw_star(draw, 175, 470, 6, sky)

# ---------- status banner pill with soft glow ----------
bbox = draw.textbbox((0, 0), banner_text, font=f_banner)
text_w = bbox[2] - bbox[0]
icon_zone = 56
banner_h = 60
banner_w = icon_zone + text_w + 50

banner_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bgd = ImageDraw.Draw(banner_glow)
bgd.rounded_rectangle([pad, pad, pad + banner_w, pad + banner_h], radius=banner_h // 2, fill=accent + (255,))
banner_glow = banner_glow.filter(ImageFilter.GaussianBlur(16))
img.paste(banner_glow, (0, 0), banner_glow)
draw = ImageDraw.Draw(img, "RGBA")

draw.rounded_rectangle([pad, pad, pad + banner_w, pad + banner_h], radius=banner_h // 2, fill=accent)
icon_cx, icon_cy = pad + icon_zone / 2 + 6, pad + banner_h / 2
if banner_icon == "check":
    draw_check(draw, icon_cx, icon_cy, 16, card_bg, weight=5)
else:
    draw_cross(draw, icon_cx, icon_cy, 14, card_bg, weight=5)
draw.text((pad + icon_zone, pad + (banner_h - (bbox[3] - bbox[1])) / 2 - bbox[1]), banner_text, font=f_banner, fill=card_bg)


# ---------- committer avatar, top right ----------
def initials_from_name(name):
    parts = [p for p in name.replace("-", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def pastel_from_name(name):
    h = sum(ord(c) for c in name)
    palette = [
        (255, 154, 178), (255, 200, 130), (255, 235, 130),
        (150, 235, 190), (140, 210, 255), (200, 170, 255),
    ]
    return palette[h % len(palette)]


avatar_d = 96
avatar_x = W - pad - avatar_d
avatar_y = pad - 6

ring_pad = 6
ring_box = [avatar_x - ring_pad, avatar_y - ring_pad, avatar_x + avatar_d + ring_pad, avatar_y + avatar_d + ring_pad]
ring_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
rgd = ImageDraw.Draw(ring_glow)
rgd.ellipse(ring_box, fill=accent + (255,))
ring_glow = ring_glow.filter(ImageFilter.GaussianBlur(14))
img.paste(ring_glow, (0, 0), ring_glow)
draw = ImageDraw.Draw(img, "RGBA")
draw.ellipse(ring_box, fill=accent)

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
    badge_color = pastel_from_name(author)
    draw.ellipse([avatar_x, avatar_y, avatar_x + avatar_d, avatar_y + avatar_d], fill=badge_color)
    initials = initials_from_name(author)
    ibbox = draw.textbbox((0, 0), initials, font=f_avatar)
    tw, th = ibbox[2] - ibbox[0], ibbox[3] - ibbox[1]
    draw.text(
        (avatar_x + (avatar_d - tw) / 2, avatar_y + (avatar_d - th) / 2 - ibbox[1]),
        initials, font=f_avatar, fill=(45, 35, 60),
    )

# ---------- title + environment ----------
y = pad + banner_h + 34
draw.text((pad, y), project, font=f_title, fill=text_bright)
y += 52

draw_leaf_icon(draw, pad, y + 2, 20, accent)
draw.text((pad + 28, y), environment, font=f_sub, fill=accent)

y += 50
draw.line([pad, y, W - pad, y], fill=divider, width=2)
y += 30

# ---------- meta rows ----------
row_icon = 22
draw_branch_icon(draw, pad, y - 2, row_icon, text_muted)
draw.text((pad + 34, y), "Branch", font=f_label, fill=text_muted)
draw.text((pad + 160, y - 3), f"{branch}  \u00b7  {short_sha}", font=f_body, fill=text_bright)
y += 42

draw_person_icon(draw, pad, y - 2, row_icon, text_muted)
draw.text((pad + 34, y), "Author", font=f_label, fill=text_muted)
draw.text((pad + 160, y - 3), author, font=f_body, fill=text_bright)
y += 42

draw_message_icon(draw, pad, y - 2, row_icon, text_muted)
draw.text((pad + 34, y), "Message", font=f_label, fill=text_muted)
msg_display = commit_msg if len(commit_msg) <= 46 else commit_msg[:43] + "..."
draw.text((pad + 160, y - 3), f"\u201c{msg_display}\u201d", font=f_body, fill=text_bright)

y += 60
draw.line([pad, y, W - pad, y], fill=divider, width=2)
y += 34


def job_pill(x, y, label, result, duration, icon_fn):
    ok = result == "success"
    color = mint if ok else coral if result == "failure" else gray_skip
    draw.rounded_rectangle([x, y, x + 400, y + 76], radius=20, fill=card_bg_hi)
    draw.ellipse([x + 18, y + 18, x + 58, y + 58], fill=color)
    cx, cy = x + 38, y + 38
    if ok:
        draw_check(draw, cx, cy, 13, card_bg, weight=4)
    elif result == "failure":
        draw_cross(draw, cx, cy, 11, card_bg, weight=4)
    else:
        draw_dash(draw, cx, cy, 11, card_bg, weight=4)
    icon_fn(draw, x + 74, y + 14, 20, text_muted)
    draw.text((x + 100, y + 12), label, font=f_body_bold, fill=text_bright)
    status_text = duration if ok else result.capitalize()
    draw.text((x + 74, y + 44), status_text, font=f_small, fill=text_muted)


job_pill(pad, y, "Lint", lint_result, lint_duration, draw_broom_icon)
job_pill(pad + 436, y, "Deploy", deploy_result, deploy_duration, draw_rocket_icon)

y += 76 + 34

# ---------- enhanced footer: timestamp pill + total-duration pill ----------
footer_h = 46

# timestamp pill (left) — icon in its own circular chip, text after
ts_text = timestamp
ts_bbox = draw.textbbox((0, 0), ts_text, font=f_footer)
ts_text_w = ts_bbox[2] - ts_bbox[0]
ts_pill_w = 40 + 14 + ts_text_w + 20
draw.rounded_rectangle([pad, y, pad + ts_pill_w, y + footer_h], radius=footer_h // 2, fill=card_bg_hi)
chip_d = footer_h - 8
draw.ellipse([pad + 4, y + 4, pad + 4 + chip_d, y + 4 + chip_d], fill=sky)
draw_clock_icon(draw, pad + 4 + chip_d * 0.22, y + 4 + chip_d * 0.22, chip_d * 0.56, card_bg, weight=3)
draw.text(
    (pad + 4 + chip_d + 14, y + (footer_h - (ts_bbox[3] - ts_bbox[1])) / 2 - ts_bbox[1]),
    ts_text, font=f_footer, fill=text_bright,
)

# total-duration pill (right of the timestamp pill), only if we have data
if total_s is not None:
    dur_text = f"{format_seconds(total_s)} total"
    dur_bbox = draw.textbbox((0, 0), dur_text, font=f_footer)
    dur_text_w = dur_bbox[2] - dur_bbox[0]
    dur_pill_w = 40 + 14 + dur_text_w + 20
    dur_x = pad + ts_pill_w + 16
    draw.rounded_rectangle([dur_x, y, dur_x + dur_pill_w, y + footer_h], radius=footer_h // 2, fill=card_bg_hi)
    draw.ellipse([dur_x + 4, y + 4, dur_x + 4 + chip_d, y + 4 + chip_d], fill=sun)
    draw_bolt_icon(draw, dur_x + 4 + chip_d * 0.28, y + 4 + chip_d * 0.15, chip_d * 0.5, card_bg)
    draw.text(
        (dur_x + 4 + chip_d + 14, y + (footer_h - (dur_bbox[3] - dur_bbox[1])) / 2 - dur_bbox[1]),
        dur_text, font=f_footer, fill=text_bright,
    )

img.save("card.png")
