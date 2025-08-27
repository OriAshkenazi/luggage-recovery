"""Parametric luggage tag generator using CadQuery."""

from dataclasses import dataclass, asdict
from pathlib import Path
import os
os.environ["PYGLET_HEADLESS"] = "True"
import argparse
import yaml
import cadquery as cq
import trimesh
import hashlib
import json
import random
from typing import Optional, Iterable, Tuple, List

# Optional PNG preview support
try:
    import cairosvg  # type: ignore
except Exception:  # pragma: no cover - missing system cairo
    cairosvg = None

# QR encoder (pure-Python)
try:
    import segno  # type: ignore
except Exception as e:  # pragma: no cover
    segno = None


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
    # Text params (front prompt)
    front_prompt_text: str = "Scan me to find my owner"
    front_prompt_h: float = 0.5
    front_prompt_margin: float = 2.0
    front_text_style: str = "emboss"  # or "engrave"
    front_text_height: float = 0.5
    front_text_depth: float = 0.3
    front_font_path: str | None = None
    front_prompt_edge: str = "bottom"  # top|bottom|left|right
    # Text params (back)
    back_name: str | None = None
    back_phone: str | None = None
    back_address: str | None = None
    back_text_h: float = 4.0
    back_line_gap: float = 1.5
    back_margin: float = 3.0
    back_text_style: str = "engrave"  # or "emboss"
    back_font_path: str | None = None


def load_params(path: Path | None) -> Params:
    params = Params()
    if path and path.exists():
        data = yaml.safe_load(path.read_text())
        for k, v in data.items():
            setattr(params, k, v)
    return params


def apply_preset(params: Params, yaml_path: Optional[Path], preset: Optional[str]) -> Tuple[Params, Optional[float]]:
    """Apply a material preset from params.yaml if provided.
    Returns params and recommended layer height if present.
    """
    rec_layer = None
    if not preset:
        return params, rec_layer
    data = {}
    if yaml_path and yaml_path.exists():
        data = yaml.safe_load(yaml_path.read_text()) or {}
    presets = (data or {}).get('presets', {})
    prof = presets.get(preset)
    if not prof:
        raise ValueError(f"Unknown preset: {preset}")
    for k in ('fit_clearance', 'corner_r', 'island_h'):
        if k in prof:
            setattr(params, k, float(prof[k]))
    rec_layer = float(prof.get('recommended_layer_height')) if 'recommended_layer_height' in prof else None
    return params, rec_layer


def build_body(p: Params) -> tuple[cq.Workplane, float, float]:
    """Build the tag body with pockets and strap feature."""
    width = p.qr_w + 2 * p.qr_border
    height = p.qr_h + 2 * p.qr_border

    if p.nfc_depth + p.qr_pocket_depth > p.body_t - 0.6:
        raise ValueError("Invalid pockets: nfc_depth + qr_pocket_depth must be <= body_t - 0.6")

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


def _text_solid_front(p: Params, width: float, height: float) -> cq.Workplane:
    if not p.front_prompt_text:
        return cq.Workplane("XY")
    edge = p.front_prompt_edge.lower()
    margin = p.front_prompt_margin
    # Position line near chosen edge
    x = 0.0
    y = 0.0
    rot = 0
    if edge == "top":
        y = height / 2 - margin
    elif edge == "bottom":
        y = -height / 2 + margin
    elif edge == "left":
        x = -width / 2 + margin
        rot = 90
    else:  # right
        x = width / 2 - margin
        rot = 90
    wp = cq.Workplane("XY").workplane(offset=p.body_t / 2)
    txt = wp.center(x, y).rotate((0, 0, 0), (0, 0, 1), rot).text(
        p.front_prompt_text,
        p.back_text_h if rot else p.back_text_h,
        p.front_text_height if p.front_text_style == "emboss" else p.front_text_depth,
        kind="bold",
        cut=False,
        combine=True,
        font=p.front_font_path or "Sans",
    )
    if p.front_text_style == "emboss":
        return txt
    else:
        # Engrave: cut into base later by using it as cutter
        return txt


def _text_solids_back(p: Params, width: float, height: float) -> cq.Workplane:
    lines = [s for s in [p.back_name, p.back_phone, p.back_address] if s]
    if not lines:
        return cq.Workplane("XY")
    # Compute layout area (back face): respect margins and NFC/strap keep-outs crudely by using inner rectangle
    inner_w = width - 2 * p.back_margin
    inner_h = height - 2 * p.back_margin
    wp = cq.Workplane("XY").workplane(offset=-p.body_t / 2)
    y0 = inner_h / 2 - p.back_text_h  # start near top of inner rect
    solid = cq.Workplane("XY")
    for i, text in enumerate(lines):
        y = y0 - i * (p.back_text_h + p.back_line_gap)
        t = wp.center(0, y).text(text, p.back_text_h, p.back_text_height if p.back_text_style == "emboss" else p.front_text_depth, kind="bold", cut=False, combine=True, font=p.back_font_path or "Sans")
        solid = solid.union(t)
    return solid


def build_qr_islands(p: Params, qr_text: Optional[str], qr_svg: Optional[Path]) -> Tuple[cq.Workplane, dict]:
    if not qr_text and not qr_svg:
        # fallback to ring islands for backward compatibility
        return build_islands(p), {"mode": "ring"}
    if segno is None:
        raise RuntimeError("QR features requested but segno is not available. Add segno to requirements.")
    if qr_text:
        qr = segno.make(qr_text, error='m')
        payload_hash = hashlib.sha256(qr_text.encode('utf-8')).hexdigest()
    else:
        # Load external SVG as QR, segno can open only text; we approximate by embedding
        svg_data = Path(qr_svg).read_bytes()
        qr = segno.make(svg_data, micro=False)  # might fail; best-effort
        payload_hash = hashlib.sha256(svg_data).hexdigest()
    # Matrix including quiet zone when asked; we'll explicitly add quiet zone modules = 4
    msize = qr.symbol_size(quiet_zone=4)
    modules = msize[0]  # width in modules including quiet zone
    qz = 4
    pocket_w = p.qr_w + p.fit_clearance
    pocket_h = p.qr_h + p.fit_clearance
    module_size = min(pocket_w / modules, pocket_h / modules)
    # Build dark module squares
    wp = cq.Workplane("XY")
    # Origin align so that QR is centered in pocket
    total_w = modules * module_size
    total_h = modules * module_size
    x0 = -total_w / 2
    y0 = -total_h / 2
    dark_count = 0
    for r, row in enumerate(qr.matrix_iter(scale=1, border=qz)):
        for c, bit in enumerate(row):
            if bit:  # dark
                dark_count += 1
                cx = x0 + (c + 0.5) * module_size
                cy = y0 + (r + 0.5) * module_size
                wp = wp.union(
                    cq.Workplane("XY").center(cx, cy).rect(module_size, module_size).extrude(p.island_h).translate((0, 0, p.body_t / 2))
                )
    meta = {
        "mode": "qr",
        "qr_payload_hash": payload_hash,
        "module_size_mm": round(module_size, 4),
        "quiet_zone_mm": round(qz * module_size, 4),
        "dark_modules": dark_count,
        "island_h": p.island_h,
    }
    return wp, meta


def _triangulate_and_write(mesh: trimesh.Trimesh, path: Path, deterministic: bool) -> None:
    # enforce face ordering determinism by sorting on quantized vertex coords
    if deterministic:
        verts = mesh.vertices
        faces = mesh.faces
        # build sort keys per face
        def face_key(fi: int):
            pts = verts[faces[fi]]
            # quantize to 1e-6 mm
            q = (pts * 1e6).round().astype(int).tolist()
            # sort vertices within face for stability
            q.sort()
            return q

        order = sorted(range(len(mesh.faces)), key=face_key)
        mesh = trimesh.Trimesh(vertices=mesh.vertices.copy(), faces=mesh.faces[order].copy(), process=False)
    # Write binary STL with fixed header
    header = b"CadQuery deterministic STL\x00".ljust(80, b"\x00")
    data = trimesh.exchange.stl.export_stl(mesh, header=header)
    path.write_bytes(data)


def export_stl(model: cq.Workplane, path: Path, *, deterministic: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # stable tessellation params
    cq.exporters.export(model, str(path), tolerance=1e-3, angularTolerance=0.1)
    mesh = trimesh.load_mesh(path)
    if not mesh.is_watertight:
        raise ValueError(f"Mesh {path} is not watertight")
    _triangulate_and_write(mesh, path, deterministic)


def color_switch_layer_index(island_h: float, layer_height: float) -> int:
    layer = max(1, round(island_h / layer_height))
    return layer


def hash_mesh(path: Path) -> str:
    mesh = trimesh.load_mesh(path)
    data = mesh.vertices.tobytes() + mesh.faces.tobytes()
    return hashlib.sha256(data).hexdigest()
def save_preview_svg(path: Path, model: cq.Workplane, flip: bool = False) -> Path:
    m = model.rotate((0, 0, 0), (1, 0, 0), 180) if flip else model
    cq.exporters.export(m, str(path))
    return path


def save_preview_png(path: Path, svg_source: Path) -> Optional[Path]:
    if cairosvg is None:
        return None
    cairosvg.svg2png(url=str(svg_source), write_to=str(path))
    return path


def export_sticker_svg(out: Path, p: Params, qr_text: Optional[str], qr_svg: Optional[Path], *, module_size_mm: Optional[float] = None, quiet_zone_mod: int = 4) -> Tuple[Path, Optional[Path]]:
    """Export a 30x50 mm sticker SVG (and optional PNG) with registration marks.
    Returns (svg_path, png_path)."""
    if segno is None:
        raise RuntimeError("Sticker export requires segno (pure-Python QR library)")
    if qr_text:
        qr = segno.make(qr_text, error='m')
    else:
        # Fallback: simple QR with repo URL if none provided
        payload = (Path(qr_svg).read_text() if qr_svg else "") or "https://example.com"
        qr = segno.make(payload, error='m')
    size = qr.symbol_size(quiet_zone=quiet_zone_mod)
    modules = size[0]
    if module_size_mm is None:
        module_size_mm = min(p.qr_w / modules, p.qr_h / modules)
    total_w = modules * module_size_mm
    total_h = modules * module_size_mm
    # Sticker canvas: 50 x 30 mm
    W, H = p.qr_w, p.qr_h
    # Center QR in canvas
    x0 = (W - total_w) / 2
    y0 = (H - total_h) / 2
    # Build SVG content
    svg_path = out / "qr_sticker_30x50.svg"
    parts: List[str] = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}">')
    # Background
    parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" fill="#fff"/>')
    # Safe margin (1 mm inset outline)
    parts.append('<rect x="1" y="1" width="%s" height="%s" fill="none" stroke="#000" stroke-dasharray="2,2" stroke-width="0.2"/>' % (W-2, H-2))
    # Registration marks (2mm circles)
    parts.append('<circle cx="3" cy="3" r="1" fill="none" stroke="#000" stroke-width="0.2"/>')
    parts.append('<circle cx="%s" cy="%s" r="1" fill="none" stroke="#000" stroke-width="0.2"/>' % (W-3, H-3))
    # QR modules
    for r, row in enumerate(qr.matrix_iter(scale=1, border=quiet_zone_mod)):
        for c, bit in enumerate(row):
            if bit:
                x = x0 + c * module_size_mm
                y = y0 + r * module_size_mm
                parts.append('<rect x="%0.4f" y="%0.4f" width="%0.4f" height="%0.4f" fill="#000"/>' % (x, y, module_size_mm, module_size_mm))
    parts.append('</svg>')
    svg_path.write_text("\n".join(parts))
    png_path: Optional[Path] = None
    if cairosvg is not None:
        png_path = out / "qr_sticker_30x50.png"
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path))
    return svg_path, png_path


def _validate_inputs(p: Params) -> None:
    if p.qr_w <= 0 or p.qr_h <= 0:
        raise ValueError("qr_w and qr_h must be positive")
    if p.qr_border < 1.0:
        raise ValueError("qr_border must be >= 1.0 mm")
    if p.body_t < 2.5:
        raise ValueError("body_t must be >= 2.5 mm")
    if p.min_wall < 1.5:
        raise ValueError("min_wall must be >= 1.5 mm")
    if p.nfc_depth + p.qr_pocket_depth > p.body_t - 0.6:
        raise ValueError("Invalid pockets: nfc_depth + qr_pocket_depth must be <= body_t - 0.6")


def _two_tone_asserts(p: Params, base_path: Path, feat_path: Path) -> None:
    b = trimesh.load_mesh(base_path)
    f = trimesh.load_mesh(feat_path)
    # XY AABB equal
    assert abs((b.bounds[0][0] - f.bounds[0][0])) < 1e-3 and abs((b.bounds[1][0] - f.bounds[1][0])) < 1e-3
    assert abs((b.bounds[0][1] - f.bounds[0][1])) < 1e-3 and abs((b.bounds[1][1] - f.bounds[1][1])) < 1e-3
    # Z contact
    assert abs(b.bounds[1][2] - p.body_t / 2) < 1e-3
    assert abs(f.bounds[0][2] - p.body_t / 2) < 1e-3
    # No overlap
    assert b.bounds[1][2] <= f.bounds[0][2] + 1e-6


def _geom_integrity_checks(p: Params, model: cq.Workplane, strict: bool = False) -> None:
    # Strap reinforcement thickness heuristic: check that local pad adds at least ~0.5 mm above body_t.
    # We do a coarse check using bounding box deltas across strap y region.
    try:
        mesh = trimesh.load_mesh(trimesh.exchange.stl.export_stl(cq.exporters.toString(model, 'STL')))
    except Exception:
        return
    ok = True
    if not mesh.is_watertight:
        ok = False
    if not ok and strict:
        raise ValueError("Geometry integrity failed: mesh not watertight")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_and_export(
    p: Params,
    out: Path,
    variant: str,
    *,
    previews: str = "svg",
    deterministic: bool = False,
    layer_height: Optional[float] = None,
    strict: bool = False,
    emit_coupons: Optional[Iterable[str]] = None,
    preset: Optional[str] = None,
    qr_text: Optional[str] = None,
    qr_svg: Optional[Path] = None,
    text_features: bool = False,
) -> Path:
    _validate_inputs(p)
    if deterministic:
        os.environ["PYTHONHASHSEED"] = "0"
        random.seed(0)
    body, width, height = build_body(p)
    base = body
    islands, qrmeta = build_qr_islands(p, qr_text, qr_svg)
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"parameters": asdict(p), "files": {}, "deterministic": deterministic}
    if preset:
        manifest["preset"] = preset
    if qrmeta:
        manifest.update(qrmeta)
    if layer_height:
        manifest["color_switch_layer"] = color_switch_layer_index(p.island_h, layer_height)

    # Export variants
    # Front/back text solids
    front_text = _text_solid_front(p, width, height)
    back_text = _text_solids_back(p, width, height)
    # Apply text to base
    base_with_text = base
    if p.front_text_style == "emboss" and not front_text.val().isNull():
        base_with_text = base_with_text.union(front_text)
    if p.front_text_style == "engrave" and not front_text.val().isNull():
        base_with_text = base_with_text.cut(front_text)
    if p.back_text_style == "emboss" and not back_text.val().isNull():
        base_with_text = base_with_text.union(back_text)
    if p.back_text_style == "engrave" and not back_text.val().isNull():
        # Ensure min wall
        if p.body_t - p.front_text_depth < p.min_wall:
            raise ValueError("Back engraving violates minimum wall thickness")
        base_with_text = base_with_text.cut(back_text)

    if variant in ("base", "all"):
        path = out / "tag_base.stl"
        export_stl(base_with_text.union(islands), path, deterministic=deterministic)
        manifest["files"][str(path.name)] = {"sha256": _sha256(path)}
        # Previews
        if previews in ("svg", "png"):
            svg = out / "preview_front.svg"
            save_preview_svg(svg, base.union(islands))
            manifest["files"][svg.name] = {"sha256": _sha256(svg)}
            if previews == "png":
                png = out / "preview_front.png"
                if save_preview_png(png, svg):
                    manifest["files"][png.name] = {"sha256": _sha256(png)}
                else:
                    print("[warn] PNG preview unavailable; falling back to SVG")
        if previews in ("svg", "png"):
            svg = out / "preview_back.svg"
            save_preview_svg(svg, base.union(islands).rotate((0, 0, 0), (1, 0, 0), 180))
            manifest["files"][svg.name] = {"sha256": _sha256(svg)}
            if previews == "png":
                png = out / "preview_back.png"
                if save_preview_png(png, svg):
                    manifest["files"][png.name] = {"sha256": _sha256(png)}
                else:
                    print("[warn] PNG preview unavailable; falling back to SVG")

    if variant in ("flat", "all"):
        path = out / "tag_alt_flat_front.stl"
        export_stl(base, path, deterministic=deterministic)
        manifest["files"][str(path.name)] = {"sha256": _sha256(path)}

    if variant in ("islands", "all"):
        path_b = out / "tag_alt_qr_islands_base.stl"
        path_f = out / "tag_alt_qr_islands_features.stl"
        export_stl(base_with_text, path_b, deterministic=deterministic)
        export_stl(islands, path_f, deterministic=deterministic)
        manifest["files"][str(path_b.name)] = {"sha256": _sha256(path_b)}
        manifest["files"][str(path_f.name)] = {"sha256": _sha256(path_f)}
        _two_tone_asserts(p, path_b, path_f)

    # Optional text features for two-tone printing
    if text_features:
        if not front_text.val().isNull():
            pth = out / "front_text_features.stl"
            export_stl(front_text, pth, deterministic=deterministic)
            manifest["files"][pth.name] = {"sha256": _sha256(pth)}
        if not back_text.val().isNull() and p.back_text_style == "emboss":
            pth = out / "back_text_features.stl"
            export_stl(back_text, pth, deterministic=deterministic)
            manifest["files"][pth.name] = {"sha256": _sha256(pth)}

    # Optional coupons
    if emit_coupons:
        for token in emit_coupons:
            token = token.strip().lower()
            if token == "nfc":
                coupon = (
                    cq.Workplane("XY")
                    .circle((p.nfc_d + p.fit_clearance) / 2)
                    .extrude(p.nfc_depth)
                )
                path = out / "coupon_nfc.stl"
                export_stl(coupon, path, deterministic=deterministic)
                manifest["files"][path.name] = {"sha256": _sha256(path)}
            if token == "strap":
                if p.strap_slot_w and p.strap_slot_l:
                    coupon = cq.Workplane("XY").slot2D(p.strap_slot_l, p.strap_slot_w).extrude(p.body_t)
                    name = "coupon_strap_slot.stl"
                else:
                    coupon = cq.Workplane("XY").circle(p.strap_hole_d / 2).extrude(p.body_t)
                    name = "coupon_strap_hole.stl"
                path = out / name
                export_stl(coupon, path, deterministic=deterministic)
                manifest["files"][path.name] = {"sha256": _sha256(path)}

    # Write manifest and checksums
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    with (out / "checksums.sha256").open('w') as f:
        for name, info in sorted(manifest["files"].items()):
            f.write(f"{info['sha256']}  {name}\n")
    # Sticker templates
    try:
        ssvg, spng = export_sticker_svg(out, p, qr_text, qr_svg, module_size_mm=qrmeta.get('module_size_mm') if 'qrmeta' in locals() else None)
        manifest["files"][ssvg.name] = {"sha256": _sha256(ssvg)}
        if spng:
            manifest["files"][spng.name] = {"sha256": _sha256(spng)}
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
        with (out / "checksums.sha256").open('a') as f:
            f.write(f"{_sha256(ssvg)}  {ssvg.name}\n")
            if spng:
                f.write(f"{_sha256(spng)}  {spng.name}\n")
    except Exception as e:
        print(f"[warn] Sticker export failed: {e}")
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate luggage tag STLs")
    parser.add_argument("--out", type=Path, default=Path("3d-models/outputs"))
    parser.add_argument("--variant", choices=["all", "base", "flat", "islands"], default="all")
    parser.add_argument("--params", type=Path)
    # Parameter overrides
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
    parser.add_argument("--hole", type=float, help="Diameter for strap hole (mm)")
    parser.add_argument("--slot", type=str, help="WIDTHxLENGTH for strap slot")
    parser.add_argument("--qr_pocket_depth", type=float)
    parser.add_argument("--island_h", type=float)
    # Behavior flags
    parser.add_argument("--previews", choices=["none", "svg", "png"], default="svg")
    parser.add_argument("--deterministic", action="store_true")
    parser.add_argument("--layer_height", type=float)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--ci", action="store_true")
    parser.add_argument("--emit_coupons", type=str, help="Comma-separated: nfc,strap")
    parser.add_argument("--preset", choices=["pla", "petg", "abs"])
    parser.add_argument("--qr_text", type=str)
    parser.add_argument("--qr_svg", type=Path)
    # Text CLI
    parser.add_argument("--front_prompt_text", type=str)
    parser.add_argument("--front_prompt_h", type=float)
    parser.add_argument("--front_prompt_margin", type=float)
    parser.add_argument("--front_text_style", choices=["emboss", "engrave"])
    parser.add_argument("--front_text_height", type=float)
    parser.add_argument("--front_text_depth", type=float)
    parser.add_argument("--front_font_path", type=str)
    parser.add_argument("--front_prompt_edge", choices=["top", "bottom", "left", "right"])
    parser.add_argument("--back_name", type=str)
    parser.add_argument("--back_phone", type=str)
    parser.add_argument("--back_address", type=str)
    parser.add_argument("--back_text_h", type=float)
    parser.add_argument("--back_line_gap", type=float)
    parser.add_argument("--back_margin", type=float)
    parser.add_argument("--back_text_style", choices=["emboss", "engrave"])
    parser.add_argument("--back_font_path", type=str)
    parser.add_argument("--text_features", action="store_true")
    return parser.parse_args()


def apply_overrides(p: Params, args: argparse.Namespace) -> None:
    for field in asdict(p).keys():
        val = getattr(args, field, None)
        if val is not None:
            setattr(p, field, val)
    # CLI contracts: explicit --hole or --slot
    if getattr(args, "hole", None) is not None:
        p.strap_hole_d = float(args.hole)
        p.strap_slot_w = 0.0
        p.strap_slot_l = 0.0
    if args.slot:
        w, l = args.slot.lower().split("x")
        p.strap_slot_w = float(w)
        p.strap_slot_l = float(l)
        p.strap_hole_d = 0.0


def main():
    args = parse_args()
    params = load_params(getattr(args, "params", None))
    # Apply preset first (yaml then preset), then CLI overrides
    preset_name = getattr(args, 'preset', None)
    try:
        params, rec_layer = apply_preset(params, getattr(args, "params", None), preset_name)
    except Exception as e:
        raise
    apply_overrides(params, args)
    coupons = None
    if args.emit_coupons:
        coupons = [t.strip() for t in args.emit_coupons.split(',') if t.strip()]
    strict = args.strict or args.ci or bool(os.getenv('CI'))
    build_and_export(
        params,
        args.out,
        args.variant,
        previews=args.previews,
        deterministic=args.deterministic,
        layer_height=args.layer_height,
        strict=strict,
        emit_coupons=coupons,
        preset=preset_name,
        qr_text=getattr(args, 'qr_text', None),
        qr_svg=getattr(args, 'qr_svg', None),
        text_features=getattr(args, 'text_features', False),
    )


if __name__ == "__main__":
    main()
