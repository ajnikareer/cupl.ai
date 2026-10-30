import os
from PIL import Image, ImageDraw, ImageFont

ARTIFACT_DIR = r"C:\Users\admin\.gemini\antigravity\brain\6d8e9353-5c79-4cdf-92cf-1fafc99c77a9"

# Load original user images
orig_icon_path = os.path.join(ARTIFACT_DIR, ".user_uploaded", "media_1793373049728_17b5f066.png")
orig_logo_path = os.path.join(ARTIFACT_DIR, ".user_uploaded", "media_1793373012054_101c4977.jpg")

orig_icon = Image.open(orig_icon_path).convert("RGBA")
orig_logo = Image.open(orig_logo_path).convert("RGB")

# Load improved assets
imp_icon = Image.open("frontend/public/img/cupl_icon_master.png").convert("RGBA")
imp_avatar = Image.open("frontend/public/img/avatar.jpg").convert("RGB")
imp_logo = Image.open("frontend/public/img/cupl_logo_cream.jpg").convert("RGB")

# Canvas size: 2400 x 1800 with warm luxury background #FAF8F5
W, H = 2400, 1850
canvas = Image.new("RGB", (W, H), (250, 248, 245))
draw = ImageDraw.Draw(canvas)

# Fonts
try:
    f_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 64)
    f_sub = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 34)
    f_card_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 40)
    f_card_sub = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 26)
    f_badge = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 24)
except Exception:
    f_title = f_sub = f_card_title = f_card_sub = f_badge = ImageFont.load_default()

# Header
draw.text((100, 70), "cupl.ai — Brand Identity & Asset Refinement", fill=(107, 27, 49), font=f_title)
draw.text((100, 150), "Comparison of original uploaded assets vs ultra-high-definition, mathematically perfected production assets", fill=(138, 106, 115), font=f_sub)

# Card helper
def draw_card(x, y, w, h, title, subtitle, badge_text, badge_color):
    # Card background
    draw.rounded_rectangle([x, y, x + w, y + h], radius=24, fill=(255, 255, 255), outline=(232, 222, 218), width=2)
    # Badge
    b_w = draw.textlength(badge_text, font=f_badge) + 30
    draw.rounded_rectangle([x + 30, y + 25, x + 30 + b_w, y + 65], radius=12, fill=badge_color[0])
    draw.text((x + 45, y + 30), badge_text, fill=badge_color[1], font=f_badge)
    # Titles
    draw.text((x + 30, y + 80), title, fill=(36, 18, 25), font=f_card_title)
    draw.text((x + 30, y + 130), subtitle, fill=(138, 106, 115), font=f_card_sub)

# ----------------- ROW 1: ICONS (ORIGINAL vs IMPROVED MASTER vs AI AVATAR MEDALLION) -----------------
# 1. Original User Icon Card
draw_card(100, 230, 680, 700, "Original Uploaded Icon", "208×199 px raster, baked-in border, aliased edges", "ORIGINAL UPLOAD", ((245, 235, 238), (160, 50, 70)))
# Paste original scaled up with clear border
orig_icon_disp = orig_icon.resize((420, 402), Image.Resampling.NEAREST)
canvas.paste(orig_icon_disp, (100 + (680 - 420) // 2, 450), mask=orig_icon_disp if orig_icon_disp.mode == 'RGBA' else None)

# 2. Improved Master Squircle Icon Card
draw_card(840, 230, 680, 700, "Refined Master Squircle Icon", "4096×4096 supersampled, transparent alpha, 18k luster", "IMPROVED PRODUCTION", ((235, 245, 238), (30, 130, 70)))
imp_icon_disp = imp_icon.resize((440, 440), Image.Resampling.LANCZOS)
canvas.paste(imp_icon_disp, (840 + (680 - 440) // 2, 430), mask=imp_icon_disp)

# 3. AI Companion Stage Avatar Medallion Card
draw_card(1580, 230, 720, 700, "AI Companion Medallion (/img/avatar.jpg)", "Circular luxury medallion replacing human girl photo", "AI STAGE REPLACEMENT", ((250, 240, 225), (160, 110, 40)))
imp_avatar_disp = imp_avatar.resize((440, 440), Image.Resampling.LANCZOS)
# Mask to circle for display
c_mask = Image.new("L", (440, 440), 0)
ImageDraw.Draw(c_mask).ellipse([0, 0, 440, 440], fill=255)
canvas.paste(imp_avatar_disp, (1580 + (720 - 440) // 2, 430), mask=c_mask)

# ----------------- ROW 2: BRAND LOGOS (ORIGINAL vs IMPROVED) -----------------
# 4. Original Logo Card
draw_card(100, 970, 1050, 800, "Original Brand Logo Upload", "638×287 px compressed JPEG with edge halo", "ORIGINAL UPLOAD", ((245, 235, 238), (160, 50, 70)))
orig_logo_disp = orig_logo.resize((960, 432), Image.Resampling.LANCZOS)
canvas.paste(orig_logo_disp, (100 + (1050 - 960) // 2, 1200))

# 5. Improved Master Logo Card
draw_card(1210, 970, 1090, 800, "Refined Master Brand Logo", "2400×700 px vector-grade typography & precision layout", "IMPROVED PRODUCTION", ((235, 245, 238), (30, 130, 70)))
imp_logo_disp = imp_logo.resize((1020, 298), Image.Resampling.LANCZOS)
canvas.paste(imp_logo_disp, (1210 + (1090 - 1020) // 2, 1260))

# Save artifact
out_path = os.path.join(ARTIFACT_DIR, "cupl_brand_refinement_comparison.jpg")
canvas.save(out_path, "JPEG", quality=95)
print(f"Comparison image saved to: {out_path}")
