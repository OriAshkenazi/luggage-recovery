import sys
from pathlib import Path
import time
import hashlib

sys.path.append(str(Path(__file__).resolve().parents[1] / '3d-models'))

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "3d-models"))

import generate_tag as gt
import pytest
import trimesh
import numpy as np
import psutil
import time
from hypothesis import given, settings, strategies as st, assume


def _build(tmp_path, params=None, variant="all"):
    p = params or gt.Params()
    gt.build_and_export(p, tmp_path, variant)
    return tmp_path


@pytest.mark.parametrize("fname", [
    "tag_base.stl",
    "tag_alt_flat_front.stl",
    "tag_alt_qr_islands_base.stl",
    "tag_alt_qr_islands_features.stl",
])
def test_geometry_integrity(tmp_path, fname):
    out = _build(tmp_path)
    mesh = trimesh.load_mesh(out / fname)
    assert mesh.is_watertight
    assert mesh.is_winding_consistent
    assert not mesh.is_empty
    assert not mesh.is_self_intersecting
    assert not np.isnan(mesh.vertices).any()


def test_dimensional_contracts(tmp_path):
    p = gt.Params()
    out = _build(tmp_path, p, variant="all")
    mesh_flat = trimesh.load_mesh(out / "tag_alt_flat_front.stl")
    width = p.qr_w + 2 * p.qr_border
    height = p.qr_h + 2 * p.qr_border
    bbox = mesh_flat.bounds
    assert abs((bbox[1][0] - bbox[0][0]) - width) < 0.1
    assert abs((bbox[1][1] - bbox[0][1]) - height) < 0.1
    assert abs((bbox[1][2] - bbox[0][2]) - p.body_t) < 0.1
    # NFC recess
    zmin = bbox[0][2]
    section_z = zmin + p.nfc_depth / 2
    section = mesh_flat.section(plane_origin=[0, 0, section_z], plane_normal=[0, 0, 1])
    poly = section.to_planar()[0]
    diam = poly.bounds[1][0] - poly.bounds[0][0]
    assert abs(diam - (p.nfc_d + p.fit_clearance)) < 0.1
    locs = mesh_flat.ray.intersects_location([[0, 0, -10]], [[0, 0, 1]])
    zs = sorted([loc[2] for loc in locs])
    assert abs((zs[1] - zs[0]) - p.nfc_depth) < 0.1
    # QR pocket depth
    locs = mesh_flat.ray.intersects_location([[0, 0, 10]], [[0, 0, -1]])
    zs = sorted([loc[2] for loc in locs], reverse=True)
    assert abs((zs[0] - zs[1]) - p.qr_pocket_depth) < 0.05


def test_variant_correctness(tmp_path):
    p = gt.Params()
    out = _build(tmp_path, p, variant="all")
    base = trimesh.load_mesh(out / "tag_base.stl")
    flat = trimesh.load_mesh(out / "tag_alt_flat_front.stl")
    islands_b = trimesh.load_mesh(out / "tag_alt_qr_islands_base.stl")
    islands_f = trimesh.load_mesh(out / "tag_alt_qr_islands_features.stl")
    assert abs(base.bounds[1][2] - (p.body_t/2 + p.island_h)) < 0.1
    assert abs(flat.bounds[1][2] - p.body_t/2) < 0.1
    # alignment
    assert np.allclose(islands_b.bounds[:, :2], islands_f.bounds[:, :2], atol=0.05)
    assert abs(islands_b.bounds[1][2] - p.body_t/2) < 0.05
    assert abs(islands_f.bounds[0][2] - p.body_t/2) < 0.05
    assert islands_b.bounds[1][2] <= islands_f.bounds[0][2] + 1e-6


def test_color_switch_layer_index():
    for ih in [0.4, 0.6]:
        for lh in [0.16, 0.20, 0.28]:
            layer = gt.color_switch_layer_index(ih, lh)
            assert layer >= 1
            assert abs(layer * lh - ih) <= 0.02


def test_cli_determinism(tmp_path):
    p = gt.Params()
    out1 = tmp_path / "a"
    out2 = tmp_path / "b"
    _build(out1, p, variant="base")
    _build(out2, p, variant="base")
    h1 = gt.hash_mesh(out1 / "tag_base.stl")
    h2 = gt.hash_mesh(out2 / "tag_base.stl")
    assert h1 == h2


def test_performance(tmp_path):
    proc = psutil.Process()
    p = gt.Params()
    start = time.perf_counter()
    _build(tmp_path / "cold", p, variant="base")
    cold = time.perf_counter() - start
    start = time.perf_counter()
    _build(tmp_path / "warm", p, variant="base")
    warm = time.perf_counter() - start
    mem = proc.memory_info().rss
    assert cold <= 8
    assert warm <= 4
    assert mem < 500 * 1024 * 1024


@settings(max_examples=5, deadline=None)
@given(
    qr_w=st.floats(45, 60),
    qr_h=st.floats(25, 40),
    qr_border=st.floats(1.5, 5),
    body_t=st.floats(2.8, 4),
    corner_r=st.floats(1.5, 6),
    nfc_depth=st.floats(0.6, 1.2),
    fit_clearance=st.floats(0.15, 0.5),
)
def test_param_fuzz(tmp_path, qr_w, qr_h, qr_border, body_t, corner_r, nfc_depth, fit_clearance):
    p = gt.Params(
        qr_w=qr_w,
        qr_h=qr_h,
        qr_border=qr_border,
        body_t=body_t,
        corner_r=corner_r,
        nfc_depth=nfc_depth,
        fit_clearance=fit_clearance,
    )
    try:
        _build(tmp_path, p, variant="base")
    except ValueError:
        assume(False)
    mesh = trimesh.load_mesh(tmp_path / "tag_base.stl")
    assert mesh.is_watertight
    width = p.qr_w + 2 * p.qr_border
    assert abs((mesh.bounds[1][0] - mesh.bounds[0][0]) - width) < 0.1
