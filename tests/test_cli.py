import sys
import subprocess
from pathlib import Path
import itertools
import trimesh

sys.path.append(str(Path(__file__).resolve().parents[1] / '3d-models'))

import generate_tag as gt


PYTHON = sys.executable


def run_cli(out, *args):
    cmd = [PYTHON, str(Path(__file__).resolve().parents[1] / '3d-models' / 'generate_tag.py'), '--out', str(out), *args]
    return subprocess.run(cmd, capture_output=True)


def test_yaml_cli_precedence(tmp_path):
    yaml_path = tmp_path / 'p.yaml'
    yaml_path.write_text('qr_border: 2\n')
    out = tmp_path / 'out'
    run_cli(out, '--params', str(yaml_path), '--qr_border', '4')
    mesh = trimesh.load_mesh(out / 'tag_base.stl')
    width = 50 + 2 * 4
    assert abs((mesh.bounds[1][0] - mesh.bounds[0][0]) - width) < 0.1


def test_cli_matrix(tmp_path):
    variants = ['base', 'flat', 'islands']
    straps = [('--strap_hole_d', '5'), ('--slot', '5x20')]
    borders = ['2', '3', '4']
    fits = ['0.2', '0.3', '0.4']
    for variant, (flag, val), border, fit in itertools.product(variants, straps, borders, fits):
        out = tmp_path / f'{variant}_{flag[2:]}_{border}_{fit}'
        res = run_cli(out, '--variant', variant, flag, val, '--qr_border', border, '--fit_clearance', fit)
        assert res.returncode == 0
        if variant == 'islands':
            assert (out / 'tag_alt_qr_islands_base.stl').exists()
            assert (out / 'tag_alt_qr_islands_features.stl').exists()
        elif variant == 'flat':
            assert (out / 'tag_alt_flat_front.stl').exists()
        else:
            assert (out / 'tag_base.stl').exists()
            assert (out / 'preview_front.png').exists()
            assert (out / 'preview_back.png').exists()


def test_invalid_combo(tmp_path):
    out = tmp_path / 'bad'
    res = run_cli(out, '--nfc_depth', '2.8', '--qr_pocket_depth', '0.5', '--body_t', '3')
    assert res.returncode != 0
    assert b'pocket depths' in res.stderr
