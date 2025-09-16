#!/usr/bin/env python3
"""
Test script to check what parameters are being passed from releases.py to annotation_transformer.py
"""

import sys
import os
sys.path.append('/workspace/project/veera-2')
sys.path.append('/workspace/project/veera-2/backend')

import sqlite3
from backend.core.annotation_transformer import BoundingBox, Polygon

def test_parameter_passing():
    """Test what parameters would be passed to annotation_transformer.py"""
    
    # Connect to database and get a real annotation
    conn = sqlite3.connect('/workspace/project/veera-2/database.db')
    cursor = conn.cursor()
    
    # Get a specific annotation with high precision coordinates
    cursor.execute('''
    SELECT 
        i.filename, i.width, i.height,
        a.class_name, a.class_id, a.x_min, a.y_min, a.x_max, a.y_max
    FROM images i 
    JOIN annotations a ON i.id = a.image_id 
    WHERE i.filename = 'car_1.jpg'
    LIMIT 1
    ''')
    
    result = cursor.fetchone()
    if not result:
        print("❌ No annotation found for car_1.jpg")
        return
        
    filename, img_width, img_height, class_name, class_id, x_min, y_min, x_max, y_max = result
    
    print("=== REAL DATABASE DATA ===")
    print(f"Image: {filename} ({img_width}x{img_height})")
    print(f"Class: {class_name} (ID: {class_id})")
    print(f"Original coordinates: ({x_min}, {y_min}) to ({x_max}, {y_max})")
    print(f"Coordinate precision: x_min has {len(str(x_min).split('.')[-1]) if '.' in str(x_min) else 0} decimals")
    
    # Simulate the parameter passing from releases.py
    print("\n=== PARAMETER PASSING SIMULATION ===")
    
    # 1. Original dimensions (from PIL image)
    original_dims = (img_width, img_height)  # (300, 168)
    print(f"original_dims: {original_dims}")
    
    # 2. Final dimensions (after transformation)
    final_dims = (240, 240)  # Resize to 240x240
    print(f"final_dims: {final_dims}")
    
    # 3. Transformation config (what gets passed to annotation_transformer.py)
    transformation_config = {
        "resize": {
            "enabled": True,
            "width": final_dims[0],
            "height": final_dims[1], 
            "resize_mode": "stretch_to"
        },
        "rotation": {
            "enabled": True,
            "angle": -23
        },
        "flip": {
            "enabled": True,
            "horizontal": True,
            "vertical": False
        }
    }
    print(f"transformation_config: {transformation_config}")
    
    # 4. Convert DB annotation to BoundingBox (same as releases.py does)
    bbox = BoundingBox(
        x_min=float(x_min),
        y_min=float(y_min),
        x_max=float(x_max),
        y_max=float(y_max),
        class_name=class_name,
        class_id=int(class_id)
    )
    print(f"BoundingBox object: x_min={bbox.x_min}, y_min={bbox.y_min}, x_max={bbox.x_max}, y_max={bbox.y_max}")
    
    # 5. Calculate expected transformations manually
    print("\n=== MANUAL CALCULATION CHECK ===")
    
    # Resize calculation: 300x168 → 240x240
    width_ratio = final_dims[0] / original_dims[0]  # 240/300 = 0.8
    height_ratio = final_dims[1] / original_dims[1]  # 240/168 = 1.4286
    
    print(f"Resize ratios: width_ratio={width_ratio:.6f}, height_ratio={height_ratio:.6f}")
    
    # Apply resize to coordinates
    resized_x_min = x_min * width_ratio
    resized_y_min = y_min * height_ratio
    resized_x_max = x_max * width_ratio
    resized_y_max = y_max * height_ratio
    
    print(f"After resize: ({resized_x_min:.6f}, {resized_y_min:.6f}) to ({resized_x_max:.6f}, {resized_y_max:.6f})")
    
    # Apply horizontal flip: x_new = current_width - x_old
    current_width = final_dims[0]  # 240
    flipped_x_min = current_width - resized_x_max
    flipped_x_max = current_width - resized_x_min
    
    print(f"After horizontal flip: ({flipped_x_min:.6f}, {resized_y_min:.6f}) to ({flipped_x_max:.6f}, {resized_y_max:.6f})")
    
    # Apply rotation: -23 degrees around center
    import math
    angle_rad = math.radians(-23)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    center_x = current_width / 2  # 120
    center_y = final_dims[1] / 2  # 120
    
    print(f"Rotation: angle={-23}°, center=({center_x}, {center_y})")
    print(f"cos({-23}°)={cos_a:.6f}, sin({-23}°)={sin_a:.6f}")
    
    # Rotate all 4 corners
    corners = [
        (flipped_x_min - center_x, resized_y_min - center_y),
        (flipped_x_max - center_x, resized_y_min - center_y),
        (flipped_x_min - center_x, resized_y_max - center_y),
        (flipped_x_max - center_x, resized_y_max - center_y)
    ]
    
    rotated_corners = []
    for (x, y) in corners:
        new_x = x * cos_a - y * sin_a + center_x
        new_y = x * sin_a + y * cos_a + center_y
        rotated_corners.append((new_x, new_y))
    
    # Find new bounding box
    xs = [corner[0] for corner in rotated_corners]
    ys = [corner[1] for corner in rotated_corners]
    final_x_min, final_x_max = min(xs), max(xs)
    final_y_min, final_y_max = min(ys), max(ys)
    
    print(f"After rotation: ({final_x_min:.6f}, {final_y_min:.6f}) to ({final_x_max:.6f}, {final_y_max:.6f})")
    
    conn.close()

if __name__ == "__main__":
    test_parameter_passing()