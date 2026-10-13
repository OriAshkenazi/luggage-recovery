"""Two-part tag: layout rules, printability checks, and the exported STLs."""

import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest
import trimesh
from shapely.geometry import LineString, box

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "3d-models"))
import layout as L  # noqa: E402
import two_part_tag as tp  # noqa: E402
from glyphs import Font, line_width, polygons, text_line  # noqa: E402

CONTACT = tp.Contact()  # placeholders only: no personal data in tests


def _layout():
    return L.default_layout(CONTACT.name, CONTACT.phone, CONTACT.email, CONTACT.qr_url)


@pytest.fixture(scope="module")
def exported(tmp_path_factory):
    out = tmp_path_factory.mktemp("two-part")
    res = tp.export(CONTACT, out)
    return out, res


# ---------------------------------------------------------------- 2D layout


def test_text_line_matches_css_width():
    f = Font.load(None, 800)
    g = text_line("FOUND MY", f, 5.8, 3.0, 0.0, 0.95)
    minx, _, maxx, _ = g.bounds
    # Ink sits within the CSS advance box, give or take side bearings (the Y overhangs a little)
    assert 3.0 <= minx < 3.6
    assert abs(maxx - (3.0 + line_width("FOUND MY", f, 5.8))) < 0.1


def test_straight_features_are_nozzle_multiples():
    assert L.check_straight_features(_layout()) == []
    lay = _layout()
    lay.ring_width = 0.6
    assert L.check_straight_features(lay) == ["ring width 0.6 mm"]


def test_thin_region_detection():
    line = LineString([(0, 0), (10, 0)])
    assert L.thin_regions(line.buffer(0.15, cap_style="flat"))  # 0.3 mm wide: flagged
    assert not L.thin_regions(line.buffer(0.2, cap_style="flat"))  # 0.4 mm: prints
    assert not L.thin_regions(box(0, 0, 1.2, 1.2))  # a QR module keeps its square corners


def test_faces_have_no_sub_nozzle_strokes():
    lay = _layout()
    for face in (lay.front, lay.back):
        assert L.thin_regions(L.build_face(lay, face, CONTACT.qr_url, None).inlay) == []


def test_long_text_shrinks_then_fails():
    lay = L.default_layout("A VERY LONG NAME FOR A TAG", CONTACT.phone, CONTACT.email, CONTACT.qr_url)
    name = next(t for t in L.build_face(lay, lay.back, CONTACT.qr_url, None).text if t["text"].startswith("A VERY"))
    assert name["size_mm"] < 7.6 and name["width_mm"] <= 77.0 + 1e-6
    lay = L.default_layout("AN ABSURDLY LONG OWNER NAME THAT CANNOT FIT", CONTACT.phone, CONTACT.email, CONTACT.qr_url)
    with pytest.raises(ValueError, match="minimum"):
        L.build_face(lay, lay.back, CONTACT.qr_url, None)


def test_text_stays_out_of_qr_quiet_zone_and_hole():
    lay = _layout()
    lay.front.column.width = 40.0  # would reach into the quiet zone
    lay.front.column.items[0].items[0].text = "FOUND MY LUGGAGE"
    with pytest.raises(ValueError):
        L.build_face(lay, lay.front, CONTACT.qr_url, None)


# ---------------------------------------------------------------- 3D export


def test_parts_exist_and_are_watertight(exported):
    out, _ = exported
    for name in ("front_base", "front_inlay", "back_base", "back_inlay"):
        for path in (out / f"{name}.stl", out / "assembled" / f"{name}.stl"):
            mesh = trimesh.load_mesh(path)
            assert mesh.is_watertight and mesh.is_volume, path


def test_print_orientation(exported):
    out, _ = exported
    b = tp.Build()
    for half in ("front", "back"):
        base = trimesh.load_mesh(out / f"{half}_base.stl")
        inlay = trimesh.load_mesh(out / f"{half}_inlay.stl")
        # Inlay is the first layers on the plate; the base shares the same footprint
        assert abs(inlay.bounds[0][2]) < 1e-3 and abs(inlay.bounds[1][2] - b.inlay_depth) < 1e-3
        assert abs(base.bounds[0][2]) < 1e-3
        assert np.allclose(base.bounds[:, :2], [[-42.5, -27.0], [42.5, 27.0]], atol=0.01)
    assert abs(trimesh.load_mesh(out / "front_base.stl").bounds[1][2] - (b.half_t + b.pin_h)) < 0.02  # pins
    assert abs(trimesh.load_mesh(out / "back_base.stl").bounds[1][2] - b.half_t) < 1e-3


def test_base_and_inlay_fill_each_half(exported):
    _, res = exported
    parts = res["parts"]
    for half in ("front", "back"):
        base, inlay = parts[f"{half}_base"].val(), parts[f"{half}_inlay"].val()
        union = base.fuse(inlay)
        # Complementary: no overlap, nothing missing
        assert abs(base.Volume() + inlay.Volume() - union.Volume()) < 0.05


def test_qr_modules_match_the_symbol(exported):
    out, res = exported
    lay = res["layout"]
    qr = res["faces"]["front"].qr
    mesh = trimesh.load_mesh(out / "assembled" / "front_inlay.stl")
    x0, y0 = lay.front.qr_origin
    m = lay.qr_module
    matrix = [list(r) for r in qr.matrix_iter(scale=1, border=0)]
    origins, expect = [], []
    for r, row in enumerate(matrix):
        for c, dark in enumerate(row):
            # face mm -> model mm (front: x right, y up)
            origins.append([x0 + (c + 0.5) * m - lay.width / 2, lay.height / 2 - (y0 + (r + 0.5) * m), 10])
            expect.append(bool(dark))
    origins = np.array(origins)
    hit = mesh.ray.intersects_any(origins, np.tile([0, 0, -1.0], (len(origins), 1)))
    assert hit.tolist() == expect


def test_hole_ring_lines_up_on_both_faces(exported):
    out, res = exported
    hx, hy = res["positions"]["hole"]
    lay = res["layout"]
    r_mid = lay.ring_outer_d / 2 - lay.ring_width / 2
    for name, z, d in (("front_inlay", 10, -1.0), ("back_inlay", -10, 1.0)):
        mesh = trimesh.load_mesh(out / "assembled" / f"{name}.stl")
        pts = [[hx + r_mid * np.cos(a), hy + r_mid * np.sin(a), z] for a in np.linspace(0, 2 * np.pi, 12, endpoint=False)]
        assert mesh.ray.intersects_any(np.array(pts), np.tile([0, 0, d], (12, 1))).all(), name


def test_back_text_reads_correctly_after_flipping(exported):
    out, _ = exported
    mesh = trimesh.load_mesh(out / "assembled" / "back_inlay.stl")
    # Back view puts the text column at the left (small x), i.e. +X in model space once
    # the tag is turned over; the hole ring sits at the back view's top-right (-X).
    text = mesh.vertices[mesh.vertices[:, 1] < 10]
    assert text[:, 0].max() > 30 and text[:, 0].min() > -40


def test_nfc_pocket_and_pins(exported):
    out, res = exported
    b = tp.Build()
    nx, ny = res["positions"]["nfc"]
    back = trimesh.load_mesh(out / "assembled" / "back_base.stl")
    hits, _, _ = back.ray.intersects_location([[nx, ny, 10]], [[0, 0, -1]])
    assert abs(hits[:, 2].max() - (-b.nfc_pocket_depth)) < 1e-3
    front = trimesh.load_mesh(out / "assembled" / "front_base.stl")
    for px, py in res["positions"]["pins"]:
        hits, _, _ = front.ray.intersects_location([[px, py, -10]], [[0, 0, 1]])
        assert abs(hits[:, 2].min() - (-b.pin_h)) < 0.02
        hits, _, _ = back.ray.intersects_location([[px, py, 10]], [[0, 0, -1]])
        assert abs(hits[:, 2].max() - (-(b.pin_h + 0.1))) < 1e-3
    assert b.pin_clearance >= 0.2


def test_build_rejects_bad_layer_multiples():
    with pytest.raises(ValueError, match="layers"):
        tp.build(CONTACT, tp.Build(inlay_depth=0.5))


def test_export_is_deterministic(exported, tmp_path):
    out, _ = exported
    tp.export(CONTACT, tmp_path)
    for name in ("front_base", "front_inlay", "back_base", "back_inlay"):
        a = hashlib.sha256((out / f"{name}.stl").read_bytes()).hexdigest()
        b = hashlib.sha256((tmp_path / f"{name}.stl").read_bytes()).hexdigest()
        assert a == b, name


def test_manifest_has_no_contact_text(exported):
    out, _ = exported
    text = (out / "manifest.json").read_text()
    for value in (CONTACT.name, CONTACT.phone, CONTACT.email):
        assert value not in text


def test_bambu_slice_check():
    import bambu_project as bp

    ok = "\n".join([
        # As in real P1S output: the start G-code loads the first filament without an M620/T pair
        "; CHANGE_LAYER", "G1 X1 Y1 E0.5", "M620 S0A", "T0", "G1 X2 Y2 E0.5",
        "; CHANGE_LAYER", "G1 X1 Y1 E0.5", "M620 S1A", "T1", "G1 X2 Y2 E0.5",
        "; CHANGE_LAYER", "G1 X1 Y1 E0.5", "M620 S0A", "T0", "G1 X2 Y2 E0.5",
        "; CHANGE_LAYER", "G1 X1 Y1 E0.5",
        "; total estimated time: 31m 2s",
    ])
    r = bp._check_slice(ok)
    assert r["dark_layers"] == [1, 2, 3] and r["swaps"] == 3 and r["layers"] == 4
    late = ok.replace("; CHANGE_LAYER\nG1 X1 Y1 E0.5\n; total", "; CHANGE_LAYER\nM620 S1A\nT1\nG1 X1 Y1 E0.5\n; total")
    with pytest.raises(SystemExit, match="Unexpected slice"):
        bp._check_slice(late)  # dark filament on layer 4: the inlay would show through the base


def test_every_glyph_is_one_solid_piece():
    """TrueType non-zero fill: overlapping or self-crossing contours (the variable font's '4')
    must not split a letter into separate pieces."""
    two_piece = set("ij?!")
    counters = {"4": 1, "8": 2, "B": 2, "@": 1, "O": 1, "A": 1}
    for weight in (700, 800):
        f = Font.load(None, weight)
        for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@.,-+/?!":
            parts = polygons(text_line(ch, f, 6.0, 0, 0, 1.0))
            assert len(parts) == (2 if ch in two_piece else 1), (weight, ch, len(parts))
            if ch in counters:
                assert sum(len(p.interiors) for p in parts) == counters[ch], (weight, ch)
