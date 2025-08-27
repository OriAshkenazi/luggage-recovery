# Tickets — Implementation Checklist (No Code in This PR)

- Registry fields and schema
  - [ ] Add `missing`, `owner_*`, `missing_updated_at`, `qr_payload_hash`, `audit` to registry storage (per SCHEMA.md).
  - [ ] Store `token_hash` only; never store raw token.

- Admin/Owner toggle
  - [ ] Implement CLI `tools/missing.py --uid <uid> --set true|false --note "..."`.
  - [ ] Update `missing`, set `missing_updated_at`, append `audit`, and refresh `updated_at`.
  - [ ] Idempotent behavior with audit note.

- Server render policy
  - [ ] GET `/r?u=<uid>&t=<token>` verifies token hash.
  - [ ] If `missing=false`: render generic page + relay form (no PII in HTML/JSON).
  - [ ] If `missing=true`: render owner details + optional relay form.
  - [ ] Add `X-Robots-Tag: noindex` and strict CORS.

- Contact relay
  - [ ] POST `/relay` with rate limiting and CAPTCHA/throttling.
  - [ ] Deliver message to owner without exposing PII (unless `missing=true` already makes it visible).
  - [ ] Minimal non-PII logging.

- Generator — dual-side text (params only; code later)
  - [ ] Front prompt params: `front_prompt_text`, `front_prompt_h (≤0.6)`, `front_prompt_margin`, `front_prompt_edge`.
  - [ ] Back text params: `back_text_lines[]`, `back_text_h`, `back_line_gap`, `back_margin`, `text_style`, `text_depth` (engrave), `text_height` (emboss), `font_path`.
  - [ ] Keep-out maps for front/back and validation rules.
  - [ ] Two-tone outputs: Option A features STL (AMS); Option B color-switch.

- Tests (see TESTPLAN.md)
  - [ ] Privacy gating tests (no PII when `missing=false`).
  - [ ] Toggle idempotence and audit field updates.
  - [ ] Geometry: layout within bounds, keep-outs, thickness ≥1.5 mm.
  - [ ] Two-tone co-registration and zero intersection.
  - [ ] Determinism and manifest checks.
  - [ ] Layer index calculation and documentation examples (0.16/0.20/0.28 mm).

- Docs
  - [ ] README updates: “Privacy & Missing Mode”, “Dual-Side Text”, “Do not commit PII” note, color-switch examples.
  - [ ] Link to SCHEMA.md and DESIGN.md.

