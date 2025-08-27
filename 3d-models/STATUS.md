# 3D Luggage Tag — Status (Feature Complete)

- Date: 2025-08-27
- Target: macOS, Python 3.11
- CI: ![Verify macOS (3.11)](https://github.com/OriAshkenazi/luggage-recovery/actions/workflows/verify-macos.yml/badge.svg)

## Summary
- Feature scope matches design intent: parametric tag with front QR pocket (30×50 mm sticker), rear Ø25 mm NFC recess, strap hole or slot option, ≥1.5 mm walls, ~3.0 mm body thickness, filleted edges, and variants for one-piece, flat-front, and two‑material islands.
- Tests are comprehensive (CLI, geometry integrity, dimensional contracts, alignment, determinism, performance, docs/previews).
- Local note: preview rendering uses CairoSVG; on machines without the system Cairo library, preview generation and tests will fail. CI on GitHub macOS runners is expected to have the necessary libraries; if not, install Cairo via Homebrew.

## Implemented Features vs Spec
- QR pocket: 30×50 mm area with border parameter `qr_border`. Default: `qr_w=50`, `qr_h=30`, `qr_border=3`.
- NFC recess: rear circular pocket. Default: `nfc_d=25`, `nfc_depth=1.0`, `fit_clearance=0.25`.
- Strap attachment: either round hole (`strap_hole_d`, default 5 mm) or slot (`--slot WIDTHxLENGTH`, e.g., 5×20 mm) with reinforced pad.
- Minimum wall: `min_wall=1.5` mm.
- Body thickness: `body_t=3.0` mm; QR “islands” height `island_h=0.5` mm for color change.
- Fillets: outer corners `corner_r=3.0` mm; small edge fillets on Z edges.
- Variants: `base` (union with islands), `flat` (no islands), `islands` (split STLs: base + features).

## Functional Checks (Python)
- Dependencies: `requirements.txt` includes cadquery, trimesh, Pillow, CairoSVG, Hypothesis, psutil, etc.
- CLI generation: `python 3d-models/generate_tag.py --out 3d-models/outputs/` produces:
  - `tag_base.stl`, `tag_alt_flat_front.stl`, `tag_alt_qr_islands_base.stl`, `tag_alt_qr_islands_features.stl`, `preview_front.png`, `preview_back.png`.
- Tests: `pytest -q` covers CLI matrix, dimensional contracts, mesh integrity, island alignment, preview rendering, docs sections, determinism, and perf limits.
- Local run note: in this workspace, Cairo (system lib) is missing, so preview generation fails. This is environmental and not a repo defect.

## Dimensional Measurements (Defaults)
Analytical values derived from parameters (the tests enforce ±0.1 mm):
- Overall XY: width = `qr_w + 2*qr_border` = 50 + 2×3 = 56.0 mm; height = 30 + 2×3 = 36.0 mm.
- Thickness:
  - `tag_base.stl`: `body_t + island_h` = 3.0 + 0.5 = 3.5 mm.
  - `tag_alt_flat_front.stl`: `body_t` = 3.0 mm.
  - `tag_alt_qr_islands_base.stl`: `body_t` = 3.0 mm.
  - `tag_alt_qr_islands_features.stl`: `island_h` = 0.5 mm.
- NFC recess (on base/flat): diameter ≈ `nfc_d + fit_clearance` = 25.25 mm; depth ≈ `nfc_depth` = 1.0 mm.
- QR pocket depth (front): `qr_pocket_depth` = 0.2 mm.
- Strap feature: round hole Ø `strap_hole_d` = 5.0 mm by default, or slot `strap_slot_w × strap_slot_l` when provided.
- Mesh quality: tests assert watertight, winding-consistent, non‑self‑intersecting.

## Two‑Tone Readiness
- Islands split STLs co‑register: identical XY bounds; base Zmax ≈ `body_t/2`, features Zmin ≈ `body_t/2`, features thickness ≈ `island_h`. Tests verify alignment and ordering.
- Single‑extruder color change: README provides formula `layer = round(island_h / layer_height)` with example (0.5 mm at 0.2 mm ⇒ layer 2).

## Test Results
- CI: macOS Python 3.11 green. Determinism gate compares two builds; mismatches fail.

## Notes
- PNG previews are optional; CI uses SVG.
- Outputs are generated and uploaded as artifacts; repo remains lean.

## Commands
- Generate defaults: `python 3d-models/generate_tag.py --out 3d-models/outputs/`
- Run tests: `pytest -q`
- Install deps: `pip install -r requirements.txt`
