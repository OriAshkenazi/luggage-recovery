# Test Plan — Privacy Gating, Text Layout, and Slicer Checks

Scope: Validate the end-to-end behavior for privacy gating (missing mode), dual-side text layout with keep-outs and minimum wall constraints, and slicer-aligned outputs for single- and multi-material prints. No implementation code is included here.

## 1) Privacy & API Behavior
- Token verification
  - GET `/r?u=<uid>&t=<token>` with valid HMAC (`hmac256:<hex>`) → 200
  - Tampered token or UID → 400; no PII leakage
  - Legacy `sha256:<hex>` rejected when `ALLOW_LEGACY_SHA256=false` (default)
- Missing flag gating
  - `missing=false` → Render generic registered page with contact relay form (no owner PII).
  - `missing=true` → Render owner-visible page with owner name/phone/address and optional relay.
- Headers & indexing
  - Responses include `X-Robots-Tag: noindex` and security headers (CSP, Referrer‑Policy `no-referrer`, Permissions‑Policy `geolocation=(), microphone=()`, `X-Content-Type-Options: nosniff`).
  - CORS restricted.
- Relay
  - POST `/relay` accepts message and minimal sender contact; rate-limited; does not expose owner PII when `missing=false`.

## 2) Toggle CLI and Audit
- CLI idempotence
  - Repeated `--set true` produces no change in `missing` but appends audit entry with `note` and timestamp.
- Audit fields
  - `missing_updated_at` updates when toggled; `updated_at` always updates.
  - Audit entries capture actor, action, note, old/new subset.

## 3) CAD/Text Geometry Validation (no rendering dependencies)
- Layout regions
  - Front prompt bounding box lies within border frame; no overlap with QR pocket/islands or strap keep-out.
  - Back text lines occupy layout rectangle = (tag back area − NFC circle − strap rectangle − margins). No overlap.
- Minimum wall
  - For engraving: `body_t - text_depth ≥ 1.5 mm` everywhere under text.
- Two-tone alignment
  - AMS/MMU: features STL for raised text co-registers with base, identical XY AABB, Z contact at surface, zero intersection volume.
  - Single-extruder: embossed height equals `island_h` for color-switch alignment.
- Mesh integrity
  - All STLs watertight, manifold, consistent winding; no self-intersections.

## 4) Determinism & Manifests
- Deterministic exports
  - Two identical builds with `--deterministic` yield identical SHA256 for all outputs.
- Manifest content
  - `manifest.json` includes parameters, QR metadata, color-switch layer (when provided), and per-file SHA256.
  - `checksums.sha256` lines match hashes in manifest.

## 5) Slicer Guidance & Layer Index
- Color-switch layer index
  - Verify `round(island_h / layer_height)` against expected example values: 0.16→3, 0.20→2, 0.28→2.
- Preview acceptance
  - SVG previews always present; PNG optional.

## 6) Presets & Tolerances
- Each preset (PLA/PETG/ABS) builds within dimensional tolerances.
- If back text cannot fit with given size/margins, strict mode fails with a clear error; optional autoscale left for future.

## 7) Data Hygiene
- No PII in repo: sample configs use redacted placeholders.
- Local registry file is git-ignored; tests use in-memory fixtures or ephemeral files.
