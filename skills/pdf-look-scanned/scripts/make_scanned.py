#!/usr/bin/env python3
"""
Make a PDF look like it was scanned, with optional signature replacement.

Usage:
  python3 make_scanned.py input.pdf [options]

Options:
  --output PATH          Output file path (default: <input>_scanned.pdf)
  --dpi INT              Render DPI, lower = grittier (default: 200)
  --quality INT          JPEG quality 1-100, lower = worse scan (default: 85)
  --noise FLOAT          Noise intensity (default: 5.0)
  --blur FLOAT           Blur radius (default: 0.6)
  --rotation FLOAT       Max rotation degrees (default: 0.7)
  --contrast-min FLOAT   Min contrast factor (default: 0.88)
  --contrast-max FLOAT   Max contrast factor (default: 0.95)
  --sig-pdf PATH         PDF with real signature pages
  --sig-page INT         Page in sig PDF to extract from (1-indexed, repeatable)
  --sig-crop L,T,R,B     Crop box as fractions e.g. 0.41,0.33,0.62,0.42 (repeatable)
  --sig-target INT       Contract page to replace signature on (1-indexed, repeatable)
  --sig-clear L,T,R,B    Area to clear old signature (fractions, repeatable)
  --sig-place X,Y        Position to paste new signature (fractions, repeatable)
  --sig-size FLOAT       Signature width as fraction of page width (default: 0.11)
  --seed INT             Random seed for reproducibility (default: 42)

Examples:
  # Simple scan effect:
  python3 make_scanned.py contract.pdf

  # Grittier scan:
  python3 make_scanned.py contract.pdf --dpi 150 --quality 75 --noise 7

  # With signature replacement (one signature):
  python3 make_scanned.py contract.pdf \\
    --sig-pdf signatures.pdf \\
    --sig-page 1 --sig-crop 0.41,0.33,0.62,0.42 \\
    --sig-target 25 --sig-clear 0.61,0.41,0.85,0.52 --sig-place 0.62,0.415

  # Two different signatures on different pages:
  python3 make_scanned.py contract.pdf \\
    --sig-pdf signatures.pdf \\
    --sig-page 1 --sig-crop 0.41,0.33,0.62,0.42 \\
    --sig-target 25 --sig-clear 0.61,0.41,0.85,0.52 --sig-place 0.62,0.415 \\
    --sig-page 2 --sig-crop 0.40,0.335,0.62,0.39 \\
    --sig-target 27 --sig-clear 0.61,0.635,0.85,0.72 --sig-place 0.60,0.655
"""

import argparse
import random
import sys
from pathlib import Path

try:
    import numpy as np
    from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
    Image.MAX_IMAGE_PIXELS = 300_000_000
    from pdf2image import convert_from_path
    import img2pdf
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip3 install pillow pdf2image img2pdf numpy")
    sys.exit(1)


def extract_signature(sig_page: Image.Image, crop_box: tuple, ink_threshold=210) -> Image.Image:
    """Extract signature from a crop region, trimming to ink bounding box."""
    w, h = sig_page.size
    l, t, r, b = crop_box
    sig_area = sig_page.crop((int(w * l), int(h * t), int(w * r), int(h * b)))

    gray = sig_area.convert("L")
    arr = np.array(gray)
    ink_mask = arr < ink_threshold
    rows = np.any(ink_mask, axis=1)
    cols = np.any(ink_mask, axis=0)

    if not rows.any():
        return sig_area

    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]

    pad = 10
    rmin = max(0, rmin - pad)
    rmax = min(arr.shape[0] - 1, rmax + pad)
    cmin = max(0, cmin - pad)
    cmax = min(arr.shape[1] - 1, cmax + pad)

    return sig_area.crop((cmin, rmin, cmax, rmax))


def replace_signature(page_img, real_sig, clear_box, place_xy, sig_size=0.11):
    """Clear old signature area and paste new signature."""
    w, h = page_img.size
    page = page_img.copy()

    cl, ct, cr, cb = clear_box
    draw = ImageDraw.Draw(page)
    draw.rectangle([int(w * cl), int(h * ct), int(w * cr), int(h * cb)], fill=(255, 255, 255))

    sig_w, sig_h = real_sig.size
    target_w = int(w * sig_size)
    scale = target_w / sig_w
    new_w = int(sig_w * scale)
    new_h = int(sig_h * scale)
    resized = real_sig.resize((new_w, new_h), Image.LANCZOS)

    sig_rgba = resized.convert("RGBA")
    sig_arr = np.array(sig_rgba)
    gray_vals = np.mean(sig_arr[:, :, :3], axis=2)
    sig_arr[:, :, 3] = np.where(gray_vals > 220, 0, 255).astype(np.uint8)
    sig_transparent = Image.fromarray(sig_arr)

    px, py = place_xy
    paste_x = int(w * px)
    paste_y = int(h * py)

    page_rgba = page.convert("RGBA")
    page_rgba.paste(sig_transparent, (paste_x, paste_y), sig_transparent)
    return page_rgba.convert("RGB")


def make_scanned_page(img, noise_std=5.0, blur_radius=0.6, max_rotation=0.7,
                      contrast_min=0.88, contrast_max=0.95):
    """Apply scanned-document effects to a page image."""
    # Grayscale
    gray = img.convert("L")
    img = gray.convert("RGB")

    # Slight rotation
    angle = random.uniform(-max_rotation, max_rotation)
    img = img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=(255, 255, 255))

    # Gaussian noise
    arr = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, noise_std, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)

    # Blur
    img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # Brightness/contrast
    brightness = ImageEnhance.Brightness(img)
    img = brightness.enhance(random.uniform(0.96, 1.03))
    contrast = ImageEnhance.Contrast(img)
    img = contrast.enhance(random.uniform(contrast_min, contrast_max))

    # Edge shadow
    shadow = Image.new("L", img.size, 255)
    draw = ImageDraw.Draw(shadow)
    w, h = img.size
    margin = 30
    for i in range(margin):
        opacity = int(255 - (margin - i) * 1.5)
        draw.rectangle([i, i, w - i - 1, h - i - 1], outline=opacity)
    img = Image.composite(img, Image.new("RGB", img.size, (200, 200, 200)), shadow)

    # Random offset
    offset_x = random.randint(-3, 3)
    offset_y = random.randint(-3, 3)
    canvas = Image.new("RGB", img.size, (245, 245, 240))
    canvas.paste(img, (offset_x, offset_y))
    return canvas


def parse_tuple(s):
    """Parse comma-separated floats."""
    return tuple(float(x) for x in s.split(","))


def main():
    parser = argparse.ArgumentParser(description="Make a PDF look scanned")
    parser.add_argument("input", help="Input PDF path")
    parser.add_argument("--output", help="Output PDF path")
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--quality", type=int, default=85)
    parser.add_argument("--noise", type=float, default=5.0)
    parser.add_argument("--blur", type=float, default=0.6)
    parser.add_argument("--rotation", type=float, default=0.7)
    parser.add_argument("--contrast-min", type=float, default=0.88)
    parser.add_argument("--contrast-max", type=float, default=0.95)
    parser.add_argument("--sig-pdf", help="PDF containing real signatures")
    parser.add_argument("--sig-page", type=int, action="append", default=[])
    parser.add_argument("--sig-crop", action="append", default=[])
    parser.add_argument("--sig-target", type=int, action="append", default=[])
    parser.add_argument("--sig-clear", action="append", default=[])
    parser.add_argument("--sig-place", action="append", default=[])
    parser.add_argument("--sig-size", type=float, default=0.11)
    parser.add_argument("--sig-dpi", type=int, default=350)
    parser.add_argument("--seed", type=int, default=42)

    args = parser.parse_args()
    random.seed(args.seed)

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_stem(input_path.stem + "_scanned")

    # Signature replacement setup
    signatures = []
    if args.sig_pdf and args.sig_page:
        print(f"Loading signature PDF at {args.sig_dpi} DPI...")
        sig_pages = convert_from_path(args.sig_pdf, dpi=args.sig_dpi)

        for i, (page_num, crop_str, target, clear_str, place_str) in enumerate(
            zip(args.sig_page, args.sig_crop, args.sig_target, args.sig_clear, args.sig_place)
        ):
            sig_img = extract_signature(sig_pages[page_num - 1], parse_tuple(crop_str))
            signatures.append({
                "sig": sig_img,
                "target": target - 1,  # 0-indexed
                "clear": parse_tuple(clear_str),
                "place": parse_tuple(place_str),
            })
            print(f"  Signature {i + 1}: extracted {sig_img.size} from page {page_num}")

    # Load contract
    print(f"Loading PDF at {args.dpi} DPI...")
    pages = convert_from_path(str(input_path), dpi=args.dpi)
    print(f"  {len(pages)} pages")

    # Replace signatures
    for s in signatures:
        idx = s["target"]
        print(f"Replacing signature on page {idx + 1}...")
        pages[idx] = replace_signature(pages[idx], s["sig"], s["clear"], s["place"], args.sig_size)

    # Apply scanned effect
    print("Applying scanned effect...")
    import tempfile
    processed = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, page in enumerate(pages):
            print(f"  Page {i + 1}/{len(pages)}...", end="\r")
            scanned = make_scanned_page(
                page,
                noise_std=args.noise,
                blur_radius=args.blur,
                max_rotation=args.rotation,
                contrast_min=args.contrast_min,
                contrast_max=args.contrast_max,
            )
            tmp_path = Path(tmpdir) / f"page_{i:03d}.jpg"
            scanned.save(str(tmp_path), "JPEG", quality=args.quality)
            processed.append(str(tmp_path))

        print(f"\nCombining into PDF...")
        with open(str(output_path), "wb") as f:
            f.write(img2pdf.convert(processed))

    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"Done! {output_path} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
