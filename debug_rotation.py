#!/usr/bin/env python3
"""
Debug the rotation calculation step by step
"""

import math

def manual_rotation_calculation():
    """Manual rotation calculation"""
    print("=== MANUAL ROTATION CALCULATION ===")
    
    # After resize: (85.333289, 96.205341) to (164.533289, 200.491055)
    x_min, y_min = 85.33328857421876, 96.20534079415458
    x_max, y_max = 164.53328857421877, 200.49105507986886
    
    # Current dimensions after resize
    current_width, current_height = 240, 240
    
    # Rotation parameters
    angle = -23
    angle_rad = math.radians(angle)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    print(f"Input coordinates: ({x_min:.6f}, {y_min:.6f}) to ({x_max:.6f}, {y_max:.6f})")
    print(f"Current dimensions: {current_width}x{current_height}")
    print(f"Rotation angle: {angle}° = {angle_rad:.6f} radians")
    print(f"cos({angle}°) = {cos_a:.6f}")
    print(f"sin({angle}°) = {sin_a:.6f}")
    
    # Rotation around image center
    center_x, center_y = current_width / 2, current_height / 2
    print(f"Rotation center: ({center_x}, {center_y})")
    
    # Transform all 4 corners of bounding box
    corners = [
        (x_min - center_x, y_min - center_y),
        (x_max - center_x, y_min - center_y),
        (x_min - center_x, y_max - center_y),
        (x_max - center_x, y_max - center_y)
    ]
    
    print(f"Corners relative to center:")
    for i, (x, y) in enumerate(corners):
        print(f"  Corner {i+1}: ({x:.6f}, {y:.6f})")
    
    rotated_corners = []
    for i, (x, y) in enumerate(corners):
        # Apply rotation matrix
        new_x = x * cos_a - y * sin_a + center_x
        new_y = x * sin_a + y * cos_a + center_y
        rotated_corners.append((new_x, new_y))
        print(f"  Rotated corner {i+1}: ({new_x:.6f}, {new_y:.6f})")
    
    # Find new bounding box from rotated corners
    xs = [corner[0] for corner in rotated_corners]
    ys = [corner[1] for corner in rotated_corners]
    new_x_min, new_x_max = min(xs), max(xs)
    new_y_min, new_y_max = min(ys), max(ys)
    
    print(f"Final rotated bbox: ({new_x_min:.6f}, {new_y_min:.6f}) to ({new_x_max:.6f}, {new_y_max:.6f})")
    
    return new_x_min, new_y_min, new_x_max, new_y_max

def annotation_transformer_rotation():
    """What annotation_transformer.py actually produces"""
    print("\n=== ANNOTATION_TRANSFORMER.PY RESULT ===")
    
    # From the debug output
    result = (78.79180983581553, 80.69635861482952, 192.44346905741594, 207.6377701369345)
    print(f"Annotation transformer result: ({result[0]:.6f}, {result[1]:.6f}) to ({result[2]:.6f}, {result[3]:.6f})")
    
    return result

if __name__ == "__main__":
    manual_result = manual_rotation_calculation()
    transformer_result = annotation_transformer_rotation()
    
    print("\n=== COMPARISON ===")
    print(f"Manual calculation:      ({manual_result[0]:.6f}, {manual_result[1]:.6f}) to ({manual_result[2]:.6f}, {manual_result[3]:.6f})")
    print(f"Annotation transformer:  ({transformer_result[0]:.6f}, {transformer_result[1]:.6f}) to ({transformer_result[2]:.6f}, {transformer_result[3]:.6f})")
    
    # Calculate differences
    diff_x_min = abs(manual_result[0] - transformer_result[0])
    diff_y_min = abs(manual_result[1] - transformer_result[1])
    diff_x_max = abs(manual_result[2] - transformer_result[2])
    diff_y_max = abs(manual_result[3] - transformer_result[3])
    
    print(f"Differences: x_min={diff_x_min:.6f}, y_min={diff_y_min:.6f}, x_max={diff_x_max:.6f}, y_max={diff_y_max:.6f}")
    
    tolerance = 0.001
    if all(diff < tolerance for diff in [diff_x_min, diff_y_min, diff_x_max, diff_y_max]):
        print("✅ ROTATION CALCULATIONS MATCH!")
    else:
        print("❌ ROTATION CALCULATIONS DON'T MATCH!")