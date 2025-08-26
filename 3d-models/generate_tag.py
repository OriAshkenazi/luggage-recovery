"""Parametric luggage tag generator using CadQuery."""

from dataclasses import dataclass, asdict
from pathlib import Path
import os
os.environ["PYGLET_HEADLESS"] = "True"
import argparse
import cairosvg
import yaml
import cadquery as cq
import trimesh
import hashlib


@dataclass
class Params:
    qr_w: float = 50.0
    qr_h: float = 30.0
    qr_border: float = 3.0
    body_t: float = 3.0
    min_wall: float = 1.5
    corner_r: float = 3.0
    nfc_d: float = 25.0
    nfc_depth: float = 1.0
    fit_clearance: float = 0.25
    strap_hole_d: float = 5.0
    strap_slot_w: float = 0.0
    strap_slot_l: float = 0.0
    qr_pocket_depth: float = 0.2
    island_h: float = 0.5


def load_params(path: Path | None) -> Params:
    params = Params()
    if path and path.exists():
        data = yaml.safe_load(path.read_text())
        for k, v in data.items():
            setattr(params, k, v)
    return params


def build_body(p: Params) -> tuple[cq.Workplane, float, float]:
    """Build the tag body with pockets and strap feature."""
    width = p.qr_w + 2 * p.qr_border
    height = p.qr_h + 2 * p.qr_border

    if p.nfc_depth + p.qr_pocket_depth > p.body_t - 0.6:
        raise ValueError("Combined pocket depths too large")

    body = (
        cq.Workplane("XY")
        .rect(width, height)
        .extrude(p.body_t / 2, both=True)
    )
    body = body.edges("|Z").fillet(p.corner_r)

    # Strap reinforcement and hole/slot
    strap_center_y = height / 2 - p.min_wall - (
        (p.strap_slot_l or p.strap_hole_d) / 2
    )
    if p.strap_slot_w and p.strap_slot_l:
        pad_len = p.strap_slot_l + 2 * p.min_wall
        pad_w = p.strap_slot_w + 2 * p.min_wall
        pad = (
            cq.Workplane("XY")
            .center(0, strap_center_y)
            .slot2D(pad_len, pad_w)
            .extrude(p.body_t / 2, both=True)
        )
        body = body.union(pad)
        body = (
            body.faces(">Z")
            .workplane()
            .center(0, strap_center_y)
            .slot2D(p.strap_slot_l, p.strap_slot_w)
            .cutThruAll()
        )
    else:
        pad_d = p.strap_hole_d + 2 * p.min_wall
        pad = (
            cq.Workplane("XY")
            .center(0, strap_center_y)
            .circle(pad_d / 2)
            .extrude(p.body_t / 2, both=True)
        )
        body = body.union(pad)
        body = (
            body.faces(">Z")
            .workplane()
            .center(0, strap_center_y)
            .circle(p.strap_hole_d / 2)
            .cutThruAll()
        )

    body = body.edges(">Z").fillet(0.5)

    # Front QR pocket
    pocket_w = p.qr_w + p.fit_clearance
    pocket_h = p.qr_h + p.fit_clearance
    body = (
        body.faces(">Z")
        .workplane()
        .rect(pocket_w, pocket_h)
        .cutBlind(-p.qr_pocket_depth)
    )

    # Back NFC recess
    body = (
        body.faces("<Z")
        .workplane()
        .circle((p.nfc_d + p.fit_clearance) / 2)
        .cutBlind(-p.nfc_depth)
    )

    return body, width, height


def build_islands(p: Params) -> cq.Workplane:
    outer_w = p.qr_w + 2 * p.qr_border
    outer_h = p.qr_h + 2 * p.qr_border
    pocket_w = p.qr_w + p.fit_clearance
    pocket_h = p.qr_h + p.fit_clearance
    ring = (
        cq.Workplane("XY")
        .rect(outer_w, outer_h)
        .rect(pocket_w, pocket_h)
        .extrude(p.island_h)
        .translate((0, 0, p.body_t / 2))
    )
    strap_center_y = outer_h / 2 - p.min_wall - ((p.strap_slot_l or p.strap_hole_d) / 2)
    if p.strap_slot_w and p.strap_slot_l:
        ring = (
            ring.faces(">Z")
            .workplane()
            .center(0, strap_center_y)
            .slot2D(p.strap_slot_l, p.strap_slot_w)
            .cutThruAll()
        )
    else:
        ring = (
            ring.faces(">Z")
            .workplane()
            .center(0, strap_center_y)
            .circle(p.strap_hole_d / 2)
            .cutThruAll()
        )
    ring = ring.edges("|Z").fillet(0.5)
    return ring


def export_stl(model: cq.Workplane, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(model, str(path))
    mesh = trimesh.load_mesh(path)
    if not mesh.is_watertight:
        raise ValueError(f"Mesh {path} is not watertight")


def color_switch_layer_index(island_h: float, layer_height: float) -> int:
    layer = max(1, round(island_h / layer_height))
    return layer


def hash_mesh(path: Path) -> str:
    mesh = trimesh.load_mesh(path)
    data = mesh.vertices.tobytes() + mesh.faces.tobytes()
    return hashlib.sha256(data).hexdigest()
def save_preview(path: Path, model: cq.Workplane, flip: bool = False):
    tmp_svg = path.with_suffix(".svg")
    m = model.rotate((0, 0, 0), (1, 0, 0), 180) if flip else model
    cq.exporters.export(m, str(tmp_svg))
    cairosvg.svg2png(url=str(tmp_svg), write_to=str(path))
    tmp_svg.unlink()


def build_and_export(p: Params, out: Path, variant: str):
    body, width, height = build_body(p)
    base = body
    islands = build_islands(p)
    thickness = p.body_t + p.island_h

    if variant in ("base", "all"):
        export_stl(base.union(islands), out / "tag_base.stl")
        save_preview(out / "preview_front.png", base.union(islands))
        save_preview(out / "preview_back.png", base.union(islands), flip=True)

    if variant in ("flat", "all"):
        export_stl(base, out / "tag_alt_flat_front.stl")

    if variant in ("islands", "all"):
        export_stl(base, out / "tag_alt_qr_islands_base.stl")
        export_stl(islands, out / "tag_alt_qr_islands_features.stl")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate luggage tag STLs")
    parser.add_argument("--out", type=Path, default=Path("3d-models/outputs"))
    parser.add_argument("--variant", choices=["all", "base", "flat", "islands"], default="all")
    parser.add_argument("--params", type=Path)
    parser.add_argument("--qr_w", type=float)
    parser.add_argument("--qr_h", type=float)
    parser.add_argument("--qr_border", type=float)
    parser.add_argument("--body_t", type=float)
    parser.add_argument("--min_wall", type=float)
    parser.add_argument("--corner_r", type=float)
    parser.add_argument("--nfc_d", type=float)
    parser.add_argument("--nfc_depth", type=float)
    parser.add_argument("--fit_clearance", type=float)
    parser.add_argument("--strap_hole_d", type=float)
    parser.add_argument("--slot", type=str, help="WIDTHxLENGTH for strap slot")
    parser.add_argument("--qr_pocket_depth", type=float)
    parser.add_argument("--island_h", type=float)
    return parser.parse_args()


def apply_overrides(p: Params, args: argparse.Namespace) -> None:
    for field in asdict(p).keys():
        val = getattr(args, field, None)
        if val is not None:
            setattr(p, field, val)
    if args.slot:
        w, l = args.slot.lower().split("x")
        p.strap_slot_w = float(w)
        p.strap_slot_l = float(l)
        p.strap_hole_d = 0.0


def main():
    args = parse_args()
    params = load_params(getattr(args, "params", None))
    apply_overrides(params, args)
    build_and_export(params, args.out, args.variant)


if __name__ == "__main__":
    main()



