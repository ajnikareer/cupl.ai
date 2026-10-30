import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ARTIFACT_DIR = r"C:\Users\admin\.gemini\antigravity\brain\6d8e9353-5c79-4cdf-92cf-1fafc99c77a9"
OUT_PATH = os.path.join(ARTIFACT_DIR, "cupl_logo_8_new_options_showcase.png")

# Canvas: 2400 x 3200
CW, CH = 2400, 3200
canvas = Image.new("RGBA", (CW, CH), (250, 247, 242, 255))  # #faf7f2 Alabaster Cream
draw = ImageDraw.Draw(canvas)

# Fonts
try:
    f_hero = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 64)
    f_subhero = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 28)
    f_badge = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 22)
    f_opt_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 32)
    f_opt_desc = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 22)
    f_logo_brand = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 52)
    f_logo_ai = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 52)
    f_tagline = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 18)
except Exception:
    f_hero = f_subhero = f_badge = f_opt_title = f_opt_desc = f_logo_brand = f_logo_ai = f_tagline = ImageFont.load_default()

# Colors
C_BURGUNDY = (107, 27, 49, 255)       # #6b1b31
C_DEEP_WINE = (80, 16, 33, 255)       # #501021
C_GOLD = (212, 165, 93, 255)          # #d4a55d
C_ROSE = (238, 159, 164, 255)         # #ee9fa4
C_PEACH = (247, 209, 198, 255)        # #f7d1c6
C_CREAM = (250, 247, 242, 255)        # #faf7f2
C_WHITE = (255, 255, 255, 255)
C_MUTED = (140, 105, 115, 255)
C_BORDER = (235, 222, 218, 255)

# --- Header ---
draw.text((100, 60), "cupl.ai — New Brand Identity & Icon Options", fill=C_BURGUNDY, font=f_hero)
draw.text((100, 140), "8 Sweet, Minimalist, Non-3D Concepts • Flat Vector Craftsmanship • App Icons & Horizontal Logos", fill=C_MUTED, font=f_subhero)

# Grid parameters
COLS = 2
ROWS = 4
CARD_W = 1060
CARD_H = 680
START_X = 100
START_Y = 210
GAP_X = 80
GAP_Y = 50

# Helper to draw an AI sparkle 4-pointed star
def draw_sparkle(d, cx, cy, r_outer, r_inner, color):
    pts = []
    for i in range(8):
        ang = i * (math.pi / 4)
        r = r_outer if i % 2 == 0 else r_inner
        pts.append((cx + r * math.sin(ang), cy - r * math.cos(ang)))
    d.polygon(pts, fill=color)

# Helper to draw a heart polygon
def draw_heart(d, cx, cy, w, h, color):
    pts = []
    for ang in np.linspace(0, 2 * math.pi, 60):
        hx = 16 * (math.sin(ang) ** 3)
        hy = -(13 * math.cos(ang) - 5 * math.cos(2*ang) - 2 * math.cos(3*ang) - math.cos(4*ang))
        pts.append((cx + (hx / 16.0) * w, cy + (hy / 16.0) * h))
    d.polygon(pts, fill=color)

# Render each option
def render_option(idx, col, row, title, desc, draw_icon_fn, dark_logo=False):
    x = START_X + col * (CARD_W + GAP_X)
    y = START_Y + row * (CARD_H + GAP_Y)

    # Card background
    draw.rounded_rectangle([x, y, x + CARD_W, y + CARD_H], radius=24, fill=C_WHITE, outline=C_BORDER, width=2)

    # Option Badge
    badge_txt = f"OPTION {idx}"
    bw = draw.textlength(badge_txt, font=f_badge) + 24
    draw.rounded_rectangle([x + 36, y + 30, x + 36 + bw, y + 68], radius=10, fill=(245, 235, 238, 255))
    draw.text((x + 48, y + 36), badge_txt, fill=C_BURGUNDY, font=f_badge)

    # Title & Desc
    draw.text((x + 36 + bw + 18, y + 32), title, fill=(30, 15, 22, 255), font=f_opt_title)
    draw.text((x + 36, y + 84), desc, fill=C_MUTED, font=f_opt_desc)

    # Section 1: Standalone App Icon (220 x 220)
    icon_box_x = x + 40
    icon_box_y = y + 140
    icon_size = 200

    icon_img = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
    i_draw = ImageDraw.Draw(icon_img)
    draw_icon_fn(i_draw, icon_size, is_app_icon=True)
    canvas.paste(icon_img, (icon_box_x, icon_box_y), mask=icon_img)

    draw.text((icon_box_x + 35, icon_box_y + icon_size + 15), "App Icon", fill=C_MUTED, font=f_tagline)

    # Section 2: Horizontal Logo Lockup
    logo_box_x = x + 300
    logo_box_y = y + 140
    logo_w = 720
    logo_h = 200

    # Draw logo container
    logo_card = Image.new("RGBA", (logo_w, logo_h), (0, 0, 0, 0))
    lc_draw = ImageDraw.Draw(logo_card)
    bg_c = C_DEEP_WINE if dark_logo else (255, 250, 248, 255)
    border_c = (120, 30, 50, 255) if dark_logo else C_BORDER
    lc_draw.rounded_rectangle([0, 0, logo_w, logo_h], radius=18, fill=bg_c, outline=border_c, width=1)

    # Small mark inside logo lockup (80 x 80)
    mark_s = 90
    mark_img = Image.new("RGBA", (mark_s, mark_s), (0, 0, 0, 0))
    m_draw = ImageDraw.Draw(mark_img)
    draw_icon_fn(m_draw, mark_s, is_app_icon=False)
    logo_card.paste(mark_img, (35, (logo_h - mark_s) // 2), mask=mark_img)

    # Text in logo lockup
    tx = 150
    ty = 48
    brand_color = C_WHITE if dark_logo else C_BURGUNDY
    ai_color = C_ROSE if dark_logo else C_GOLD
    tag_color = (235, 215, 220, 255) if dark_logo else C_MUTED

    lc_draw.text((tx, ty), "cupl", fill=brand_color, font=f_logo_brand)
    cw = lc_draw.textlength("cupl", font=f_logo_brand)

    # .ai
    lc_draw.text((tx + cw, ty), ".ai", fill=ai_color, font=f_logo_ai)

    # Heart or spark dot over 'i'
    # Tagline
    lc_draw.text((tx + 2, ty + 70), "Your AI concierge for life together", fill=tag_color, font=f_tagline)

    canvas.paste(logo_card, (logo_box_x, logo_box_y), mask=logo_card)
    draw.text((logo_box_x + 280, logo_box_y + logo_h + 15), "Horizontal Logo Lockup", fill=C_MUTED, font=f_tagline)


# =============================================================
# OPTION 1: The Woven Infinity Heart
# =============================================================
def draw_opt1(d, S, is_app_icon):
    # Squircle base
    if is_app_icon:
        d.rounded_rectangle([4, 4, S-4, S-4], radius=int(S*0.26), fill=C_BURGUNDY)
    cx, cy = S // 2, S // 2
    r = int(S * 0.22)
    w = max(4, int(S * 0.08))
    gold = C_GOLD if is_app_icon else C_BURGUNDY
    rose = C_ROSE if is_app_icon else C_GOLD

    # Draw two intersecting loops forming an infinity heart
    d.ellipse([cx - int(r*1.3), cy - int(r*0.6), cx + int(r*0.1), cy + int(r*0.8)], outline=gold, width=w)
    d.ellipse([cx - int(r*0.1), cy - int(r*0.6), cx + int(r*1.3), cy + int(r*0.8)], outline=rose, width=w)
    # Top crossover
    d.arc([cx - int(r*1.3), cy - int(r*0.6), cx + int(r*0.1), cy + int(r*0.8)], start=290, end=350, fill=gold, width=w)

# =============================================================
# OPTION 2: Dual Petals & AI Spark
# =============================================================
def draw_opt2(d, S, is_app_icon):
    if is_app_icon:
        d.rounded_rectangle([4, 4, S-4, S-4], radius=int(S*0.26), fill=(255, 245, 246, 255), outline=C_BORDER, width=2)
    cx, cy = S // 2, S // 2 + int(S * 0.04)
    tip = (cx, cy + int(S * 0.32))

    # Left petal (Burgundy)
    lp = [tip, (cx - int(S*0.35), cy + int(S*0.1)), (cx - int(S*0.35), cy - int(S*0.22)), (cx - int(S*0.08), cy - int(S*0.3)), (cx, cy - int(S*0.05)), tip]
    d.polygon(lp, fill=C_BURGUNDY)

    # Right petal (Rose Pink)
    rp = [tip, (cx + int(S*0.35), cy + int(S*0.1)), (cx + int(S*0.35), cy - int(S*0.22)), (cx + int(S*0.08), cy - int(S*0.3)), (cx, cy - int(S*0.05)), tip]
    d.polygon(rp, fill=C_ROSE)

    # Golden AI Sparkle in center cleft
    draw_sparkle(d, cx, cy - int(S * 0.28), int(S * 0.12), int(S * 0.04), C_GOLD)

# =============================================================
# OPTION 3: Minimalist Interlocking Wedding Bands (Luxury Line Art)
# =============================================================
def draw_opt3(d, S, is_app_icon):
    if is_app_icon:
        d.rounded_rectangle([4, 4, S-4, S-4], radius=int(S*0.26), fill=C_DEEP_WINE)
    cx, cy = S // 2, S // 2
    r = int(S * 0.26)
    w = max(4, int(S * 0.065))
    col = C_GOLD if is_app_icon else C_BURGUNDY

    # Right ring
    d.ellipse([cx - int(r*0.4), cy - r, cx + int(r*1.6), cy + r], outline=col, width=w)
    # Left ring
    d.ellipse([cx - int(r*1.6), cy - r, cx + int(r*0.4), cy + r], outline=col, width=w)
    # Weave overpass
    d.arc([cx - int(r*0.4), cy - r, cx + int(r*1.6), cy + r], start=120, end=175, fill=col, width=w)

# =============================================================
# OPTION 4: Embracing "c" & "u" Monogram (Clean & Modern)
# =============================================================
def draw_opt4(d, S, is_app_icon):
    if is_app_icon:
        d.rounded_rectangle([4, 4, S-4, S-4], radius=int(S*0.26), fill=(255, 255, 255, 255), outline=C_BORDER, width=2)
    cx, cy = S // 2, S // 2
    w = max(5, int(S * 0.11))

    # Outer 'c' embracing from left (Burgundy)
    d.arc([cx - int(S*0.35), cy - int(S*0.32), cx + int(S*0.18), cy + int(S*0.32)], start=55, end=305, fill=C_BURGUNDY, width=w)

    # Inner 'u' resting inside (Rose / Gold)
    d.arc([cx - int(S*0.08), cy - int(S*0.18), cx + int(S*0.32), cy + int(S*0.22)], start=0, end=180, fill=C_ROSE, width=w)
    # 'u' vertical stems
    d.line([(cx + int(S*0.32), cy - int(S*0.16)), (cx + int(S*0.32), cy + int(S*0.02))], fill=C_ROSE, width=w)
    d.line([(cx - int(S*0.08), cy - int(S*0.16)), (cx - int(S*0.08), cy + int(S*0.02))], fill=C_ROSE, width=w)

    # Small gold dot / spark between them
    d.ellipse([cx + int(S*0.12) - int(S*0.04), cy - int(S*0.22) - int(S*0.04), cx + int(S*0.12) + int(S*0.04), cy - int(S*0.22) + int(S*0.04)], fill=C_GOLD)

# =============================================================
# OPTION 5: The Taste Venn Diagram (Harmonized Love)
# =============================================================
def draw_opt5(d, S, is_app_icon):
    if is_app_icon:
        d.rounded_rectangle([4, 4, S-4, S-4], radius=int(S*0.26), fill=C_BURGUNDY)
    cx, cy = S // 2, S // 2
    r = int(S * 0.28)

    # Two overlapping translucent circles
    temp = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    td = ImageDraw.Draw(temp)
    # Circle 1 (Rose)
    td.ellipse([cx - int(r*1.2), cy - r, cx + int(r*0.2), cy + r], fill=(238, 159, 164, 180))
    # Circle 2 (Gold)
    td.ellipse([cx - int(r*0.2), cy - r, cx + int(r*1.2), cy + r], fill=(212, 165, 93, 180))
    # Heart in center intersection
    draw_heart(td, cx, cy, int(S * 0.12), int(S * 0.12), C_WHITE if is_app_icon else C_BURGUNDY)

    # Paste onto d's canvas
    d._image.paste(temp, (0, 0), mask=temp)

# =============================================================
# OPTION 6: The AI Spark Heart
# =============================================================
def draw_opt6(d, S, is_app_icon):
    if is_app_icon:
        d.rounded_rectangle([4, 4, S-4, S-4], radius=int(S*0.26), fill=(255, 252, 250, 255), outline=C_BORDER, width=2)
    cx, cy = S // 2, S // 2 + int(S * 0.05)
    w = max(5, int(S * 0.075))

    # Heart outline in burgundy
    d.arc([cx - int(S*0.35), cy - int(S*0.32), cx, cy + int(S*0.05)], start=140, end=360, fill=C_BURGUNDY, width=w)
    d.line([(cx - int(S*0.35), cy - int(S*0.05)), (cx, cy + int(S*0.28))], fill=C_BURGUNDY, width=w)
    d.line([(cx, cy + int(S*0.28)), (cx + int(S*0.3), cy)], fill=C_BURGUNDY, width=w)
    d.arc([cx, cy - int(S*0.32), cx + int(S*0.35), cy + int(S*0.05)], start=180, end=270, fill=C_BURGUNDY, width=w)

    # Sparkle star completing the right lobe
    draw_sparkle(d, cx + int(S * 0.22), cy - int(S * 0.2), int(S * 0.14), int(S * 0.05), C_GOLD)

# =============================================================
# OPTION 7: Continuous Couple Ribbon Knot
# =============================================================
def draw_opt7(d, S, is_app_icon):
    if is_app_icon:
        d.rounded_rectangle([4, 4, S-4, S-4], radius=int(S*0.26), fill=C_DEEP_WINE)
    cx, cy = S // 2, S // 2
    w = max(5, int(S * 0.08))

    # Rose loop
    d.arc([cx - int(S*0.3), cy - int(S*0.28), cx + int(S*0.1), cy + int(S*0.22)], start=100, end=340, fill=C_ROSE, width=w)
    # Gold loop interlocking
    d.arc([cx - int(S*0.1), cy - int(S*0.22), cx + int(S*0.3), cy + int(S*0.28)], start=280, end=160, fill=C_GOLD, width=w)
    # Center connection
    d.ellipse([cx - int(S*0.06), cy - int(S*0.06), cx + int(S*0.06), cy + int(S*0.06)], fill=C_WHITE if is_app_icon else C_BURGUNDY)

# =============================================================
# OPTION 8: The Circular AI Medallion (Twin Doves / Rose Silhouette)
# =============================================================
def draw_opt8(d, S, is_app_icon):
    if is_app_icon:
        d.ellipse([4, 4, S-4, S-4], fill=C_BURGUNDY, outline=C_GOLD, width=int(S*0.03))
    cx, cy = S // 2, S // 2

    # Elegant abstract twin silhouettes meeting in a heart
    draw_heart(d, cx, cy - int(S*0.02), int(S * 0.22), int(S * 0.22), C_ROSE if is_app_icon else C_BURGUNDY)
    draw_sparkle(d, cx, cy - int(S * 0.02), int(S * 0.08), int(S * 0.03), C_GOLD)


# Render all 8 options
render_option(1, 0, 0, "The Woven Infinity Heart", "Intertwining champagne gold & rose ribbon forming an infinity heart", draw_opt1, dark_logo=False)
render_option(2, 1, 0, "Dual Petals & AI Spark", "Two botanical lovers' petals crowned by a 4-point AI intelligence star", draw_opt2, dark_logo=False)
render_option(3, 0, 1, "Interlocking Wedding Rings", "Ultra-clean luxury line-art wedding bands with deep velvet burgundy", draw_opt3, dark_logo=True)
render_option(4, 1, 1, "Embracing 'c' & 'u' Monogram", "Modern typographic monogram where 'c' holds and cradles 'u'", draw_opt4, dark_logo=False)
render_option(5, 0, 2, "Taste Venn Diagram", "Two harmonized taste profiles overlapping into a luminous shared heart", draw_opt5, dark_logo=True)
render_option(6, 1, 2, "The AI Spark Heart", "Continuous romantic heart curve blossoming into a golden AI spark", draw_opt6, dark_logo=False)
render_option(7, 0, 3, "The Love Ribbon Knot", "Two intertwined paths tying into an unbroken couple knot", draw_opt7, dark_logo=True)
render_option(8, 1, 3, "The Luxury AI Medallion", "Circular royal medallion with nested couple silhouettes & golden star", draw_opt8, dark_logo=True)

# Save
canvas.convert("RGB").save(OUT_PATH, "JPEG", quality=95)
print(f"Saved 8-option showcase collage to: {OUT_PATH}")

