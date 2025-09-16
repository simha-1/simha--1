#!/usr/bin/env python3
"""
Trace EXACT order of image transformations
"""

def trace_releases_py_image_transformation():
    """Trace what happens in releases.py for image transformation"""
    
    print("=== IMAGE TRANSFORMATION ORDER IN RELEASES.PY ===")
    
    # Step 1: User transformations are added first
    print("STEP 1: User transformations added to config_dict")
    config_dict = {}
    
    # Simulate user transformations (rotation, flip)
    user_transformations = {
        "rotation": {"enabled": True, "angle": -23},
        "flip": {"enabled": True, "horizontal": True, "vertical": False}
    }
    
    for k, v in user_transformations.items():
        cfg = dict(v)
        cfg["enabled"] = True
        config_dict[k] = cfg
    
    print(f"  config_dict after user transformations: {list(config_dict.keys())}")
    
    # Step 2: Baseline resize is appended LAST (Line 2826-2829)
    print("\nSTEP 2: Baseline resize appended LAST")
    resize_baseline_params = {
        "enabled": True,
        "width": 240,
        "height": 240,
        "resize_mode": "stretch_to"
    }
    
    if resize_baseline_params:
        config_dict["resize"] = resize_baseline_params  # Line 2829
    
    print(f"  config_dict after baseline resize: {list(config_dict.keys())}")
    
    # Step 3: Image transformer processes in dictionary order
    print("\nSTEP 3: ImageTransformer.apply_transformations() processes in dictionary order")
    print("  Line 129: for transform_name, params in config.items():")
    
    for i, (transform_name, params) in enumerate(config_dict.items()):
        if params.get('enabled', True):
            print(f"    {i+1}. {transform_name} - {params}")
    
    return config_dict

def trace_annotation_transformation_order():
    """Trace what happens in annotation transformation"""
    
    print("\n=== ANNOTATION TRANSFORMATION ORDER ===")
    
    # This comes from track_transformations_for_annotations()
    transformation_config = {
        "rotation": {"enabled": True, "angle": -23},
        "flip": {"enabled": True, "horizontal": True, "vertical": False},
        "resize": {"enabled": True, "width": 240, "height": 240, "resize_mode": "stretch_to"}
    }
    
    print("transformation_config from tracking function:")
    for i, (transform_name, params) in enumerate(transformation_config.items()):
        if params.get('enabled', True):
            print(f"  {i+1}. {transform_name} - {params}")
    
    return transformation_config

if __name__ == "__main__":
    image_config = trace_releases_py_image_transformation()
    annotation_config = trace_annotation_transformation_order()
    
    print("\n=== COMPARISON ===")
    image_order = list(image_config.keys())
    annotation_order = list(annotation_config.keys())
    
    print(f"Image transformation order:      {image_order}")
    print(f"Annotation transformation order: {annotation_order}")
    
    if image_order == annotation_order:
        print("✅ ORDERS MATCH!")
    else:
        print("❌ ORDERS DON'T MATCH!")
        print(f"  Image applies:      {' → '.join(image_order)}")
        print(f"  Annotation applies: {' → '.join(annotation_order)}")