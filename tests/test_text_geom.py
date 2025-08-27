from pathlib import Path
import json
import numpy as np
import trimesh
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / '3d-models'))
import generate_tag as gt


def _bbox(mesh):
    b = mesh.bounds
    return b[0], b[1]


def test_front_prompt_and_back_text_within_bounds(tmp_path):
    p = gt.Params(
        front_prompt_text='Scan me to find my owner',
        front_text_style='emboss',
        front_text_height=0.5,
        front_prompt_edge='bottom',
        back_name='REDACTED', back_phone='REDACTED', back_address='REDACTED',
        back_text_style='engrave',
        back_text_h=4.0, back_line_gap=1.2, back_margin=3.0,
    )
    out = gt.build_and_export(p, tmp_path, variant='islands', previews='none', deterministic=True, text_features=True)
    # Base includes text in islands base
    base = trimesh.load_mesh(out / 'tag_alt_qr_islands_base.stl')
    # Rough band check: front text should be in lower band (y near -height/2..)
    width = p.qr_w + 2 * p.qr_border
    height = p.qr_h + 2 * p.qr_border
    bmin, bmax = _bbox(base)
    # ensure extents match
    assert abs((bmax[0]-bmin[0]) - width) < 0.2
    assert abs((bmax[1]-bmin[1]) - height) < 0.2
    # If features exist, ensure co-registration
    if (out / 'front_text_features.stl').exists():
        f = trimesh.load_mesh(out / 'front_text_features.stl')
        # XY bounds inside base XY
        fbmin, fbmax = _bbox(f)
        assert fbmin[0] >= bmin[0] - 1e-3 and fbmax[0] <= bmax[0] + 1e-3
        assert fbmin[1] >= bmin[1] - 1e-3 and fbmax[1] <= bmax[1] + 1e-3


def test_min_wall_for_back_engrave():
    p = gt.Params(back_name='X', back_text_style='engrave', back_text_h=4.0, back_line_gap=1.2)
    # Make engraving too deep via front_text_depth used for engrave distance
    p.front_text_depth = p.body_t - p.min_wall + 0.2
    try:
        gt.build_and_export(p, Path('/tmp')/ 'noop', variant='flat', previews='none', deterministic=True)
        assert False, 'Expected wall thickness violation'
    except ValueError:
        pass

