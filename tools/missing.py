#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def toggle(path: Path, uid: str, value: bool, note: str = "", actor: str = "cli") -> bool:
    """Toggle missing flag for uid. Returns True if updated."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    found = False
    now = datetime.now(timezone.utc).isoformat()
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except Exception:
                    continue
                if row.get("uid") == uid:
                    old_missing = bool(row.get("missing", False))
                    row["missing"] = bool(value)
                    row["missing_updated_at"] = now
                    row["updated_at"] = now
                    audit = row.get("audit", [])
                    audit.append({
                        "ts": now,
                        "actor": actor,
                        "action": f"set-missing {value}",
                        "note": note,
                        "old": {"missing": old_missing},
                        "new": {"missing": value},
                    })
                    row["audit"] = audit
                    found = True
                rows.append(row)
    if not found:
        # Create new row skeleton (PII not set here)
        row = {
            "uid": uid,
            "token_hash": "",
            "missing": bool(value),
            "created_at": now,
            "updated_at": now,
            "missing_updated_at": now,
            "audit": [
                {
                    "ts": now,
                    "actor": actor,
                    "action": f"set-missing {value}",
                    "note": note,
                    "old": {},
                    "new": {"missing": value},
                }
            ],
        }
        rows.append(row)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    return True


def main():
    ap = argparse.ArgumentParser(description="Toggle missing flag for a tag")
    ap.add_argument("--uid", required=True)
    ap.add_argument("--set", choices=["true", "false"], required=True)
    ap.add_argument("--note", default="")
    ap.add_argument("--path", default=os.environ.get("REGISTRY_PATH", "registry.jsonl"))
    args = ap.parse_args()
    val = True if args._get_kwargs() and args.__dict__["set"] == "true" else False
    toggle(Path(args.path), args.uid, val, args.note)


if __name__ == "__main__":
    main()

