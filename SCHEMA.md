# 3D Tag Registry — Proposed Schema

This document specifies the JSON Lines (JSONL) schema for the tag registry used to drive website rendering and audit changes to the missing flag. Example values below are redacted and must not contain real PII in the repository.

## Storage
- Development: `registry.jsonl` (git-ignored). One JSON object per line.
- Production: database table with an equivalent schema (indexes noted below).

## Fields
- `uid` (string, required): Unique tag identifier (from QR payload).
- `token_hash` (string, required): Hash of the secret token from the QR URL query `t`. Never store raw token.
- `missing` (boolean, default false): Privacy gate; if false, no PII is returned.
- `owner_name` (string, optional, PII): Redacted in docs; stored locally only.
- `owner_phone` (string, optional, PII): E.164 preferred. Stored locally only.
- `owner_address` (string, optional, PII): Single string, formatted e.g., “Bnei Brak 17 apt. 3 Tel Aviv Israel”. Stored locally only.
- `qr_payload_hash` (string, optional): Hash of the canonical QR payload for integrity/debug.
- `contact_email` (string, optional): For relay delivery.
- `relay_prefs` (object, optional): Preferences for contact relays.
- `notes` (string, optional): Freeform admin notes (non-PII recommended).
- `created_at` (RFC3339 string, required): Creation timestamp.
- `updated_at` (RFC3339 string, required): Last update timestamp.
- `missing_updated_at` (RFC3339 string, optional): When `missing` last changed.
- `audit` (array of objects, append-only): Audit events:
  - `ts` (RFC3339 string), `actor` (string: cli|owner|admin), `action` (string, e.g., set-missing true/false), `note` (string), `old` (object subset), `new` (object subset)

## Indexes
- Primary: (`uid`)
- Secondary: (`token_hash`)
- Optional: (`missing`, `updated_at` DESC)

## Example (redacted)
```json
{"uid":"U12345","token_hash":"sha256:...","missing":false,"owner_name":"[REDACTED]","owner_phone":"[REDACTED]","owner_address":"[REDACTED]","qr_payload_hash":"sha256:...","created_at":"2025-08-27T12:00:00Z","updated_at":"2025-08-27T12:00:00Z","audit":[]}
```

## Server Render Policy
- GET `/r?u=<uid>&t=<token>`
  - Verify `token_hash`.
  - If `missing=false`: return generic template and contact relay form (no PII in response or HTML).
  - If `missing=true`: return owner-visible template with PII and optional relay form.

## Toggle Interface (CLI)
- Command: `python tools/missing.py --uid <uid> --set true|false --note "..."`
- Behavior: update `missing`, set `missing_updated_at`, append to `audit`, update `updated_at`.
- Idempotence: no-op if already set; still append audit entry with note.

