import os
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
    banner_text, banner_icon = "ALL GOOD", "\u2713"
else:
    accent, accent_dark = (237, 108, 108), (196, 68, 68)
    banner_text, banner_icon = "NEEDS ATTENTION", "\u2715"

bg, card_bg = (250, 247, 242), (255, 255, 255)
text_dark, text_muted = (51, 46, 42), (150, 142, 132)
pastel = [(255, 214, 224), (214, 234, 255), (255, 244, 214)]

W, H = 1000, 620
img = Image.new("RGB", (W, H), bg)
FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def font(path, size):
    try:
        return ImageFont.truetype(os.path.join(FONT_DIR, path), size)
    except Exception:
        return ImageFont.load_default()


f_title = font("DejaVuSans-Bold.ttf", 40)
f_sub = font("DejaVuSans.ttf", 24)
f_body = font("DejaVuSans.ttf", 26)
f_body_bold = font("DejaVuSans-Bold.ttf", 26)
f_small = font("DejaVuSans.ttf", 20)
f_banner = font("DejaVuSans-Bold.ttf", 30)
f_icon = font("DejaVuSans-Bold.ttf", 34)
f_avatar = font("DejaVuSans-Bold.ttf", 30)

# soft drop shadow behind the card
shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow)
sd.rounded_rectangle([40, 46, W - 40, H - 34], radius=36, fill=(0, 0, 0, 35))
shadow = shadow.filter(ImageFilter.GaussianBlur(14))
img.paste(shadow, (0, 0), shadow)

draw = ImageDraw.Draw(img)
draw.rounded_rectangle([40, 40, W - 40, H - 40], radius=36, fill=card_bg)

pad = 64

# status banner pill
banner_w, banner_h = 300, 62
draw.rounded_rectangle([pad, pad, pad + banner_w, pad + banner_h], radius=banner_h // 2, fill=accent)
draw.text((pad + 24, pad + 12), banner_icon, font=f_icon, fill="white")
draw.text((pad + 66, pad + 16), banner_text, font=f_banner, fill="white")


# ---- committer avatar, top right: real GitHub avatar if available, else colored initials badge ----
def initials_from_name(name):
    parts = [p for p in name.replace("-", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def pastel_from_name(name):
    # deterministic pastel color per person, so the same author always gets the same badge color
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
draw.ellipse(ring_box, fill=accent)  # colored ring matching overall status

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
    bbox = draw.textbbox((0, 0), initials, font=f_avatar)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        (avatar_x + (avatar_d - tw) / 2, avatar_y + (avatar_d - th) / 2 - bbox[1]),
        initials, font=f_avatar, fill=(90, 70, 60),
    )

y = pad + banner_h + 34
draw.text((pad, y), project, font=f_title, fill=text_dark)
y += 50
draw.text((pad, y), f"\U0001F331 {environment}", font=f_sub, fill=accent_dark)

y += 56
draw.line([pad, y, W - pad, y], fill=(235, 230, 222), width=2)
y += 30

draw.text((pad, y), "\U0001F33F Branch", font=f_small, fill=text_muted)
draw.text((pad + 160, y - 3), f"{branch}  \u00b7  {short_sha}", font=f_body, fill=text_dark)
y += 42
draw.text((pad, y), "\U0001F464 Author", font=f_small, fill=text_muted)
draw.text((pad + 160, y - 3), author, font=f_body, fill=text_dark)
y += 42
draw.text((pad, y), "\U0001F4AC Message", font=f_small, fill=text_muted)
msg_display = commit_msg if len(commit_msg) <= 46 else commit_msg[:43] + "..."
draw.text((pad + 160, y - 3), f"\u201c{msg_display}\u201d", font=f_body, fill=text_dark)

y += 60
draw.line([pad, y, W - pad, y], fill=(235, 230, 222), width=2)
y += 34


def job_pill(x, y, label, result, duration):
    ok = result == "success"
    color = accent if ok else (237, 108, 108) if result == "failure" else (200, 196, 190)
    icon = "\u2713" if ok else ("\u2715" if result == "failure" else "\u2013")
    draw.rounded_rectangle([x, y, x + 400, y + 76], radius=20, fill=(248, 246, 242))
    draw.ellipse([x + 18, y + 18, x + 58, y + 58], fill=color)
    draw.text((x + 30, y + 20), icon, font=f_body_bold, fill="white")
    draw.text((x + 74, y + 12), label, font=f_body_bold, fill=text_dark)
    status_text = duration if ok else result.capitalize()
    draw.text((x + 74, y + 42), status_text, font=f_small, fill=text_muted)


job_pill(pad, y, "\U0001F9F9 Lint", lint_result, lint_duration)
job_pill(pad + 436, y, "\U0001F680 Deploy", deploy_result, deploy_duration)

y += 76 + 34
draw.text((pad, y), f"\u23F1  {timestamp}", font=f_small, fill=text_muted)

img.save("card.png")

draw.text((pad, y), project, font=f_title, fill=text_dark)
y += 50
draw.text((pad, y), f"\U0001F331 {environment}", font=f_sub, fill=accent_dark)

y += 56
draw.line([pad, y, W - pad, y], fill=(235, 230, 222), width=2)
y += 30

draw.text((pad, y), "\U0001F33F Branch", font=f_small, fill=text_muted)
draw.text((pad + 160, y - 3), f"{branch}  \u00b7  {short_sha}", font=f_body, fill=text_dark)
y += 42
draw.text((pad, y), "\U0001F464 Author", font=f_small, fill=text_muted)
draw.text((pad + 160, y - 3), author, font=f_body, fill=text_dark)
y += 42
draw.text((pad, y), "\U0001F4AC Message", font=f_small, fill=text_muted)
msg_display = commit_msg if len(commit_msg) <= 46 else commit_msg[:43] + "..."
draw.text((pad + 160, y - 3), f"\u201c{msg_display}\u201d", font=f_body, fill=text_dark)

y += 60
draw.line([pad, y, W - pad, y], fill=(235, 230, 222), width=2)
y += 34


def job_pill(x, y, label, result, duration):
    ok = result == "success"
    color = accent if ok else (237, 108, 108) if result == "failure" else (200, 196, 190)
    icon = "\u2713" if ok else ("\u2715" if result == "failure" else "\u2013")
    draw.rounded_rectangle([x, y, x + 400, y + 76], radius=20, fill=(248, 246, 242))
    draw.ellipse([x + 18, y + 18, x + 58, y + 58], fill=color)
    draw.text((x + 30, y + 20), icon, font=f_body_bold, fill="white")
    draw.text((x + 74, y + 12), label, font=f_body_bold, fill=text_dark)
    status_text = duration if ok else result.capitalize()
    draw.text((x + 74, y + 42), status_text, font=f_small, fill=text_muted)


job_pill(pad, y, "\U0001F9F9 Lint", lint_result, lint_duration)
job_pill(pad + 436, y, "\U0001F680 Deploy", deploy_result, deploy_duration)

y += 76 + 34
draw.text((pad, y), f"\u23F1  {timestamp}", font=f_small, fill=text_muted)

img.save("card.png")
