#!/usr/bin/env python
"""
Create a sample DXF floorplan with 6 booth rectangles for testing.
This script generates a simple test file that can be uploaded to the application.

Usage:
    python backend/create_sample_dxf.py
"""

import os
import ezdxf
from pathlib import Path

def create_sample_floorplan():
    """
    Create a sample DXF file with 6 rectangular booths arranged in 2 rows.

    Layout:
        A-1      A-2      A-3
        B-1      B-2      B-3
    """

    # Create new DXF document
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()

    # Booth dimensions (must be 50-5000 sq ft per processor threshold)
    # 60 x 50 = 3000 sq ft (fits within 50-5000 range)
    booth_width = 60
    booth_height = 50
    spacing = 10  # Gap between booths

    print("Generating sample floorplan with 6 booths...")

    # Create booths in 2 rows x 3 columns
    for row in range(2):
        for col in range(3):
            # Calculate booth position
            x = col * (booth_width + spacing)
            y = row * (booth_height + spacing)

            # Create booth as a closed polyline (rectangle)
            points = [
                (x, y),
                (x + booth_width, y),
                (x + booth_width, y + booth_height),
                (x, y + booth_height),
                (x, y)  # Close the polyline
            ]

            # Add polyline to represent booth
            polyline = msp.add_lwpolyline(points)
            polyline.close(True)

            # Generate booth ID (A-1, A-2, etc.)
            booth_id = f"{chr(65 + row)}-{col + 1}"

            # Add text label with booth ID
            center_x = x + booth_width / 2
            center_y = y + booth_height / 2

            text = msp.add_text(booth_id, dxfattribs={
                'insert': (center_x, center_y),
                'height': 15,
                'halign': 1,  # Center horizontal
                'valign': 1   # Center vertical
            })

            print(f"  Created booth: {booth_id} at ({x:.0f}, {y:.0f})")

    # Create output directory if it doesn't exist
    output_dir = Path(__file__).parent / '..' / 'data' / 'sample'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save the DXF file
    output_path = output_dir / 'test_floorplan.dxf'
    doc.saveas(str(output_path))

    print(f"\n✅ Sample floorplan created successfully!")
    print(f"📁 File saved to: {output_path}")
    print(f"\nTo test the application:")
    print(f"1. Start the Flask server: python backend/app.py")
    print(f"2. Open http://localhost:5000 in your browser")
    print(f"3. Upload the file: {output_path}")
    print(f"4. You should see 6 booths appear on the map (A-1 through B-3)")

if __name__ == '__main__':
    create_sample_floorplan()
