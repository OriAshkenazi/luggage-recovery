from pathlib import Path
from bs4 import BeautifulSoup


def load_html(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')


def test_grid_2x2_structure():
    doc = load_html(Path('site/ui/contrast_sandbox.html'))
    grid = doc.select_one('#grid-2x2')
    assert grid is not None
    buttons = grid.select('.btn')
    assert len(buttons) == 4
    # 2x2 grid check: presence of 4 items and grid container is sufficient for static HTML
    for b in buttons:
        # Label present
        assert b.get('aria-label') or b.get_text(strip=True)
        # Role or button tag
        assert b.name == 'button' or b.get('role') == 'button'
        # Focusable
        assert b.has_attr('tabindex') or b.name == 'button'


def test_row_1x4_structure():
    doc = load_html(Path('site/ui/contrast_sandbox.html'))
    row = doc.select_one('#row-1x4')
    assert row is not None
    btns = row.select('.btn')
    assert len(btns) == 4
    # Visible focus style present
    head_styles = doc.select('style#focus-style-marker')
    assert head_styles and ':focus' in head_styles[0].get_text()

