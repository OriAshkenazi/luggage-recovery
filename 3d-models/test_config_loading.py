#!/usr/bin/env python3
"""
Test script to verify layout configuration loading without CadQuery dependency.
"""

import json
from pathlib import Path

def test_config_loading():
    """Test loading and parsing of layout configuration."""

    layout_config_path = Path("layout_config.json")

    if layout_config_path.exists():
        print(f"📖 Loading layout config from {layout_config_path}")
        with open(layout_config_path, 'r') as f:
            layout_data = json.load(f)

        # Extract configuration values
        cfg = layout_data['input']
        computed = layout_data['computed']
        stacking = layout_data['stacking']

        print(f"✅ Configuration loaded successfully:")
        print(f"   Canvas: {cfg['tagW']} × {cfg['tagH']} mm")
        print(f"   QR: {cfg['modules']}×{cfg['modules']} @ {cfg['moduleSize']}mm/module")
        print(f"   Computed QR size: {computed['qrSize']:.1f}mm")
        print(f"   Left column: {computed['leftColMm']:.1f}mm")
        print(f"   Right column: {computed['rightColMm']:.1f}mm")
        print(f"   Slit position: ({computed['slitCenter']['x']:.1f}, {computed['slitCenter']['y']:.1f})")

        print(f"\n🔄 Stacking configuration:")
        print(f"   Top side: {stacking['topSide']['description']}")
        print(f"   Bottom side: {stacking['bottomSide']['description']}")
        print(f"   Web thickness: {stacking['webThickness']}mm")
        print(f"   Half depth: {stacking['halfDepth']:.2f}mm")

        # Test the values match expected defaults
        expected_values = {
            'tagW': 240.0,
            'tagH': 94.0,
            'modules': 37,
            'moduleSize': 2.0,
            'quiet': 0,
            'slitWidth': 4.5,
            'slitHeight': 20.0
        }

        print(f"\n🧪 Validation:")
        all_valid = True
        for key, expected in expected_values.items():
            actual = cfg[key]
            if actual == expected:
                print(f"   ✅ {key}: {actual} (matches expected)")
            else:
                print(f"   ❌ {key}: {actual} (expected {expected})")
                all_valid = False

        if all_valid:
            print(f"\n🎉 All configuration values match web layout defaults!")
        else:
            print(f"\n⚠️  Some configuration values don't match expected defaults")

        return layout_data

    else:
        print(f"❌ Layout config not found at {layout_config_path}")
        print("   Run 'node ../web/extract_layout.js' to generate it")
        return None

if __name__ == "__main__":
    test_config_loading()