#!/usr/bin/env python3
"""Dual-color luggage tag generator for BambuLab P1S with AMS."""

import cadquery as cq
import segno
from pathlib import Path
import json
import argparse

def create_dual_color_luggage_tag(
    width: float = 85.0,
    height: float = 54.0,
    thickness: float = 3.0,
    qr_url: str = "https://oriashkenazi.github.io/luggage-recovery",
    name: str = "Ori Ashkenazi",
    phone: str = "+972-50-971-3042",
    email: str = "oriashkenazi93@gmail.com",
    output_dir: Path = Path("outputs"),
    reversible: bool = True
):
    """
    Create a dual-color luggage tag optimized for BambuLab P1S.

    For dual-color printing:
    - Base layer: Dark color (black, navy)
    - Top layer: Light color (white, yellow)
    - Both layers are FLUSH - same height, different colors
    """

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Creating dual-color luggage tag: {width}×{height}×{thickness}mm")

    # Create base shape - credit card proportions
    base = (
        cq.Workplane("XY")
        .rect(width, height)
        .extrude(thickness)
        .edges("|Z")
        .fillet(4.0)
    )

    # Add strap hole - positioned to avoid content conflicts
    hole_x = -width/2 + 10  # 10mm from left edge
    hole_y = height/2 - 8    # 8mm from top edge
    hole_diameter = 6.0

    base = (
        base.faces(">Z")
        .workplane()
        .center(hole_x, hole_y)
        .circle(hole_diameter/2)
        .cutThruAll()
    )

    print("Creating features for BOTH sides (truly reversible)...")

    # Create all the features that will be the second color (light)
    # Features will exist on BOTH sides of the tag
    features_front = cq.Workplane("XY")
    features_back = cq.Workplane("XY")

    # CSS-validated layout positions
    content_margin = 4.0
    content_left = -width/2 + content_margin
    content_right = width/2 - content_margin
    content_top = height/2 - content_margin
    content_bottom = -height/2 + content_margin

    # 1. QR Code - create on BOTH sides for true reversibility
    print("Generating QR code for BOTH sides...")
    qr_size = 26.0  # Optimized size for dual-layout
    qr_x = content_left + qr_size/2 + 4  # Closer to left edge for more right space
    qr_y = -2  # Slightly below center to avoid hole area

    qr = segno.make(qr_url, error='m')
    matrix_size = qr.symbol_size()
    modules = matrix_size[0]
    module_size = qr_size / modules

    print(f"QR code: {modules}×{modules} modules, {module_size:.2f}mm per module")

    # Create QR light modules for FRONT side
    for row_idx, row in enumerate(qr.matrix_iter(scale=1, border=0)):
        for col_idx, is_dark in enumerate(row):
            if not is_dark:  # Light modules = second color features
                x = qr_x - qr_size/2 + (col_idx + 0.5) * module_size
                y = qr_y + qr_size/2 - (row_idx + 0.5) * module_size

                # Front side QR (from bottom up)
                front_square = (
                    cq.Workplane("XY")
                    .center(x, y)
                    .rect(module_size * 0.85, module_size * 0.85)
                    .extrude(thickness / 2)  # Half thickness
                )
                features_front = features_front.union(front_square)

                # Back side QR (from top down, NOT mirrored)
                back_square = (
                    cq.Workplane("XY")
                    .workplane(offset=thickness)
                    .center(x, y)  # Same position, not mirrored
                    .rect(module_size * 0.85, module_size * 0.85)
                    .extrude(-thickness / 2)  # Extrude downward
                )
                features_back = features_back.union(back_square)

    # 2. Text features on BOTH sides for true reversibility
    print("Creating text features on BOTH sides...")

    # Header text - ALL CAPS with Assistant font, readable both sides
    header = "FOUND MY LUGGAGE?"  # Already caps
    header_x = 0  # Center horizontally
    header_y = content_top - 6  # Near top with safe margin

    # Front side header (from bottom up)
    header_front = (
        cq.Workplane("XY")
        .center(header_x, header_y)
        .text(header, 4.0, thickness / 2, font="Assistant", combine=True)
    )
    features_front = features_front.union(header_front)

    # Back side header (from top down, NOT mirrored)
    header_back = (
        cq.Workplane("XY")
        .workplane(offset=thickness)
        .center(header_x, header_y)  # Same position
        .text(header, 4.0, -thickness / 2, font="Assistant", combine=True)
    )
    features_back = features_back.union(header_back)

    # Contact info - positioned in available space after QR
    # QR occupies from qr_x-qr_size/2 to qr_x+qr_size/2
    qr_right_edge = qr_x + qr_size/2
    available_right_space = content_right - qr_right_edge

    print(f"Layout check: QR right edge at {qr_right_edge:.1f}, available space: {available_right_space:.1f}mm")

    # Position contact text in the center of available right space
    contact_x = qr_right_edge + available_right_space/2
    contact_y_start = 8  # Higher up to use vertical space better
    line_spacing = 5.2

    contact_lines = [
        (name.upper(), 4.2),  # ALL CAPS
        (phone.upper(), 3.8),  # ALL CAPS
        (email.upper(), 3.2)   # ALL CAPS
    ]

    for i, (text, font_size) in enumerate(contact_lines):
        y_pos = contact_y_start - i * line_spacing

        # Front side contact line
        line_front = (
            cq.Workplane("XY")
            .center(contact_x, y_pos)
            .text(text, font_size, thickness / 2, font="Assistant", combine=True)
        )
        features_front = features_front.union(line_front)

        # Back side contact line (NOT mirrored)
        line_back = (
            cq.Workplane("XY")
            .workplane(offset=thickness)
            .center(contact_x, y_pos)  # Same position
            .text(text, font_size, -thickness / 2, font="Assistant", combine=True)
        )
        features_back = features_back.union(line_back)

    # Footer - bottom center, ALL CAPS on BOTH sides
    footer = "SCAN QR OR CALL/TEXT"  # Already caps
    footer_x = 0
    footer_y = content_bottom + 4  # Near bottom with margin

    # Front side footer
    footer_front = (
        cq.Workplane("XY")
        .center(footer_x, footer_y)
        .text(footer, 3.5, thickness / 2, font="Assistant", combine=True)
    )
    features_front = features_front.union(footer_front)

    # Back side footer (NOT mirrored)
    footer_back = (
        cq.Workplane("XY")
        .workplane(offset=thickness)
        .center(footer_x, footer_y)  # Same position
        .text(footer, 3.5, -thickness / 2, font="Assistant", combine=True)
    )
    features_back = features_back.union(footer_back)

    # Combine all features from both sides
    all_features = features_front.union(features_back)

    print("Performing boolean operations for truly reversible tag...")
    # Create base with features subtracted (first color - dark)
    base_with_holes = base.cut(all_features)

    # Export files
    print("Exporting STL files...")

    # Base with holes (first color - dark)
    base_file = output_dir / "luggage_tag_base.stl"
    cq.exporters.export(base_with_holes, str(base_file))

    # Features (second color - light) - now includes both sides
    features_file = output_dir / "luggage_tag_features.stl"
    cq.exporters.export(all_features, str(features_file))

    # Combined preview (original full base)
    preview_file = output_dir / "luggage_tag_combined.stl"
    cq.exporters.export(base, str(preview_file))

    # Create QR test image
    qr_test = output_dir / "qr_test.png"
    qr.save(qr_test, scale=8, border=2)

    # Create printing instructions
    instructions = {
        "bambulab_p1s_setup": {
            "slicer": "BambuStudio or Bambu Handy",
            "layer_height": "0.2mm",
            "base_color": "Dark (black, navy, etc.) - AMS Slot 1",
            "feature_color": "Light (white, yellow, etc.) - AMS Slot 2",
            "color_change_layer": int(thickness / 0.2),
            "print_time": "~25 minutes"
        },
        "files": {
            "base": base_file.name,
            "features": features_file.name,
            "preview": preview_file.name,
            "qr_test": qr_test.name
        },
        "tag_info": {
            "dimensions": f"{width}×{height}×{thickness}mm",
            "qr_size": f"{qr_size}mm",
            "qr_url": qr_url,
            "contact": f"{name} | {phone} | {email}"
        }
    }

    (output_dir / "instructions.json").write_text(json.dumps(instructions, indent=2))

    print(f"✅ Dual-color luggage tag complete!")
    print(f"📁 Output: {output_dir}")
    print(f"🎨 Color change at layer {instructions['bambulab_p1s_setup']['color_change_layer']}")
    print(f"📱 QR size: {qr_size}mm (scannable)")

    return output_dir

def main():
    parser = argparse.ArgumentParser(description="Generate dual-color luggage tag for BambuLab P1S")
    parser.add_argument("--width", type=float, default=85.0, help="Tag width in mm")
    parser.add_argument("--height", type=float, default=54.0, help="Tag height in mm")
    parser.add_argument("--thickness", type=float, default=3.0, help="Tag thickness in mm")
    parser.add_argument("--url", default="https://oriashkenazi.github.io/luggage-recovery", help="QR code URL")
    parser.add_argument("--name", default="Ori Ashkenazi", help="Your name")
    parser.add_argument("--phone", default="+972-50-971-3042", help="Phone number")
    parser.add_argument("--email", default="oriashkenazi93@gmail.com", help="Email address")
    parser.add_argument("--out", type=Path, default=Path("outputs"), help="Output directory")

    args = parser.parse_args()

    create_dual_color_luggage_tag(
        width=args.width,
        height=args.height,
        thickness=args.thickness,
        qr_url=args.url,
        name=args.name,
        phone=args.phone,
        email=args.email,
        output_dir=args.out
    )

if __name__ == "__main__":
    main()