import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

# 1. Generate Ultra-Crisp Master Icon (1024x1024 with 2x supersampling at 2048x2048)
S = 2048
im = Image.new("RGBA", (S, S), (0, 0, 0, 0))

# Create Squircle Base
# In 2048x2048:
margin = 80
rect = [margin, margin, S - margin, S - margin]
radius = 540  # iOS continuous squircle corner

# Create gradient mask for the squircle
mask = Image.new("L", (S, S), 0)
m_draw = ImageDraw.Draw(mask)
m_draw.rounded_rectangle(rect, radius=radius, fill=255)

# Gradient background for luxury velvet burgundy
# Top-left slightly brighter (#7d1f35), bottom-right deeper (#5e1424)
bg_arr = np.zeros((S, S, 4), dtype=np.uint8)
for y in range(S):
    t = y / S
    r = int(125 * (1 - 0.25 * t))
    g = int(32 * (1 - 0.3 * t))
    b = int(54 * (1 - 0.3 * t))
    bg_arr[y, :, 0] = r
    bg_arr[y, :, 1] = g
    bg_arr[y, :, 2] = b
    bg_arr[y, :, 3] = 255

bg_img = Image.fromarray(bg_arr, "RGBA")
im.paste(bg_img, (0, 0), mask=mask)

# Add subtle inner border / ambient rim light
rim_mask = Image.new("L", (S, S), 0)
rim_draw = ImageDraw.Draw(rim_mask)
rim_draw.rounded_rectangle(rect, radius=radius, outline=255, width=12)
rim_glow = Image.new("RGBA", (S, S), (255, 215, 175, 45))
im.paste(rim_glow, (0, 0), mask=rim_mask)

# Rings Geometry
# Centers:
cx1 = S // 2 - 170  # 854
cx2 = S // 2 + 170  # 1194
cy = S // 2         # 1024
radius_ring = 350
stroke_w = 76

# We draw rings on a separate layer for clean anti-aliasing and depth
rings_layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
r_draw = ImageDraw.Draw(rings_layer)

gold_base = (218, 168, 98, 255)       # Champagne gold #daa862
gold_highlight = (245, 218, 168, 255)  # Warm highlight #f5daa8
gold_shadow = (175, 128, 65, 255)      # Deep gold #af8041

# Draw Right Ring first (below on top crossover)
r_draw.ellipse(
    [cx2 - radius_ring, cy - radius_ring, cx2 + radius_ring, cy + radius_ring],
    outline=gold_base,
    width=stroke_w
)

# Draw Left Ring
r_draw.ellipse(
    [cx1 - radius_ring, cy - radius_ring, cx1 + radius_ring, cy + radius_ring],
    outline=gold_base,
    width=stroke_w
)

# Interlocking Cross-Over:
# At the bottom intersection (cy > S//2), right ring should be in FRONT
# Top intersection: Left ring is in front.
# We redraw an arc of the Right ring near bottom intersection:
# Angle in PIL: 0 is 3 o'clock. Bottom intersection is around angle 110 to 160 degrees for right ring.
bbox_r = [cx2 - radius_ring, cy - radius_ring, cx2 + radius_ring, cy + radius_ring]
r_draw.arc(bbox_r, start=115, end=175, fill=gold_base, width=stroke_w)

# Add subtle inner specular shine to rings
shine_layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
s_draw = ImageDraw.Draw(shine_layer)
s_draw.ellipse(
    [cx2 - radius_ring + 4, cy - radius_ring + 4, cx2 + radius_ring - 4, cy + radius_ring - 4],
    outline=(255, 240, 210, 80),
    width=6
)
s_draw.ellipse(
    [cx1 - radius_ring + 4, cy - radius_ring + 4, cx1 + radius_ring - 4, cy + radius_ring - 4],
    outline=(255, 240, 210, 80),
    width=6
)
s_draw.arc([cx2 - radius_ring + 4, cy - radius_ring + 4, cx2 + radius_ring - 4, cy + radius_ring - 4], start=115, end=175, fill=(255, 240, 210, 80), width=6)

# Composite layers
im = Image.alpha_composite(im, rings_layer)
im = Image.alpha_composite(im, shine_layer)

# Downscale with high-quality Lanczos resampling to 1024x1024
master_1024 = im.resize((1024, 1024), Image.Resampling.LANCZOS)
master_1024.save(r"frontend/public/img/cupl_icon_master.png")
print("Saved frontend/public/img/cupl_icon_master.png")

# Also save avatar.jpg (circular or square for AI avatar)
# For the AI avatar: 512x512 JPEG with soft silk background
avatar_512 = master_1024.resize((512, 512), Image.Resampling.LANCZOS)

# Create avatar canvas with circular luxury background for AI stage
avatar_canvas = Image.new("RGB", (512, 512), (111, 26, 46))
# Paste icon centered
avatar_512_crop = master_1024.resize((480, 480), Image.Resampling.LANCZOS)
avatar_canvas.paste(avatar_512_crop, (16, 16), mask=avatar_512_crop)

avatar_canvas.save(r"frontend/public/img/avatar.jpg", quality=98)
avatar_canvas.save(r"backend/dist/img/avatar.jpg", quality=98)
print("Saved frontend/public/img/avatar.jpg and backend/dist/img/avatar.jpg")

