#!/usr/bin/env python3
"""
CSS-like layout system for luggage tag - validate positioning and prevent overlaps.
"""

from dataclasses import dataclass
from typing import List, Tuple
import math

@dataclass
class Element:
    """Represents a positioned element on the tag."""
    name: str
    x: float  # center x
    y: float  # center y
    width: float
    height: float
    margin: float = 2.0  # clearance around element

    @property
    def left(self) -> float:
        return self.x - self.width/2 - self.margin

    @property
    def right(self) -> float:
        return self.x + self.width/2 + self.margin

    @property
    def top(self) -> float:
        return self.y + self.height/2 + self.margin

    @property
    def bottom(self) -> float:
        return self.y - self.height/2 - self.margin

    def overlaps_with(self, other: 'Element') -> bool:
        """Check if this element overlaps with another."""
        return not (self.right <= other.left or
                   self.left >= other.right or
                   self.top <= other.bottom or
                   self.bottom >= other.top)

class TagLayout:
    """CSS-like layout manager for luggage tag."""

    def __init__(self, width: float = 85.0, height: float = 54.0):
        self.width = width
        self.height = height
        self.elements: List[Element] = []

        # Define safe zones (like CSS margins)
        self.margin = 4.0
        self.content_left = -width/2 + self.margin
        self.content_right = width/2 - self.margin
        self.content_top = height/2 - self.margin
        self.content_bottom = -height/2 + self.margin

        # Define the strap hole (fixed obstacle)
        self.hole = Element("strap_hole", -width/2 + 12, height/2 - 10, 6, 6, margin=3)

    def add_element(self, element: Element) -> bool:
        """Add element if it fits and doesn't overlap."""
        # Check if element fits within tag bounds
        if (element.left < self.content_left or
            element.right > self.content_right or
            element.top > self.content_top or
            element.bottom < self.content_bottom):
            print(f"❌ {element.name} extends outside content area!")
            return False

        # Check hole overlap
        if element.overlaps_with(self.hole):
            print(f"❌ {element.name} overlaps with strap hole!")
            return False

        # Check overlap with existing elements
        for existing in self.elements:
            if element.overlaps_with(existing):
                print(f"❌ {element.name} overlaps with {existing.name}!")
                return False

        self.elements.append(element)
        print(f"✅ {element.name} positioned at ({element.x:.1f}, {element.y:.1f})")
        return True

    def validate_layout(self) -> bool:
        """Validate entire layout like CSS validator."""
        print("\n🔍 LAYOUT VALIDATION (like CSS validator)")
        print("=" * 50)

        valid = True

        # Check all elements fit
        for element in self.elements:
            if (element.left < self.content_left or
                element.right > self.content_right or
                element.top > self.content_top or
                element.bottom < self.content_bottom):
                print(f"❌ {element.name} exceeds content bounds")
                valid = False

        # Check no overlaps
        for i, elem1 in enumerate(self.elements):
            # Check hole
            if elem1.overlaps_with(self.hole):
                print(f"❌ {elem1.name} overlaps strap hole")
                valid = False

            # Check other elements
            for j, elem2 in enumerate(self.elements[i+1:], i+1):
                if elem1.overlaps_with(elem2):
                    print(f"❌ {elem1.name} overlaps {elem2.name}")
                    valid = False

        if valid:
            print("✅ Layout is valid - no overlaps!")

        return valid

    def print_layout(self):
        """Print layout like CSS inspector."""
        print(f"\n📐 TAG LAYOUT INSPECTOR")
        print("=" * 50)
        print(f"Tag: {self.width}×{self.height}mm")
        print(f"Content area: {self.content_left:.1f} to {self.content_right:.1f} (x), {self.content_bottom:.1f} to {self.content_top:.1f} (y)")
        print(f"Strap hole: center=({self.hole.x:.1f}, {self.hole.y:.1f}), size={self.hole.width}×{self.hole.height}mm")

        print(f"\nElements ({len(self.elements)}):")
        for elem in self.elements:
            print(f"  {elem.name}:")
            print(f"    Position: ({elem.x:.1f}, {elem.y:.1f})")
            print(f"    Size: {elem.width:.1f}×{elem.height:.1f}mm")
            print(f"    Bounds: x={elem.left:.1f} to {elem.right:.1f}, y={elem.bottom:.1f} to {elem.top:.1f}")

def design_optimal_layout() -> TagLayout:
    """Design the optimal layout step by step like CSS."""
    print("🎨 DESIGNING LUGGAGE TAG LAYOUT (CSS-style)")
    print("=" * 50)

    layout = TagLayout(85.0, 54.0)

    # 1. QR Code - largest element, position first (like main content div)
    qr_size = 35.0  # Large enough for 3D printing
    qr_x = layout.content_left + qr_size/2 + 2  # 2mm extra margin
    qr_y = 0  # Center vertically
    qr_element = Element("qr_code", qr_x, qr_y, qr_size, qr_size, margin=2)

    if not layout.add_element(qr_element):
        # Try smaller QR if doesn't fit
        qr_size = 30.0
        qr_element = Element("qr_code", qr_x, qr_y, qr_size, qr_size, margin=2)
        layout.add_element(qr_element)

    # 2. Header text - positioned to avoid hole (like header div)
    header_text = "FOUND MY LUGGAGE?"
    # Calculate text width roughly (12 chars * font_size * 0.6)
    header_width = len(header_text) * 4.5 * 0.6
    header_x = 0  # Center horizontally
    header_y = layout.content_top - 3  # Near top with margin
    header_element = Element("header", header_x, header_y, header_width, 4.5, margin=1)

    if not layout.add_element(header_element):
        # Try moving down if conflicts with hole
        header_y = layout.content_top - 8
        header_element = Element("header", header_x, header_y, header_width, 4.5, margin=1)
        layout.add_element(header_element)

    # 3. Contact info - right side (like sidebar div)
    contact_width = 30  # Estimate for 3 lines
    contact_height = 16  # 3 lines * 5.5 spacing
    contact_x = layout.content_right - contact_width/2
    contact_y = 0  # Center vertically
    contact_element = Element("contact_info", contact_x, contact_y, contact_width, contact_height, margin=2)

    if not layout.add_element(contact_element):
        # Try moving left or adjusting size
        contact_x = qr_x + qr_size/2 + contact_width/2 + 4  # Right of QR
        contact_element = Element("contact_info", contact_x, contact_y, contact_width, contact_height, margin=2)
        layout.add_element(contact_element)

    # 4. Footer - bottom (like footer div)
    footer_text = "SCAN QR OR CALL/TEXT"
    footer_width = len(footer_text) * 3.8 * 0.6
    footer_x = 0  # Center
    footer_y = layout.content_bottom + 3  # Near bottom with margin
    footer_element = Element("footer", footer_x, footer_y, footer_width, 3.8, margin=1)

    layout.add_element(footer_element)

    # Validate the layout
    layout.validate_layout()
    layout.print_layout()

    return layout

if __name__ == "__main__":
    layout = design_optimal_layout()