#!/usr/bin/env python3
"""
Debug the full transformation sequence step by step
"""

import math

def full_manual_calculation():
    """Complete manual calculation of all transformations"""
    print("=== FULL MANUAL TRANSFORMATION SEQUENCE ===")
    
    # Original coordinates from database
    original_x_min, original_y_min = 106.66661071777344, 67.3437385559082
    original_x_max, original_y_max = 205.66661071777344, 140.3437385559082
    
    print(f"Original coordinates: ({original_x_min:.6f}, {original_y_min:.6f}) to ({original_x_max:.6f}, {original_y_max:.6f})")
    
    # Original dimensions
    original_width, original_height = 300, 168
    print(f"Original dimensions: {original_width}x{original_height}")
    
    # STEP 1: RESIZE (300x168 → 240x240)
    print(f"\n--- STEP 1: RESIZE ---")
    target_width, target_height = 240, 240
    width_ratio = target_width / original_width   # 240/300 = 0.8
    height_ratio = target_height / original_height # 240/168 = 1.4286
    
    print(f"Target dimensions: {target_width}x{target_height}")
    print(f"Resize ratios: width_ratio={width_ratio:.6f}, height_ratio={height_ratio:.6f}")
    
    # Apply resize
    resized_x_min = original_x_min * width_ratio
    resized_y_min = original_y_min * height_ratio
    resized_x_max = original_x_max * width_ratio
    resized_y_max = original_y_max * height_ratio
    current_width, current_height = target_width, target_height
    
    print(f"After resize: ({resized_x_min:.6f}, {resized_y_min:.6f}) to ({resized_x_max:.6f}, {resized_y_max:.6f})")
    
    # STEP 2: ROTATION (-23°)
    print(f"\n--- STEP 2: ROTATION ---")
    angle = -23
    angle_rad = math.radians(angle)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    print(f"Rotation angle: {angle}° = {angle_rad:.6f} radians")
    print(f"cos({angle}°) = {cos_a:.6f}, sin({angle}°) = {sin_a:.6f}")
    
    # Rotation around image center
    center_x, center_y = current_width / 2, current_height / 2
    print(f"Rotation center: ({center_x}, {center_y})")
    
    # Transform all 4 corners of bounding box
    corners = [
        (resized_x_min - center_x, resized_y_min - center_y),
        (resized_x_max - center_x, resized_y_min - center_y),
        (resized_x_min - center_x, resized_y_max - center_y),
        (resized_x_max - center_x, resized_y_max - center_y)
    ]
    
    rotated_corners = []
    for (x, y) in corners:
        # Apply rotation matrix
        new_x = x * cos_a - y * sin_a + center_x
        new_y = x * sin_a + y * cos_a + center_y
        rotated_corners.append((new_x, new_y))
    
    # Find new bounding box from rotated corners
    xs = [corner[0] for corner in rotated_corners]
    ys = [corner[1] for corner in rotated_corners]
    rotated_x_min, rotated_x_max = min(xs), max(xs)
    rotated_y_min, rotated_y_max = min(ys), max(ys)
    
    print(f"After rotation: ({rotated_x_min:.6f}, {rotated_y_min:.6f}) to ({rotated_x_max:.6f}, {rotated_y_max:.6f})")
    
    # STEP 3: HORIZONTAL FLIP
    print(f"\n--- STEP 3: HORIZONTAL FLIP ---")
    print(f"Current dimensions: {current_width}x{current_height}")
    
    # Apply horizontal flip: x_new = current_width - x_old
    flipped_x_min = current_width - rotated_x_max
    flipped_x_max = current_width - rotated_x_min
    flipped_y_min = rotated_y_min  # Y coordinates don't change for horizontal flip
    flipped_y_max = rotated_y_max
    
    print(f"After horizontal flip: ({flipped_x_min:.6f}, {flipped_y_min:.6f}) to ({flipped_x_max:.6f}, {flipped_y_max:.6f})")
    
    return flipped_x_min, flipped_y_min, flipped_x_max, flipped_y_max

def annotation_transformer_result():
    """What annotation_transformer.py actually produces"""
    print("\n=== ANNOTATION_TRANSFORMER.PY RESULT ===")
    
    # From the debug output
    result = (47.55653094258406, 80.69635861482952, 161.2081901641845, 207.6377701369345)
    print(f"Final result: ({result[0]:.6f}, {result[1]:.6f}) to ({result[2]:.6f}, {result[3]:.6f})")
    
    return result

if __name__ == "__main__":
    manual_result = full_manual_calculation()
    transformer_result = annotation_transformer_result()
    
    print("\n=== FINAL COMPARISON ===")
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
        print("✅ ALL TRANSFORMATIONS MATCH PERFECTLY!")
    else:
        print("❌ TRANSFORMATIONS DON'T MATCH!")