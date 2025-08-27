from pathlib import Path
from PIL import Image
import numpy as np
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / '3d-models'))
import generate_tag as gt


def test_readme_sections():
    text = Path('3d-models/README.md').read_text()
    for section in [
        '## Features',
        '## Install',
        '## Usage',
        '## Variants',
        '## Printing',
        '## Color-Change Layer',
        '## Assembly',
        '## Tolerances',
        '## Troubleshooting',
    ]:
        assert section in text
    for phrase in ['30×50 mm', 'Ø 25 mm', 'color change']:
        assert phrase in text
    assert '![Front preview](outputs/preview_front.png)' in text
    assert '![Back preview](outputs/preview_back.png)' in text


def test_previews(tmp_path):
    p = gt.Params()
    out = tmp_path
    gt.build_and_export(p, out, variant='base', previews='svg')
    # Accept SVG only in CI
    assert (out / 'preview_front.svg').exists()
    assert (out / 'preview_back.svg').exists()
    # If PNG pipeline available, also validate visual similarity
    if gt.cairosvg is not None:  # type: ignore
        # generate PNGs from SVG
        gt.save_preview_png(out / 'preview_front.png', out / 'preview_front.svg')
        gt.save_preview_png(out / 'preview_back.png', out / 'preview_back.svg')
        for name in ['preview_front.png', 'preview_back.png']:
            img = Image.open(out / name)
            assert img.width >= 800
        tmp_png = tmp_path / 'ref.png'
        svg_ref = tmp_path / 'ref.svg'
        gt.save_preview_svg(svg_ref, gt.build_body(p)[0].union(gt.build_islands(p)))
        gt.save_preview_png(tmp_png, svg_ref)
        img1 = np.array(Image.open(out / 'preview_front.png').convert('1'))
        img2 = np.array(Image.open(tmp_png).convert('1'))
        inter = np.logical_and(img1, img2).sum()
        union = np.logical_or(img1, img2).sum()
        assert inter / union >= 0.98
