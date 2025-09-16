#!/usr/bin/env python3
"""
Test script to debug transformation tracking issues.
This will help us understand why has_geometric_transforms might be False.
"""

import sys
import os
sys.path.append('/workspace/project/veera-1')
sys.path.append('/workspace/project/veera-1/backend')

# Import the tracking function from releases.py
import importlib.util
spec = importlib.util.spec_from_file_location("releases", "/workspace/project/veera-1/backend/api/routes/releases.py")
releases_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(releases_module)

import json

def test_transformation_tracking():
    """Test the transformation tracking function"""
    
    print("🔍 TESTING TRANSFORMATION TRACKING")
    print("=" * 50)
    
    # Test Case 1: Simple resize transformation
    print("📊 TEST CASE 1: Simple resize transformation")
    transformations = [
        {
            "type": "resize",
            "params": {
                "width": 640,
                "height": 480,
                "resize_mode": "stretch_to"
            }
        }
    ]
    
    original_dims = (1024, 768)
    final_dims = (640, 480)
    
    print(f"   Transformations: {transformations}")
    print(f"   Original dims: {original_dims}")
    print(f"   Final dims: {final_dims}")
    
    tracking_data = releases_module.track_transformations_for_annotations(
        transformations=transformations,
        original_dims=original_dims,
        final_dims=final_dims
    )
    
    print(f"   Result:")
    print(f"     has_geometric_transforms: {tracking_data.get('has_geometric_transforms')}")
    print(f"     geometric_count: {tracking_data.get('geometric_count')}")
    print(f"     photometric_count: {tracking_data.get('photometric_count')}")
    print(f"     geometric_transforms: {len(tracking_data.get('geometric_transforms', []))}")
    print()
    
    # Test Case 2: Only photometric transformation
    print("📊 TEST CASE 2: Only photometric transformation")
    transformations = [
        {
            "type": "brightness",
            "params": {
                "brightness_factor": 1.2
            }
        }
    ]
    
    original_dims = (640, 480)  # Same dimensions
    final_dims = (640, 480)
    
    print(f"   Transformations: {transformations}")
    print(f"   Original dims: {original_dims}")
    print(f"   Final dims: {final_dims}")
    
    tracking_data = releases_module.track_transformations_for_annotations(
        transformations=transformations,
        original_dims=original_dims,
        final_dims=final_dims
    )
    
    print(f"   Result:")
    print(f"     has_geometric_transforms: {tracking_data.get('has_geometric_transforms')}")
    print(f"     geometric_count: {tracking_data.get('geometric_count')}")
    print(f"     photometric_count: {tracking_data.get('photometric_count')}")
    print(f"     geometric_transforms: {len(tracking_data.get('geometric_transforms', []))}")
    print()
    
    # Test Case 3: Photometric + dimension change (should add baseline resize)
    print("📊 TEST CASE 3: Photometric + dimension change (should add baseline resize)")
    transformations = [
        {
            "type": "brightness",
            "params": {
                "brightness_factor": 1.2
            }
        }
    ]
    
    original_dims = (1024, 768)  # Different dimensions
    final_dims = (640, 480)
    
    print(f"   Transformations: {transformations}")
    print(f"   Original dims: {original_dims}")
    print(f"   Final dims: {final_dims}")
    
    tracking_data = releases_module.track_transformations_for_annotations(
        transformations=transformations,
        original_dims=original_dims,
        final_dims=final_dims
    )
    
    print(f"   Result:")
    print(f"     has_geometric_transforms: {tracking_data.get('has_geometric_transforms')}")
    print(f"     geometric_count: {tracking_data.get('geometric_count')}")
    print(f"     photometric_count: {tracking_data.get('photometric_count')}")
    print(f"     geometric_transforms: {len(tracking_data.get('geometric_transforms', []))}")
    
    # Show the geometric transforms
    if tracking_data.get('geometric_transforms'):
        print(f"     geometric_transforms details:")
        for i, gt in enumerate(tracking_data['geometric_transforms']):
            print(f"       {i}: {gt['type']} - {gt.get('params', {})}")
    print()
    
    # Test Case 4: Empty transformations with dimension change
    print("📊 TEST CASE 4: Empty transformations with dimension change")
    transformations = []
    
    original_dims = (1024, 768)
    final_dims = (640, 480)
    
    print(f"   Transformations: {transformations}")
    print(f"   Original dims: {original_dims}")
    print(f"   Final dims: {final_dims}")
    
    tracking_data = releases_module.track_transformations_for_annotations(
        transformations=transformations,
        original_dims=original_dims,
        final_dims=final_dims
    )
    
    print(f"   Result:")
    print(f"     has_geometric_transforms: {tracking_data.get('has_geometric_transforms')}")
    print(f"     geometric_count: {tracking_data.get('geometric_count')}")
    print(f"     photometric_count: {tracking_data.get('photometric_count')}")
    print(f"     geometric_transforms: {len(tracking_data.get('geometric_transforms', []))}")
    
    # Show the geometric transforms
    if tracking_data.get('geometric_transforms'):
        print(f"     geometric_transforms details:")
        for i, gt in enumerate(tracking_data['geometric_transforms']):
            print(f"       {i}: {gt['type']} - {gt.get('params', {})}")
    
    # Save full tracking data for the last test case
    debug_file = "/workspace/project/veera-1/transformation_tracking_debug.json"
    with open(debug_file, 'w') as f:
        json.dump(tracking_data, f, indent=2)
    print(f"📄 Full tracking data saved to: {debug_file}")

if __name__ == "__main__":
    test_transformation_tracking()