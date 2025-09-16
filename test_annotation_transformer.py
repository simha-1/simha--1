#!/usr/bin/env python3
"""
Test annotation_transformer.py with the exact parameters from releases.py
"""

import sys
import os
sys.path.append('/workspace/project/veera-2')
sys.path.append('/workspace/project/veera-2/backend')

from backend.core.annotation_transformer import update_annotations_for_transformations, BoundingBox

def test_annotation_transformer():
    """Test annotation_transformer.py with exact parameters from releases.py"""
    
    print("=== TESTING ANNOTATION_TRANSFORMER.PY ===")
    
    # Real data from database (car_1.jpg)
    original_coords = (106.66661071777344, 67.3437385559082, 205.66661071777344, 140.3437385559082)
    print(f"Original coordinates: {original_coords}")
    
    # Create BoundingBox object (same as releases.py does)
    bbox = BoundingBox(
        x_min=original_coords[0],
        y_min=original_coords[1],
        x_max=original_coords[2],
        y_max=original_coords[3],
        class_name="green car",
        class_id=11
    )
    
    # Parameters passed from releases.py
    transformation_config = {
        "resize": {
            "enabled": True,
            "width": 240,
            "height": 240,
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
    
    original_dims = (300, 168)  # car_1.jpg dimensions
    new_dims = (240, 240)       # final dimensions
    
    print(f"transformation_config: {transformation_config}")
    print(f"original_dims: {original_dims}")
    print(f"new_dims: {new_dims}")
    
    # Call annotation_transformer.py (same as releases.py does)
    try:
        transformed_annotations, debug_info = update_annotations_for_transformations(
            annotations=[bbox],
            transformation_config=transformation_config,
            original_dims=original_dims,
            new_dims=new_dims,
            affine_matrix=None,
            debug_tracking=True
        )
        
        print(f"\n=== ANNOTATION_TRANSFORMER.PY RESULTS ===")
        print(f"Number of transformed annotations: {len(transformed_annotations)}")
        
        if transformed_annotations:
            result = transformed_annotations[0]
            print(f"Transformed coordinates: ({result.x_min:.6f}, {result.y_min:.6f}) to ({result.x_max:.6f}, {result.y_max:.6f})")
            
            # Compare with manual calculation
            expected = (69.709578, 84.551537, 183.361237, 211.492949)
            actual = (result.x_min, result.y_min, result.x_max, result.y_max)
            
            print(f"\n=== COMPARISON ===")
            print(f"Expected (manual): ({expected[0]:.6f}, {expected[1]:.6f}) to ({expected[2]:.6f}, {expected[3]:.6f})")
            print(f"Actual (transformer): ({actual[0]:.6f}, {actual[1]:.6f}) to ({actual[2]:.6f}, {actual[3]:.6f})")
            
            # Check differences
            diff_x_min = abs(expected[0] - actual[0])
            diff_y_min = abs(expected[1] - actual[1])
            diff_x_max = abs(expected[2] - actual[2])
            diff_y_max = abs(expected[3] - actual[3])
            
            print(f"Differences: x_min={diff_x_min:.6f}, y_min={diff_y_min:.6f}, x_max={diff_x_max:.6f}, y_max={diff_y_max:.6f}")
            
            tolerance = 0.001
            if all(diff < tolerance for diff in [diff_x_min, diff_y_min, diff_x_max, diff_y_max]):
                print("✅ RESULTS MATCH! Transformation is working correctly.")
            else:
                print("❌ RESULTS DON'T MATCH! There's a bug in the transformation.")
                
                # Check individual transformations
                print(f"\n=== DEBUG INFO ===")
                if debug_info and 'annotation_steps' in debug_info:
                    for step in debug_info['annotation_steps'][0].get('transformation_steps', []):
                        print(f"Step {step.get('step', '?')}: {step.get('transform_name', '?')} -> {step.get('after_coords', '?')}")
        else:
            print("❌ NO TRANSFORMED ANNOTATIONS RETURNED!")
            
        # Print debug info
        if debug_info:
            print(f"\n=== DEBUG INFO ===")
            print(f"Debug keys: {list(debug_info.keys())}")
            if 'annotation_steps' in debug_info and debug_info['annotation_steps']:
                ann_debug = debug_info['annotation_steps'][0]
                print(f"Annotation debug keys: {list(ann_debug.keys())}")
                if 'transformation_steps' in ann_debug:
                    print(f"Number of transformation steps: {len(ann_debug['transformation_steps'])}")
                    for i, step in enumerate(ann_debug['transformation_steps']):
                        print(f"  Step {i}: {step}")
        
    except Exception as e:
        print(f"❌ ERROR calling annotation_transformer: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_annotation_transformer()