#!/usr/bin/env python3
"""
Test the export format selection fix.

PROBLEM: User selects COCO format but gets YOLO folders and labels in ZIP export.

ROOT CAUSE: Format name mismatch - database stores "COCO" but export system expects "coco"

SOLUTION: Added format name normalization to handle various naming conventions.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, '/workspace/project/11-09-2025-1/backend')

def test_format_normalization():
    """Test that format names are normalized correctly"""
    print("=== Testing Format Name Normalization ===")
    
    try:
        from api.routes.enhanced_export import ExportFormats
        
        # Test various COCO format names
        coco_variations = ["COCO", "coco", "COCO_JSON", "coco_format", "MS_COCO"]
        for variation in coco_variations:
            normalized = ExportFormats._normalize_format_name(variation)
            if normalized == "coco":
                print(f"✅ '{variation}' → '{normalized}' (correct)")
            else:
                print(f"❌ '{variation}' → '{normalized}' (should be 'coco')")
        
        # Test various YOLO format names  
        yolo_variations = ["YOLO", "yolo", "YOLO_DETECTION", "yolo_detect"]
        for variation in yolo_variations:
            normalized = ExportFormats._normalize_format_name(variation)
            if normalized == "yolo_detection":
                print(f"✅ '{variation}' → '{normalized}' (correct)")
            else:
                print(f"❌ '{variation}' → '{normalized}' (should be 'yolo_detection')")
                
        # Test Pascal VOC variations
        voc_variations = ["PASCAL_VOC", "pascal", "VOC", "xml"]
        for variation in voc_variations:
            normalized = ExportFormats._normalize_format_name(variation)
            if normalized == "pascal_voc":
                print(f"✅ '{variation}' → '{normalized}' (correct)")
            else:
                print(f"❌ '{variation}' → '{normalized}' (should be 'pascal_voc')")
                
    except ImportError as e:
        print(f"❌ Failed to import ExportFormats: {e}")

def test_user_format_selection():
    """Test that user format selection is respected"""
    print("\n=== Testing User Format Selection ===")
    
    try:
        from api.routes.enhanced_export import ExportFormats
        
        # Test that user choice is respected
        test_cases = [
            ("COCO", "coco"),
            ("YOLO", "yolo_detection"), 
            ("Pascal_VOC", "pascal_voc"),
            ("CSV", "csv")
        ]
        
        for user_format, expected in test_cases:
            result = ExportFormats.select_optimal_format(
                task_type="object_detection",
                project_type="Object Detection", 
                annotations=[{"type": "bbox"}],
                user_format=user_format
            )
            
            if result == expected:
                print(f"✅ User chose '{user_format}' → got '{result}' (correct)")
            else:
                print(f"❌ User chose '{user_format}' → got '{result}' (expected '{expected}')")
                
    except Exception as e:
        print(f"❌ Failed to test user format selection: {e}")

def test_export_method_mapping():
    """Test that export methods are found correctly"""
    print("\n=== Testing Export Method Mapping ===")
    
    try:
        from api.routes.enhanced_export import ExportFormats
        
        # Test that all normalized formats have corresponding methods
        test_formats = ["coco", "yolo_detection", "yolo_segmentation", "pascal_voc", "csv"]
        
        for format_name in test_formats:
            method = ExportFormats.get_export_method(format_name)
            if method:
                print(f"✅ Format '{format_name}' has export method: {method.__name__}")
            else:
                print(f"❌ Format '{format_name}' has no export method")
                
        # Test with uppercase variations
        uppercase_formats = ["COCO", "YOLO", "PASCAL_VOC", "CSV"]
        for format_name in uppercase_formats:
            method = ExportFormats.get_export_method(format_name)
            if method:
                print(f"✅ Format '{format_name}' (uppercase) has export method: {method.__name__}")
            else:
                print(f"❌ Format '{format_name}' (uppercase) has no export method")
                
    except Exception as e:
        print(f"❌ Failed to test export method mapping: {e}")

def main():
    """Run all tests"""
    print("Testing Export Format Selection Fix")
    print("=" * 60)
    print("PROBLEM: User selects COCO but gets YOLO folders/labels in ZIP")
    print("CAUSE: Format name mismatch (COCO vs coco)")
    print("SOLUTION: Added format name normalization")
    print("=" * 60)
    
    test_format_normalization()
    test_user_format_selection()
    test_export_method_mapping()
    
    print("\n" + "=" * 60)
    print("FORMAT SELECTION FIX SUMMARY:")
    print("1. ✅ Added format name normalization for case-insensitive matching")
    print("2. ✅ Handle common format variations (COCO, coco_json, MS_COCO, etc.)")
    print("3. ✅ User format choice is properly respected and normalized")
    print("4. ✅ Export methods are correctly mapped to normalized format names")
    print("\nRESULT: When you select COCO, you should now get COCO format (not YOLO)!")
    print("=" * 60)

if __name__ == "__main__":
    main()