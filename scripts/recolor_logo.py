import numpy as np
from PIL import Image

SRC = r"C:\Users\admin\.gemini\antigravity\brain\6d8e9353-5c79-4cdf-92cf-1fafc99c77a9\.user_uploaded\media_1793371425876_4bcc0954.jpg"
OUT_DIR = r"C:\Users\admin\.gemini\antigravity\brain\6d8e9353-5c79-4cdf-92cf-1fafc99c77a9"

img = Image.open(SRC).convert("RGB")
arr = np.array(img, dtype=float)
H, W, _ = arr.shape

# Calculate perceived luminance (0..255)
lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
bg_val = 247.0

def build_variant(cupl_hex, ai_hex, tag_hex, bg_hex, name):
    def hex_to_rgb(h):
        h = h.lstrip("#")
        return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], dtype=float)

    c_cupl = hex_to_rgb(cupl_hex)
    c_ai = hex_to_rgb(ai_hex)
    c_tag = hex_to_rgb(tag_hex)
    c_bg = hex_to_rgb(bg_hex)

    out = np.zeros_like(arr)

    # Cutoff for cupl vs .ai
    # 'l' ends at 618. 
    # Let's use x_split = 624
    x_split = 624
    y_tagline = 600

    for y in range(H):
        for x in range(W):
            l = lum[y, x]
            if l >= bg_val:
                out[y, x] = c_bg
            else:
                if y >= y_tagline:
                    # Tagline (original is dark)
                    # Ink opacity: 0 is dark (l ~ 90), 1 is bg (l ~ 247)
                    ink_factor = np.clip((bg_val - l) / (bg_val - 85.0), 0.0, 1.0)
                    out[y, x] = c_bg * (1.0 - ink_factor) + c_tag * ink_factor
                elif x <= x_split:
                    # 'cupl'
                    # Original dark purple has min luminance around 65-80
                    ink_factor = np.clip((bg_val - l) / (bg_val - 70.0), 0.0, 1.0)
                    out[y, x] = c_bg * (1.0 - ink_factor) + c_cupl * ink_factor
                else:
                    # '.ai' and heart
                    # Original rose gold has luminance around 170-220
                    # Let's calculate relative intensity of the rose ink
                    ink_factor = np.clip((bg_val - l) / (bg_val - 170.0), 0.0, 1.0)
                    # Give it subtle shading variation
                    shade = 0.88 + 0.24 * (1.0 - np.clip((l - 170.0) / 60.0, 0.0, 1.0))
                    target_color = np.clip(c_ai * shade, 0, 255)
                    out[y, x] = c_bg * (1.0 - ink_factor) + target_color * ink_factor

    result = np.clip(out, 0, 255).astype(np.uint8)
    Image.fromarray(result).save(f"{OUT_DIR}/{name}.jpg", quality=98)
    print(f"Saved {name}.jpg")

# 1. Signature Brand: Velvet Burgundy (#731e33) + Champagne Rose-Gold (#d4a060)
build_variant(
    cupl_hex="#731e33",
    ai_hex="#d4a060",
    tag_hex="#4a1525",
    bg_hex="#fdfbf9",
    name="cupl_ai_style_signature_champagne"
)

# 2. Romantic Petal: Velvet Burgundy (#731e33) + Soft Metallic Rose-Gold (#d88395)
build_variant(
    cupl_hex="#731e33",
    ai_hex="#d88395",
    tag_hex="#4a1525",
    bg_hex="#fdfbf9",
    name="cupl_ai_style_petal_rosegold"
)

# 3. Rich Sunset Luxury: Crimson Wine (#84223c) + Warm Honey Gold (#df9e51)
build_variant(
    cupl_hex="#84223c",
    ai_hex="#df9e51",
    tag_hex="#3d111d",
    bg_hex="#fefcfb",
    name="cupl_ai_style_honey_gold"
)
