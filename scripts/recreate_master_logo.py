import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Canvas dimensions: 2600 x 932 (4x the original 651 x 233)
W, H = 2604, 932
SCALE = 4.0

# 1. Background: Rich velvet burgundy #4f0f20
bg_color = (79, 15, 32, 255)  # #4f0f20
im = Image.new("RGBA", (W, H), bg_color)
draw = ImageDraw.Draw(im)

# 2. Render High-Resolution Heart Mark on Left
# In original 651x233:
# Heart bbox was roughly X: 94..219, Y: 62..190 -> Center ~ (156, 126), Width ~ 125, Height ~ 128
# At 4x: Center ~ (624, 504), Size ~ 500x512
# Let's draw the two petals using supersampled high-precision polygon / bezier curves

# Supersample factor 2x for the heart layer (5200 x 1864)
SS = 2
HW, HH = W * SS, H * SS
heart_layer = Image.new("RGBA", (HW, HH), (0, 0, 0, 0))
h_draw = ImageDraw.Draw(heart_layer)

# Scale coordinates for SS
s = SCALE * SS

# Heart anchor points (in original 1x coordinates, scaled by s):
# Tip of heart: (198, 188)
tip_x = 196 * s
tip_y = 188 * s

# --- Left Petal (Warm Peach Blush #f7d1c6) ---
# Tilted oval / teardrop petal
# Left petal crest: (126, 62)
# Left petal outer waist: (94, 93)
# Left petal inner waist: (144, 125)
peach_color = (247, 209, 198, 255)  # #f7d1c6
rose_color = (206, 113, 123, 255)   # #ce7179

# Generate left petal bezier / polygon curve:
# A smooth tilted lobe
def get_left_petal_points():
    pts = []
    # Start at tip
    pts.append((tip_x, tip_y))
    # Curve up the left side through outer waist (94, 93) to crest (126, 62)
    # Cubic bezier: tip -> cp1 -> cp2 -> crest
    # tip is (196, 188)
    p0 = np.array([tip_x, tip_y])
    p1 = np.array([90 * s, 170 * s])
    p2 = np.array([84 * s, 105 * s])
    p3 = np.array([126 * s, 62 * s])
    for t in np.linspace(0, 1, 60):
        pt = (1-t)**3 * p0 + 3*(1-t)**2*t * p1 + 3*(1-t)*t**2 * p2 + t**3 * p3
        pts.append((pt[0], pt[1]))

    # Top crest curve from (126, 62) down to inner curve (155, 95)
    p0 = np.array([126 * s, 62 * s])
    p1 = np.array([146 * s, 54 * s])
    p2 = np.array([168 * s, 72 * s])
    p3 = np.array([162 * s, 102 * s])
    for t in np.linspace(0, 1, 40):
        pt = (1-t)**3 * p0 + 3*(1-t)**2*t * p1 + 3*(1-t)*t**2 * p2 + t**3 * p3
        pts.append((pt[0], pt[1]))

    # Inner curve down to tip
    p0 = np.array([162 * s, 102 * s])
    p1 = np.array([142 * s, 130 * s])
    p2 = np.array([150 * s, 168 * s])
    p3 = np.array([tip_x, tip_y])
    for t in np.linspace(0, 1, 40):
        pt = (1-t)**3 * p0 + 3*(1-t)**2*t * p1 + 3*(1-t)*t**2 * p2 + t**3 * p3
        pts.append((pt[0], pt[1]))

    return [(float(x), float(y)) for x, y in pts]

# --- Right Petal (Rose Pink #ce7179) ---
# Right petal crest: (186, 78)
# Right petal outer curve: (218, 120) to (214, 165)
# Inner overlap seam down to tip
def get_right_petal_points():
    pts = []
    # Start at tip
    pts.append((tip_x, tip_y))
    # Curve up the right side through (218, 145) to (186, 78)
    p0 = np.array([tip_x, tip_y])
    p1 = np.array([218 * s, 180 * s])
    p2 = np.array([225 * s, 120 * s])
    p3 = np.array([186 * s, 78 * s])
    for t in np.linspace(0, 1, 60):
        pt = (1-t)**3 * p0 + 3*(1-t)**2*t * p1 + 3*(1-t)*t**2 * p2 + t**3 * p3
        pts.append((pt[0], pt[1]))

    # Top crest curve from (186, 78) down to inner seam (158, 92)
    p0 = np.array([186 * s, 78 * s])
    p1 = np.array([172 * s, 74 * s])
    p2 = np.array([160 * s, 84 * s])
    p3 = np.array([154 * s, 98 * s])
    for t in np.linspace(0, 1, 40):
        pt = (1-t)**3 * p0 + 3*(1-t)**2*t * p1 + 3*(1-t)*t**2 * p2 + t**3 * p3
        pts.append((pt[0], pt[1]))

    # Inner seam curve down to tip (creating the graceful crescent overlap)
    p0 = np.array([154 * s, 98 * s])
    p1 = np.array([142 * s, 125 * s])
    p2 = np.array([146 * s, 160 * s])
    p3 = np.array([tip_x, tip_y])
    for t in np.linspace(0, 1, 40):
        pt = (1-t)**3 * p0 + 3*(1-t)**2*t * p1 + 3*(1-t)*t**2 * p2 + t**3 * p3
        pts.append((pt[0], pt[1]))

    return [(float(x), float(y)) for x, y in pts]

# Draw Left Petal
left_pts = get_left_petal_points()
h_draw.polygon(left_pts, fill=peach_color)

# Draw Right Petal with realistic translucent opacity (so overlap shows)
right_layer = Image.new("RGBA", (HW, HH), (0, 0, 0, 0))
r_draw = ImageDraw.Draw(right_layer)
right_pts = get_right_petal_points()
r_draw.polygon(right_pts, fill=(206, 113, 121, 230))  # 90% opacity rose

# Highlight curve along the overlap seam (delicate light line)
seam_pts = []
p0 = np.array([154 * s, 98 * s])
p1 = np.array([142 * s, 125 * s])
p2 = np.array([146 * s, 160 * s])
p3 = np.array([tip_x, tip_y])
for t in np.linspace(0, 1, 60):
    pt = (1-t)**3 * p0 + 3*(1-t)**2*t * p1 + 3*(1-t)*t**2 * p2 + t**3 * p3
    seam_pts.append((float(pt[0]), float(pt[1])))
r_draw.line(seam_pts, fill=(255, 235, 230, 180), width=int(3 * s))

# Composite right petal onto heart layer
heart_layer = Image.alpha_composite(heart_layer, right_layer)

# Downscale heart layer with Lanczos to master canvas
heart_down = heart_layer.resize((W, H), Image.Resampling.LANCZOS)
im = Image.alpha_composite(im, heart_down)


# -------------------------------------------------------------
# 3. RENDER CRISP TYPOGRAPHY FOR "cupl.ai" AND ENLARGED TAGLINE
# -------------------------------------------------------------
t_draw = ImageDraw.Draw(im)

# Load font: Segoe UI Bold / Bahnschrift for rounded geometric modern brand
try:
    font_main = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", int(92 * SCALE))
    font_ai = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", int(92 * SCALE))
    # Tagline: make it significantly bigger as requested!
    # Original was ~14px (56px at 4x). Let's make it 24px (96px at 4x) or 22px (88px at 4x) - bold, clear, legible!
    font_tagline = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", int(23 * SCALE))
except Exception:
    font_main = font_ai = font_tagline = ImageFont.load_default()

# Coordinates matching user logo layout
text_start_x = int(238 * SCALE)
text_y = int(52 * SCALE)

# "cupl" in pure white #ffffff
t_draw.text((text_start_x, text_y), "cupl", fill=(255, 255, 255, 255), font=font_main)
cupl_len = t_draw.textlength("cupl", font=font_main)

# ".a" in soft rose pink #ee9fa4
dot_ai_x = text_start_x + cupl_len
t_draw.text((dot_ai_x, text_y), ".a", fill=(238, 159, 164, 255), font=font_ai)
dot_a_len = t_draw.textlength(".a", font=font_ai)

# 'i' stem in soft rose pink (without standard dot, we draw the heart tittle!)
i_x = dot_ai_x + dot_a_len + int(3 * SCALE)
# Draw the stem of 'i'
# In segoeuib at this size:
stem_w = int(14 * SCALE)
stem_h = int(58 * SCALE)
stem_top = text_y + int(34 * SCALE)
stem_left = i_x + int(4 * SCALE)
t_draw.rounded_rectangle([stem_left, stem_top, stem_left + stem_w, stem_top + stem_h], radius=int(4*SCALE), fill=(238, 159, 164, 255))

# Draw the CUTE SOLID PINK HEART TITTLE above the 'i'!
# Heart center ~ (stem_left + stem_w/2, text_y + 14 * SCALE)
hc_x = stem_left + stem_w / 2
hc_y = text_y + int(14 * SCALE)
hr_w = int(14 * SCALE)
hr_h = int(13 * SCALE)

# Heart polygon
def get_heart_tittle_points(cx, cy, w, h):
    pts = []
    # Parametric heart equation
    for angle in np.linspace(0, 2 * math.pi, 60):
        # standard cardioid / heart curve
        hx = 16 * (math.sin(angle) ** 3)
        hy = -(13 * math.cos(angle) - 5 * math.cos(2*angle) - 2 * math.cos(3*angle) - math.cos(4*angle))
        px = cx + (hx / 16.0) * w
        py = cy + (hy / 16.0) * h
        pts.append((px, py))
    return pts

heart_tittle_pts = get_heart_tittle_points(hc_x, hc_y, hr_w, hr_h)
t_draw.polygon(heart_tittle_pts, fill=(238, 159, 164, 255))


# -------------------------------------------------------------
# 4. ENLARGED, CRISP, BEAUTIFULLY PROPORTIONED TAGLINE
# -------------------------------------------------------------
# User request: "make that tagline font little bigger, and then apply properly in the places"
tagline_text = "Your AI concierge for life together"
tagline_y = text_y + int(112 * SCALE)

# In the original, the tagline starts below the heart or wordmark.
# Original tagline X was roughly 185 to 540
tagline_x = int(184 * SCALE)
t_draw.text((tagline_x, tagline_y), tagline_text, fill=(255, 255, 255, 255), font=font_tagline)

# Save Master Logo
out_master = "frontend/public/img/cupl_logo.png"
im.save(out_master, "PNG")
im.convert("RGB").save("frontend/public/img/cupl_logo.jpg", "JPEG", quality=98)
im.save("backend/dist/img/cupl_logo.png", "PNG")
im.convert("RGB").save("backend/dist/img/cupl_logo.jpg", "JPEG", quality=98)

# Also save artifact for inspection
artifact_path = r"C:\Users\admin\.gemini\antigravity\brain\6d8e9353-5c79-4cdf-92cf-1fafc99c77a9\cupl_logo_recreated_hd.png"
im.save(artifact_path, "PNG")

print("Successfully recreated master logo at 2604x932 with razor-sharp vector-grade quality!")
print(f"Saved to {out_master} and {artifact_path}")
