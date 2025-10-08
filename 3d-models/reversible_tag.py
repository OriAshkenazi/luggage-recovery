#!/usr/bin/env python3
"""
Reversible luggage tag generator.

Generates two STLs for dual-color printing on BambuLab P1S with AMS:
- "base" STL: base plate with features subtracted
- "features" STL: the positive inlays (dual stack: front + back), mirrored across Z

Layout: header (top), QR on the left, text on the right, footer (bottom).
The QR and text are sized for good legibility at 0.2 mm layers.
"""

import cadquery as cq
import segno
from pathlib import Path
from typing import Optional
import json
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.append(str(HERE))

from svg_to_3d import generate_3d_from_svg

def create_truly_reversible_tag(
    qr_url: str = "https://oriashkenazi.github.io/luggage-recovery",
    name: str = "ORI ASHKENAZI",
    phone: str = "+972-50-971-3042",
    email: str = "ORIASHKENAZI93@GMAIL.COM",
    output_dir: Path = Path("outputs"),
    font_path: Path = Path("assets/fonts/SF-Pro-Rounded-Bold.otf"),
    layout_config_path: Path = Path("layout_config.json"),
    override_config: dict = None,
    precise_svg_path: Optional[Path] = None
):
    """Create a reversible luggage tag with dual-stack mirrored features.

    Exports exactly two STLs:
    - reversible_tag_base.stl (base with features subtracted)
    - reversible_tag_features.stl (front + back features, mirrored in Z)
    """

    print("Creating REVERSIBLE luggage tag (dual-stack mirrored features)...")

    # Load layout configuration from web layout engine
    if layout_config_path.exists():
        print(f"📖 Loading layout config from {layout_config_path}")
        with open(layout_config_path, 'r') as f:
            layout_data = json.load(f)

        # Extract configuration values
        cfg = layout_data['input']
        computed = layout_data['computed']
        stacking = layout_data['stacking']

        # Apply any overrides
        if override_config:
            cfg.update(override_config)
            print(f"⚡ Applied config overrides: {list(override_config.keys())}")

        # Extract values with web layout names
        width = cfg['tagW']
        height = cfg['tagH']
        thickness = stacking['totalThickness']
        web_thickness = stacking['webThickness']
        modules = cfg['modules']
        module_size = cfg['moduleSize']
        quiet_modules = cfg['quiet']

        # Margins and padding
        margin_outer_t = cfg['outerT']
        margin_outer_r = cfg['outerR']
        margin_outer_b = cfg['outerB']
        margin_outer_l = cfg['outerL']
        gutter = cfg['gutter']

        # QR padding
        qrPadT = cfg['qrPadT']
        qrPadR = cfg['qrPadR']
        qrPadB = cfg['qrPadB']
        qrPadL = cfg['qrPadL']

        # Text padding
        txPadT = cfg['txPadT']
        txPadR = cfg['txPadR']
        txPadB = cfg['txPadB']
        txPadL = cfg['txPadL']

        # Font sizes
        fsH = cfg['fsH']
        fsN = cfg['fsN']
        fsP = cfg['fsP']
        fsE = cfg['fsE']
        fsF = cfg['fsF']

        # Slit configuration
        slit_width = cfg['slitWidth']
        slit_height = cfg['slitHeight']
        slit_margin_r = cfg['slitMarginR']

        print(f"✅ Using web layout: {width}×{height}mm, QR {modules}×{modules} @ {module_size}mm/module")

        # If precise SVG exists, prefer SVG-driven geometry
        if precise_svg_path is None:
            precise_svg_path = output_dir / "luggage_tag_precise.svg"
        if precise_svg_path.exists():
            print(f"🎯 Using precise SVG geometry: {precise_svg_path}")
            result = generate_3d_from_svg(
                precise_svg_path,
                output_dir=output_dir,
                thickness=thickness,
                web_thickness=web_thickness,
                font_path=font_path,
                base_name="reversible_tag"
            )

            manifest = {
                "source": "svg",
                "dimensions_mm": {"w": width, "h": height, "t": thickness},
                "slit": {
                    "cx": computed['slitCenter']['x'],
                    "cy": computed['slitCenter']['y'],
                    "width": cfg['slitWidth'],
                    "height": cfg['slitHeight']
                },
                "qr": {
                    "size": computed['qrSize'],
                    "modules": modules,
                    "module_mm": module_size,
                    "quiet_modules": quiet_modules,
                    "url": qr_url
                },
                "stacking": stacking,
                "files": {
                    "base": result['base_file'].name,
                    "features": result['features_file'].name
                }
            }
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "reversible_manifest.json").write_text(json.dumps(manifest, indent=2))
            print("✅ Reversible tag exported from precise SVG (base + features)")
            return output_dir
        else:
            print(f"⚠️ Precise SVG not found at {precise_svg_path}, falling back to parametric generator")

    else:
        print(f"⚠️  Layout config not found at {layout_config_path}, using fallback defaults")
        # Fallback to new defaults matching web layout
        width = 200.0
        height = 74.0
        thickness = 3.0
        web_thickness = 0.4
        modules = 29
        module_size = 2.0
        quiet_modules = 0

        margin_outer_t = margin_outer_r = margin_outer_b = margin_outer_l = 4.0
        gutter = 3.0
        qrPadT = qrPadR = qrPadB = qrPadL = 0.0
        txPadT = txPadB = 8.0
        txPadR = txPadL = 3.0

        fsH = 10.0; fsN = 6.0; fsP = 5.0; fsE = 5.0; fsF = 7.0
        slit_width = 5.0
        slit_height = 20.0
        slit_margin_r = 5.0

    # Determine font for measuring
    if font_path and Path(font_path).exists():
        font = str(Path(font_path).resolve())
    else:
        font = "SF Pro Rounded"

    def _font_kwargs():
        return dict(font=font, fontPath=str(Path(font_path).resolve()) if Path(font_path).exists() else None, kind="bold")

    # Generate QR code
    qr = segno.make(qr_url, error='l')
    actual_qr_modules = qr.symbol_size()[0]

    # Validate QR module count matches configuration
    if actual_qr_modules != modules:
        print(f"⚠️  QR code has {actual_qr_modules} modules but config expects {modules}")
        modules = actual_qr_modules

    half_depth = max(0.1, (thickness - web_thickness) / 2)
    print(f"💾 Stacking: {half_depth:.2f}mm depth per side, {web_thickness}mm central web")

    # Measure max text width at target sizes
    def _measure_w(text: str, fs: float) -> float:
        return float(cq.Workplane("XY").text(text, fs, half_depth, halign='left', valign='center', combine=True, **_font_kwargs()).val().BoundingBox().xlen)

    max_text_w = max(
        _measure_w("FOUND MY LUGGAGE?", fsH),
        _measure_w(name.upper(), fsN),
        _measure_w(phone.upper(), fsP),
        _measure_w(email.upper(), fsE),
        _measure_w("SCAN QR OR CALL/TEXT", fsF),
    )
    text_col_min_w = max_text_w + (txPadL + txPadR)

    # Compute required QR side with quiet zone and ensure left column inner width/height fits
    qr_required_side = module_size * (modules + 2*quiet_modules)
    left_col_min_w = qr_required_side + (qrPadL + qrPadR)

    # Check if dimensions are adequate (but don't auto-expand - use web layout as authoritative)
    content_min_w = left_col_min_w + gutter + text_col_min_w
    width_min = content_min_w + margin_outer_l + margin_outer_r
    if width < width_min:
        print(f"⚠️  Width {width:.1f}mm may be too small (needs {width_min:.1f}mm)")

    content_min_h = qr_required_side + margin_outer_t + margin_outer_b
    if height < content_min_h:
        print(f"⚠️  Height {height:.1f}mm may be too small (needs {content_min_h:.1f}mm)")

    # Content box using web layout margins
    left_edge = -width/2 + margin_outer_l
    right_edge = width/2 - margin_outer_r
    top = height/2 - margin_outer_t
    bottom = -height/2 + margin_outer_b

    # Build base with final dims
    base = (
        cq.Workplane("XY")
        .rect(width, height)
        .extrude(thickness)
        .edges("|Z")
        .fillet(4.0)
    )

    # Defer hole cutting until after layout (hole lives inside text column)
    # (no-op here)

    # Columns: left is QR column sized exactly to requirement; right takes remainder
    content_w = right_edge - left_edge
    left_col_xmin = left_edge
    # Use computed left column width from web layout
    left_col_actual_w = qr_required_side + (qrPadL + qrPadR)
    left_col_xmax = left_edge + left_col_actual_w
    right_col_xmin = left_col_xmax + gutter
    right_col_xmax = right_edge

    # QR box in left column
    qr_box_w = (left_col_xmax - left_col_xmin) - (qrPadL + qrPadR)
    qr_box_h = (top - bottom) - (qrPadT + qrPadB)
    actual_module_size_check = min(qr_box_w, qr_box_h) / (modules + 2*quiet_modules)
    quiet_zone = quiet_modules * module_size
    qr_size = modules * module_size
    # Use exact QR center position from web layout computation
    if 'computed' in locals() and computed:
        qr_x = computed['qrCenter']['x']
        qr_y = computed['qrCenter']['y']
        print(f"🎯 Using web layout QR center: ({qr_x:.1f}, {qr_y:.1f})")
    else:
        # Fallback calculation
        qr_x = (left_col_xmin + qrPadL + quiet_zone) + qr_size/2.0
        qr_y = (bottom + qrPadB + quiet_zone) + qr_size/2.0
        print(f"⚠️  Using fallback QR center: ({qr_x:.1f}, {qr_y:.1f})")
    module_size_ok = abs(actual_module_size_check - module_size) < 0.05
    print(f"QR: {modules}×{modules}, module {module_size:.2f}mm (actual: {actual_module_size_check:.2f}mm), size {qr_size:.1f}mm (quiet {quiet_zone:.2f}mm)")

    # Features are split into two stacks with a central web left in the base
    # so the stacks do not merge into one. This avoids through-cuts.
    half_depth = max(0.1, (thickness - web_thickness) / 2)
    features_front = cq.Workplane("XY")
    features_back = cq.Workplane("XY")

    # Light modules become features; dark modules remain base
    for r, row in enumerate(qr.matrix_iter(scale=1, border=0)):
        for c, is_dark in enumerate(row):
            if not is_dark:
                x = qr_x - qr_size/2 + (c + 0.5) * module_size
                y = qr_y + qr_size/2 - (r + 0.5) * module_size
                sz = module_size  # full module squares to meet >= 2x2 mm

                front = (
                    cq.Workplane("XY")
                    .center(x, y)
                    .rect(sz, sz)
                    .extrude(half_depth)
                )
                features_front = features_front.union(front)

                back = (
                    cq.Workplane("XY").workplane(offset=thickness)
                    .center(x, y)
                    .rect(sz, sz)
                    .extrude(-half_depth)
                )
                features_back = features_back.union(back)

    # Text features (header, contact, footer) sized for P1S at 0.2mm — font already set above
    # Helpers: fit text to a max width by probing font size

    def fit_font_size(text: str, fs_init: float, max_width: float, depth: float) -> float:
        fs = fs_init
        # Build a temporary text at origin to measure width
        tmp = cq.Workplane("XY").text(text, fs, depth, halign='left', valign='center', combine=True, **_font_kwargs())
        width = tmp.val().BoundingBox().xlen
        if width <= max_width:
            return fs
        scale = max_width / max(width, 1e-6)
        fs_adj = max(2.2, fs * scale)  # clamp minimal size
        return fs_adj

    # Use exact text area coordinates from web layout
    if 'computed' in locals() and computed:
        text_area_left = computed['textArea']['left']
        text_area_right = computed['textArea']['right']
        text_area_top = computed['textArea']['top']
        text_area_bottom = computed['textArea']['bottom']
        print(f"🎯 Using web layout text area: ({text_area_left:.1f}, {text_area_top:.1f}) to ({text_area_right:.1f}, {text_area_bottom:.1f})")
    else:
        # Fallback calculation
        text_area_left = right_col_xmin + txPadL
        text_area_right = right_col_xmax - txPadR
        text_area_top = top - txPadT
        text_area_bottom = bottom + txPadB
        print(f"⚠️  Using fallback text area")

    # Header text positioning
    header_text = "FOUND MY LUGGAGE?"
    header_fs = fsH
    header_y = text_area_top - header_fs/2  # Position from top of text area

    header_front = (
        cq.Workplane("XY").center(text_area_left, header_y)
        .text(header_text, header_fs, half_depth, halign='left', valign='top', combine=True, **_font_kwargs())
    )
    header_back = (
        cq.Workplane("XY").workplane(offset=thickness).center(text_area_left, header_y)
        .text(header_text, header_fs, -half_depth, halign='left', valign='top', combine=True, **_font_kwargs())
    )
    features_front = features_front.union(header_front)
    features_back = features_back.union(header_back)

    # Contact lines using exact web layout coordinates
    contact_left_x = text_area_left
    contact_lines = [
        (name.upper(), fsN),
        (phone.upper(), fsP),
        (email.upper(), fsE),
    ]
    line_gap = fsN * 1.25
    # Center contact info in middle of text area
    contact_y0 = (text_area_top + text_area_bottom) / 2.0 + fsN
    for i, (txt, fs) in enumerate(contact_lines):
        y = contact_y0 - i * line_gap
        lf = cq.Workplane("XY").center(contact_left_x, y).text(txt, fs, half_depth, halign='left', valign='center', combine=True, **_font_kwargs())
        lb = (
            cq.Workplane("XY").workplane(offset=thickness)
            .center(contact_left_x, y).text(txt, fs, -half_depth, halign='left', valign='center', combine=True, **_font_kwargs())
        )
        features_front = features_front.union(lf)
        features_back = features_back.union(lb)

    # Footer using exact web layout coordinates
    footer_text = "SCAN QR OR CALL/TEXT"
    footer_fs = fsF
    footer_y = text_area_bottom + footer_fs/2  # Position from bottom of text area
    footer_front = cq.Workplane("XY").center(text_area_left, footer_y).text(footer_text, footer_fs, half_depth, halign='left', valign='bottom', combine=True, **_font_kwargs())
    footer_back = (
        cq.Workplane("XY").workplane(offset=thickness)
        .center(text_area_left, footer_y).text(footer_text, footer_fs, -half_depth, halign='left', valign='bottom', combine=True, **_font_kwargs())
    )
    features_front = features_front.union(footer_front)
    features_back = features_back.union(footer_back)

    # CRITICAL STACKING ORDER from web layout configuration:
    # From reversible_tag.py:227-231 and layout_config stacking rules:

    if 'stacking' in locals() and stacking:  # Use web config if available
        bottom_mirrored = stacking['bottomSide']['mirrored']
        top_mirrored = stacking['topSide']['mirrored']
        mirror_plane = stacking['bottomSide'].get('mirrorPlane', 'YZ')

        print(f"🔄 Stacking from web config: bottom={'mirrored' if bottom_mirrored else 'normal'}, top={'mirrored' if top_mirrored else 'normal'}")

        # Apply mirroring based on configuration
        if bottom_mirrored:
            print(f"   → Mirroring bottom stack across {mirror_plane}")
            features_front = features_front.mirror(mirrorPlane=mirror_plane)
    else:
        print("🔄 Using default stacking: bottom mirrored YZ, top normal")
        # Default behavior: mirror bottom stack
        features_front = features_front.mirror(mirrorPlane='YZ')

    # Use exact slit position from web layout
    if 'computed' in locals() and computed:
        slit_cx = computed['slitCenter']['x']
        slit_cy = computed['slitCenter']['y']
        print(f"🎯 Using web layout slit center: ({slit_cx:.1f}, {slit_cy:.1f})")
    else:
        # Fallback calculation
        slit_cx = width/2 - slit_margin_r - slit_width/2
        slit_cy = 0.0
        print(f"⚠️  Using fallback slit center: ({slit_cx:.1f}, {slit_cy:.1f})")
    print(f"🔧 Slit: {slit_width}×{slit_height}mm at ({slit_cx:.1f}, {slit_cy:.1f})")

    # Create vertical slit (rounded ends)
    slit_shape = (
        cq.Workplane("XY")
        .center(slit_cx, slit_cy)
        .rect(slit_width, slit_height - slit_width)  # main rectangle
        .circle(slit_width/2).extrude(thickness)  # rounded ends
        .union(
            cq.Workplane("XY")
            .center(slit_cx, slit_cy + (slit_height - slit_width)/2)
            .circle(slit_width/2).extrude(thickness)
        )
        .union(
            cq.Workplane("XY")
            .center(slit_cx, slit_cy - (slit_height - slit_width)/2)
            .circle(slit_width/2).extrude(thickness)
        )
    )
    base = base.cut(slit_shape)

    # Union both sides to form the dual-stack feature solid
    features = features_front.union(features_back)

    # Subtract features from base to get the base STL
    print("Boolean subtract features from base...")
    base_with_subtractions = base.cut(features)

    # Export exactly two STLs
    output_dir.mkdir(parents=True, exist_ok=True)
    base_file = output_dir / "reversible_tag_base.stl"
    features_file = output_dir / "reversible_tag_features.stl"
    cq.exporters.export(base_with_subtractions, str(base_file))
    cq.exporters.export(features, str(features_file))

    # Minimal metadata for reference
    manifest = {
        "dimensions_mm": {"w": width, "h": height, "t": thickness},
        "slit": {"cx": slit_cx, "cy": slit_cy, "width": slit_width, "height": slit_height},
        "qr": {"size": qr_size, "modules": modules, "module_mm": module_size, "actual_mm": actual_module_size_check, "url": qr_url, "size_ok": module_size_ok},
        "stacking": {
            "top": "non-mirrored",
            "bottom": "mirrored across YZ (horizontal)",
            "web_mm": web_thickness,
            "half_depth_mm": round(half_depth, 3)
        },
        "font": {
            "name": font,
            "path": str(Path(font_path).resolve()) if Path(font_path).exists() else None,
            "kind": "bold"
        },
        "files": {"base": base_file.name, "features": features_file.name},
    }
    (output_dir / "reversible_manifest.json").write_text(json.dumps(manifest, indent=2))

    print("✅ Reversible tag exported (base + features)")
    return output_dir

if __name__ == "__main__":
    create_truly_reversible_tag()
