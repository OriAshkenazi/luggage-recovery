import json
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).resolve().parents[1] / 'tools'))

import contrast_check as cc


def test_contrast_sample_pass(tmp_path):
    # Use repo tokens as golden sample
    data = json.loads((Path(__file__).resolve().parents[1] / 'tokens' / 'buttons.json').read_text())
    failures, worst = cc.check_tokens(data)
    assert failures == []
    assert worst > 3.0


def test_contrast_large_text_rule(tmp_path):
    # Construct a color on white that passes >=3:1 but fails <4.5:1 by search
    def ratio_of(grey_hex):
        return cc.contrast_ratio(grey_hex, '#FFFFFF')

    # Search a grey between #555555 and #999999 to find ratio window
    chosen = None
    for val in range(0x55, 0x99):
        hx = f'#{val:02x}{val:02x}{val:02x}'
        r = ratio_of(hx)
        if 3.0 <= r < 4.5:
            chosen = hx
            break
    assert chosen, 'Failed to find suitable grey in range'

    data = {
        'buttons': {
            'test': {
                'normal': {'fg': chosen, 'bg': '#FFFFFF'},
                'large': {'fg': chosen, 'bg': '#FFFFFF', 'large': True}
            }
        },
        'focus': {'ring': '#1A73E8', 'adjacent': '#FFFFFF'}
    }
    failures, _ = cc.check_tokens(data)
    # Expect normal to fail and large to pass
    keys = {(v, s) for v, s, *_ in failures}
    assert ('test', 'normal') in keys
    assert ('test', 'large') not in keys


def test_contrast_failure_exit_code(tmp_path, monkeypatch):
    bad = {
        'buttons': {
            'weak': {'default': {'fg': '#AAAAAA', 'bg': '#FFFFFF'}}
        }
    }
    failures, _ = cc.check_tokens(bad)
    assert failures, 'Expected failure for low contrast'

