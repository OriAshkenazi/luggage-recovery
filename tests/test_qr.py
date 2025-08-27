from pathlib import Path
import json
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / '3d-models'))
import generate_tag as gt

try:
    import segno  # type: ignore
except Exception:
    segno = None


def _dark_count(text: str) -> int:
    assert segno is not None
    qr = segno.make(text, error='m')
    # include quiet zone = 4
    return sum(1 for row in qr.matrix_iter(scale=1, border=4) for bit in row if bit)


def test_qr_islands_dark_count(tmp_path):
    text = 'HELLO-WORLD-1234'
    p = gt.Params()
    out = gt.build_and_export(p, tmp_path, variant='islands', previews='none', deterministic=True, qr_text=text)
    manifest = json.loads((out / 'manifest.json').read_text())
    if segno is not None:
        assert manifest.get('dark_modules') == _dark_count(text)
    # features STL exists
    assert (out / 'tag_alt_qr_islands_features.stl').exists()


def test_sticker_svg_dimensions(tmp_path):
    p = gt.Params()
    out = gt.build_and_export(p, tmp_path, variant='islands', previews='none', deterministic=True, qr_text='DEMO')
    svg = (out / 'qr_sticker_30x50.svg').read_text()
    assert 'width="50mm"' in svg and 'height="30mm"' in svg
    assert '<circle' in svg and '<rect' in svg


def test_presets_basic(tmp_path):
    for preset in ['pla', 'petg', 'abs']:
        p = gt.Params()
        out = gt.build_and_export(p, tmp_path / preset, variant='flat', previews='none', deterministic=True, preset=preset)
        mesh = __import__('trimesh').load_mesh(out / 'tag_alt_flat_front.stl')
        width = p.qr_w + 2 * p.qr_border
        height = p.qr_h + 2 * p.qr_border
        bbox = mesh.bounds
        assert abs((bbox[1][0] - bbox[0][0]) - width) < 0.1
        assert abs((bbox[1][1] - bbox[0][1]) - height) < 0.1


def test_determinism_hashes(tmp_path):
    p = gt.Params()
    args = dict(variant='islands', previews='none', deterministic=True, qr_text='DEMO', layer_height=0.20)
    out1 = gt.build_and_export(p, tmp_path / 'a', **args)
    out2 = gt.build_and_export(p, tmp_path / 'b', **args)
    m1 = json.loads((out1 / 'manifest.json').read_text())
    m2 = json.loads((out2 / 'manifest.json').read_text())
    # Compare checksums for STLs
    for k in ['tag_alt_qr_islands_base.stl', 'tag_alt_qr_islands_features.stl']:
        assert m1['files'][k]['sha256'] == m2['files'][k]['sha256']


def test_strict_invalid_pockets(tmp_path):
    p = gt.Params(body_t=3.0, nfc_depth=2.8, qr_pocket_depth=0.5)
    try:
        gt.build_and_export(p, tmp_path, variant='flat', previews='none', deterministic=True, qr_text='X', strict=True)
        assert False, 'Expected ValueError'
    except ValueError:
        pass

