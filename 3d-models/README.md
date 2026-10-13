# Two-part luggage tag

An 85 × 54 × 3.2 mm tag printed as two halves on a Bambu Lab P1S with AMS, each half
two-colour: a light base with a flush dark inlay in its first three layers. The halves
glue back-to-back with an NFC sticker sealed between them.

- **Front:** QR code (33 modules × 1.2 mm) to the recovery page, "Found my luggage?" prompt.
- **Back:** contact details, readable when the tag is turned over.
- **Inside:** Ø20 mm NFC pocket behind the QR, three Ø2 mm alignment pins.
- **Strap hole:** Ø6 mm, 9 mm in from the top and side edges, with a printed ring.

## Layout first

The artwork is planned as an HTML/CSS page at 10 px = 1 mm (the "Luggage Tag Layout"
design canvas), then mirrored in millimetres in [`layout.py`](layout.py): absolutely placed
features plus flex columns with `gap` and `justify-content: space-between`.
[`glyphs.py`](glyphs.py) lays text out with the same metrics a browser uses (hhea ascent and
descent, advance widths, `kern` pairs, letter-spacing), so the STLs match the plan.

Change the design in the canvas first, then carry the numbers into `layout.py`.

## Generate

```bash
pip install -r requirements.txt
cp 3d-models/contact.example.yaml 3d-models/contact.local.yaml   # then edit; git-ignored
python 3d-models/two_part_tag.py
```

Outputs land in `3d-models/outputs/two-part/` (git-ignored): `front_base.stl`,
`front_inlay.stl`, `back_base.stl`, `back_inlay.stl` in print orientation,
`assembled/` copies for previewing, `manifest.json` and `PRINTING.md`.

Flags override the contact file: `--name`, `--phone`, `--email`, `--qr_url`, `--font_path`,
`--contact`, `--out`. The text font is Assistant (weights 700/800, instanced from the variable
font and cached in `.font-cache/`); install it from Google Fonts or pass `--font_path`.

## Preview

```bash
python -m http.server -d 3d-models 8765
# open http://localhost:8765/viewer.html
```

Assembled view (flip, explode with the NFC sticker shown) and both print plates.

## Print rules the generator enforces

- The 0.4 mm nozzle is fixed. Straight inlay features (QR modules, rules, ring, arrow stroke)
  are whole multiples of 0.4 mm.
- No inlay stroke is thinner than 0.4 mm: a morphological opening finds thinner regions, and
  sub-nozzle glyph parts (commas, `/`, the `@`) are thickened just enough to print.
- Inlay depth, half thickness and pocket depth are whole 0.20 mm layers.
- Text never enters the QR quiet zone, the strap-hole ring keep-out, or the last 1 mm of the
  edge. Lines too wide for their column shrink to a 3.6 mm minimum, then fail.
- Every STL is watertight; output is byte-for-byte deterministic.

## Print and assemble

See the generated `PRINTING.md`. In short: load each half's base and inlay STLs together as
one object with two parts, base on filament 1 (light), inlay on filament 2 (dark), face-down
as loaded, 0.20 mm layers. Set elephant foot compensation to 0 and the initial layer line width to
0.42 mm: the first layer is the visible face, and the defaults thin or drop inlay strokes. Write the NFC sticker, place it in the back half's pocket, glue the
halves with the pins engaged.

**Pin fit:** pins Ø2.0 × 0.6 mm, holes Ø2.3 × 0.7 mm (0.3 mm on diameter, a snug slip fit on
a P1S). Adjust `Build.pin_clearance` if they bind or rattle.
