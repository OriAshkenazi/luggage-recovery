# Lost Luggage Recovery System

End-to-end system for recovering lost luggage via a mobile-first contact page and printable 3D tag models.

Note: The website lives in `/docs/` (GitHub Pages). There is no `/website/` folder.

## Overview

Components:
- Contact Page (`/docs/`): Mobile-first static site for finders to reach the owner.
- 3D Models (`/3d-models/`): Two-part, two-colour tag generator (CadQuery): QR + prompt front, contact back, NFC sealed inside.
- Privacy Gate App (`/app/`): Minimal FastAPI endpoint used for token-gated owner info (optional).
- Tools (`/tools/`): Utilities such as the missing-toggle CLI and a WCAG contrast checker.
- Tests (`/tests/`): Geometry, CLI, docs, privacy, and contrast/layout checks.

## Quick Start

Website (local):
```bash
cd docs
python -m http.server 8000
# open http://localhost:8000/
```

Two-part tag (Bambu Lab P1S + AMS) — see [3d-models/README.md](3d-models/README.md):
```bash
pip install -r requirements.txt
cp 3d-models/contact.example.yaml 3d-models/contact.local.yaml   # edit; git-ignored
python 3d-models/two_part_tag.py
```

Privacy app (optional):
```bash
export RECOVERY_SECRET=changeme
uvicorn app.main:app --reload
```

## File Structure (key paths)

```
docs/                   # Website (GitHub Pages)
3d-models/              # Tag generator, layout, viewer, README
app/                    # FastAPI privacy gate
tools/                  # Utilities (toggle missing, contrast)
tests/                  # Pytest suite
tokens/                 # Sample color tokens for contrast checks
site/ui/contrast_sandbox.html
.github/workflows/verify-macos.yml
requirements.txt
```

## Server Notes (Privacy Gate)

- Tokens: Verified using HMAC‑SHA256 with `RECOVERY_SECRET` (set via environment). Legacy plain SHA‑256 tokens are rejected by default; set `ALLOW_LEGACY_SHA256=true` temporarily if migrating.
- Data storage: `registry.jsonl` (git‑ignored) holds rows with `uid`, `token_hash`, `missing`, and optional owner fields. Never commit PII.
- Local testing: `uvicorn app.main:app --reload` (ensure `RECOVERY_SECRET` is exported).

## License

MIT — see [LICENSE](LICENSE).

