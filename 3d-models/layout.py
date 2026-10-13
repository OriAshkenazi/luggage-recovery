"""Face layouts for the two-part tag, mirroring the HTML/CSS plan (10 px on the canvas = 1 mm).

Each face is described the way the plan's CSS describes it: absolutely placed physical
features (strap-hole ring, QR) plus a flex column of text and rules with ``gap`` and
``justify-content: space-between``. ``build_face`` turns that into 2D inlay geometry in
face coordinates: millimetres from the face's top-left corner, y down, as seen when
looking at that face.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple, Union

import segno
from shapely.geometry import LineString, Point, Polygon, box
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from glyphs import Font, line_width, polygons, text_line

NOZZLE = 0.4  # fixed: the P1S nozzle. Straight features are whole multiples; no stroke is thinner.
# Bead widths Arachne prints cleanly with a 0.4 mm nozzle. A text stroke is "round" when it
# splits into a whole number of beads inside this range.
BEAD_MIN, BEAD_MAX = 0.36, 0.48
# Assistant ExtraBold sizes whose every stroke (stems, bars, bowls) is 2, 3 or 4 beads.
TEXT_TIERS = (5.0, 7.4, 10.0)
MARGIN = 7.6  # every face: the QR's visible margin, the hole ring's edge, the text's left edge


# ---------------------------------------------------------------- layout primitives (CSS-like)


@dataclass
class Text:
    text: str
    size: float  # CSS font-size, mm
    weight: int = 800
    line_height: float = 1.0
    tracking: float = 0.0  # CSS letter-spacing, em
    uppercase: bool = True
    min_size: float = TEXT_TIERS[0]  # a line too wide for its column steps down tiers to this


@dataclass
class Rule:
    width: float
    height: float  # stroke thickness: a multiple of NOZZLE


@dataclass
class Arrow:
    """Right-pointing arrow (plan: 54x30 px box, 6..8 px stroke)."""

    width: float = 5.4
    height: float = 3.0
    stroke: float = 0.8


@dataclass
class Row:
    items: List["Item"]
    gap: float = 0.0  # align-items: center


@dataclass
class Column:
    items: List["Item"]
    gap: float = 0.0
    max_width: Optional[float] = None


Item = Union[Text, Rule, Arrow, Row, Column]


@dataclass
class Box:
    """A positioned flex column: justify-content: space-between."""

    x: float
    top: float
    width: float
    height: float
    items: List[Item]


@dataclass
class Face:
    ring_center: Tuple[float, float]
    column: Box
    qr_origin: Optional[Tuple[float, float]] = None  # top-left of the symbol (no quiet zone)


@dataclass
class TagLayout:
    width: float = 112.0
    height: float = 68.0
    corner_r: float = 4.0
    hole_d: float = 6.0
    hole_inset: float = 12.4  # hole centre from the top and side edge: the ring sits on the margin
    ring_outer_d: float = 9.6
    ring_width: float = 0.8
    qr_module: float = 1.6  # 4 nozzle lines
    qr_quiet: int = 4
    qr_error: str = "m"
    front: Face = None  # type: ignore[assignment]
    back: Face = None  # type: ignore[assignment]


def default_layout(name: str, phone: str, email: str, url: str) -> TagLayout:
    """The approved plan ("Luggage Tag Layout" canvas), in millimetres.

    Every line sits on a TEXT_TIERS size, so each stroke is a whole number of nozzle lines.
    """
    lay = TagLayout()
    i = lay.hole_inset
    m = MARGIN
    # QR v4 (33 modules) x 1.6 mm = 52.8 mm, with its 4-module quiet zone inside the tag;
    # its visible edge sets the margin used everywhere else.
    qr = 33 * lay.qr_module
    qx, qy = lay.width - m - qr, m
    lay.front = Face(
        ring_center=(i, i),
        qr_origin=(qx, qy),
        # From under the ring to the QR's bottom edge, three groups spaced evenly
        column=Box(x=m, top=19.6, width=qx - lay.qr_quiet * lay.qr_module - m, height=qy + qr - 19.6, items=[
            Column([Text("Found my", 7.4, 800, 0.95, 0.01), Text("luggage?", 7.4, 800, 0.95, 0.01)]),
            Column(gap=1.6, items=[
                Rule(10.4, 0.8),
                Row(gap=1.6, items=[Text("Scan or tap", 5.0, 800, 1.0, 0.0), Arrow(6.8, 3.6, 0.8)]),
            ]),
            Column([Text("to reach", 5.0, 800, 1.0, 0.03), Text("the owner", 5.0, 800, 1.0, 0.03)]),
        ]),
    )
    lay.back = Face(
        ring_center=(lay.width - i, i),  # top-right once the tag is flipped left-right
        column=Box(x=m, top=m, width=lay.width - 2 * m, height=lay.height - 2 * m, items=[
            Column(gap=2.4, max_width=80.0, items=[Text("If found, please contact", 5.0, 800, 1.0, 0.08), Rule(10.4, 0.8)]),
            Column(gap=2.0, items=[
                Text(name, 10.0, 800, 0.95, 0.01),
                Text(phone, 7.4, 800, 1.0, 0.02),
                Text(email, 5.0, 800, 1.0, 0.02),
            ]),
            # The GitHub Pages path is case-sensitive: keep the URL as typed.
            Text(url.split("://", 1)[-1], 5.0, 800, 1.0, 0.0, uppercase=False),
        ]),
    )
    return lay


def stroke_beads(font: Font, size: float) -> Optional[Tuple[int, float, float]]:
    """(beads, narrowest bead, widest bead) when every main stroke of ``font`` at ``size`` splits
    into the same whole number of beads within BEAD_MIN..BEAD_MAX; else None.

    Strokes measured: the I stem, the H bar and the O bowl (thinnest to thickest in Assistant).
    """
    widths = [w * size for w in _stroke_ratios(font)]
    for n in range(1, 8):
        lo, hi = min(widths) / n, max(widths) / n
        if BEAD_MIN - 1e-9 <= lo and hi <= BEAD_MAX + 1e-9:
            return n, lo, hi
    return None


_RATIOS: Dict[int, Tuple[float, ...]] = {}


def _stroke_ratios(font: Font) -> Tuple[float, ...]:
    """Main stroke widths as a fraction of font size."""
    if id(font) not in _RATIOS:
        size = 10.0

        def cut(ch: str, vertical: bool) -> float:
            g = text_line(ch, font, size, 0, 0, 1.0)
            x0, y0, x1, y1 = g.bounds
            line = (LineString([((x0 + x1) / 2, y0 - 1), ((x0 + x1) / 2, y1 + 1)]) if vertical
                    else LineString([(x0 - 1, (y0 + y1) / 2), (x1 + 1, (y0 + y1) / 2)]))
            inter = g.intersection(line)
            return min(part.length for part in getattr(inter, "geoms", [inter]) if part.length > 0)

        _RATIOS[id(font)] = (cut("I", False) / size, cut("H", True) / size, cut("O", False) / size)
    return _RATIOS[id(font)]


# ---------------------------------------------------------------- flex layout -> geometry


@dataclass
class Placed:
    geom: BaseGeometry
    report: List[dict] = field(default_factory=list)


class _Ctx:
    def __init__(self, font_path: Optional[str]):
        self.font_path = font_path
        self.report: List[dict] = []

    def font(self, weight: int) -> Font:
        return Font.load(self.font_path, weight)

    # -- measuring
    def fit_text(self, t: Text, avail: float) -> Tuple[str, float, float]:
        s = t.text.upper() if t.uppercase else t.text
        size = t.size
        f = self.font(t.weight)
        w = line_width(s, f, size, t.tracking)
        if w > avail + 1e-6:
            # Step down to a smaller round-stroke size rather than an arbitrary one
            smaller = [z for z in TEXT_TIERS if t.min_size - 1e-9 <= z < size]
            for z in sorted(smaller, reverse=True):
                if line_width(s, f, z, t.tracking) <= avail + 1e-6:
                    return s, z, line_width(s, f, z, t.tracking)
            raise ValueError(f"{s!r} is {w:.1f} mm wide at {t.size} mm and needs {avail:.1f} mm; "
                             f"it does not fit at any text size down to the {t.min_size} mm minimum")
        return s, size, w

    def size(self, item: Item, avail: float) -> Tuple[float, float]:
        if isinstance(item, Text):
            _, size, w = self.fit_text(item, avail)
            return w, item.line_height * size
        if isinstance(item, Rule):
            return item.width, item.height
        if isinstance(item, Arrow):
            return item.width, item.height
        if isinstance(item, Row):
            ws, hs = zip(*(self.size(c, avail) for c in item.items))
            return sum(ws) + item.gap * (len(ws) - 1), max(hs)
        if isinstance(item, Column):
            a = min(avail, item.max_width or avail)
            ws, hs = zip(*(self.size(c, a) for c in item.items))
            return max(ws), sum(hs) + item.gap * (len(hs) - 1)
        raise TypeError(item)

    # -- drawing (x, top in face mm)
    def draw(self, item: Item, x: float, top: float, avail: float) -> List[BaseGeometry]:
        if isinstance(item, Text):
            s, size, w = self.fit_text(item, avail)
            self.report.append({"text": s, "size_mm": round(size, 2), "width_mm": round(w, 2), "x": round(x, 2), "top": round(top, 2)})
            return [text_line(s, self.font(item.weight), size, x, top, item.line_height, item.tracking)]
        if isinstance(item, Rule):
            return [box(x, top, x + item.width, top + item.height)]
        if isinstance(item, Arrow):
            # Plan path: M3 15h44 M35 4l12 11-12 11 in a 54x30 box, square caps
            k = item.width / 54
            cy = top + 15 * k
            shaft = LineString([(x + 3 * k, cy), (x + 47 * k, cy)])
            head = LineString([(x + 35 * k, top + 4 * k), (x + 47 * k, cy), (x + 35 * k, top + 26 * k)])
            r = item.stroke / 2
            return [shaft.buffer(r, cap_style="square", join_style="mitre"), head.buffer(r, cap_style="square", join_style="mitre")]
        if isinstance(item, Row):
            _, row_h = self.size(item, avail)
            out, cx = [], x
            for c in item.items:
                w, h = self.size(c, avail)
                out += self.draw(c, cx, top + (row_h - h) / 2, avail)
                cx += w + item.gap
            return out
        if isinstance(item, Column):
            a = min(avail, item.max_width or avail)
            out, cy = [], top
            for c in item.items:
                _, h = self.size(c, a)
                out += self.draw(c, x, cy, a)
                cy += h + item.gap
            return out
        raise TypeError(item)

    def layout_box(self, b: Box) -> List[BaseGeometry]:
        heights = [self.size(it, b.width)[1] for it in b.items]
        free = b.height - sum(heights)
        if free < -1e-6:
            raise ValueError(f"Column content is {sum(heights):.1f} mm tall but the box is {b.height:.1f} mm")
        gap = free / (len(b.items) - 1) if len(b.items) > 1 else 0.0
        out, top = [], b.top
        for it, h in zip(b.items, heights):
            out += self.draw(it, b.x, top, b.width)
            top += h + gap
        return out


def qr_geometry(lay: TagLayout, url: str, origin: Tuple[float, float]) -> Tuple[BaseGeometry, segno.QRCode]:
    qr = segno.make(url, error=lay.qr_error)
    m = lay.qr_module
    x0, y0 = origin
    rects = []
    for r, row in enumerate(qr.matrix_iter(scale=1, border=0)):
        row = list(row)
        c = 0
        while c < len(row):
            if not row[c]:
                c += 1
                continue
            start = c
            while c < len(row) and row[c]:
                c += 1
            rects.append(box(x0 + start * m, y0 + r * m, x0 + c * m, y0 + (r + 1) * m))
    # A hair of growth fuses diagonal neighbours into valid, manifold polygons.
    return unary_union(rects).buffer(0.002, join_style="mitre"), qr


def hole_geometry(lay: TagLayout, center: Tuple[float, float]) -> Tuple[BaseGeometry, BaseGeometry]:
    """(printed ring, keep-out disc that no other inlay may enter)."""
    c = Point(center)
    outer = lay.ring_outer_d / 2
    ring = c.buffer(outer, quad_segs=32).difference(c.buffer(outer - lay.ring_width, quad_segs=32))
    return ring, c.buffer(outer + 0.8, quad_segs=32)


@dataclass
class FaceGeometry:
    inlay: BaseGeometry
    text: List[dict]
    qr: Optional[segno.QRCode] = None
    qr_bounds: Optional[Tuple[float, float, float, float]] = None  # symbol incl. quiet zone
    thickened_mm2: float = 0.0


def build_face(lay: TagLayout, face: Face, url: str, font_path: Optional[str]) -> FaceGeometry:
    ctx = _Ctx(font_path)
    parts = ctx.layout_box(face.column)
    text_geom = unary_union(parts)
    ring, ring_keep = hole_geometry(lay, face.ring_center)
    if text_geom.intersects(ring_keep):
        raise ValueError("Text or rules run into the strap-hole ring")
    pieces = [text_geom, ring]
    qr, qr_bounds = None, None
    if face.qr_origin:
        qr_geom, qr = qr_geometry(lay, url, face.qr_origin)
        q = lay.qr_quiet * lay.qr_module
        n = qr.symbol_size(border=0)[0] * lay.qr_module
        x0, y0 = face.qr_origin
        qr_bounds = (x0 - q, y0 - q, x0 + n + q, y0 + n + q)
        if box(*qr_bounds).intersects(unary_union([text_geom, ring_keep])):
            raise ValueError("Something intrudes on the QR quiet zone")
        pieces.append(qr_geom)
    inlay = unary_union(pieces)
    # Punctuation and the '@' have strokes under one nozzle width at these sizes.
    inlay, added = thicken(inlay)
    # +2 microns detaches counters that touch their outline at a single point (e.g. '4', '@'):
    # valid for shapely, invalid as an OCC face.
    inlay = inlay.buffer(0.002, join_style="mitre")
    outline = box(0, 0, lay.width, lay.height)
    if not outline.buffer(-1.0).contains(inlay):
        raise ValueError("Inlay comes closer than 1 mm to the tag edge")
    return FaceGeometry(inlay, ctx.report, qr, qr_bounds, round(added, 3))


# ---------------------------------------------------------------- print checks


def check_straight_features(lay: TagLayout) -> List[str]:
    """Straight inlay features must be whole multiples of the nozzle width."""
    problems = []

    def mult(v: float) -> bool:
        return abs(v / NOZZLE - round(v / NOZZLE)) < 1e-6 and v > 0

    if not mult(lay.ring_width):
        problems.append(f"ring width {lay.ring_width} mm")
    if not mult(lay.qr_module):
        problems.append(f"QR module {lay.qr_module} mm")

    def walk(items: Sequence[Item]):
        for it in items:
            if isinstance(it, Rule) and not mult(it.height):
                problems.append(f"rule thickness {it.height} mm")
            if isinstance(it, Arrow) and not mult(it.stroke):
                problems.append(f"arrow stroke {it.stroke} mm")
            if isinstance(it, (Row, Column)):
                walk(it.items)

    for face in (lay.front, lay.back):
        walk(face.column.items)
    return problems


def check_text_strokes(lay: TagLayout, font_path: Optional[str] = None) -> List[str]:
    """Every line of text must sit on a size whose strokes are whole nozzle lines."""
    problems = []

    def walk(items: Sequence[Item]):
        for it in items:
            if isinstance(it, Text):
                if stroke_beads(Font.load(font_path, it.weight), it.size) is None:
                    problems.append(f"{it.text!r} at {it.size} mm (weight {it.weight})")
            if isinstance(it, (Row, Column)):
                walk(it.items)

    for face in (lay.front, lay.back):
        walk(face.column.items)
    return problems


def thicken(geom: BaseGeometry, step: float = 0.05, rounds: int = 6) -> Tuple[BaseGeometry, float]:
    """Grow only the strokes narrower than the nozzle until they print.

    Thin areas (what an opening of NOZZLE width removes) are dilated by ``step`` per round and
    merged back. Returns the new geometry and the total area added in mm^2.
    """
    r = NOZZLE / 2 - 0.005  # numeric slack only: a stroke of exactly 0.40 mm passes
    start = geom.area
    for _ in range(rounds):
        opened = geom.buffer(-r, join_style="mitre").buffer(r, join_style="mitre")
        lost = [p for p in polygons(geom.difference(opened.buffer(1e-4))) if p.area > 0.03]
        if not lost:
            break
        geom = unary_union([geom] + [p.buffer(step, join_style="round") for p in lost])
    return geom, geom.area - start


def thin_regions(geom: BaseGeometry, min_area: float = 0.03) -> List[Tuple[float, float, float]]:
    """Regions narrower than the nozzle: what a morphological opening of NOZZLE width removes.

    Returns (x, y, area) for every lost region bigger than ``min_area`` mm^2. Mitre joins keep
    square corners intact, so only genuinely thin strokes and slivers show up.
    """
    r = NOZZLE / 2 - 0.005  # numeric slack only: a stroke of exactly 0.40 mm passes
    opened = geom.buffer(-r, join_style="mitre").buffer(r, join_style="mitre")
    lost = geom.difference(opened.buffer(1e-4))
    out = []
    for p in polygons(lost):
        if p.area > min_area:
            c = p.representative_point()
            out.append((round(c.x, 2), round(c.y, 2), round(p.area, 3)))
    return sorted(out, key=lambda t: -t[2])
