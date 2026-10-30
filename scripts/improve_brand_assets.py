import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Set up paths
FRONTEND_IMG = r"frontend/public/img"
BACKEND_DIST_IMG = r"backend/dist/img"
ARTIFACT_DIR = r"C:\Users\admin\.gemini\antigravity\brain\6d8e9353-5c79-4cdf-92cf-1fafc99c77a9"

os.makedirs(FRONTEND_IMG, exist_ok=True)
os.makedirs(BACKEND_DIST_IMG, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

# -------------------------------------------------------------
# 1. RENDER MASTER SQUIRCLE ICON AT 4096 x 4096 (Supersampled 4x)
# -------------------------------------------------------------
S = 4096
im = Image.new("RGBA", (S, S), (0, 0, 0, 0))

# Squircle bounds
margin = 160
rect = [margin, margin, S - margin, S - margin]
corner_radius = 1080  # Smooth continuous curvature

# 1A. Squircle Mask
sq_mask = Image.new("L", (S, S), 0)
m_draw = ImageDraw.Draw(sq_mask)
m_draw.rounded_rectangle(rect, radius=corner_radius, fill=255)

# 1B. Velvet Burgundy Gradient Canvas
# Top-center to bottom-center subtle luxury radial-linear falloff
# Center: #7a1c36 (122, 28, 54), Edge: #50101f (80, 16, 31)
bg_arr = np.zeros((S, S, 4), dtype=np.uint8)
center_y = S // 2
center_x = S // 2
max_dist = math.hypot(S // 2 - margin, S // 2 - margin)

# Vectorized gradient calculation for speed
y_coords, x_coords = np.ogrid[:S, :S]
dist_from_center = np.sqrt((x_coords - center_x) ** 2 + (y_coords - center_y) ** 2)
t_dist = np.clip(dist_from_center / max_dist, 0.0, 1.0)

# Vertical bias (light comes from top-left)
t_vert = (y_coords / S) * 0.4 + (x_coords / S) * 0.2

t_blend = np.clip(t_dist * 0.6 + t_vert * 0.4, 0.0, 1.0)

# Colors
r_val = (124 * (1 - 0.35 * t_blend)).astype(np.uint8)
g_val = (28 * (1 - 0.40 * t_blend)).astype(np.uint8)
b_val = (54 * (1 - 0.42 * t_blend)).astype(np.uint8)

bg_arr[:, :, 0] = r_val
bg_arr[:, :, 1] = g_val
bg_arr[:, :, 2] = b_val
bg_arr[:, :, 3] = 255

bg_img = Image.fromarray(bg_arr, "RGBA")
im.paste(bg_img, (0, 0), mask=sq_mask)

# 1C. Subtle Inner Ambient Rim Light (Delicate champagne rim)
rim_outer = Image.new("L", (S, S), 0)
ImageDraw.Draw(rim_outer).rounded_rectangle(rect, radius=corner_radius, fill=255)

inner_margin = margin + 18
inner_radius = corner_radius - 18
rim_inner = Image.new("L", (S, S), 0)
ImageDraw.Draw(rim_inner).rounded_rectangle([inner_margin, inner_margin, S - inner_margin, S - inner_margin], radius=inner_radius, fill=255)

rim_border = Image.fromarray(np.clip(np.array(rim_outer, dtype=np.int16) - np.array(rim_inner, dtype=np.int16), 0, 255).astype(np.uint8))
rim_color = Image.new("RGBA", (S, S), (245, 218, 175, 45))  # 18% opacity champagne rim
im.paste(rim_color, (0, 0), mask=rim_border)


# -------------------------------------------------------------
# 2. RENDER INTERLOCKING CHAMPAGNE GOLD RINGS
# -------------------------------------------------------------
# Proportions matched to user's icon:
# Radius = 700 px at 4096 (175 px at 1024)
# Stroke width = 152 px at 4096 (38 px at 1024)
# Separation = 680 px at 4096 (170 px at 1024)
cx1 = center_x - 340  # 1708
cx2 = center_x + 340  # 2388
cy = center_y         # 2048
R_ring = 700
w_ring = 152

# Create multi-stop gradient for the champagne gold rings
# Champagne gold: #fae2be (highlight), #d2aa62 (core), #a87936 (shadow)
def create_ring_layer():
    ring_img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    return ring_img

# We draw left and right rings with anti-aliasing and depth:
rings_canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0))

# Left ring mask
mask_r1 = Image.new("L", (S, S), 0)
d1 = ImageDraw.Draw(mask_r1)
d1.ellipse([cx1 - R_ring, cy - R_ring, cx1 + R_ring, cy + R_ring], fill=255)
d1.ellipse([cx1 - R_ring + w_ring, cy - R_ring + w_ring, cx1 + R_ring - w_ring, cy + R_ring - w_ring], fill=0)

# Right ring mask
mask_r2 = Image.new("L", (S, S), 0)
d2 = ImageDraw.Draw(mask_r2)
d2.ellipse([cx2 - R_ring, cy - R_ring, cx2 + R_ring, cy + R_ring], fill=255)
d2.ellipse([cx2 - R_ring + w_ring, cy - R_ring + w_ring, cx2 + R_ring - w_ring, cy + R_ring - w_ring], fill=0)

# Champagne gold metallic texture (subtle diagonal gradient for natural jewelry luster)
gold_arr = np.zeros((S, S, 4), dtype=np.uint8)
diag = ((x_coords * 0.7 + (S - y_coords) * 0.3) / S)
t_gold = 0.5 + 0.5 * np.sin(diag * math.pi * 3.5)

# Champagne palette:
# base #d0a762 (208, 167, 98)
# highlight #fae5be (250, 229, 190)
# shadow #ab7b35 (171, 123, 53)
r_g = (171 + (250 - 171) * (0.6 * t_gold + 0.4)).astype(np.uint8)
g_g = (123 + (229 - 123) * (0.6 * t_gold + 0.4)).astype(np.uint8)
b_g = (53 + (190 - 53) * (0.6 * t_gold + 0.4)).astype(np.uint8)

gold_arr[:, :, 0] = r_g
gold_arr[:, :, 1] = g_g
gold_arr[:, :, 2] = b_g
gold_arr[:, :, 3] = 255
gold_tex = Image.fromarray(gold_arr, "RGBA")

# 2A. Render Right Ring Base
rings_canvas.paste(gold_tex, (0, 0), mask=mask_r2)

# 2B. Render Left Ring on top (Top intersection: Left ring is ON TOP)
# Add subtle drop shadow from left ring onto right ring at top intersection
r1_shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
r1_shadow.paste((20, 5, 10, 140), (0, 16), mask=mask_r1)
r1_shadow = r1_shadow.filter(ImageFilter.GaussianBlur(radius=24))
rings_canvas.paste(r1_shadow, (0, 0), mask=mask_r2)

# Paste left ring
rings_canvas.paste(gold_tex, (0, 0), mask=mask_r1)

# 2C. Interlocking Weave:
# At the bottom intersection (y > cy), the RIGHT ring must cross OVER the left ring!
# We create a mask for the bottom crossover of the right ring:
# Angle range: right ring from 110 to 175 degrees
mask_r2_crossover = Image.new("L", (S, S), 0)
d_cross = ImageDraw.Draw(mask_r2_crossover)
# Pie slice or arc bbox
d_cross.pieslice([cx2 - R_ring - 10, cy - R_ring - 10, cx2 + R_ring + 10, cy + R_ring + 10], start=112, end=172, fill=255)
# Intersect with right ring mask
mask_r2_crossover_arr = np.minimum(np.array(mask_r2_crossover), np.array(mask_r2))
mask_r2_crossover_clean = Image.fromarray(mask_r2_crossover_arr, "L")

# Shadow under bottom crossover onto left ring
r2_cross_shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
r2_cross_shadow.paste((20, 5, 10, 140), (0, 16), mask=mask_r2_crossover_clean)
r2_cross_shadow = r2_cross_shadow.filter(ImageFilter.GaussianBlur(radius=24))
rings_canvas.paste(r2_cross_shadow, (0, 0), mask=mask_r1)

# Paste right ring bottom crossover on top!
rings_canvas.paste(gold_tex, (0, 0), mask=mask_r2_crossover_clean)

# 2D. Add Subtle Specular Rim Light to Rings (Jewelry bevel effect)
spec_layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
s_draw = ImageDraw.Draw(spec_layer)
spec_stroke = 14
# Inner and outer delicate edge arcs
s_draw.ellipse([cx1 - R_ring + 8, cy - R_ring + 8, cx1 + R_ring - 8, cy + R_ring - 8], outline=(255, 245, 220, 60), width=spec_stroke)
s_draw.ellipse([cx2 - R_ring + 8, cy - R_ring + 8, cx2 + R_ring - 8, cy + R_ring - 8], outline=(255, 245, 220, 60), width=spec_stroke)

# Composite rings onto squircle
# First, subtle ambient ring shadow on the burgundy velvet base
ambient_ring_mask = Image.fromarray(np.maximum(np.array(mask_r1), np.array(mask_r2)), "L")
ambient_shadow = Image.new("RGBA", (S, S), (15, 3, 7, 160))
im.paste(ambient_shadow, (0, 24), mask=ambient_ring_mask.filter(ImageFilter.GaussianBlur(radius=40)))

# Paste rings
im = Image.alpha_composite(im, rings_canvas)
im = Image.alpha_composite(im, spec_layer)

# -------------------------------------------------------------
# 3. EXPORT MASTER ASSETS (LANCZOS DOWNSAMPLED FOR SILKY CRISPNESS)
# -------------------------------------------------------------
print("Downsampling master 4096x4096 to production resolutions...")
icon_1024 = im.resize((1024, 1024), Image.Resampling.LANCZOS)
icon_512 = im.resize((512, 512), Image.Resampling.LANCZOS)
icon_256 = im.resize((256, 256), Image.Resampling.LANCZOS)
icon_128 = im.resize((128, 128), Image.Resampling.LANCZOS)
icon_64 = im.resize((64, 64), Image.Resampling.LANCZOS)

# Save Master Icons
icon_1024.save(os.path.join(FRONTEND_IMG, "cupl_icon_master.png"), "PNG")
icon_512.save(os.path.join(FRONTEND_IMG, "cupl_icon_squircle.png"), "PNG")
icon_1024.save(os.path.join(BACKEND_DIST_IMG, "cupl_icon_master.png"), "PNG")
icon_512.save(os.path.join(BACKEND_DIST_IMG, "cupl_icon_squircle.png"), "PNG")

# Save Favicons
icon_64.save(r"frontend/public/favicon.png", "PNG")
icon_256.save(r"frontend/public/favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
if os.path.exists(r"backend/dist"):
    icon_64.save(r"backend/dist/favicon.png", "PNG")
    icon_256.save(r"backend/dist/favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

print("Saved master icons and favicons.")


# -------------------------------------------------------------
# 4. MASTER LUXURY CIRCULAR AVATAR MEDALLION FOR AI COMPANION STAGE
# -------------------------------------------------------------
# Circular luxury medallion specifically designed for circular avatars (ChatPage AI stage, voice overlay, chat bubbles)
medallion = Image.new("RGBA", (S, S), (0, 0, 0, 0))

# Circular Mask
circle_margin = 120
circle_rect = [circle_margin, circle_margin, S - circle_margin, S - circle_margin]
c_mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(c_mask).ellipse(circle_rect, fill=255)

# Radial Burgundy Gradient for Circular Medallion
med_arr = np.zeros((S, S, 4), dtype=np.uint8)
t_circ_dist = np.clip(dist_from_center / (S // 2 - circle_margin), 0.0, 1.0)
# Center #821f3a, Edge #460c19 (deep velvet radial depth)
r_med = (130 * (1 - 0.45 * t_circ_dist)).astype(np.uint8)
g_med = (31 * (1 - 0.50 * t_circ_dist)).astype(np.uint8)
b_med = (58 * (1 - 0.52 * t_circ_dist)).astype(np.uint8)
med_arr[:, :, 0] = r_med
med_arr[:, :, 1] = g_med
med_arr[:, :, 2] = b_med
med_arr[:, :, 3] = 255
med_bg = Image.fromarray(med_arr, "RGBA")
medallion.paste(med_bg, (0, 0), mask=c_mask)

# Circular Outer Gold Rim Light
c_rim_mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(c_rim_mask).ellipse(circle_rect, outline=255, width=28)
c_rim_color = Image.new("RGBA", (S, S), (245, 218, 175, 70))
medallion.paste(c_rim_color, (0, 0), mask=c_rim_mask)

# Concentric Golden Aura Ring (subtle elegance)
aura_rect = [circle_margin + 140, circle_margin + 140, S - circle_margin - 140, S - circle_margin - 140]
aura_mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(aura_mask).ellipse(aura_rect, outline=255, width=12)
aura_color = Image.new("RGBA", (S, S), (218, 168, 98, 40))
medallion.paste(aura_color, (0, 0), mask=aura_mask)

# Paste the Interlocking Rings onto Medallion
medallion.paste(ambient_shadow, (0, 24), mask=ambient_ring_mask.filter(ImageFilter.GaussianBlur(radius=40)))
medallion = Image.alpha_composite(medallion, rings_canvas)
medallion = Image.alpha_composite(medallion, spec_layer)

# Downscale to 512x512 JPEG for avatar.jpg (crisp, zero compression noise)
avatar_512 = medallion.resize((512, 512), Image.Resampling.LANCZOS)
# Flatten to RGB with velvet background for JPEG
avatar_final = Image.new("RGB", (512, 512), (109, 27, 49))
avatar_final.paste(avatar_512, (0, 0), mask=avatar_512)

avatar_final.save(os.path.join(FRONTEND_IMG, "avatar.jpg"), "JPEG", quality=98)
avatar_final.save(os.path.join(BACKEND_DIST_IMG, "avatar.jpg"), "JPEG", quality=98)
print("Saved luxury circular AI medallion: avatar.jpg")


# -------------------------------------------------------------
# 5. RENDER HIGH-RESOLUTION HORIZONTAL BRAND LOGO
# -------------------------------------------------------------
# Width 2400 x Height 700 with transparent background
LW, LH = 2400, 700
logo_im = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))

# Paste Squircle Icon on the left
icon_logo_size = 480
icon_for_logo = icon_1024.resize((icon_logo_size, icon_logo_size), Image.Resampling.LANCZOS)
logo_icon_x = 120
logo_icon_y = (LH - icon_logo_size) // 2 - 20
logo_im.paste(icon_for_logo, (logo_icon_x, logo_icon_y), mask=icon_for_logo)

# Draw "cupl.ai" and Tagline
l_draw = ImageDraw.Draw(logo_im)

# Load fonts
try:
    font_main = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 260)
    font_sub = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 58)
except Exception:
    font_main = ImageFont.load_default()
    font_sub = ImageFont.load_default()

# Text positions
text_x = logo_icon_x + icon_logo_size + 80
text_y = logo_icon_y + 40

# "cupl" in Velvet Burgundy #6b1b31
l_draw.text((text_x, text_y), "cupl", fill=(107, 27, 49, 255), font=font_main)
cupl_w = l_draw.textlength("cupl", font=font_main)

# ".ai" in Champagne Gold or Burgundy
# User's logo had ".ai" in matching burgundy
l_draw.text((text_x + cupl_w, text_y), ".ai", fill=(107, 27, 49, 255), font=font_main)

# Tagline "Your AI concierge for life together"
tagline_y = text_y + 245
tagline_text = "Your AI concierge for life together"
l_draw.text((text_x + 6, tagline_y), tagline_text, fill=(138, 110, 95, 255), font=font_sub)

logo_im.save(os.path.join(FRONTEND_IMG, "cupl_logo_horizontal.png"), "PNG")
logo_im.save(os.path.join(BACKEND_DIST_IMG, "cupl_logo_horizontal.png"), "PNG")

# Also save version with Alabaster Cream background (#f7f6f1) like user's upload
logo_cream = Image.new("RGBA", (LW, LH), (247, 246, 241, 255))
logo_cream = Image.alpha_composite(logo_cream, logo_im)
logo_cream.convert("RGB").save(os.path.join(FRONTEND_IMG, "cupl_logo_cream.jpg"), "JPEG", quality=98)
logo_cream.convert("RGB").save(os.path.join(ARTIFACT_DIR, "cupl_improved_logo_preview.jpg"), "JPEG", quality=98)

# Save Icon preview artifact
icon_1024.save(os.path.join(ARTIFACT_DIR, "cupl_improved_icon_master.png"), "PNG")
avatar_final.save(os.path.join(ARTIFACT_DIR, "cupl_improved_avatar_preview.jpg"), "JPEG", quality=98)

print("All improved brand assets generated and saved successfully!")
