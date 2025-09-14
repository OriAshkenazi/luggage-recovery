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
    output_dir: Path = Path("outputs")
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

    # Add strap hole in top-left corner, away from content
    hole_x = -width/2 + 12  # 12mm from left edge
    hole_y = height/2 - 10   # 10mm from top edge
    hole_diameter = 6.0

    base = (
        base.faces(">Z")
        .workplane()
        .center(hole_x, hole_y)
        .circle(hole_diameter/2)
        .cutThruAll()
    )

    print("Creating base layer (dark color)...")
    # Base layer - this will be the dark color and forms the substrate

    print("Creating top layer (light color)...")
    # Top layer - this will be the light color, starts at top of base
    top_layer_thickness = 0.6  # 3 layers at 0.2mm = substantial enough for slicer

    # Create a top layer plate that covers the entire tag
    top_layer = (
        cq.Workplane("XY")
        .workplane(offset=thickness)
        .rect(width, height)
        .extrude(top_layer_thickness)
        .edges("|Z")
        .fillet(4.0)
    )

    # Add the same strap hole to top layer
    top_layer = (
        top_layer.faces("<Z")  # Bottom face of top layer
        .workplane()
        .center(hole_x, hole_y)
        .circle(hole_diameter/2)
        .cutThruAll()
    )

    # Now CUT OUT areas where we want the base (dark) color to show through

    # 1. QR Code - cut out DARK modules (let base show through)
    print("Generating QR code pattern...")
    qr_size = 25.0
    qr_x = -width/2 + qr_size/2 + 8  # 8mm from left edge
    qr_y = 0  # Center vertically

    qr = segno.make(qr_url, error='m')
    matrix_size = qr.symbol_size()
    modules = matrix_size[0]
    module_size = qr_size / modules

    print(f"QR code: {modules}×{modules} modules, {module_size:.2f}mm per module")

    # Create cuts for dark QR modules
    qr_cuts = cq.Workplane("XY").workplane(offset=thickness)

    for row_idx, row in enumerate(qr.matrix_iter(scale=1, border=0)):
        for col_idx, is_dark in enumerate(row):
            if is_dark:  # Dark modules - CUT from top layer (let base show)
                x = qr_x - qr_size/2 + (col_idx + 0.5) * module_size
                y = qr_y + qr_size/2 - (row_idx + 0.5) * module_size

                cut_square = (
                    cq.Workplane("XY")
                    .workplane(offset=thickness)
                    .center(x, y)
                    .rect(module_size * 0.85, module_size * 0.85)
                    .extrude(top_layer_thickness)
                )
                qr_cuts = qr_cuts.union(cut_square)

    # Cut the QR dark modules from top layer
    try:
        top_layer = top_layer.cut(qr_cuts)
    except:
        print("Warning: QR cuts failed, continuing without cuts")

    # 2. Create text areas that will be LIGHT color (keep in top layer)
    # We don't cut these - they stay as part of the top layer

    print("Creating text areas (staying in top layer)...")

    # Create raised text areas to ensure good layering
    text_height = 0.2  # Slightly raised above the base top layer

    # Header text
    header = "FOUND MY LUGGAGE?"
    header_x = 0
    header_y = height/2 - 8

    header_text = (
        cq.Workplane("XY")
        .workplane(offset=thickness + top_layer_thickness)
        .center(header_x, header_y)
        .text(header, 4.5, text_height, font="Liberation Sans", combine=True)
    )

    # Contact info
    contact_x = width/2 - 25
    contact_y_start = 8
    line_spacing = 5.5
    contact_text = cq.Workplane("XY")

    contact_lines = [
        (name, 5.0),
        (phone, 4.0),
        (email, 3.5)
    ]

    for i, (text, font_size) in enumerate(contact_lines):
        y_pos = contact_y_start - i * line_spacing

        line_text = (
            cq.Workplane("XY")
            .workplane(offset=thickness + top_layer_thickness)
            .center(contact_x, y_pos)
            .text(text, font_size, text_height, font="Liberation Sans", combine=True)
        )
        contact_text = contact_text.union(line_text)

    # Footer
    footer = "SCAN QR OR CALL/TEXT"
    footer_y = -height/2 + 6

    footer_text = (
        cq.Workplane("XY")
        .workplane(offset=thickness + top_layer_thickness)
        .center(0, footer_y)
        .text(footer, 3.8, text_height, font="Liberation Sans", combine=True)
    )

    # Add all text to top layer
    all_text = header_text.union(contact_text).union(footer_text)
    top_layer = top_layer.union(all_text)

    # Export files
    print("Exporting STL files...")

    # Base layer (dark color - black/navy)
    base_file = output_dir / "luggage_tag_base.stl"
    cq.exporters.export(base, str(base_file))

    # Top layer (light color - white/yellow)
    top_file = output_dir / "luggage_tag_top.stl"
    cq.exporters.export(top_layer, str(top_file))

    # Combined preview
    combined = base.union(top_layer)
    preview_file = output_dir / "luggage_tag_combined.stl"
    cq.exporters.export(combined, str(preview_file))

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
            "top": top_file.name,
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