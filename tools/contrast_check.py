#!/usr/bin/env python3
"""WCAG AA contrast checker for button tokens.

Library + CLI skeleton.

Usage:
  python tools/contrast_check.py tokens/buttons.json

JSON schema (example):
{
  "buttons": {
    "primary": {"default": {"fg": "#FFFFFF", "bg": "#0D6EFD"},
                 "hover": {"fg": "#FFFFFF", "bg": "#0B5ED7", "large": false}},
    "link": {"default": {"fg": "#0B3D91", "bg": "#FFFFFF", "large": true}}
  },
  "focus": {"ring": "#1A73E8", "adjacent": "#FFFFFF"}
}
"""

from __future__ import annotations
import sys
import json
import math
from pathlib import Path
from typing import Dict, Tuple, List


def _parse_hex(color: str) -> Tuple[float, float, float]:
    c = color.strip()
    if c.startswith('#'):
        c = c[1:]
    if len(c) == 3:
        c = ''.join([ch * 2 for ch in c])
    if len(c) != 6:
        raise ValueError(f"Invalid color: {color}")
    r = int(c[0:2], 16) / 255.0
    g = int(c[2:4], 16) / 255.0
    b = int(c[4:6], 16) / 255.0
    return r, g, b


def _linearize(channel: float) -> float:
    # sRGB to linear
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    r, g, b = _parse_hex(hex_color)
    rl, gl, bl = _linearize(r), _linearize(g), _linearize(b)
    # Rec 709 luminance
    return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl


def contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    L1 = relative_luminance(fg_hex)
    L2 = relative_luminance(bg_hex)
    lighter = max(L1, L2)
    darker = min(L1, L2)
    return (lighter + 0.05) / (darker + 0.05)


def check_tokens(tokens: Dict, *, large_map: Dict[Tuple[str, str], bool] | None = None) -> Tuple[List[Tuple[str, str, float, float]], float]:
    """Return list of failures: (variant, state, ratio, threshold) and worst ratio."""
    failures: List[Tuple[str, str, float, float]] = []
    worst = math.inf
    btns = tokens.get('buttons', {})
    for variant, states in btns.items():
        for state, spec in states.items():
            fg = spec.get('fg')
            bg = spec.get('bg')
            if not fg or not bg:
                continue
            ratio = round(contrast_ratio(fg, bg), 2)
            worst = min(worst, ratio)
            large_flag = spec.get('large', False)
            if large_map and (variant, state) in large_map:
                large_flag = large_map[(variant, state)]
            threshold = 3.0 if large_flag else 4.5
            if ratio < threshold:
                failures.append((variant, state, ratio, threshold))

    # Focus ring rule
    focus = tokens.get('focus', {})
    ring = focus.get('ring')
    adj = focus.get('adjacent')
    if ring and adj:
        r = round(contrast_ratio(ring, adj), 2)
        worst = min(worst, r)
        if r < 3.0:
            failures.append(("focus", "ring", r, 3.0))
    return failures, (worst if worst is not math.inf else 0.0)


def main(argv: List[str]) -> int:
    if len(argv) < 2:
        print("Usage: contrast_check.py <tokens.json>")
        return 2
    path = Path(argv[1])
    data = json.loads(path.read_text())
    failures, worst = check_tokens(data)
    # Print table
    if failures:
        print("Contrast failures:")
        for v, s, ratio, thr in failures:
            print(f"- {v}.{s}: ratio={ratio:.2f} < {thr:.1f}")
        return 1
    else:
        print(f"All contrast checks passed. Worst ratio: {worst:.2f}")
        return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))

