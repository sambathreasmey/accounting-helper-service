import os
import math
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

if overall_ok:
    accent, accent_dark = (88, 194, 122), (56, 158, 92)
    banner_text, banner_icon = "ALL GOOD", "check"
else:
    accent, accent_dark = (237, 108, 108), (196, 68, 68)
    banner_text, banner_icon = "NEEDS ATTENTION", "cross"

bg, card_bg = (250, 247, 242), (255, 255, 255)
text_dark, text_muted = (51, 46, 42), (150, 142, 132)

W, H = 1000, 620
img = Image.new("RGB", (W, H), bg)
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

# ---------- soft drop shadow behind the card ----------
shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow)
sd.rounded_rectangle([40, 46, W - 40, H - 34], radius=36, fill=(0, 0, 0, 35))
shadow = shadow.filter(ImageFilter.GaussianBlur(14))
img.paste(shadow, (0, 0), shadow)

draw = ImageDraw.Draw(img)
draw.rounded_rectangle([40, 40, W - 40, H - 40], radius=36, fill=card_bg)

pad = 64


# ---------- small vector icon helpers (no emoji font needed) ----------
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
    # simple leaf shape for "environment"
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


def draw_clock_icon(d, x, y, size, color):
    d.ellipse([x, y, x + size, y + size], outline=color, width=3)
    cx, cy = x + size / 2, y + size / 2
    d.line([(cx, cy), (cx, cy - size * 0.3)], fill=color, width=3)
    d.line([(cx, cy), (cx + size * 0.22, cy + size * 0.1)], fill=color, width=3)


def draw_broom_icon(d, x, y, size, color):
    d.line([(x + size * 0.2, y), (x + size * 0.8, y + size * 0.8)], fill=color, width=4)
    d.polygon(
        [(x + size * 0.65, y + size * 0.6), (x + size * 1.0, y + size * 0.75),
         (x + size * 0.9, y + size * 1.0), (x + size * 0.55, y + size * 0.85)],
        fill=color,
    )


def draw_rocket_icon(d, x, y, size, color):
    cx = x + size / 2
    d.polygon(
        [(cx, y), (x + size * 0.75, y + size * 0.65), (x + size * 0.25, y + size * 0.65)],
        fill=color,
    )
    d.polygon([(x + size * 0.25, y + size * 0.65), (x + size * 0.1, y + size), (x + size * 0.35, y + size * 0.8)], fill=color)
    d.polygon([(x + size * 0.75, y + size * 0.65), (x + size * 0.9, y + size), (x + size * 0.65, y + size * 0.8)], fill=color)


# ---------- status banner pill (sized to fit its text) ----------
bbox = draw.textbbox((0, 0), banner_text, font=f_banner)
text_w = bbox[2] - bbox[0]
icon_zone = 56
banner_h = 60
banner_w = icon_zone + text_w + 50
draw.rounded_rectangle([pad, pad, pad + banner_w, pad + banner_h], radius=banner_h // 2, fill=accent)
icon_cx, icon_cy = pad + icon_zone / 2 + 6, pad + banner_h / 2
if banner_icon == "check":
    draw_check(draw, icon_cx, icon_cy, 16, "white", weight=5)
else:
    draw_cross(draw, icon_cx, icon_cy, 14, "white", weight=5)
draw.text((pad + icon_zone, pad + (banner_h - (bbox[3] - bbox[1])) / 2 - bbox[1]), banner_text, font=f_banner, fill="white")


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
        (255, 179, 186), (255, 223, 186), (255, 255, 186),
        (186, 255, 201), (186, 225, 255), (218, 198, 255),
    ]
    return palette[h % len(palette)]


avatar_d = 96
avatar_x = W - pad - avatar_d
avatar_y = pad - 6

ring_pad = 6
ring_box = [avatar_x - ring_pad, avatar_y - ring_pad, avatar_x + avatar_d + ring_pad, avatar_y + avatar_d + ring_pad]
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
        initials, font=f_avatar, fill=(90, 70, 60),
    )

# ---------- title + environment ----------
y = pad + banner_h + 34
draw.text((pad, y), project, font=f_title, fill=text_dark)
y += 52

draw_leaf_icon(draw, pad, y + 2, 20, accent_dark)
draw.text((pad + 28, y), environment, font=f_sub, fill=accent_dark)

y += 50
draw.line([pad, y, W - pad, y], fill=(235, 230, 222), width=2)
y += 30

# ---------- meta rows ----------
row_icon = 22
draw_branch_icon(draw, pad, y - 2, row_icon, text_muted)
draw.text((pad + 34, y), "Branch", font=f_label, fill=text_muted)
draw.text((pad + 160, y - 3), f"{branch}  \u00b7  {short_sha}", font=f_body, fill=text_dark)
y += 42

draw_person_icon(draw, pad, y - 2, row_icon, text_muted)
draw.text((pad + 34, y), "Author", font=f_label, fill=text_muted)
draw.text((pad + 160, y - 3), author, font=f_body, fill=text_dark)
y += 42

draw_message_icon(draw, pad, y - 2, row_icon, text_muted)
draw.text((pad + 34, y), "Message", font=f_label, fill=text_muted)
msg_display = commit_msg if len(commit_msg) <= 46 else commit_msg[:43] + "..."
draw.text((pad + 160, y - 3), f"\u201c{msg_display}\u201d", font=f_body, fill=text_dark)

y += 60
draw.line([pad, y, W - pad, y], fill=(235, 230, 222), width=2)
y += 34


def job_pill(x, y, label, result, duration, icon_fn):
    ok = result == "success"
    color = accent if ok else (237, 108, 108) if result == "failure" else (200, 196, 190)
    draw.rounded_rectangle([x, y, x + 400, y + 76], radius=20, fill=(248, 246, 242))
    draw.ellipse([x + 18, y + 18, x + 58, y + 58], fill=color)
    cx, cy = x + 38, y + 38
    if ok:
        draw_check(draw, cx, cy, 13, "white", weight=4)
    elif result == "failure":
        draw_cross(draw, cx, cy, 11, "white", weight=4)
    else:
        draw_dash(draw, cx, cy, 11, "white", weight=4)
    icon_fn(draw, x + 74, y + 14, 20, text_muted)
    draw.text((x + 100, y + 12), label, font=f_body_bold, fill=text_dark)
    status_text = duration if ok else result.capitalize()
    draw.text((x + 74, y + 44), status_text, font=f_small, fill=text_muted)


job_pill(pad, y, "Lint", lint_result, lint_duration, draw_broom_icon)
job_pill(pad + 436, y, "Deploy", deploy_result, deploy_duration, draw_rocket_icon)

y += 76 + 34
draw_clock_icon(draw, pad, y - 2, 18, text_muted)
draw.text((pad + 28, y - 3), timestamp, font=f_small, fill=text_muted)

img.save("card.png")
