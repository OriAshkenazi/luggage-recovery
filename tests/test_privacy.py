import json
import os
from pathlib import Path

from fastapi.testclient import TestClient

import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / 'app'))
from main import app  # noqa


def sha256_hex(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def make_row(uid: str, token: str, missing: bool, name='[REDACTED]', phone='[REDACTED]', addr='[REDACTED]'):
    return {
        'uid': uid,
        'token_hash': 'sha256:' + sha256_hex(token),
        'missing': missing,
        'owner_name': name,
        'owner_phone': phone,
        'owner_address': addr,
        'created_at': '2025-01-01T00:00:00Z',
        'updated_at': '2025-01-01T00:00:00Z',
    }


def test_privacy_gate(tmp_path, monkeypatch):
    reg = tmp_path / 'registry.jsonl'
    uid, tok = 'U1', 'T1'
    with reg.open('w') as f:
        f.write(json.dumps(make_row(uid, tok, False)) + '\n')
    monkeypatch.setenv('REGISTRY_PATH', str(reg))
    client = TestClient(app)
    # missing=false → no PII
    r = client.get('/r', params={'u': uid, 't': tok})
    assert r.status_code == 200
    assert '[REDACTED]' not in r.text
    # toggle to missing=true
    with reg.open('w') as f:
        f.write(json.dumps(make_row(uid, tok, True)) + '\n')
    r = client.get('/r', params={'u': uid, 't': tok})
    assert r.status_code == 200
    assert '[REDACTED]' in r.text
    # tamper token
    r = client.get('/r', params={'u': uid, 't': 'BAD'})
    assert r.status_code == 400

