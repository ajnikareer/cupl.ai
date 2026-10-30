import os
from PIL import Image, ImageDraw, ImageFont

orig_path = r"C:/Users/admin/.gemini/antigravity/brain/6d8e9353-5c79-4cdf-92cf-1fafc99c77a9/.user_uploaded/media_1793375167260_58ad09ec.jpg"
new_path = r"frontend/public/img/cupl_logo.png"

im_orig = Image.open(orig_path).convert("RGB")
im_new = Image.open(new_path).convert("RGB")

# Target width for comparison card: 1200 px each
W = 1200
H_orig = int(im_orig.height * (W / im_orig.width))
H_new = int(im_new.height * (W / im_new.width))

im_orig_scaled = im_orig.resize((W, H_orig), Image.Resampling.LANCZOS)
im_new_scaled = im_new.resize((W, H_new), Image.Resampling.LANCZOS)

comp_w = W + 80
comp_h = H_orig + H_new + 240

comp = Image.new("RGB", (comp_w, comp_h), (250, 248, 246))
draw = ImageDraw.Draw(comp)

try:
    f_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 36)
    f_label = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 26)
    f_sub = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 20)
except Exception:
    f_title = f_label = f_sub = ImageFont.load_default()

# Header
draw.text((40, 25), "cupl.ai — Logo Recreation (HD Quality + Bigger Tagline)", fill=(79, 15, 32), font=f_title)

# Card 1: Original
y1 = 80
draw.text((40, y1), "1. Original Upload (Low Resolution / Blurry Tagline):", fill=(120, 80, 90), font=f_label)
comp.paste(im_orig_scaled, (40, y1 + 40))

# Card 2: Recreated
y2 = y1 + 40 + H_orig + 40
draw.text((40, y2), "2. Recreated Master Logo (Razor-Sharp Vector-Grade + Enlarged Tagline):", fill=(30, 110, 50), font=f_label)
comp.paste(im_new_scaled, (40, y2 + 40))

out_path = r"C:\Users\admin\.gemini\antigravity\brain\6d8e9353-5c79-4cdf-92cf-1fafc99c77a9\logo_recreation_comparison.jpg"
comp.save(out_path, "JPEG", quality=95)
print(f"Saved comparison to: {out_path}")
