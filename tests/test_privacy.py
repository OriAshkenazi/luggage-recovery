import json
import os
from pathlib import Path

from fastapi.testclient import TestClient

import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / 'app'))
from main import app  # noqa


def hmac_hex(secret: str, s: str) -> str:
    import hashlib, hmac
    return hmac.new(secret.encode('utf-8'), s.encode('utf-8'), hashlib.sha256).hexdigest()


def make_row(uid: str, token: str, missing: bool, name='[REDACTED]', phone='[REDACTED]', addr='[REDACTED]', *, secret='S'):
    return {
        'uid': uid,
        'token_hash': 'hmac256:' + hmac_hex(secret, token),
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
    secret = 'S'
    with reg.open('w') as f:
        f.write(json.dumps(make_row(uid, tok, False, secret=secret)) + '\n')
    monkeypatch.setenv('REGISTRY_PATH', str(reg))
    monkeypatch.setenv('RECOVERY_SECRET', secret)
    monkeypatch.setenv('ALLOW_LEGACY_SHA256', 'false')
    client = TestClient(app)
    # missing=false → no PII
    r = client.get('/r', params={'u': uid, 't': tok})
    assert r.status_code == 200
    assert '[REDACTED]' not in r.text
    # toggle to missing=true
    with reg.open('w') as f:
        f.write(json.dumps(make_row(uid, tok, True, secret=secret)) + '\n')
    r = client.get('/r', params={'u': uid, 't': tok})
    assert r.status_code == 200
    assert '[REDACTED]' in r.text
    # tamper token
    r = client.get('/r', params={'u': uid, 't': 'BAD'})
    assert r.status_code == 400


def test_security_headers(tmp_path, monkeypatch):
    reg = tmp_path / 'registry.jsonl'
    uid, tok, secret = 'U2', 'T2', 'S'
    with reg.open('w') as f:
        f.write(json.dumps(make_row(uid, tok, False, secret=secret)) + '\n')
    monkeypatch.setenv('REGISTRY_PATH', str(reg))
    monkeypatch.setenv('RECOVERY_SECRET', secret)
    client = TestClient(app)
    r = client.get('/r', params={'u': uid, 't': tok})
    assert r.headers.get('Content-Security-Policy')
    assert r.headers.get('Referrer-Policy') == 'no-referrer'
    assert 'geolocation' in r.headers.get('Permissions-Policy', '')


def test_legacy_sha256_rejected_by_default(tmp_path, monkeypatch):
    import hashlib
    reg = tmp_path / 'registry.jsonl'
    uid, tok = 'U3', 'T3'
    with reg.open('w') as f:
        f.write(json.dumps({
            'uid': uid,
            'token_hash': 'sha256:' + hashlib.sha256(tok.encode()).hexdigest(),
            'missing': False,
            'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-01-01T00:00:00Z',
        }) + '\n')
    monkeypatch.setenv('REGISTRY_PATH', str(reg))
    monkeypatch.delenv('ALLOW_LEGACY_SHA256', raising=False)
    monkeypatch.setenv('RECOVERY_SECRET', 'S')
    client = TestClient(app)
    r = client.get('/r', params={'u': uid, 't': tok})
    assert r.status_code == 400
