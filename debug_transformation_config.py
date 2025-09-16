#!/usr/bin/env python3
"""
Debug what's actually in the transformation_config
"""

import sys
import os
sys.path.append('/workspace/project/veera-2')
sys.path.append('/workspace/project/veera-2/backend')

def simulate_tracking_function():
    """Simulate the track_transformations_for_annotations function"""
    
    # Simulate user transformations (rotation, flip)
    transformations = [
        {"type": "rotation", "params": {"angle": -23}},
        {"type": "flip", "params": {"horizontal": True, "vertical": False}}
    ]
    
    original_dims = (300, 168)  # car_1.jpg
    final_dims = (240, 240)     # after resize
    
    print("=== SIMULATING TRACKING FUNCTION ===")
    print(f"User transformations: {[t['type'] for t in transformations]}")
    print(f"original_dims: {original_dims}")
    print(f"final_dims: {final_dims}")
    
    # Step 1: Process user transformations first
    transformation_config = {}
    geometric_transforms = []
    
    for idx, transform in enumerate(transformations):
        transform_type = transform.get("type")
        transform_params = transform.get("params", {})
        
        # Add to config format (for annotation_transformer.py compatibility)
        transformation_config[transform_type] = {
            "enabled": True,
            **transform_params
        }
        
        geometric_transforms.append({
            "type": transform_type,
            "params": dict(transform_params),
            "index": idx
        })
    
    print(f"\nAfter processing user transformations:")
    print(f"transformation_config keys: {list(transformation_config.keys())}")
    print(f"geometric_transforms: {[t['type'] for t in geometric_transforms]}")
    
    # Step 2: Add baseline resize (this is where the bug happens!)
    if original_dims != final_dims:
        print(f"\nAdding baseline resize...")
        
        # Add resize to beginning of geometric transforms (it happens first)
        baseline_resize = {
            "type": "resize",
            "params": {
                "width": final_dims[0],
                "height": final_dims[1],
                "resize_mode": "stretch_to"
            },
            "index": -1,  # Indicates baseline transformation
            "is_baseline": True
        }
        
        geometric_transforms.insert(0, baseline_resize)  # ✅ This is correct
        transformation_config["resize"] = {              # ❌ This OVERWRITES any existing resize!
            "enabled": True,
            "width": final_dims[0],
            "height": final_dims[1],
            "resize_mode": "stretch_to"
        }
    
    print(f"\nAfter adding baseline resize:")
    print(f"transformation_config keys: {list(transformation_config.keys())}")
    print(f"geometric_transforms: {[t['type'] for t in geometric_transforms]}")
    
    print(f"\n=== FINAL TRANSFORMATION_CONFIG ===")
    for key, value in transformation_config.items():
        print(f"{key}: {value}")
    
    print(f"\n=== ITERATION ORDER TEST ===")
    print("When annotation_transformer.py iterates over transformation_config.items():")
    for i, (transform_name, params) in enumerate(transformation_config.items()):
        if params.get('enabled', True):
            print(f"  {i+1}. {transform_name}")
    
    return transformation_config

if __name__ == "__main__":
    simulate_tracking_function()