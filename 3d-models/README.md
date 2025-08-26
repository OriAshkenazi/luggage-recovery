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
Works on macOS and Windows 11 with Python 3.10+.

## Usage
Generate default models and previews:
```bash
python 3d-models/generate_tag.py --out 3d-models/outputs/
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

## Printing
- Material: PETG or ABS
- Layer height: 0.2 mm
- Perimeters: ≥4
- Infill: 20–30 %
- Top/Bottom: 5 layers
- No supports required; add a brim if needed

## Color-Change Layer
To switch colours on a single-extruder printer, change filament at layer index:
```
layer = round(island_h / layer_height)
```
For example, with `island_h = 0.5` mm and `layer_height = 0.2` mm ⇒ layer `2`.

## Assembly
- Press-fit the Ø 25 mm NFC tag into the rear recess
- Apply the 30×50 mm QR sticker into the front pocket
- Attach a strap through the hole or slot

## Tolerances
Default clearance is 0.25 mm for the QR sticker and NFC tag. Increase `fit_clearance` to 0.3–0.4 mm if parts are tight.

## Troubleshooting
If generation fails, ensure that `nfc_depth + qr_pocket_depth < body_t - 0.6` and that required Python packages are installed.

## Previews
![Front preview](outputs/preview_front.png)
![Back preview](outputs/preview_back.png)
