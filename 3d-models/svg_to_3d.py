#!/usr/bin/env python3
"""
SVG-to-3D Converter: Water-tight geometry transfer from web layout.

This script imports the precise SVG geometry exported from the web layout
and creates 3D models with zero coordinate translation errors.

Usage: python svg_to_3d.py [svg_file] [output_dir]
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import cadquery as cq
import json


def load_svg_layers(svg_path: Path):
    """Load and parse layered SVG from web export."""
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Extract SVG dimensions
    width = float(root.get('width', 240))
    height = float(root.get('height', 94))

    print(f"📐 SVG dimensions: {width} × {height} mm")

    # Find layer groups
    layers = {}
    for group in root.findall('.//{http://www.w3.org/2000/svg}g'):
        layer_id = group.get('id')
        if layer_id:
            layers[layer_id] = {
                'description': group.get('data-description', ''),
                'elements': list(group)
            }
            print(f"🔍 Found layer '{layer_id}': {group.get('data-description', 'No description')}")

    return {
        'dimensions': {'width': width, 'height': height},
        'layers': layers,
        'svg_root': root
    }


def create_base_from_svg(layer_data, thickness=3.0):
    """Create base solid from SVG base layer."""
    if 'base-outline' not in layer_data['layers']:
        raise ValueError("No base-outline layer found in SVG")

    base_layer = layer_data['layers']['base-outline']
    dimensions = layer_data['dimensions']

    # Find the base rectangle
    for element in base_layer['elements']:
        if element.tag.endswith('rect') and element.get('class') == 'base-shape':
            width = float(element.get('width'))
            height = float(element.get('height'))
            rx = float(element.get('rx', 0))

            print(f"🏗️  Creating base: {width} × {height} × {thickness} mm (radius {rx})")

            # Create base with corner radius, centered at origin
            base = (
                cq.Workplane("XY")
                .rect(width, height)
                .extrude(thickness)
                .edges("|Z")
                .fillet(rx)
            )

            return base

    raise ValueError("No base-shape rectangle found in base-outline layer")


def create_qr_features_from_svg(layer_data, thickness=3.0, web_thickness=0.4):
    """Create QR module features from exact SVG positions."""
    if 'qr-modules' not in layer_data['layers']:
        print("⚠️  No QR modules layer found")
        return cq.Workplane("XY"), cq.Workplane("XY")

    qr_layer = layer_data['layers']['qr-modules']
    dimensions = layer_data['dimensions']
    half_depth = (thickness - web_thickness) / 2

    print(f"🔲 Processing QR modules with {half_depth:.2f}mm depth per side")

    features_front = cq.Workplane("XY")
    features_back = cq.Workplane("XY")

    module_count = 0
    for element in qr_layer['elements']:
        if element.tag.endswith('rect') and element.get('class') == 'qr-module':
            # Get exact position and size from SVG
            x = float(element.get('x'))
            y = float(element.get('y'))
            width = float(element.get('width'))
            height = float(element.get('height'))

            # Convert from top-left SVG coordinates to center-based CadQuery coordinates
            center_x = x + width/2 - dimensions['width']/2
            center_y = dimensions['height']/2 - (y + height/2)  # Flip Y axis

            # Create front feature (bottom side - will be mirrored)
            front_module = (
                cq.Workplane("XY")
                .center(center_x, center_y)
                .rect(width, height)
                .extrude(half_depth)
            )
            features_front = features_front.union(front_module)

            # Create back feature (top side - normal)
            back_module = (
                cq.Workplane("XY").workplane(offset=thickness)
                .center(center_x, center_y)
                .rect(width, height)
                .extrude(-half_depth)
            )
            features_back = features_back.union(back_module)

            module_count += 1

    print(f"✅ Created {module_count} QR modules")

    # Apply mirroring to front stack (bottom side)
    features_front = features_front.mirror(mirrorPlane='YZ')
    print("🔄 Applied YZ mirroring to front stack")

    return features_front, features_back


def create_text_features_from_svg(layer_data, thickness=3.0, web_thickness=0.4, font_path=None):
    """Create text features from SVG text layer."""
    if 'text-features' not in layer_data['layers']:
        print("⚠️  No text features layer found")
        return cq.Workplane("XY"), cq.Workplane("XY")

    text_layer = layer_data['layers']['text-features']
    dimensions = layer_data['dimensions']
    half_depth = (thickness - web_thickness) / 2

    # Determine font
    if font_path and Path(font_path).exists():
        font = str(Path(font_path).resolve())
        print(f"📝 Using font: {font}")
    else:
        font = "SF Pro Rounded"
        print(f"📝 Using system font: {font}")

    def _font_kwargs():
        return dict(
            font=font,
            fontPath=str(Path(font_path).resolve()) if font_path and Path(font_path).exists() else None,
            kind="bold"
        )

    features_front = cq.Workplane("XY")
    features_back = cq.Workplane("XY")

    text_count = 0
    for element in text_layer['elements']:
        if element.tag.endswith('rect'):
            # Get text data and position
            text_content = element.get('data-text', 'TEXT')
            x = float(element.get('x'))
            y = float(element.get('y'))
            width = float(element.get('width'))
            height = float(element.get('height'))

            # Convert coordinates
            center_x = x + width/2 - dimensions['width']/2
            center_y = dimensions['height']/2 - (y + height/2)

            # Estimate font size from bounding box height
            font_size = height * 0.7  # Approximate font size from height

            print(f"📝 Creating text '{text_content}' at ({center_x:.1f}, {center_y:.1f}) size {font_size:.1f}")

            try:
                # Create front text feature
                front_text = (
                    cq.Workplane("XY")
                    .center(center_x, center_y)
                    .text(text_content, font_size, half_depth, halign='center', valign='center', combine=True, **_font_kwargs())
                )
                features_front = features_front.union(front_text)

                # Create back text feature
                back_text = (
                    cq.Workplane("XY").workplane(offset=thickness)
                    .center(center_x, center_y)
                    .text(text_content, font_size, -half_depth, halign='center', valign='center', combine=True, **_font_kwargs())
                )
                features_back = features_back.union(back_text)

                text_count += 1

            except Exception as e:
                print(f"⚠️  Failed to create text '{text_content}': {e}")

    print(f"✅ Created {text_count} text features")

    # Apply mirroring to front stack
    features_front = features_front.mirror(mirrorPlane='YZ')

    return features_front, features_back


def create_slit_cutout_from_svg(layer_data):
    """Create slit cutout from SVG slit layer."""
    if 'slit-cutout' not in layer_data['layers']:
        print("⚠️  No slit cutout layer found")
        return None

    slit_layer = layer_data['layers']['slit-cutout']
    dimensions = layer_data['dimensions']

    for element in slit_layer['elements']:
        if element.tag.endswith('rect') and element.get('class') == 'slit-cutout':
            x = float(element.get('x'))
            y = float(element.get('y'))
            width = float(element.get('width'))
            height = float(element.get('height'))
            rx = float(element.get('rx', width/2))

            # Convert coordinates
            center_x = x + width/2 - dimensions['width']/2
            center_y = dimensions['height']/2 - (y + height/2)

            print(f"✂️  Creating slit cutout: {width} × {height} at ({center_x:.1f}, {center_y:.1f})")

            # Create rounded rectangle slit (robust approach: union of center rect + end arcs)
            plate = (
                cq.Workplane("XY")
                .center(center_x, center_y)
                .rect(width - 2 * rx, height)
                .extrude(10)
            )
            top_circle = (
                cq.Workplane("XY")
                .center(center_x, center_y + (height / 2 - rx))
                .circle(rx)
                .extrude(10)
            )
            bottom_circle = (
                cq.Workplane("XY")
                .center(center_x, center_y - (height / 2 - rx))
                .circle(rx)
                .extrude(10)
            )
            slit = plate.union(top_circle).union(bottom_circle)

            return slit

    return None


def generate_3d_from_svg(
    svg_path: Path,
    output_dir: Path = Path("outputs"),
    thickness: float = 3.0,
    web_thickness: float = 0.4,
    font_path: Path = None,
    base_name: str = "svg_tag"
):
    """Generate water-tight 3D models from precise SVG geometry."""

    print(f"🎯 Processing SVG: {svg_path}")

    # Load SVG layers
    layer_data = load_svg_layers(svg_path)

    # Create base solid
    base = create_base_from_svg(layer_data, thickness)
    print("✅ Base solid created")

    # Create QR features
    qr_front, qr_back = create_qr_features_from_svg(layer_data, thickness, web_thickness)

    # Create text features
    text_front, text_back = create_text_features_from_svg(layer_data, thickness, web_thickness, font_path)

    # Combine all features
    features_front = qr_front.union(text_front) if text_front else qr_front
    features_back = qr_back.union(text_back) if text_back else qr_back
    features_combined = features_front.union(features_back)

    print("✅ Features combined")

    # Create slit cutout
    slit = create_slit_cutout_from_svg(layer_data)
    if slit:
        base = base.cut(slit)
        print("✅ Slit cutout applied")

    # Subtract features from base
    print("🔄 Performing boolean subtraction...")
    base_final = base.cut(features_combined)
    print("✅ Boolean operations complete")

    # Export STL files
    output_dir.mkdir(parents=True, exist_ok=True)

    base_file = output_dir / f"{base_name}_base.stl"
    features_file = output_dir / f"{base_name}_features.stl"

    cq.exporters.export(base_final, str(base_file))
    cq.exporters.export(features_combined, str(features_file))

    print(f"🎉 STL files exported:")
    print(f"   📁 {base_file}")
    print(f"   📁 {features_file}")

    return {
        "output_dir": output_dir,
        "base_file": base_file,
        "features_file": features_file
    }


def main():
    import sys

    svg_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("luggage_tag_precise.svg")
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("outputs")
    font_path = Path("assets/fonts/SF-Pro-Rounded-Bold.otf")

    if not svg_file.exists():
        print(f"❌ SVG file not found: {svg_file}")
        print("   Export SVG from web layout first using 'Export SVG' button")
        return 1

    try:
        generate_3d_from_svg(svg_file, output_dir, font_path=font_path)
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
