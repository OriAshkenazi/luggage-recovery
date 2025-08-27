from __future__ import annotations
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
import hmac


REGISTRY_PATH = Path(os.environ.get("REGISTRY_PATH", "registry.jsonl"))
RECOVERY_SECRET = os.environ.get("RECOVERY_SECRET", "")
ALLOW_LEGACY = os.environ.get("ALLOW_LEGACY_SHA256", "false").lower() == "true"


def _hmac_token(token: str) -> str:
    if not RECOVERY_SECRET:
        raise RuntimeError("RECOVERY_SECRET not set")
    return hmac.new(RECOVERY_SECRET.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()


def _load_row(uid: str) -> Optional[dict]:
    if not REGISTRY_PATH.exists():
        return None
    with REGISTRY_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except Exception:
                continue
            if row.get("uid") == uid:
                return row
    return None


app = FastAPI(title="Luggage Recovery")


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'none'; style-src 'self'; img-src 'self'"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/r", response_class=HTMLResponse)
def resolve(uid: str = Query(alias="u"), token: str = Query(alias="t")):
    row = _load_row(uid)
    if not row:
        raise HTTPException(status_code=404, detail="Unknown tag")
    th = row.get("token_hash", "")
    if th.startswith("hmac256:"):
        expect = th.split(":", 1)[1]
        try:
            calc = _hmac_token(token)
        except RuntimeError:
            raise HTTPException(status_code=500, detail="Server not configured")
        if not hmac.compare_digest(calc, expect):
            raise HTTPException(status_code=400, detail="Invalid token")
    elif th.startswith("sha256:") and ALLOW_LEGACY:
        legacy = th.split(":", 1)[1]
        if hashlib.sha256(token.encode("utf-8")).hexdigest() != legacy:
            raise HTTPException(status_code=400, detail="Invalid token")
    else:
        raise HTTPException(status_code=400, detail="Invalid token")

    missing = bool(row.get("missing", False))
    owner_name = row.get("owner_name") if missing else None
    owner_phone = row.get("owner_phone") if missing else None
    owner_address = row.get("owner_address") if missing else None

    from fastapi.templating import Jinja2Templates
    from fastapi import Request
    templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
    class DummyReq:
        def __init__(self):
            self.url = type("U", (), {"path": "/r"})()
    req = DummyReq()
    ctx = {"request": req}
    if not missing:
        return templates.TemplateResponse("registered.html", ctx)
    else:
        ctx.update({"owner_name": owner_name, "owner_phone": owner_phone, "owner_address": owner_address})
        return templates.TemplateResponse("owner.html", ctx)
