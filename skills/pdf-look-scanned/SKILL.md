---
name: pdf-look-scanned
description: >
  Make PDF documents look like they were scanned on a physical scanner. Applies realistic
  effects: grayscale conversion, Gaussian noise, slight rotation, blur, edge shadows, and
  random offset. Optionally extract real handwritten signatures from a source PDF (or user-provided
  images) and replace digital signatures on specific pages. Use when the user asks to: make a PDF
  look scanned, give a PDF a scanned appearance, replace digital signatures with real/handwritten
  ones, fake a scan, add scan effects to a document, or make a document look printed and scanned.
---

# PDF Look Scanned

Make PDFs look like physical scans with optional signature replacement.

## Dependencies

```bash
pip3 install pillow pdf2image img2pdf numpy
```

Also requires `poppler` (provides `pdftoppm`):
- macOS: `brew install poppler`
- Ubuntu/Debian: `apt install poppler-utils`
- Fedora/RHEL: `dnf install poppler-utils`
- Arch: `pacman -S poppler`
- Windows: `conda install -c conda-forge poppler` or download from [poppler releases](https://github.com/osber/poppler-windows/releases)

## Quick Start

Run `scripts/make_scanned.py` for the core functionality. Read the script's `--help` for all options.

### Simple scan effect

```bash
python3 scripts/make_scanned.py document.pdf
```

### Adjust scan quality

Lower DPI and quality = grittier, more realistic cheap-scanner look:

```bash
python3 scripts/make_scanned.py document.pdf --dpi 150 --quality 75 --noise 7
```

Higher DPI = cleaner scan, larger file:

```bash
python3 scripts/make_scanned.py document.pdf --dpi 300 --quality 92
```

## Signature Replacement

### Finding signature coordinates

Before replacing signatures, determine crop and placement coordinates. All coordinates are **fractions of page dimensions** (0.0-1.0).

1. **Convert the source PDF to images** and visually inspect to find the signature region
2. **Iteratively crop** to isolate just the signature ink (no text, no table lines)
3. **On the target PDF**, find the area to clear (old digital signature) and where to paste

Use this Python snippet to explore coordinates interactively:

```python
from pdf2image import convert_from_path
from PIL import Image

pages = convert_from_path("document.pdf", dpi=200)
page = pages[0]  # 0-indexed
w, h = page.size

# Crop a region and save for inspection
crop = page.crop((int(w*0.5), int(h*0.4), int(w*0.8), int(h*0.6)))
import tempfile, os
crop.save(os.path.join(tempfile.gettempdir(), "crop_test.png"))
```

### Replace one signature

```bash
python3 scripts/make_scanned.py contract.pdf \
  --sig-pdf signatures.pdf \
  --sig-page 1 --sig-crop 0.41,0.33,0.62,0.42 \
  --sig-target 25 --sig-clear 0.61,0.41,0.85,0.52 --sig-place 0.62,0.415
```

### Replace multiple different signatures

Each set of `--sig-page`, `--sig-crop`, `--sig-target`, `--sig-clear`, `--sig-place` adds one replacement. They are matched positionally:

```bash
python3 scripts/make_scanned.py contract.pdf \
  --sig-pdf signatures.pdf \
  --sig-page 1 --sig-crop 0.41,0.33,0.62,0.42 \
  --sig-target 25 --sig-clear 0.61,0.41,0.85,0.52 --sig-place 0.62,0.415 \
  --sig-page 2 --sig-crop 0.40,0.335,0.62,0.39 \
  --sig-target 27 --sig-clear 0.61,0.635,0.85,0.72 --sig-place 0.60,0.655
```

### Signature parameters

| Parameter | Description |
|-----------|-------------|
| `--sig-pdf` | Source PDF containing real signatures |
| `--sig-page N` | Page number in source PDF (1-indexed) |
| `--sig-crop L,T,R,B` | Crop box to extract signature (fractions) |
| `--sig-target N` | Target page to replace signature on (1-indexed) |
| `--sig-clear L,T,R,B` | Area to white-out old signature (fractions) |
| `--sig-place X,Y` | Top-left position to paste new signature (fractions) |
| `--sig-size F` | Signature width as fraction of page width (default: 0.11) |
| `--sig-dpi N` | DPI for rendering source signature PDF (default: 350) |

## Scan effect parameters

| Parameter | Default | Effect |
|-----------|---------|--------|
| `--dpi` | 200 | Render resolution. Lower = grittier |
| `--quality` | 85 | JPEG compression. Lower = more artifacts |
| `--noise` | 5.0 | Gaussian noise stddev. Higher = noisier |
| `--blur` | 0.6 | Gaussian blur radius. Higher = softer |
| `--rotation` | 0.7 | Max rotation in degrees |
| `--contrast-min` | 0.88 | Min contrast (lower = more washed out) |
| `--contrast-max` | 0.95 | Max contrast |

## Workflow for signature replacement

When the user provides a PDF and a separate signature source:

1. **Check dependencies** are installed (`pillow`, `pdf2image`, `img2pdf`, `numpy`, `poppler`)
2. **Examine the source signature PDF** — convert to images, identify which pages have signatures
3. **Extract signatures** — iteratively crop to isolate the ink, verify no text bleeds in
4. **Examine the target PDF** — find pages with digital signatures, note the "Подпись:" or "Signature:" label positions
5. **Determine coordinates** — clear area must cover old signature without eating into labels; place position should be right after the label
6. **Run the script** with all parameters
7. **Verify output** — check signature pages visually, adjust coordinates if needed
8. **Check metadata** — run `exiftool` on the output to ensure no software traces remain

Common pitfalls:
- Crop box too tight: signature strokes get clipped on edges
- Clear area too wide: eats into "Подпись:"/"Signature:" labels or surrounding text
- Signature too large/small: adjust `--sig-size` (0.11 is typical for contracts)
- Source PDF is a phone photo: use higher `--sig-dpi` (350+) and higher ink threshold
