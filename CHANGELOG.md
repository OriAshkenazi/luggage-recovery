# Changelog

## v1.0.0 — 2025-08-27

- Feature complete 3D luggage tag generator.
- QR-driven islands from `--qr_text`/`--qr_svg` with strict validation and two-tone alignment guarantees.
- Sticker templates: `qr_sticker_30x50.svg` (and PNG if available) with safe margin and registration marks.
- Material presets: `--preset {pla,petg,abs}` tuning clearances and island height; CLI overrides win.
- Deterministic exports: pinned dependencies, stable STL tessellation and face order; `manifest.json` and `checksums.sha256` emitted.
- Minimal CI: macOS + Python 3.11 only; strict by default; determinism gate via double build.
- Docs: README covers QR workflow, printing guidance, color-switch layers, artifacts, troubleshooting.

Release notes: See README for printing guidance and color-switch instructions; artifacts (STLs, sticker SVG/PNG, manifest, checksums, previews) are attached to the GitHub Release.
