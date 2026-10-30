import os
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

# 1. Load User's Uploaded Logo
src_path = r"C:/Users/admin/.gemini/antigravity/brain/6d8e9353-5c79-4cdf-92cf-1fafc99c77a9/.user_uploaded/media_1793378671335_05c4bf68.png"
orig = Image.open(src_path).convert("RGBA")
W, H = orig.size
print(f"Original Logo Size: {W} x {H}")

# 2. Ultra-High-Definition 4x Upscaling (Full HD: 1904 x 624)
TARGET_W = W * 4  # 1904
TARGET_H = H * 4  # 624

# First step: High-fidelity Lanczos 4x interpolation
hd = orig.resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)

# Second step: Subpixel edge crisping and contrast recovery
# Apply gentle unsharp mask to crisp up text edges and heart curves without creating ringing artifacts
sharpened = hd.filter(ImageFilter.UnsharpMask(radius=3, percent=140, threshold=2))

# Third step: Clean up background noise
# The background is a flat warm cream #faefeb (250, 239, 235)
arr = np.array(sharpened)
r, g, b, a = arr[:,:,0], arr[:,:,1], arr[:,:,2], arr[:,:,3]

# Identify solid background pixels (high lightness, near 250, 239, 235)
bg_mask = (r > 245) & (g > 233) & (b > 228) & (np.abs(r.astype(int) - g.astype(int) - 11) < 8)

# Smooth background to pure #faefeb for zero compression noise
arr[bg_mask, 0] = 250
arr[bg_mask, 1] = 239
arr[bg_mask, 2] = 235
arr[bg_mask, 3] = 255

hd_clean = Image.fromarray(arr, "RGBA")

# Also save at 5x (2380 x 780 - true 2K/Full HD asset)
hd_2k = orig.resize((W * 5, H * 5), Image.Resampling.LANCZOS).filter(ImageFilter.UnsharpMask(radius=3.5, percent=150, threshold=2))
arr_2k = np.array(hd_2k)
r2, g2, b2 = arr_2k[:,:,0], arr_2k[:,:,1], arr_2k[:,:,2]
bg_mask_2k = (r2 > 245) & (g2 > 233) & (b2 > 228) & (np.abs(r2.astype(int) - g2.astype(int) - 11) < 8)
arr_2k[bg_mask_2k, 0] = 250
arr_2k[bg_mask_2k, 1] = 239
arr_2k[bg_mask_2k, 2] = 235
arr_2k[bg_mask_2k, 3] = 255
hd_2k_clean = Image.fromarray(arr_2k, "RGBA")

# Save to destination paths
out_png = "frontend/public/img/cupl_logo.png"
out_jpg = "frontend/public/img/cupl_logo.jpg"
dist_png = "backend/dist/img/cupl_logo.png"
dist_jpg = "backend/dist/img/cupl_logo.jpg"

hd_clean.save(out_png, "PNG")
hd_clean.convert("RGB").save(out_jpg, "JPEG", quality=98)
hd_clean.save(dist_png, "PNG")
hd_clean.convert("RGB").save(dist_jpg, "JPEG", quality=98)

# Also save Full HD 2K version for high-DPI displays
hd_2k_clean.save("frontend/public/img/cupl_logo_2k.png", "PNG")
hd_2k_clean.save("backend/dist/img/cupl_logo_2k.png", "PNG")

# Save inspection artifact
artifact_path = r"C:\Users\admin\.gemini\antigravity\brain\6d8e9353-5c79-4cdf-92cf-1fafc99c77a9\cupl_logo_full_hd_preview.png"
hd_clean.save(artifact_path, "PNG")

print(f"Successfully created Full HD logo ({TARGET_W}x{TARGET_H}) and 2K logo ({W*5}x{H*5})!")
print(f"Saved to {out_png} and {artifact_path}")

