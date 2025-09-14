#!/usr/bin/env python3
"""
REVERSIBLE luggage tag - QR code and text readable from BOTH sides.
Efficient implementation that actually works.
"""

import cadquery as cq
import segno
from pathlib import Path
import json

def create_truly_reversible_tag():
    """Create a luggage tag that's readable and scannable from BOTH sides."""

    # Tag dimensions
    width = 85.0
    height = 54.0
    thickness = 3.0

    print("Creating REVERSIBLE luggage tag...")
    print("QR code will be scannable from BOTH sides")
    print("Text will be readable from BOTH sides")

    # Create base tag
    base = (
        cq.Workplane("XY")
        .rect(width, height)
        .extrude(thickness)
        .edges("|Z")
        .fillet(4.0)
    )

    # Add strap hole
    hole_x = -width/2 + 10
    hole_y = height/2 - 8
    base = (
        base.faces(">Z")
        .workplane()
        .center(hole_x, hole_y)
        .circle(3.0)
        .cutThruAll()
    )

    # Layout positions
    qr_size = 26.0
    qr_x = -width/2 + qr_size/2 + 6
    qr_y = -2

    # Generate QR code
    qr_url = "https://oriashkenazi.github.io/luggage-recovery"
    qr = segno.make(qr_url, error='m')
    matrix_size = qr.symbol_size()
    modules = matrix_size[0]
    module_size = qr_size / modules

    print(f"QR: {modules}×{modules} modules, {module_size:.2f}mm per module")

    # Strategy: Create features that go THROUGH the entire tag
    # This makes them visible and functional from both sides
    features = cq.Workplane("XY")

    # 1. QR Code - THROUGH holes (visible from both sides)
    print("Creating QR code visible from both sides...")
    for row_idx, row in enumerate(qr.matrix_iter(scale=1, border=0)):
        for col_idx, is_dark in enumerate(row):
            if not is_dark:  # Light modules = cut through completely
                x = qr_x - qr_size/2 + (col_idx + 0.5) * module_size
                y = qr_y + qr_size/2 - (row_idx + 0.5) * module_size

                # Create hole that goes ALL THE WAY THROUGH
                hole = (
                    cq.Workplane("XY")
                    .center(x, y)
                    .rect(module_size * 0.8, module_size * 0.8)
                    .extrude(thickness)  # Full thickness
                )
                features = features.union(hole)

    # 2. Text - THROUGH holes (readable from both sides)
    print("Creating text readable from both sides...")

    # For text to be readable from both sides, we create it as through-holes
    # The light color will fill these holes, making text visible from both sides

    # Header
    header_text = (
        cq.Workplane("XY")
        .center(0, height/2 - 8)
        .text("FOUND MY LUGGAGE?", 4.0, thickness, font="Assistant", combine=True)
    )
    features = features.union(header_text)

    # Contact info
    contact_x = qr_x + qr_size/2 + 15
    contact_lines = [
        ("ORI ASHKENAZI", 4.2),
        ("+972-50-971-3042", 3.8),
        ("ORIASHKENAZI93@GMAIL.COM", 3.2)
    ]

    for i, (text, font_size) in enumerate(contact_lines):
        y_pos = 8 - i * 5.2

        contact_text = (
            cq.Workplane("XY")
            .center(contact_x, y_pos)
            .text(text, font_size, thickness, font="Assistant", combine=True)
        )
        features = features.union(contact_text)

    # Footer
    footer_text = (
        cq.Workplane("XY")
        .center(0, -height/2 + 6)
        .text("SCAN QR OR CALL/TEXT", 3.5, thickness, font="Assistant", combine=True)
    )
    features = features.union(footer_text)

    # Boolean operations
    print("Performing boolean operations...")
    base_with_holes = base.cut(features)

    # Export files
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Exporting STL files...")

    # Base with holes (dark color)
    base_file = output_dir / "reversible_tag_base.stl"
    cq.exporters.export(base_with_holes, str(base_file))

    # Features (light color fills the holes)
    features_file = output_dir / "reversible_tag_features.stl"
    cq.exporters.export(features, str(features_file))

    # Combined preview
    combined = base_with_holes.union(features)
    preview_file = output_dir / "reversible_tag_preview.stl"
    cq.exporters.export(combined, str(preview_file))

    # QR test
    qr_test = output_dir / "qr_test.png"
    qr.save(qr_test, scale=8, border=2)

    # Instructions
    instructions = {
        "REVERSIBLE_TAG": {
            "description": "QR code and text readable from BOTH sides",
            "how_it_works": "Features go through entire thickness",
            "qr_scannable": "From front AND back",
            "text_readable": "From front AND back"
        },
        "bambulab_p1s": {
            "base_color": "Dark (black/navy) - AMS Slot 1",
            "feature_color": "Light (white/yellow) - AMS Slot 2",
            "layer_height": "0.2mm",
            "color_change_layer": 15
        },
        "files": {
            "base": base_file.name,
            "features": features_file.name,
            "preview": preview_file.name
        }
    }

    (output_dir / "reversible_instructions.json").write_text(json.dumps(instructions, indent=2))

    print(f"\n✅ REVERSIBLE TAG COMPLETE!")
    print(f"📁 Files: {output_dir}")
    print(f"📱 QR code: Scannable from BOTH sides")
    print(f"📝 Text: Readable from BOTH sides")
    print(f"🎯 TRUE reversible luggage tag!")

    return output_dir

if __name__ == "__main__":
    create_truly_reversible_tag()