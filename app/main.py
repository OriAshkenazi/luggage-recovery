from __future__ import annotations
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse


REGISTRY_PATH = Path(os.environ.get("REGISTRY_PATH", "registry.jsonl"))


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


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


@app.get("/r", response_class=HTMLResponse)
def resolve(uid: str = Query(alias="u"), token: str = Query(alias="t")):
    row = _load_row(uid)
    if not row:
        raise HTTPException(status_code=404, detail="Unknown tag")
    th = row.get("token_hash", "")
    if th.startswith("sha256:"):
        th = th.split(":", 1)[1]
    if _hash_token(token) != th:
        raise HTTPException(status_code=400, detail="Invalid token")

    missing = bool(row.get("missing", False))
    owner_name = row.get("owner_name") if missing else None
    owner_phone = row.get("owner_phone") if missing else None
    owner_address = row.get("owner_address") if missing else None

    # Simple inline templates
    if not missing:
        body = f"""
        <html><head>
          <meta name=\"color-scheme\" content=\"light\"> 
          <meta name=\"robots\" content=\"noindex\">
          <title>Registered Tag</title>
        </head>
        <body>
          <h1>This tag is registered</h1>
          <p>Contact relay is available to reach the owner without revealing personal data.</p>
        </body></html>
        """
        return HTMLResponse(content=body)
    else:
        def _esc(x: Optional[str]) -> str:
            return (x or "").replace("<", "&lt;").replace(">", "&gt;")

        body = f"""
        <html><head>
          <meta name=\"color-scheme\" content=\"light\"> 
          <meta name=\"robots\" content=\"noindex\">
          <title>Owner Details</title>
        </head>
        <body>
          <h1>Owner Details</h1>
          <ul>
            <li>Name: {_esc(owner_name)}</li>
            <li>Phone: {_esc(owner_phone)}</li>
            <li>Address: {_esc(owner_address)}</li>
          </ul>
        </body></html>
        """
        return HTMLResponse(content=body)

