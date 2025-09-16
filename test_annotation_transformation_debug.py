#!/usr/bin/env python3
"""
Test script to debug annotation transformation issues.
This will help us understand why annotations are getting original coordinates.
"""

import sys
import os
sys.path.append('/workspace/project/veera-1')
sys.path.append('/workspace/project/veera-1/backend')

from backend.core.annotation_transformer import update_annotations_for_transformations, BoundingBox, Polygon
import json

def test_annotation_transformation():
    """Test the annotation transformation with simple data"""
    
    print("🔍 TESTING ANNOTATION TRANSFORMATION")
    print("=" * 50)
    
    # Create test annotation (bounding box)
    test_bbox = BoundingBox(
        x_min=100.0,
        y_min=50.0, 
        x_max=200.0,
        y_max=150.0,
        class_name="car",
        class_id=1
    )
    
    # Create test transformation config (simple resize)
    transformation_config = {
        "resize": {
            "enabled": True,
            "width": 640,
            "height": 480,
            "resize_mode": "stretch_to"
        }
    }
    
    original_dims = (1024, 768)  # Original image size
    new_dims = (640, 480)        # Target image size
    
    print(f"📊 TEST DATA:")
    print(f"   Original BBox: ({test_bbox.x_min}, {test_bbox.y_min}, {test_bbox.x_max}, {test_bbox.y_max})")
    print(f"   Original dims: {original_dims}")
    print(f"   New dims: {new_dims}")
    print(f"   Transformation: {transformation_config}")
    print()
    
    # Test with debug tracking enabled
    print("🚀 RUNNING TRANSFORMATION...")
    try:
        transformed_annotations, debug_info = update_annotations_for_transformations(
            annotations=[test_bbox],
            transformation_config=transformation_config,
            original_dims=original_dims,
            new_dims=new_dims,
            affine_matrix=None,  # Use legacy sequential path
            debug_tracking=True
        )
        
        print("✅ TRANSFORMATION COMPLETED")
        print(f"   Input count: 1")
        print(f"   Output count: {len(transformed_annotations)}")
        
        if transformed_annotations:
            result_bbox = transformed_annotations[0]
            print(f"   Result BBox: ({result_bbox.x_min}, {result_bbox.y_min}, {result_bbox.x_max}, {result_bbox.y_max})")
            
            # Calculate expected coordinates
            width_ratio = new_dims[0] / original_dims[0]  # 640/1024 = 0.625
            height_ratio = new_dims[1] / original_dims[1]  # 480/768 = 0.625
            
            expected_x_min = test_bbox.x_min * width_ratio   # 100 * 0.625 = 62.5
            expected_y_min = test_bbox.y_min * height_ratio  # 50 * 0.625 = 31.25
            expected_x_max = test_bbox.x_max * width_ratio   # 200 * 0.625 = 125.0
            expected_y_max = test_bbox.y_max * height_ratio  # 150 * 0.625 = 93.75
            
            print(f"   Expected BBox: ({expected_x_min}, {expected_y_min}, {expected_x_max}, {expected_y_max})")
            
            # Check if transformation worked
            if (abs(result_bbox.x_min - expected_x_min) < 0.1 and 
                abs(result_bbox.y_min - expected_y_min) < 0.1 and
                abs(result_bbox.x_max - expected_x_max) < 0.1 and
                abs(result_bbox.y_max - expected_y_max) < 0.1):
                print("✅ COORDINATES TRANSFORMED CORRECTLY!")
            else:
                print("❌ COORDINATES NOT TRANSFORMED - USING ORIGINAL VALUES!")
        
        # Save debug info to JSON
        debug_file = "/workspace/project/veera-1/annotation_transformation_debug.json"
        with open(debug_file, 'w') as f:
            json.dump(debug_info, f, indent=2)
        print(f"📄 Debug info saved to: {debug_file}")
        
    except Exception as e:
        print(f"❌ TRANSFORMATION FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_annotation_transformation()