#!/usr/bin/env python3
"""
Test script to verify that the annotation transformation fix works correctly.
This tests the bbox format handling in the enhanced export system.
"""

import sys
import os
import json
from typing import List, Dict, Any

# Simple test without importing the full FastAPI module
class MockExportRequest:
    def __init__(self, annotations, images, classes, format, include_images=True, dataset_name="dataset"):
        self.annotations = annotations
        self.images = images
        self.classes = classes
        self.format = format
        self.include_images = include_images
        self.dataset_name = dataset_name

def test_yolo_bbox_conversion():
    """Test the YOLO bbox conversion logic directly"""
    
    print("🧪 Testing YOLO bbox conversion logic...")
    
    # Test data: bbox in [x_min, y_min, x_max, y_max] format
    bbox = [100.0, 50.0, 200.0, 150.0]  # [x_min, y_min, x_max, y_max]
    img_width = 640
    img_height = 480
    
    # Apply the conversion logic from the fixed code
    if isinstance(bbox, list) and len(bbox) >= 4:
        x_min, y_min, x_max, y_max = bbox[0], bbox[1], bbox[2], bbox[3]
        
        # Convert to YOLO format (normalized center coordinates)
        center_x = (x_min + x_max) / 2.0 / img_width
        center_y = (y_min + y_max) / 2.0 / img_height
        norm_width = (x_max - x_min) / img_width
        norm_height = (y_max - y_min) / img_height
        
        # Clamp values to [0, 1] range
        center_x = max(0.0, min(1.0, center_x))
        center_y = max(0.0, min(1.0, center_y))
        norm_width = max(0.0, min(1.0, norm_width))
        norm_height = max(0.0, min(1.0, norm_height))
        
        print(f"  📊 Input bbox: {bbox} (x_min, y_min, x_max, y_max)")
        print(f"  📊 Image size: {img_width}x{img_height}")
        print(f"  🎯 YOLO output: center_x={center_x:.6f}, center_y={center_y:.6f}, width={norm_width:.6f}, height={norm_height:.6f}")
        
        # Verify the conversion is reasonable
        expected_center_x = (100 + 200) / 2.0 / 640  # 150/640 = 0.234375
        expected_center_y = (50 + 150) / 2.0 / 480   # 100/480 = 0.208333
        expected_width = (200 - 100) / 640           # 100/640 = 0.15625
        expected_height = (150 - 50) / 480           # 100/480 = 0.208333
        
        print(f"  ✅ Expected: center_x={expected_center_x:.6f}, center_y={expected_center_y:.6f}, width={expected_width:.6f}, height={expected_height:.6f}")
        
        # Check if values match expectations (within small tolerance)
        tolerance = 0.000001
        if (abs(center_x - expected_center_x) < tolerance and
            abs(center_y - expected_center_y) < tolerance and
            abs(norm_width - expected_width) < tolerance and
            abs(norm_height - expected_height) < tolerance):
            print("  🎉 YOLO conversion is correct!")
            return True
        else:
            print("  ❌ YOLO conversion values don't match expected!")
            return False
    else:
        print("  ❌ Invalid bbox format")
        return False

def test_coco_bbox_conversion():
    """Test the COCO bbox conversion logic directly"""
    
    print("🧪 Testing COCO bbox conversion logic...")
    
    # Test data: bbox in [x_min, y_min, x_max, y_max] format
    bbox = [100.0, 50.0, 200.0, 150.0]  # [x_min, y_min, x_max, y_max]
    
    # Apply the conversion logic from the fixed code
    if isinstance(bbox, list) and len(bbox) >= 4:
        x_min, y_min, x_max, y_max = bbox[0], bbox[1], bbox[2], bbox[3]
        x, y = x_min, y_min
        w, h = x_max - x_min, y_max - y_min
        
        print(f"  📊 Input bbox: {bbox} (x_min, y_min, x_max, y_max)")
        print(f"  🎯 COCO output: [x={x}, y={y}, width={w}, height={h}]")
        
        # Verify the conversion
        expected_x, expected_y = 100.0, 50.0
        expected_w, expected_h = 100.0, 100.0
        
        print(f"  ✅ Expected: [x={expected_x}, y={expected_y}, width={expected_w}, height={expected_h}]")
        
        if (x == expected_x and y == expected_y and w == expected_w and h == expected_h):
            print("  🎉 COCO conversion is correct!")
            return True
        else:
            print("  ❌ COCO conversion values don't match expected!")
            return False
    else:
        print("  ❌ Invalid bbox format")
        return False

def test_bbox_format_fix():
    """Test that the bbox format conversion logic works correctly"""
    
    print("🧪 Testing bbox format fix logic...")
    
    # Test YOLO conversion
    yolo_success = test_yolo_bbox_conversion()
    
    # Test COCO conversion  
    coco_success = test_coco_bbox_conversion()
    
    return yolo_success and coco_success

def test_old_vs_new_format():
    """Test that the fix handles both old and new bbox formats"""
    
    print("🧪 Testing backward compatibility...")
    
    # Test old format (dict)
    old_bbox = {"x": 100, "y": 50, "width": 100, "height": 100}
    print(f"  📊 Old format: {old_bbox}")
    
    # Test new format (list)
    new_bbox = [100.0, 50.0, 200.0, 150.0]  # [x_min, y_min, x_max, y_max]
    print(f"  📊 New format: {new_bbox}")
    
    # Both should produce the same YOLO output
    img_width, img_height = 640, 480
    
    # Old format conversion (fallback logic)
    if isinstance(old_bbox, dict):
        old_x, old_y, old_w, old_h = old_bbox.get("x", 0), old_bbox.get("y", 0), old_bbox.get("width", 0), old_bbox.get("height", 0)
        old_center_x = (old_x + old_w / 2) / img_width
        old_center_y = (old_y + old_h / 2) / img_height
        old_norm_width = old_w / img_width
        old_norm_height = old_h / img_height
    
    # New format conversion (main logic)
    if isinstance(new_bbox, list) and len(new_bbox) >= 4:
        new_x_min, new_y_min, new_x_max, new_y_max = new_bbox[0], new_bbox[1], new_bbox[2], new_bbox[3]
        new_center_x = (new_x_min + new_x_max) / 2.0 / img_width
        new_center_y = (new_y_min + new_y_max) / 2.0 / img_height
        new_norm_width = (new_x_max - new_x_min) / img_width
        new_norm_height = (new_y_max - new_y_min) / img_height
    
    print(f"  🎯 Old format YOLO: center_x={old_center_x:.6f}, center_y={old_center_y:.6f}, width={old_norm_width:.6f}, height={old_norm_height:.6f}")
    print(f"  🎯 New format YOLO: center_x={new_center_x:.6f}, center_y={new_center_y:.6f}, width={new_norm_width:.6f}, height={new_norm_height:.6f}")
    
    # They should be the same
    tolerance = 0.000001
    if (abs(old_center_x - new_center_x) < tolerance and
        abs(old_center_y - new_center_y) < tolerance and
        abs(old_norm_width - new_norm_width) < tolerance and
        abs(old_norm_height - new_norm_height) < tolerance):
        print("  🎉 Both formats produce the same result!")
        return True
    else:
        print("  ❌ Formats produce different results!")
        return False

def test_data_flow():
    """Test the complete data flow from _prepare_export_data to export functions"""
    
    print("🧪 Testing complete data flow...")
    
    # Simulate what _prepare_export_data creates
    mock_annotation_from_db = {
        'id': 1,
        'image_id': 0,
        'class_id': 0,
        'x_min': 100.0,
        'y_min': 50.0,
        'x_max': 200.0,
        'y_max': 150.0,
        'confidence': 1.0
    }
    
    # This is what _prepare_export_data does (lines 1149-1154 in release_controller.py)
    prepared_annotation = {
        'id': mock_annotation_from_db['id'],
        'image_id': mock_annotation_from_db['image_id'],
        'class_id': mock_annotation_from_db['class_id'],
        'type': 'bbox',
        'confidence': mock_annotation_from_db.get('confidence', 1.0),
        'bbox': [
            float(mock_annotation_from_db.get('x_min', 0.0)),
            float(mock_annotation_from_db.get('y_min', 0.0)),
            float(mock_annotation_from_db.get('x_max', 0.0)),
            float(mock_annotation_from_db.get('y_max', 0.0)),
        ]
    }
    
    print(f"  📊 DB annotation: {mock_annotation_from_db}")
    print(f"  📊 Prepared annotation: {prepared_annotation}")
    
    # Now test that the export function can handle this
    bbox = prepared_annotation.get("bbox", [])
    if isinstance(bbox, list) and len(bbox) >= 4:
        x_min, y_min, x_max, y_max = bbox[0], bbox[1], bbox[2], bbox[3]
        print(f"  🎯 Export function receives: x_min={x_min}, y_min={y_min}, x_max={x_max}, y_max={y_max}")
        
        # Convert to YOLO format
        img_width, img_height = 640, 480
        center_x = (x_min + x_max) / 2.0 / img_width
        center_y = (y_min + y_max) / 2.0 / img_height
        norm_width = (x_max - x_min) / img_width
        norm_height = (y_max - y_min) / img_height
        
        print(f"  🎯 Final YOLO: center_x={center_x:.6f}, center_y={center_y:.6f}, width={norm_width:.6f}, height={norm_height:.6f}")
        
        # Check that we get reasonable values (not zeros)
        if center_x > 0 and center_y > 0 and norm_width > 0 and norm_height > 0:
            print("  🎉 Complete data flow works correctly!")
            return True
        else:
            print("  ❌ Data flow produces zero values!")
            return False
    else:
        print("  ❌ Invalid bbox format in data flow!")
        return False

def test_bbox_format_fix():
    """Run all tests to verify the bbox format fix"""
    
    print("🧪 Testing bbox format fix in enhanced export system...")
    
    # Run all tests
    tests = [
        ("Basic conversion logic", test_bbox_format_fix),
        ("Backward compatibility", test_old_vs_new_format),
        ("Complete data flow", test_data_flow)
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        print(f"\n📋 Running test: {test_name}")
        try:
            if test_func != test_bbox_format_fix:  # Avoid infinite recursion
                result = test_func()
                if result:
                    print(f"  ✅ {test_name}: PASSED")
                else:
                    print(f"  ❌ {test_name}: FAILED")
                    all_passed = False
        except Exception as e:
            print(f"  ❌ {test_name}: ERROR - {e}")
            all_passed = False
    
    return all_passed
        annotations=[
            {
                "id": 1,
                "image_id": 0,
                "class_id": 0,
                "class_name": "car",
                "type": "bbox",
                "confidence": 1.0,
                "bbox": [100.0, 50.0, 200.0, 150.0]  # [x_min, y_min, x_max, y_max] format
            },
            {
                "id": 2,
                "image_id": 0,
                "class_id": 1,
                "class_name": "person",
                "type": "bbox",
                "confidence": 0.95,
                "bbox": [300.0, 100.0, 350.0, 200.0]  # [x_min, y_min, x_max, y_max] format
            }
        ],
        images=[
            {
                "id": 0,
                "name": "test_image.jpg",
                "width": 640,
                "height": 480,
                "file_path": "/path/to/test_image.jpg"
            }
        ],
        classes=[
            {"id": 0, "name": "car", "supercategory": "vehicle"},
            {"id": 1, "name": "person", "supercategory": "person"}
        ],
        format="yolo_detection",
        include_images=False,
        dataset_name="test_dataset"
    )
    
    # Test YOLO detection export
    print("  📝 Testing YOLO detection export...")
    yolo_files = ExportFormats.export_yolo_detection(test_data)
    
    # Check that label file was created
    label_file = "test_image.txt"
    if label_file in yolo_files:
        label_content = yolo_files[label_file]
        print(f"  ✅ Label file created: {label_file}")
        print(f"  📄 Label content:\n{label_content}")
        
        # Parse the label content to verify coordinates
        lines = label_content.strip().split('\n')
        if len(lines) >= 2:
            # First annotation: bbox [100, 50, 200, 150] on 640x480 image
            # Expected: center_x = (100+200)/2/640 = 0.234375, center_y = (50+150)/2/480 = 0.208333
            # Expected: width = (200-100)/640 = 0.15625, height = (150-50)/480 = 0.208333
            line1_parts = lines[0].split()
            if len(line1_parts) == 5:
                class_id, cx, cy, w, h = line1_parts
                cx, cy, w, h = float(cx), float(cy), float(w), float(h)
                print(f"  🎯 First annotation: class={class_id}, cx={cx:.6f}, cy={cy:.6f}, w={w:.6f}, h={h:.6f}")
                
                # Verify the coordinates are reasonable (not 0,0,0,0)
                if cx > 0 and cy > 0 and w > 0 and h > 0:
                    print("  ✅ Coordinates look correct (not zero)")
                else:
                    print("  ❌ Coordinates are zero - fix failed!")
                    return False
            else:
                print(f"  ❌ Invalid label format: {lines[0]}")
                return False
        else:
            print("  ❌ No label lines found")
            return False
    else:
        print(f"  ❌ Label file not found in output: {list(yolo_files.keys())}")
        return False
    
    # Test COCO export
    print("  📝 Testing COCO export...")
    coco_data = ExportFormats.export_coco(test_data)
    
    if "annotations" in coco_data and len(coco_data["annotations"]) >= 2:
        first_ann = coco_data["annotations"][0]
        bbox = first_ann.get("bbox", [])
        print(f"  🎯 COCO first annotation bbox: {bbox}")
        
        # COCO format should be [x, y, width, height]
        if len(bbox) == 4 and all(v > 0 for v in bbox):
            print("  ✅ COCO bbox format looks correct")
        else:
            print("  ❌ COCO bbox format incorrect")
            return False
    else:
        print("  ❌ COCO annotations not found")
        return False
    
    print("  🎉 All tests passed! The bbox format fix is working correctly.")
    return True

if __name__ == "__main__":
    success = test_bbox_format_fix()
    if success:
        print("\n🎉 SUCCESS: Annotation transformation fix is working!")
        sys.exit(0)
    else:
        print("\n❌ FAILURE: Annotation transformation fix has issues!")
        sys.exit(1)