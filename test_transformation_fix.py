#!/usr/bin/env python3
"""
Test the transformation fixes
"""

import sys
import os
sys.path.append('/workspace/project/veera-1/backend')

from core.annotation_transformer import update_annotations_for_transformations

# Test data - simulate a bounding box on an 800x600 image
test_annotations = [
    {
        'type': 'bbox',
        'class_name': 'car',
        'class_id': 1,
        'x_min': 200.0,  # Left edge
        'y_min': 150.0,  # Top edge  
        'x_max': 600.0,  # Right edge
        'y_max': 450.0   # Bottom edge
    }
]

# Test 1: Resize from 800x600 to 240x240
print("=== TEST 1: RESIZE 800x600 → 240x240 ===")
resize_config = {
    'resize': {
        'enabled': True,
        'width': 240,
        'height': 240,
        'resize_mode': 'stretch_to'
    }
}

result = update_annotations_for_transformations(
    annotations=test_annotations,
    transformation_config=resize_config,
    original_dims=(800, 600),
    new_dims=(240, 240),
    debug_tracking=True
)

print(f"Original bbox: x_min={test_annotations[0]['x_min']}, y_min={test_annotations[0]['y_min']}, x_max={test_annotations[0]['x_max']}, y_max={test_annotations[0]['y_max']}")
if result['annotations']:
    new_bbox = result['annotations'][0]
    print(f"Resized bbox:  x_min={new_bbox['x_min']}, y_min={new_bbox['y_min']}, x_max={new_bbox['x_max']}, y_max={new_bbox['y_max']}")
    
    # Calculate expected values
    scale_x = 240 / 800  # 0.3
    scale_y = 240 / 600  # 0.4
    expected_x_min = 200.0 * scale_x  # 60.0
    expected_y_min = 150.0 * scale_y  # 60.0
    expected_x_max = 600.0 * scale_x  # 180.0
    expected_y_max = 450.0 * scale_y  # 180.0
    
    print(f"Expected bbox: x_min={expected_x_min}, y_min={expected_y_min}, x_max={expected_x_max}, y_max={expected_y_max}")
    print(f"Scale factors: x={scale_x}, y={scale_y}")

print()

# Test 2: Rotation by 90 degrees
print("=== TEST 2: ROTATION 90° ===")
rotation_config = {
    'rotation': {
        'enabled': True,
        'angle': 90
    }
}

result = update_annotations_for_transformations(
    annotations=test_annotations,
    transformation_config=rotation_config,
    original_dims=(800, 600),
    new_dims=(800, 600),  # Same size for rotation
    debug_tracking=True
)

print(f"Original bbox: x_min={test_annotations[0]['x_min']}, y_min={test_annotations[0]['y_min']}, x_max={test_annotations[0]['x_max']}, y_max={test_annotations[0]['y_max']}")
if result['annotations']:
    new_bbox = result['annotations'][0]
    print(f"Rotated bbox: x_min={new_bbox['x_min']:.1f}, y_min={new_bbox['y_min']:.1f}, x_max={new_bbox['x_max']:.1f}, y_max={new_bbox['y_max']:.1f}")

print()

# Test 3: Horizontal flip
print("=== TEST 3: HORIZONTAL FLIP ===")
flip_config = {
    'flip': {
        'enabled': True,
        'horizontal': True,
        'vertical': False
    }
}

result = update_annotations_for_transformations(
    annotations=test_annotations,
    transformation_config=flip_config,
    original_dims=(800, 600),
    new_dims=(800, 600),
    debug_tracking=True
)

print(f"Original bbox: x_min={test_annotations[0]['x_min']}, y_min={test_annotations[0]['y_min']}, x_max={test_annotations[0]['x_max']}, y_max={test_annotations[0]['y_max']}")
if result['annotations']:
    new_bbox = result['annotations'][0]
    print(f"Flipped bbox:  x_min={new_bbox['x_min']}, y_min={new_bbox['y_min']}, x_max={new_bbox['x_max']}, y_max={new_bbox['y_max']}")
    
    # For horizontal flip, x coordinates should be: new_x = width - old_x
    # So x_min=200 becomes 800-600=200, x_max=600 becomes 800-200=600
    # Wait, that's wrong. Let me recalculate:
    # For horizontal flip: new_x_min = width - old_x_max, new_x_max = width - old_x_min
    expected_x_min = 800 - 600  # 200
    expected_x_max = 800 - 200  # 600
    print(f"Expected bbox: x_min={expected_x_min}, y_min={test_annotations[0]['y_min']}, x_max={expected_x_max}, y_max={test_annotations[0]['y_max']}")