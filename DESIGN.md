# 3D Tag — Missing Mode, Dual-Side Text, and QR Workflow (Design)

## Overview
This design defines how the website reveals owner data only when a tag is marked missing, how the physical tag carries dual-side text (front prompt + back owner details), and how the generator supports engraved/embossed text while maintaining printability and privacy.

Goals:
- Privacy-by-default: personal data never rendered unless `missing=true`.
- Non-breaking QR: QR URL and payload remain unchanged; server decides what to render.
- Parametric, print-friendly text on both sides with keep-outs and minimum wall guarantees.

Out of scope: Implementation code. This document is a plan only.


## User Flows
- Normal (not missing)
  - User scans QR on tag front.
  - Server verifies tag token and loads the registry row.
  - `missing=false` → Render a generic “This tag is registered” page:
    - Show non-identifying info (e.g., model, QR payload hash suffix).
    - Offer a contact relay form (message → forwarded to owner email/phone) without revealing any PII.
  - No owner name/phone/address is ever shown.

- Missing
  - Owner (or admin) toggles the tag to `missing=true` via CLI or simple owner portal.
  - Finder scans QR.
  - `missing=true` → Render an “Owner Details” page:
    - Show owner name/phone/address and optional relay form.
    - Display last updated time and advisory text.

- Edge cases
  - Unknown UID/token → Show a safe generic page with support link.
  - Rate-limited scanners or bots → Same generic page, with minimal information and no PII.


## Architecture
- Static QR payload (`/r?u=<uid>&t=<token>`). Server controls rendering.
- Registry stored locally for development as `registry.jsonl` (git-ignored) or a DB in production.
- Admin/Owner toggle available via CLI first; optional minimal web UI later.
- Contact relay service (email or SMS) without exposing PII when not missing.


## Data Model & API
- See SCHEMA.md for a complete schema proposal.

API endpoints (initial minimal set):
- GET `/r?u=<uid>&t=<token>`
  - Validates token using HMAC‑SHA256 (`RECOVERY_SECRET`) against `token_hash` (`hmac256:<hex>` in registry).
  - Checks `missing`.
  - Renders one of two templates:
    - Public (missing=false): generic status + non-PII relay form.
    - Owner-visible (missing=true): owner PII + optional relay form.
  - Includes non-indexing headers/meta and short TTL caching (if any) to respect toggle changes.

- POST `/relay`
  - Accepts message and contact details from finder.
  - Validates server-side anti-abuse (rate limit, CAPTCHA, throttle by tag).
  - Sends message to owner via email/SMS relay; does not expose owner PII unless already in missing=true context.
  - Stores a minimal, non-PII audit entry.

Admin/Owner toggle:
- CLI: `python tools/missing.py --uid <uid> --set true|false --note "<reason>"`
- Future optional UI: passwordless link or token-gated form for the owner to set missing.
- All toggles audit logged: timestamp, actor, note, previous/new values.

Security/Privacy controls:
- Privacy default: `missing=false` returns no PII in response.
- Store HMAC token hash, never raw token; legacy SHA‑256 disabled by default.
- Security headers: CSP `default-src 'none'; style-src 'self'; img-src 'self'`, Referrer‑Policy `no-referrer`, Permissions‑Policy `geolocation=(), microphone=()`, `X-Content-Type-Options: nosniff`.
- No PII in server logs; redact address/phone/name in any analytics.
- Responses include `X-Robots-Tag: noindex` and light color scheme meta; CORS restricted to same-origin.
- Development registry stored locally in a git-ignored file; documentation uses redacted examples only.


## CAD/Text Layout Spec
Parameters (additive to existing generator):
- Front prompt
  - `front_prompt_text` (string, default: “Scan me to find my owner”).
  - `front_prompt_h` (mm): embossed text height in Z; ≤ 0.6 mm to support single-extruder color change at a known layer.
  - `front_prompt_margin` (mm): distance from outer frame/QR pocket edge.
  - `front_prompt_edge` (enum: top|bottom|left|right, default: top).

- Back owner text
  - `back_text_lines` (array of strings): order as printed.
  - `back_text_h` (mm): nominal text size in XY; governs glyph bounding boxes.
  - `back_line_gap` (mm): line spacing.
  - `back_margin` (mm): perimeter inset from tag edge.
  - `text_style` (enum: engrave|emboss).
  - `text_depth` (mm, engrave): 0.3–0.5 mm cut into body.
  - `text_height` (mm, emboss): ~0.5 mm above surface.
  - `font_path` (optional): font TTF/OTF path; fallback to system sans.

Keep-outs & constraints:
- Minimum wall: remaining solid thickness ≥ 1.5 mm after any engraving.
- Front keep-outs: QR pocket and island area, strap feature zone; place prompt on the border frame.
- Back keep-outs: NFC recess circle (Ø ≈ `nfc_d + fit_clearance`), strap feature rectangle, and margins.
- Text must not overlap keep-outs or extend beyond margins.
- For embossing, ensure raised text doesn’t exceed `island_h` if using single-extruder color change at a known layer.

Two-tone options:
- Option A (AMS/MMU): export raised text as a separate “features” STL with identical XY bounds and matching origin; Z contact at the body surface with zero intersection.
- Option B (single-extruder): use `text_height` = `island_h` and document color-switch layer `round(island_h / layer_height)`.

Layout strategy:
- Front prompt: lay out along chosen edge as a straight line (no curvature) centered within the available span, trimmed to avoid corners.
- Back text: compute a rectangular layout region = tag back area minus keep-outs and margins; flow multi-line text with word wrapping; if text cannot fit at requested size, fail with a clear validation error (or auto-scale if a `back_text_autoscale=true` flag is allowed later).

Validation checks (strict):
- Text bounding boxes fully within allowed regions.
- No overlap with keep-outs.
- Remaining thickness after engraving ≥ 1.5 mm.
- Two-tone features co-register with base; zero intersection and correct Z contact.
- All meshes watertight and manifold.


## Print Guidance
- Single-extruder color switch: compute `layer = round(island_h / layer_height)`; examples: 0.16→3, 0.20→2, 0.28→2.
- Recommended presets: PLA/PETG/ABS profiles tune `fit_clearance`, `corner_r`, and `island_h`.
- Slicer: ≥4 perimeters, 0.2 mm layer height typical, no supports; add a brim if needed.


## Operational Notes
- The switch to `missing=true` propagates immediately; templates avoid caches or set very short max-age.
- Admin CLI is authoritative for early phases; an owner portal can be added with token-gated access.


## Implementation Plan (tickets in TICKETS.md)
- Registry fields and audit logging.
- Server render policy and templates.
- CLI toggle and logging.
- Generator text parameters, keep-out maps, and validations.
- Tests: privacy gating, audit, geometry layout, two-tone alignment, slicer layer calculation.
