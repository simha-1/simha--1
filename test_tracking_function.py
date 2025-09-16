def track_transformations_for_annotations(transformations: List[dict], original_dims: tuple, final_dims: tuple) -> dict:
    """
    Track EXACT transformations applied to images for annotation coordinate transformation.
    
    This function captures all transformation details needed to apply the same transformations
    to annotation coordinates using the enhanced annotation_transformer.py.
    
    Args:
        transformations: List of transformation dicts [{"type": "rotate", "params": {"angle": -26}}, ...]
        original_dims: (width, height) of original image
        final_dims: (width, height) of final transformed image
        
    Returns:
        dict: Complete transformation tracking data for annotation processing
        {
            "transformation_sequence": [...],  # Sequential transformations applied
            "transformation_config": {...},   # Config format for annotation_transformer.py
            "original_dims": (width, height),
            "final_dims": (width, height),
            "has_geometric_transforms": bool,
            "geometric_transforms": [...],     # Only geometric transforms that affect coordinates
            "photometric_transforms": [...]    # Only photometric transforms (for reference)
        }
    """
    logger.debug("operations.transformations", f"Starting transformation tracking for annotations", "transformation_tracking_start", {
        'transformation_count': len(transformations),
        'original_dims': original_dims,
        'final_dims': final_dims,
        'purpose': 'annotation_coordinate_transformation'
    })
    
    # Define geometric vs photometric transformations
    geometric_transform_types = {
        'resize', 'rotate', 'flip', 'crop', 'random_zoom', 
        'affine_transform', 'perspective_warp', 'shear'
    }
    photometric_transform_types = {
        'brightness', 'contrast', 'blur', 'hue', 'saturation', 
        'gamma', 'noise', 'color_jitter'
    }
    
    transformation_sequence = []
    transformation_config = {}
    geometric_transforms = []
    photometric_transforms = []
    
    # Process each transformation in sequence
    for idx, transform in enumerate(transformations):
        transform_type = transform.get("type")
        transform_params = transform.get("params", {})
        
        logger.debug("operations.transformations", f"Tracking transformation", "transformation_track_item", {
            'index': idx,
            'type': transform_type,
            'params': transform_params,
            'is_geometric': transform_type in geometric_transform_types
        })
        
        # Add to sequence (preserves order)
        transformation_sequence.append({
            "index": idx,
            "type": transform_type,
            "params": dict(transform_params),
            "is_geometric": transform_type in geometric_transform_types,
            "is_photometric": transform_type in photometric_transform_types
        })
        
        # Add to config format (for annotation_transformer.py compatibility)
        transformation_config[transform_type] = {
            "enabled": True,
            **transform_params
        }
        
        # Categorize transforms
        if transform_type in geometric_transform_types:
            geometric_transforms.append({
                "type": transform_type,
                "params": dict(transform_params),
                "index": idx
            })
        elif transform_type in photometric_transform_types:
            photometric_transforms.append({
                "type": transform_type,
                "params": dict(transform_params),
                "index": idx
            })
    
    # Add baseline resize transformation (ALL images get resized)
    # This is the critical insight from the user - even photometric images get geometric transformations
    if original_dims != final_dims:
        logger.debug("operations.transformations", f"Adding baseline resize transformation", "baseline_resize_detected", {
            'original_dims': original_dims,
            'final_dims': final_dims,
            'reason': 'all_images_get_geometric_transformation'
        })
        
        # Add resize to beginning of geometric transforms (it happens first)
        baseline_resize = {
            "type": "resize",
            "params": {
                "width": final_dims[0],
                "height": final_dims[1],
                "resize_mode": "stretch_to"  # Default mode
            },
            "index": -1,  # Indicates baseline transformation
            "is_baseline": True
        }
        
        geometric_transforms.insert(0, baseline_resize)
        transformation_config["resize"] = {
            "enabled": True,
            "width": final_dims[0],
            "height": final_dims[1],
            "resize_mode": "stretch_to"
        }
    
    tracking_data = {
        "transformation_sequence": transformation_sequence,
        "transformation_config": transformation_config,
        "original_dims": original_dims,
        "final_dims": final_dims,
        "has_geometric_transforms": len(geometric_transforms) > 0,
        "geometric_transforms": geometric_transforms,
        "photometric_transforms": photometric_transforms,
        "total_transforms": len(transformations),
        "geometric_count": len(geometric_transforms),
        "photometric_count": len(photometric_transforms)
    }
    
    logger.debug("operations.transformations", f"Transformation tracking completed", "transformation_tracking_complete", {
        'total_transforms': tracking_data["total_transforms"],
        'geometric_count': tracking_data["geometric_count"],
        'photometric_count': tracking_data["photometric_count"],
        'has_geometric_transforms': tracking_data["has_geometric_transforms"],
        'baseline_resize_added': original_dims != final_dims
    })
    
    return tracking_data


def apply_transformations_to_annotations(annotations: List, tracking_data: dict) -> List:
    """
    Apply the same transformations to annotations that were applied to images.
    
    Uses the enhanced annotation_transformer.py with complete geometric transformation support.
    
    Args:
        annotations: List of annotation objects (BoundingBox/Polygon from DB)
        tracking_data: Output from track_transformations_for_annotations()
        
    Returns:
