# Luggage Tag STL Generator

## Features
- Holds a 30×50 mm QR sticker on the front
- Rear recess for Ø 25 mm NFC tag, 1 mm deep
- Reinforced strap attachment with optional round hole or 5 × 20 mm slot
- Filleted corners and minimum wall thickness of 1.5 mm
- Supports multi-material and single-extruder colour change

## Install
```bash
pip install -r requirements.txt
```
Supported: macOS (CI) and Windows 11. Python 3.11 is the supported version. Dependencies are fully pinned in `requirements.txt` for deterministic builds.

## Usage
Generate default models and previews:
```bash
python 3d-models/generate_tag.py --out 3d-models/outputs/ --previews svg --deterministic
```
Deterministic build with QR demo and manifest/checksums:
```bash
python 3d-models/generate_tag.py \
  --out 3d-models/outputs/ \
  --previews svg --deterministic \
  --preset petg --qr_text "https://example.com/RECOVER?u=DEMO" \
  --layer_height 0.20
```
Override parameters or load a YAML profile:
```bash
python 3d-models/generate_tag.py --qr_w 50 --qr_h 30 --qr_border 3 --slot 5x20
python 3d-models/generate_tag.py --params 3d-models/params.yaml --qr_border 4
```

## Variants
- `base` – one-piece model with raised QR features for single-extruder color change
- `flat` – shallow front pocket only for using a printed sticker
- `islands` – split STLs for multi-material printing (`tag_alt_qr_islands_base.stl` and `tag_alt_qr_islands_features.stl`)

## QR Workflow
- Generate QR-driven islands from text:
```bash
python 3d-models/generate_tag.py \
  --out 3d-models/outputs/ \
  --variant islands \
  --qr_text "https://example.com/RECOVER?u=DEMO" \
  --previews svg --deterministic --preset petg --layer_height 0.20
```
- Or provide an external SVG payload with `--qr_svg path.svg`.
- Sticker templates are always exported: `qr_sticker_30x50.svg` (and PNG if available). Print at 100% scale (300 DPI) to get exactly 30×50 mm. Includes 1 mm safe margin and two registration marks.
- AMS vs. color-switch: For multi-material, use the `islands` STLs; for single-extruder, print `base` and change filament at `layer = round(island_h / layer_height)`.

## Printing
- Material: PETG or ABS
- Layer height: 0.2 mm
- Perimeters: ≥4
- Infill: 20–30 %
- Top/Bottom: 5 layers
- No supports required; add a brim if needed

### Material Presets
Use `--preset {pla,petg,abs}` for tuned clearances and edges. CLI overrides still take precedence.

## Color-Change Layer
To switch colours on a single-extruder printer, change filament at layer index:
```
layer = round(island_h / layer_height)
```
Examples for `island_h = 0.5 mm`:
- `layer_height = 0.16 mm` → layer `3`
- `layer_height = 0.20 mm` → layer `2`
- `layer_height = 0.28 mm` → layer `2`

## Assembly
- Press-fit the Ø 25 mm NFC tag into the rear recess
- Apply the 30×50 mm QR sticker into the front pocket
- Attach a strap through the hole or slot

## Tolerances
Default clearance is 0.25 mm for the QR sticker and NFC tag. If parts are too tight, increase `fit_clearance` to 0.30–0.40 mm; if loose, reduce to 0.15–0.20 mm.

## Troubleshooting
- If generation fails, ensure `nfc_depth + qr_pocket_depth <= body_t - 0.6` and that required Python packages are installed.
- PNG previews are optional. CI uses SVG by default; PNG requires the system Cairo library. Use `--previews svg` to avoid PNG entirely.

## Artifacts and Determinism
- `manifest.json` lists parameters, QR metadata, file SHA256, and color-switch layer (when provided).
- `checksums.sha256` contains `sha256  filename` lines for all outputs.
- CI performs two identical deterministic builds and fails if any hash differs.

## License
This project is licensed under the MIT License. See [LICENSE](../LICENSE).

## Previews
![Front preview](outputs/preview_front.png)
![Back preview](outputs/preview_back.png)
