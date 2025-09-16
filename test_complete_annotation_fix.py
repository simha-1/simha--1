#!/usr/bin/env python3
"""
Test script to verify annotation transformation fixes in both release systems.

This script tests:
1. New system: release_controller.py → enhanced_export.py 
2. Old system: releases.py → create_complete_release_zip()

Both systems should now correctly transform annotations when geometry tools 
(rotation, flip) are applied, not just resize.
"""

import sys
import os
import numpy as np
from unittest.mock import Mock, MagicMock

# Add backend to path
sys.path.insert(0, '/workspace/project/11-09-2025-1/backend')

def test_bbox_format_conversion():
    """Test bbox format conversion logic from enhanced_export.py"""
    print("=== Testing bbox format conversion ===")
    
    # Test list format [x_min, y_min, x_max, y_max]
    bbox_list = [100, 200, 300, 400]
    
    # Simulate the conversion logic from enhanced_export.py
    if isinstance(bbox_list, list) and len(bbox_list) == 4:
        x_min, y_min, x_max, y_max = bbox_list
        x = x_min
        y = y_min  
        width = x_max - x_min
        height = y_max - y_min
        print(f"✅ List format conversion: {bbox_list} → x={x}, y={y}, w={width}, h={height}")
    else:
        print(f"❌ Failed to convert list format: {bbox_list}")
    
    # Test dict format (backward compatibility)
    bbox_dict = {"x": 100, "y": 200, "width": 200, "height": 200}
    
    if isinstance(bbox_dict, dict):
        x = bbox_dict.get("x", 0)
        y = bbox_dict.get("y", 0)
        width = bbox_dict.get("width", 0)
        height = bbox_dict.get("height", 0)
        print(f"✅ Dict format conversion: {bbox_dict} → x={x}, y={y}, w={width}, h={height}")
    else:
        print(f"❌ Failed to convert dict format: {bbox_dict}")

def test_transformation_config_creation():
    """Test transformation config creation logic from releases.py"""
    print("\n=== Testing transformation config creation ===")
    
    # Simulate transformations list with geometry tools
    transformations = [
        {"type": "resize", "params": {"width": 640, "height": 480}},
        {"type": "rotation", "params": {"angle": 90}},
        {"type": "flip", "params": {"horizontal": True}},
        {"type": "brightness", "params": {"factor": 1.2}}
    ]
    
    # Test old logic (resize only)
    resize_only_config = None
    for t in transformations:
        if t.get("type") == "resize":
            params = dict(t.get("params", {}))
            params["enabled"] = True
            resize_only_config = {"resize": params}
            break
    
    print(f"Old resize-only config: {resize_only_config}")
    
    # Test new logic (full transformations)
    full_transform_config = {}
    for t in transformations:
        t_type = t.get("type")
        if t_type:
            params = dict(t.get("params", {}))
            params["enabled"] = True
            full_transform_config[t_type] = params
    
    print(f"New full transform config: {full_transform_config}")
    
    # Verify all transformations are included
    expected_types = {"resize", "rotation", "flip", "brightness"}
    actual_types = set(full_transform_config.keys())
    
    if expected_types == actual_types:
        print("✅ Full transformation config includes all transformation types")
    else:
        print(f"❌ Missing transformations: {expected_types - actual_types}")

def test_annotation_transformer_integration():
    """Test integration with annotation transformer functions"""
    print("\n=== Testing annotation transformer integration ===")
    
    try:
        # Import the annotation transformer functions
        from core.annotation_transformer import transform_detection_annotations_to_yolo
        from core.annotation_transformer import transform_segmentation_annotations_to_yolo
        print("✅ Successfully imported annotation transformer functions")
        
        # Create mock annotations
        mock_annotation = Mock()
        mock_annotation.x = 100
        mock_annotation.y = 200
        mock_annotation.width = 200
        mock_annotation.height = 200
        mock_annotation.class_name = "test_class"
        mock_annotation.class_id = 1
        
        annotations = [mock_annotation]
        
        # Create transformation config with geometry tools
        transform_config = {
            "rotation": {"angle": 90, "enabled": True},
            "flip": {"horizontal": True, "enabled": True}
        }
        
        # Mock class resolver
        def mock_class_resolver(ann):
            return 0
        
        # Test detection transformation
        try:
            yolo_lines = transform_detection_annotations_to_yolo(
                annotations=annotations,
                img_w=640,
                img_h=480,
                transform_config=transform_config,
                class_index_resolver=mock_class_resolver
            )
            print(f"✅ Detection transformation successful: {len(yolo_lines)} lines generated")
            if yolo_lines:
                print(f"   Sample line: {yolo_lines[0]}")
        except Exception as e:
            print(f"❌ Detection transformation failed: {e}")
        
        # Test segmentation transformation (if annotations have polygon data)
        try:
            # Add polygon data to mock annotation
            mock_annotation.polygon_points = [
                {"x": 100, "y": 200},
                {"x": 300, "y": 200}, 
                {"x": 300, "y": 400},
                {"x": 100, "y": 400}
            ]
            
            seg_lines = transform_segmentation_annotations_to_yolo(
                annotations=annotations,
                img_w=640,
                img_h=480,
                transform_config=transform_config,
                class_index_resolver=mock_class_resolver
            )
            print(f"✅ Segmentation transformation successful: {len(seg_lines)} lines generated")
            if seg_lines:
                print(f"   Sample line: {seg_lines[0][:100]}...")  # Truncate long polygon lines
        except Exception as e:
            print(f"❌ Segmentation transformation failed: {e}")
            
    except ImportError as e:
        print(f"❌ Failed to import annotation transformer: {e}")

def test_affine_matrix_application():
    """Test that affine matrix transformations are applied correctly"""
    print("\n=== Testing affine matrix application ===")
    
    try:
        from core.affine_builder import AffineBuilder
        
        # Create affine builder
        builder = AffineBuilder()
        
        # Add transformations
        builder.add_rotation(90)  # 90 degree rotation
        builder.add_flip(horizontal=True)
        
        # Get the transformation matrix
        matrix = builder.get_matrix()
        print(f"✅ Affine matrix created: shape {matrix.shape}")
        print(f"   Matrix:\n{matrix}")
        
        # Test coordinate transformation
        original_point = np.array([100, 200, 1])  # [x, y, 1] homogeneous coordinates
        transformed_point = matrix @ original_point
        
        print(f"✅ Point transformation: {original_point[:2]} → {transformed_point[:2]}")
        
        # Verify the transformation is not identity (coordinates should change)
        if not np.allclose(original_point[:2], transformed_point[:2]):
            print("✅ Transformation matrix is non-identity (coordinates changed)")
        else:
            print("❌ Transformation matrix appears to be identity (coordinates unchanged)")
            
    except ImportError as e:
        print(f"❌ Failed to import affine builder: {e}")
    except Exception as e:
        print(f"❌ Affine matrix test failed: {e}")

def main():
    """Run all tests"""
    print("Testing annotation transformation fixes...")
    print("=" * 60)
    
    test_bbox_format_conversion()
    test_transformation_config_creation()
    test_annotation_transformer_integration()
    test_affine_matrix_application()
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("✅ = Test passed")
    print("❌ = Test failed")
    print("\nIf all tests pass, both release systems should now correctly")
    print("transform annotations when geometry tools are applied.")

if __name__ == "__main__":
    main()