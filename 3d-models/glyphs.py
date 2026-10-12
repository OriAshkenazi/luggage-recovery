"""Font outlines as 2D shapely geometry, laid out the way a browser lays out a line of text.

Text is placed with the same metrics CSS uses (hhea ascent/descent for the content box,
advance widths, ``kern`` pair kerning, letter-spacing after every glyph), so geometry built
here lines up with the HTML/CSS layout plan. Coordinates are millimetres, y pointing down
(CSS-style); callers convert to model coordinates.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont
from shapely import affinity
from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union
from shapely.validation import make_valid

HERE = Path(__file__).resolve().parent
FONT_CACHE = HERE / ".font-cache"
FONT_CANDIDATES = [
    Path.home() / "Library/Fonts/Assistant-VariableFont_wght.ttf",
    Path("/Library/Fonts/Assistant-VariableFont_wght.ttf"),
    Path("/usr/share/fonts/truetype/assistant/Assistant-VariableFont_wght.ttf"),
]
CURVE_STEPS = 10  # line segments per Bezier segment (sub-0.01 mm error at tag text sizes)


class _FlattenPen(BasePen):
    """Collects glyph contours as polylines (font units, y up)."""

    def __init__(self, glyph_set):
        super().__init__(glyph_set)
        self.contours: List[List[Tuple[float, float]]] = []
        self._cur: List[Tuple[float, float]] = []

    def _moveTo(self, pt):
        self._cur = [pt]

    def _lineTo(self, pt):
        self._cur.append(pt)

    def _curveToOne(self, p1, p2, p3):
        (x0, y0) = self._cur[-1]
        for i in range(1, CURVE_STEPS + 1):
            t = i / CURVE_STEPS
            a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
            self._cur.append((a * x0 + b * p1[0] + c * p2[0] + d * p3[0], a * y0 + b * p1[1] + c * p2[1] + d * p3[1]))

    def _qCurveToOne(self, p1, p2):
        (x0, y0) = self._cur[-1]
        for i in range(1, CURVE_STEPS + 1):
            t = i / CURVE_STEPS
            a, b, c = (1 - t) ** 2, 2 * t * (1 - t), t * t
            self._cur.append((a * x0 + b * p1[0] + c * p2[0], a * y0 + b * p1[1] + c * p2[1]))

    def _closePath(self):
        if len(self._cur) >= 3:
            self.contours.append(self._cur)
        self._cur = []

    _endPath = _closePath


def _signed_area(pts: Sequence[Tuple[float, float]]) -> float:
    return 0.5 * sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, list(pts[1:]) + [pts[0]]))


def resolve_font(path: Optional[str] = None) -> Path:
    candidates = [Path(path)] if path else FONT_CANDIDATES
    for cand in candidates:
        if cand.exists():
            return cand
    raise FileNotFoundError(
        "Assistant font not found. Install it (fonts.google.com/specimen/Assistant) or pass a TTF path; tried: "
        + ", ".join(map(str, candidates))
    )


def _static_instance(src: Path, weight: int) -> Path:
    """A static instance of a variable font at ``weight``, cached by source hash."""
    font = TTFont(str(src))
    if "fvar" not in font:
        return src
    digest = hashlib.sha256(src.read_bytes()).hexdigest()[:12]
    out = FONT_CACHE / f"{src.stem}-w{weight}-{digest}.ttf"
    if not out.exists():
        from fontTools.varLib import instancer

        axis = next(a for a in font["fvar"].axes if a.axisTag == "wght")
        w = max(axis.minValue, min(axis.maxValue, weight))
        FONT_CACHE.mkdir(exist_ok=True)
        instancer.instantiateVariableFont(font, {"wght": w}).save(str(out))
    return out


@dataclass(eq=False)  # identity hash, so per-font caches work
class Font:
    path: Path
    upm: int
    ascent: float  # font units, positive
    descent: float  # font units, positive
    _tt: TTFont
    _kern: Dict[Tuple[str, str], int]

    @classmethod
    @lru_cache(maxsize=None)
    def load(cls, source: Optional[str], weight: int) -> "Font":
        path = _static_instance(resolve_font(source), weight)
        tt = TTFont(str(path))
        hhea = tt["hhea"]
        return cls(path, tt["head"].unitsPerEm, hhea.ascent, -hhea.descent, tt, _read_kerning(tt))

    def glyph_name(self, ch: str) -> str:
        cmap = self._tt.getBestCmap()
        if ord(ch) not in cmap:
            raise ValueError(f"Font {self.path.name} has no glyph for {ch!r}")
        return cmap[ord(ch)]

    @lru_cache(maxsize=None)
    def outline(self, name: str) -> BaseGeometry:
        """Filled glyph outline in font units (y up), nonzero-style fill."""
        gs = self._tt.getGlyphSet()
        pen = _FlattenPen(gs)
        gs[name].draw(pen)
        if not pen.contours:
            return Polygon()
        # Outer contours share the winding of the largest one; the others are counters.
        areas = [_signed_area(c) for c in pen.contours]
        outer_sign = 1 if areas[max(range(len(areas)), key=lambda i: abs(areas[i]))] > 0 else -1
        polys = [(make_valid(Polygon(c)), a) for c, a in zip(pen.contours, areas)]
        fill = unary_union([p for p, a in polys if a * outer_sign > 0])
        holes = unary_union([p for p, a in polys if a * outer_sign < 0])
        return fill.difference(holes)

    def advance(self, name: str) -> int:
        return self._tt["hmtx"][name][0]


def _read_kerning(tt: TTFont) -> Dict[Tuple[str, str], int]:
    """Pair kerning (XAdvance) from the GPOS lookups behind the ``kern`` feature."""
    pairs: Dict[Tuple[str, str], int] = {}
    if "GPOS" not in tt:
        return pairs
    table = tt["GPOS"].table
    lookups = set()
    for rec in table.FeatureList.FeatureRecord:
        if rec.FeatureTag == "kern":
            lookups.update(rec.Feature.LookupListIndex)
    for idx in sorted(lookups):
        for st in table.LookupList.Lookup[idx].SubTable:
            if st.LookupType == 9:  # extension
                st = st.ExtSubTable
            if getattr(st, "LookupType", 2) != 2:
                continue
            firsts = st.Coverage.glyphs
            if st.Format == 1:
                for first, pset in zip(firsts, st.PairSet):
                    for rec in pset.PairValueRecord:
                        v = getattr(rec.Value1, "XAdvance", 0) if rec.Value1 else 0
                        if v:
                            pairs.setdefault((first, rec.SecondGlyph), v)
            elif st.Format == 2:
                c1 = st.ClassDef1.classDefs if st.ClassDef1 else {}
                c2 = st.ClassDef2.classDefs
                by_class2: Dict[int, List[str]] = {}
                for g, c in c2.items():
                    by_class2.setdefault(c, []).append(g)
                for first in firsts:
                    row = st.Class1Record[c1.get(first, 0)]
                    for k, rec in enumerate(row.Class2Record):
                        v = getattr(rec.Value1, "XAdvance", 0) if rec.Value1 else 0
                        if v:
                            for second in by_class2.get(k, []):
                                pairs.setdefault((first, second), v)
    return pairs


def line_width(text: str, font: Font, size: float, tracking: float = 0.0) -> float:
    """CSS advance width of one line (letter-spacing counted after every glyph, as browsers do)."""
    s = size / font.upm
    names = [font.glyph_name(ch) for ch in text]
    w = sum(font.advance(n) for n in names) + sum(font._kern.get(p, 0) for p in zip(names, names[1:]))
    return w * s + tracking * size * len(text)


def text_line(text: str, font: Font, size: float, x: float, top: float, line_height: float, tracking: float = 0.0) -> BaseGeometry:
    """One line of text whose CSS line box has its top-left at (x, top)."""
    s = size / font.upm
    content = (font.ascent + font.descent) * s
    baseline = top + (line_height * size - content) / 2 + font.ascent * s
    names = [font.glyph_name(ch) for ch in text]
    pen = 0.0
    shapes = []
    for i, name in enumerate(names):
        g = font.outline(name)
        if not g.is_empty:
            # font units (y up) -> mm (y down)
            shapes.append(affinity.affine_transform(g, [s, 0, 0, -s, x + pen * s, baseline]))
        pen += font.advance(name)
        if i + 1 < len(names):
            pen += font._kern.get((name, names[i + 1]), 0)
        pen += tracking * size / s
    return unary_union(shapes) if shapes else Polygon()


def polygons(geom: BaseGeometry) -> List[Polygon]:
    if geom.is_empty:
        return []
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    return [g for part in getattr(geom, "geoms", []) for g in polygons(part)]
