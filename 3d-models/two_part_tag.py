#!/usr/bin/env python3
"""Two-part, two-colour luggage tag for a Bambu Lab P1S with AMS.

The tag is two halves, each printed face-down so the visible face is the smooth
build-plate side. Each half is a light base with a flush dark inlay (QR, text, strap-hole
ring) in its first layers. The halves are glued back-to-back with an NFC sticker sealed
in a pocket between them; three pins keep them aligned.

The face artwork comes from ``layout.py`` (the HTML/CSS plan in millimetres). Outputs, in
print orientation, each pair co-registered:

    front_base.stl + front_inlay.stl   -> one object, two parts
    back_base.stl  + back_inlay.stl    -> one object, two parts

``assembled/`` holds the same parts in assembled position for previewing (viewer.html).
Contact details come from CLI flags or the git-ignored ``contact.local.yaml``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Optional, Sequence

import cadquery as cq
import trimesh
import yaml
from shapely import affinity
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layout as L  # noqa: E402
from glyphs import polygons  # noqa: E402

HERE = Path(__file__).resolve().parent
DEFAULT_CONTACT = HERE / "contact.local.yaml"
OVERSHOOT = 0.05  # inlay cutters poke out of the face: coplanar booleans are unreliable in OCC


@dataclass
class Build:
    half_t: float = 1.6  # each half; the tag is 2 * half_t
    inlay_depth: float = 0.6  # 3 layers at 0.20 mm
    face_chamfer: float = 0.4
    nfc_d: float = 20.0
    nfc_clearance: float = 0.3
    nfc_pocket_depth: float = 0.6
    pin_d: float = 2.0
    pin_h: float = 0.6
    pin_clearance: float = 0.3  # on diameter
    pin_inset: float = 6.0  # pin centre from the side and top/bottom edges
    layer_h: float = 0.2


@dataclass
class Contact:
    name: str = "YOUR NAME"
    phone: str = "+000 00 000 0000"
    email: str = "YOU@EXAMPLE.COM"
    qr_url: str = "https://example.github.io/luggage-recovery"
    font_path: Optional[str] = None


# ---------------------------------------------------------------- 2D face -> 3D


def _to_model(geom, lay: L.TagLayout, *, back: bool):
    """Face mm (top-left origin, y down) -> model XY (centred, y up). The back face is
    viewed after flipping the tag left-right, so its x is mirrored."""
    W, H = lay.width, lay.height
    if back:
        return affinity.affine_transform(geom, [-1, 0, 0, -1, W / 2, H / 2])
    return affinity.affine_transform(geom, [1, 0, 0, -1, -W / 2, H / 2])


def _wire(coords) -> cq.Wire:
    return cq.Wire.makePolygon([cq.Vector(x, y, 0) for x, y in list(coords)[:-1]], close=True)


def _extrude(geom, z0: float, h: float) -> cq.Workplane:
    solids = []
    for p in polygons(geom):
        p = p.simplify(0.003)
        if p.is_empty or not isinstance(p, Polygon):
            continue
        p = orient(p, 1.0)
        face = cq.Face.makeFromWires(_wire(p.exterior.coords), [_wire(r.coords) for r in p.interiors])
        if not face.isValid():
            raise ValueError(f"Inlay polygon near {p.representative_point().coords[0]} is not a valid face")
        solids.append(cq.Solid.extrudeLinear(face, cq.Vector(0, 0, h)).translate(cq.Vector(0, 0, z0)))
    return cq.Workplane("XY").add(cq.Compound.makeCompound(solids))


def _outline(lay: L.TagLayout, z0: float, h: float) -> cq.Workplane:
    return cq.Workplane("XY").workplane(offset=z0).rect(lay.width, lay.height).extrude(h).edges("|Z").fillet(lay.corner_r)


def _cyl(x: float, y: float, d: float, z0: float, h: float) -> cq.Workplane:
    return cq.Workplane("XY").workplane(offset=z0).center(x, y).circle(d / 2).extrude(h)


def build(contact: Contact, b: Build = Build(), lay: Optional[L.TagLayout] = None) -> dict:
    lay = lay or L.default_layout(contact.name, contact.phone, contact.email, contact.qr_url)
    problems = L.check_straight_features(lay)
    if problems:
        raise ValueError("Not a multiple of the 0.4 mm nozzle: " + ", ".join(problems))
    for v, label in ((b.inlay_depth, "inlay_depth"), (b.half_t, "half_t"), (b.nfc_pocket_depth, "nfc_pocket_depth")):
        if abs(v / b.layer_h - round(v / b.layer_h)) > 1e-6:
            raise ValueError(f"{label} {v} mm is not a whole number of {b.layer_h} mm layers")
    t = b.half_t
    if b.inlay_depth + b.nfc_pocket_depth > t - 0.4:
        raise ValueError("inlay_depth + nfc_pocket_depth must leave >= 0.4 mm in the back half")
    if b.pin_h + 0.1 + b.inlay_depth > t - 0.2:
        raise ValueError("Pin holes would reach the back inlay; reduce pin_h or increase half_t")

    faces = {
        "front": L.build_face(lay, lay.front, contact.qr_url, contact.font_path),
        "back": L.build_face(lay, lay.back, contact.qr_url, contact.font_path),
    }
    for name, fg in faces.items():
        thin = L.thin_regions(fg.inlay)
        if thin:
            raise ValueError(f"{name} inlay has strokes under 0.4 mm at {thin[:3]}")

    W, H = lay.width, lay.height
    hx, hy = lay.front.ring_center[0] - W / 2, H / 2 - lay.front.ring_center[1]
    i = b.pin_inset
    pins = [(-W / 2 + i, -H / 2 + i), (W / 2 - i, -H / 2 + i), (W / 2 - i, H / 2 - i)]
    # NFC behind the QR centre, where people tap
    qn = faces["front"].qr.symbol_size(border=0)[0] * lay.qr_module
    qx, qy = lay.front.qr_origin
    nfc = (qx + qn / 2 - W / 2, H / 2 - (qy + qn / 2))

    # Front half: z in [0, t], visible face at z = t
    front = _outline(lay, 0, t).faces(">Z").chamfer(b.face_chamfer)
    front = front.cut(_cyl(hx, hy, lay.hole_d, -1, t + 2))
    for px, py in pins:
        front = front.union(_cyl(px, py, b.pin_d, -b.pin_h, b.pin_h + 0.01))
    front_tool = _extrude(_to_model(faces["front"].inlay, lay, back=False), t - b.inlay_depth, b.inlay_depth + OVERSHOOT)

    # Back half: z in [-t, 0], visible face at z = -t
    back = _outline(lay, -t, t).faces("<Z").chamfer(b.face_chamfer)
    back = back.cut(_cyl(hx, hy, lay.hole_d, -t - 1, t + 2))
    for px, py in pins:
        back = back.cut(_cyl(px, py, b.pin_d + b.pin_clearance, -(b.pin_h + 0.1), b.pin_h + 0.2))
    back = back.cut(_cyl(*nfc, b.nfc_d + b.nfc_clearance, -b.nfc_pocket_depth, b.nfc_pocket_depth + 0.1))
    back_tool = _extrude(_to_model(faces["back"].inlay, lay, back=True), -t - OVERSHOOT, b.inlay_depth + OVERSHOOT)

    q = faces["front"].qr
    return {
        "parts": {
            "front_base": front.cut(front_tool),
            "front_inlay": front.intersect(front_tool),
            "back_base": back.cut(back_tool),
            "back_inlay": back.intersect(back_tool),
        },
        "layout": lay,
        "faces": faces,
        "positions": {"hole": (hx, hy), "pins": pins, "nfc": nfc},
        "qr": {"version": q.version, "error": q.error, "modules": q.symbol_size(border=0)[0], "module_mm": lay.qr_module},
    }


def to_print(name: str, part: cq.Workplane, b: Build) -> cq.Workplane:
    """Face-down: the visible face on the plate at z = 0 (the front half flips over Y)."""
    if name.startswith("front"):
        part = part.rotate((0, 0, 0), (0, 1, 0), 180)
    return part.translate((0, 0, b.half_t))


# ---------------------------------------------------------------- export


def export_stl(model: cq.Workplane, path: Path) -> None:
    """Watertight-checked binary STL with a fixed header and face order (byte-stable output)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(model, str(path), tolerance=0.005, angularTolerance=0.1)
    mesh = trimesh.load_mesh(path)
    if not mesh.is_watertight:
        raise ValueError(f"{path.name} is not watertight")
    keys = (mesh.vertices[mesh.faces] * 1e5).round().astype(int)
    order = sorted(range(len(mesh.faces)), key=lambda k: sorted(keys[k].tolist()))
    mesh = trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.faces[order], process=False)
    data = trimesh.exchange.stl.export_stl(mesh)
    path.write_bytes(b"two-part luggage tag".ljust(80, b"\0") + data[80:])


PRINTING = """# Printing the two-part tag (Bambu Lab P1S + AMS)

Filaments: AMS slot 1 = light (base), slot 2 = dark (inlay). The same two for both halves.

For each half (front, then back):
1. In Bambu Studio, drag `HALF_base.stl` and `HALF_inlay.stl` in together.
2. "Load these files as a single object with multiple parts?" -> **Yes**.
3. Objects list: `HALF_base` -> filament 1, `HALF_inlay` -> filament 2.
4. Leave it face-down as loaded: the visible face is on the plate.
5. Layer height {layer} mm, first layer {layer} mm. The inlay is the first {inlay_layers} layers,
   so colour swaps only happen there; the other layers of the {half_layers} are base colour.
6. Smooth PEI plate: glossy face. Textured PEI: matte, textured face.
7. Process > Quality: set **Elephant foot compensation = 0** and **Initial layer line width = 0.42**.
   The visible face is the first layer; the default 0.15 mm compensation shrinks every inlay
   stroke and the 0.5 mm first-layer width skips the thinnest ones (about 10% of the artwork).

Assembly:
1. Write the NFC sticker first (e.g. NFC Tools, URL record: {url}).
2. Stick the Ø{nfc_d:g} mm sticker in the pocket on the inside of the back half.
3. Thin CA or epoxy on the inner faces (not in the pocket), engage the three pins, clamp 10 min.

QR: version {qr_version}, {module} mm modules. Scan-test the front before gluing.
"""


def export(contact: Contact, out: Path, b: Build = Build()) -> dict:
    res = build(contact, b)
    for name, part in res["parts"].items():
        export_stl(to_print(name, part, b), out / f"{name}.stl")
        export_stl(part, out / "assembled" / f"{name}.stl")
    faces = res["faces"]
    manifest = {
        "build": asdict(b),
        "size_mm": [res["layout"].width, res["layout"].height, round(2 * b.half_t, 3)],
        "qr": res["qr"],
        "positions": res["positions"],
        # Sizes only: the contact text itself stays out of generated metadata
        "text_sizes_mm": {k: [t["size_mm"] for t in f.text] for k, f in faces.items()},
        "thickened_mm2": {k: f.thickened_mm2 for k, f in faces.items()},
        "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob("*.stl"))},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (out / "PRINTING.md").write_text(PRINTING.format(
        layer=b.layer_h, inlay_layers=round(b.inlay_depth / b.layer_h), half_layers=round(b.half_t / b.layer_h),
        url=contact.qr_url, nfc_d=b.nfc_d, qr_version=res["qr"]["version"], module=res["qr"]["module_mm"],
    ).replace("HALF", "{front|back}"))
    res["manifest"] = manifest
    return res


def load_contact(path: Optional[Path], overrides: Dict[str, Optional[str]]) -> Contact:
    c = Contact()
    path = path or DEFAULT_CONTACT
    if path.exists():
        for k, v in (yaml.safe_load(path.read_text()) or {}).items():
            if hasattr(c, k):
                setattr(c, k, str(v))
    for k, v in overrides.items():
        if v is not None:
            setattr(c, k, v)
    return c


def main(argv: Optional[Sequence[str]] = None) -> None:
    ap = argparse.ArgumentParser(description="Generate the two-part, two-colour luggage tag STLs")
    ap.add_argument("--out", type=Path, default=HERE / "outputs" / "two-part")
    ap.add_argument("--contact", type=Path, help=f"YAML with name/phone/email/qr_url/font_path (default: {DEFAULT_CONTACT.name})")
    fields = ("name", "phone", "email", "qr_url", "font_path")
    for f in fields:
        ap.add_argument(f"--{f}")
    args = ap.parse_args(argv)
    contact = load_contact(args.contact, {f: getattr(args, f) for f in fields})
    res = export(contact, args.out)
    q = res["qr"]
    print(f"QR v{q['version']}-{q['error']}, {q['modules']} modules x {q['module_mm']} mm")
    for face, fg in res["faces"].items():
        for t in fg.text:
            print(f"{face:5s} {t['size_mm']:4.1f} mm  {t['text']}")
        if fg.thickened_mm2:
            print(f"{face:5s} thickened sub-0.4 mm strokes by {fg.thickened_mm2} mm^2")
    print(f"Wrote {args.out} (see PRINTING.md)")


if __name__ == "__main__":
    main()
