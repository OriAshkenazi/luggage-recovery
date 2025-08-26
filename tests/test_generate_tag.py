import sys
from pathlib import Path

# Allow import from 3d-models directory
sys.path.append(str(Path(__file__).resolve().parents[1] / '3d-models'))

import generate_tag as gt
import trimesh


def test_default_bbox_and_watertight(tmp_path):
    params = gt.Params()
    model = gt.build_islands(params).union(gt.build_body(params)[0])
    stl_path = tmp_path / 'tag.stl'
    gt.export_stl(model, stl_path)
    mesh = trimesh.load_mesh(stl_path)
    assert mesh.is_watertight
    width = params.qr_w + 2 * params.qr_border
    height = params.qr_h + 2 * params.qr_border
    thickness_min = params.body_t + params.island_h
    thickness_max = params.body_t + params.island_h + 1.1
    bbox = mesh.extents
    assert abs(bbox[0] - width) < 0.1
    assert abs(bbox[1] - height) < 0.1
    assert thickness_min - 0.1 <= bbox[2] <= thickness_max
