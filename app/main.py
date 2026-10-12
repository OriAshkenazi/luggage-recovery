"""Minimal privacy gate: reveals owner details only for a valid token on a tag marked missing."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


def _registry_path() -> Path:
    return Path(os.environ.get("REGISTRY_PATH", "registry.jsonl"))


def _secret() -> str:
    return os.environ.get("RECOVERY_SECRET", "")


def _allow_legacy() -> bool:
    return os.environ.get("ALLOW_LEGACY_SHA256", "false").lower() == "true"


def _hmac_token(token: str) -> str:
    secret = _secret()
    if not secret:
        raise RuntimeError("RECOVERY_SECRET not set")
    return hmac.new(secret.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()


def _load_row(uid: str) -> Optional[dict]:
    path = _registry_path()
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("uid") == uid:
                return row
    return None


def _token_valid(token_hash: str, token: str) -> bool:
    if token_hash.startswith("hmac256:"):
        try:
            calc = _hmac_token(token)
        except RuntimeError:
            raise HTTPException(status_code=500, detail="Server not configured")
        return hmac.compare_digest(calc, token_hash.split(":", 1)[1])
    if token_hash.startswith("sha256:") and _allow_legacy():
        legacy = hashlib.sha256(token.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy, token_hash.split(":", 1)[1])
    return False


app = FastAPI(title="Luggage Recovery")


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'none'; style-src 'self'; img-src 'self'"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/r", response_class=HTMLResponse)
def resolve(request: Request, uid: str = Query(alias="u"), token: str = Query(alias="t")):
    row = _load_row(uid)
    if not row:
        raise HTTPException(status_code=404, detail="Unknown tag")
    if not _token_valid(row.get("token_hash", ""), token):
        raise HTTPException(status_code=400, detail="Invalid token")

    if not row.get("missing", False):
        return TEMPLATES.TemplateResponse(request, "registered.html", {})
    ctx = {
        "owner_name": row.get("owner_name"),
        "owner_phone": row.get("owner_phone"),
        "owner_address": row.get("owner_address"),
    }
    return TEMPLATES.TemplateResponse(request, "owner.html", ctx)
