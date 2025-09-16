"""
Annotation geometry transformer

Provides reusable utilities to transform annotation coordinates (bounding boxes
and polygons) using either:
  - a precise 3x3 homogeneous transform matrix (preferred), or
  - the legacy sequential config-based approach (fallback).

This keeps labels consistent with augmented images.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
import numpy as np
from logging_system.professional_logger import get_professional_logger

logger = get_professional_logger()


@dataclass
class BoundingBox:
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    class_name: str
    class_id: int
    confidence: float = 1.0


@dataclass
class Polygon:
    points: List[Tuple[float, float]]
    class_name: str
    class_id: int
    confidence: float = 1.0


# ---------------------------
# Helpers for matrix-based path
# ---------------------------

def _apply_matrix_to_point(A: np.ndarray, x: float, y: float) -> Tuple[float, float]:
    """Apply a 3x3 homogeneous transform (affine or perspective) to a point."""
    p = np.array([x, y, 1.0], dtype=float).reshape(3, 1)
    p2 = A @ p
    w = p2[2, 0]
    if abs(w) < 1e-12:
        # Extremely rare; avoid divide-by-zero. Return large/sentinel-ish but log it.
        logger.warning("errors.validation", "Homography w ~ 0 while transforming point", "homography_w_near_zero", {
            "x": x, "y": y, "w": float(w)
        })
        w = 1e-12
    return (p2[0, 0] / w, p2[1, 0] / w)


def _clip(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _clip_bbox_to_dims(x_min: float, y_min: float, x_max: float, y_max: float,
                       width: int, height: int) -> Optional[Tuple[float, float, float, float]]:
    x_min = _clip(x_min, 0, width)
    x_max = _clip(x_max, 0, width)
    y_min = _clip(y_min, 0, height)
    y_max = _clip(y_max, 0, height)
    if x_min >= x_max or y_min >= y_max:
        return None
    return (x_min, y_min, x_max, y_max)


def _transform_bbox_with_matrix(bbox: BoundingBox, A: np.ndarray,
                                new_dims: Tuple[int, int]) -> Optional[BoundingBox]:
    x_min, y_min, x_max, y_max = bbox.x_min, bbox.y_min, bbox.x_max, bbox.y_max
    corners = [
        (x_min, y_min),
        (x_max, y_min),
        (x_min, y_max),
        (x_max, y_max),
    ]
    tx = []
    ty = []
    for (x, y) in corners:
        x2, y2 = _apply_matrix_to_point(A, x, y)
        tx.append(x2); ty.append(y2)

    new_x_min, new_x_max = min(tx), max(tx)
    new_y_min, new_y_max = min(ty), max(ty)

    w, h = new_dims
    clipped = _clip_bbox_to_dims(new_x_min, new_y_min, new_x_max, new_y_max, w, h)
    if clipped is None:
        logger.warning("errors.validation", "Invalid bounding box after matrix transform, skipping",
                       "invalid_bbox_after_matrix", {
                           "old": [x_min, y_min, x_max, y_max],
                           "new": [new_x_min, new_y_min, new_x_max, new_y_max],
                           "new_dims": new_dims
                       })
        return None

    cx_min, cy_min, cx_max, cy_max = clipped
    return BoundingBox(cx_min, cy_min, cx_max, cy_max, bbox.class_name, bbox.class_id, bbox.confidence)


def _transform_polygon_with_matrix(polygon: Polygon, A: np.ndarray,
                                   new_dims: Tuple[int, int]) -> Optional[Polygon]:
    w, h = new_dims
    out: List[Tuple[float, float]] = []
    for (x, y) in polygon.points:
        x2, y2 = _apply_matrix_to_point(A, x, y)
        # clip to image bounds
        out.append((_clip(x2, 0, w), _clip(y2, 0, h)))

    # keep only valid polygons (>=3 points)
    if len(out) < 3:
        logger.warning("errors.validation", "Polygon < 3 points after matrix transform, skipping",
                       "invalid_polygon_after_matrix", {"original_points": len(polygon.points)})
        return None

    return Polygon(out, polygon.class_name, polygon.class_id, polygon.confidence)


# ------------------------------------------------------
# Public API (now supports precise matrix A if provided)
# ------------------------------------------------------

def update_annotations_for_transformations(
    annotations: List[Union[BoundingBox, Polygon]],
    transformation_config: Dict[str, Any],
    original_dims: Tuple[int, int],
    new_dims: Tuple[int, int],
    affine_matrix: Optional[Union[List[float], List[List[float]], np.ndarray]] = None,
    debug_tracking: bool = False
) -> Union[List[Union[BoundingBox, Polygon]], Tuple[List[Union[BoundingBox, Polygon]], Dict]]:
    """
    Update annotations based on applied transformations.

    Preferred path:
        If `affine_matrix` (3x3) is provided, use it to transform geometry exactly,
        then clip to `new_dims`.

    Fallback path:
        Use the legacy sequential config-based method to approximate updates.

    Args:
        annotations: list of BoundingBox / Polygon
        transformation_config: the (resolved) config used for the image
        original_dims: (width, height) of source image
        new_dims: (width, height) of resulting image
        affine_matrix: optional 3x3 matrix (list or np.ndarray) used on pixels
        debug_tracking: if True, return (annotations, debug_info) tuple

    Returns:
        List of updated annotations (invalid ones are dropped).
        If debug_tracking=True, returns (annotations, debug_info) tuple.
    """
    if not annotations:
        if debug_tracking:
            return [], {}
        return []

    logger.info("operations.transformations", f"Updating {len(annotations)} annotations", "annotations_update_start", {
        'annotation_count': len(annotations),
        'transformation_types': list(transformation_config.keys()),
        'original_dims': original_dims,
        'new_dims': new_dims,
        'has_affine_matrix': affine_matrix is not None,
        'debug_tracking': debug_tracking
    })

    updated_annotations: List[Union[BoundingBox, Polygon]] = []
    
    # Initialize debug tracking data
    debug_info = {
        'transformation_method': 'matrix' if affine_matrix is not None else 'sequential',
        'transformation_config': transformation_config,
        'original_dims': original_dims,
        'new_dims': new_dims,
        'annotation_steps': []
    } if debug_tracking else None

    # --- Matrix-based precise path ---
    if affine_matrix is not None:
        try:
            # normalize to 3x3 np.ndarray
            A = np.array(affine_matrix, dtype=float).reshape(3, 3)
        except Exception as e:
            logger.error("errors.validation", f"Bad affine_matrix shape/value: {str(e)}; falling back to legacy path",
                         "affine_matrix_invalid", {})
            A = None

        if A is not None:
            for ann in annotations:
                try:
                    if isinstance(ann, BoundingBox):
                        u = _transform_bbox_with_matrix(ann, A, new_dims)
                        if u is not None:
                            updated_annotations.append(u)
                    elif isinstance(ann, Polygon):
                        u = _transform_polygon_with_matrix(ann, A, new_dims)
                        if u is not None:
                            updated_annotations.append(u)
                    else:
                        updated_annotations.append(ann)
                except Exception as e:
                    logger.warning("errors.validation", f"Matrix-based annotation update failed: {str(e)}",
                                   "annotation_update_failed_matrix", {"type": type(ann).__name__})
                    updated_annotations.append(ann)

            logger.info("operations.transformations", f"Updated {len(updated_annotations)} annotations (matrix path)",
                        "annotations_updated_matrix", {
                            'annotation_count': len(updated_annotations),
                            'original_count': len(annotations)
                        })
            
            if debug_tracking:
                debug_info['annotation_steps'] = [
                    {
                        'annotation_id': i,
                        'transformation_method': 'matrix_based',
                        'matrix_applied': True,
                        'note': 'Precise matrix transformation applied'
                    }
                    for i in range(len(updated_annotations))
                ]
                return updated_annotations, debug_info
            return updated_annotations

    # --- Legacy fallback (sequential config order) ---
    for ann_idx, annotation in enumerate(annotations):
        try:
            if debug_tracking:
                updated_annotation, ann_debug = _transform_single_annotation_with_debug(
                    annotation, transformation_config, original_dims, new_dims, ann_idx
                )
                debug_info['annotation_steps'].append(ann_debug)
            else:
                updated_annotation = _transform_single_annotation(
                    annotation, transformation_config, original_dims, new_dims
                )
            
            if updated_annotation:
                updated_annotations.append(updated_annotation)
        except Exception as e:
            logger.warning("errors.validation", f"Failed to update annotation: {str(e)}", "annotation_update_failed", {
                'error': str(e),
                'annotation_type': type(annotation).__name__
            })
            updated_annotations.append(annotation)
            
            if debug_tracking:
                debug_info['annotation_steps'].append({
                    'annotation_id': ann_idx,
                    'transformation_method': 'sequential_failed',
                    'error': str(e),
                    'fallback_used': True
                })

    logger.info("operations.transformations", f"Updated {len(updated_annotations)} annotations (legacy path)",
                "annotations_updated", {
                    'annotation_count': len(updated_annotations),
                    'original_count': len(annotations)
                })
    
    if debug_tracking:
        return updated_annotations, debug_info
    return updated_annotations


# ------------------------------------------------------
# Legacy per-transform fallback (unchanged from before)
# ------------------------------------------------------

def _transform_single_annotation(annotation: Union[BoundingBox, Polygon],
                                 transformation_config: Dict[str, Any],
                                 original_dims: Tuple[int, int],
                                 new_dims: Tuple[int, int]) -> Optional[Union[BoundingBox, Polygon]]:
    """Legacy path: transform a single annotation using old method with sequential order."""
    if isinstance(annotation, BoundingBox):
        return _transform_bbox(annotation, transformation_config, original_dims, new_dims)
    elif isinstance(annotation, Polygon):
        return _transform_polygon(annotation, transformation_config, original_dims, new_dims)
    else:
        return annotation


def _transform_single_annotation_with_debug(annotation: Union[BoundingBox, Polygon],
                                           transformation_config: Dict[str, Any],
                                           original_dims: Tuple[int, int],
                                           new_dims: Tuple[int, int],
                                           annotation_id: int) -> Tuple[Optional[Union[BoundingBox, Polygon]], Dict]:
    """Legacy path with debug tracking: transform a single annotation and track each step."""
    
    # Initialize debug tracking for this annotation
    ann_debug = {
        'annotation_id': annotation_id,
        'annotation_type': type(annotation).__name__,
        'class_name': getattr(annotation, 'class_name', 'unknown'),
        'class_id': getattr(annotation, 'class_id', 0),
        'transformation_method': 'sequential',
        'transformation_steps': [],
        'original_coordinates': None,
        'final_coordinates': None
    }
    
    # Record original coordinates
    if isinstance(annotation, BoundingBox):
        ann_debug['original_coordinates'] = {
            'type': 'bbox',
            'x_min': float(annotation.x_min),
            'y_min': float(annotation.y_min),
            'x_max': float(annotation.x_max),
            'y_max': float(annotation.y_max)
        }
        updated_annotation = _transform_bbox(annotation, transformation_config, original_dims, new_dims, debug_info=ann_debug)
    elif isinstance(annotation, Polygon):
        ann_debug['original_coordinates'] = {
            'type': 'polygon',
            'points': [(float(x), float(y)) for x, y in annotation.points]
        }
        updated_annotation = _transform_polygon(annotation, transformation_config, original_dims, new_dims, debug_info=ann_debug)
    else:
        ann_debug['transformation_steps'].append({
            'step': 0,
            'transformation': 'no_transformation',
            'note': 'Unknown annotation type, no transformation applied'
        })
        updated_annotation = annotation
    
    # Record final coordinates
    if updated_annotation and isinstance(updated_annotation, BoundingBox):
        ann_debug['final_coordinates'] = {
            'type': 'bbox',
            'x_min': float(updated_annotation.x_min),
            'y_min': float(updated_annotation.y_min),
            'x_max': float(updated_annotation.x_max),
            'y_max': float(updated_annotation.y_max)
        }
    elif updated_annotation and isinstance(updated_annotation, Polygon):
        ann_debug['final_coordinates'] = {
            'type': 'polygon',
            'points': [(float(x), float(y)) for x, y in updated_annotation.points]
        }
    
    return updated_annotation, ann_debug


def _transform_bbox(bbox: BoundingBox, transformation_config: Dict[str, Any],
                    original_dims: Tuple[int, int], new_dims: Tuple[int, int], 
                    debug_info: Optional[Dict] = None) -> Optional[BoundingBox]:
    """Transform bbox coordinates using sequential transforms with optional debug tracking."""
    x_min, y_min, x_max, y_max = bbox.x_min, bbox.y_min, bbox.x_max, bbox.y_max
    orig_width, orig_height = original_dims
    new_width, new_height = new_dims

    current_width, current_height = orig_width, orig_height
    
    # Updated coordinate_transforms to match transformation_config.py
    # GEOMETRY TOOLS (affect coordinates): resize, rotation, flip, crop, random_zoom, affine_transform, perspective_warp, shear
    # APPEARANCE TOOLS (don't affect coordinates): brightness, contrast, blur, noise, color_jitter, saturation, gamma, clahe, cutout
    coordinate_transforms = {'resize', 'rotation', 'flip', 'crop', 'random_zoom', 'affine_transform', 'perspective_warp', 'shear'}
    
    step_counter = 0

    for transform_name, params in transformation_config.items():
        if transform_name in coordinate_transforms and params.get('enabled', True):
            # Record coordinates before this transformation (for debug tracking)
            if debug_info is not None:
                before_coords = {
                    'x_min': float(x_min),
                    'y_min': float(y_min),
                    'x_max': float(x_max),
                    'y_max': float(y_max)
                }
            
            if transform_name == 'flip':
                if params.get('horizontal', False):
                    x_min, x_max = current_width - x_max, current_width - x_min
                if params.get('vertical', False):
                    y_min, y_max = current_height - y_max, current_height - y_min

            elif transform_name == 'resize':
                target_width = params.get('width', 640)
                target_height = params.get('height', 640)
                resize_mode = params.get('resize_mode', 'stretch_to')

                if resize_mode == 'stretch_to':
                    width_ratio = target_width / current_width
                    height_ratio = target_height / current_height
                    x_min *= width_ratio; x_max *= width_ratio
                    y_min *= height_ratio; y_max *= height_ratio
                    current_width, current_height = target_width, target_height

                elif resize_mode == 'fill_center_crop':
                    original_aspect = current_width / current_height
                    target_aspect = target_width / target_height
                    if original_aspect > target_aspect:
                        scale_factor = target_height / current_height
                        scaled_width = int(current_width * scale_factor)
                        x_min *= scale_factor; x_max *= scale_factor
                        y_min *= scale_factor; y_max *= scale_factor
                        crop_offset = (scaled_width - target_width) // 2
                        x_min -= crop_offset; x_max -= crop_offset
                    else:
                        scale_factor = target_width / current_width
                        scaled_height = int(current_height * scale_factor)
                        x_min *= scale_factor; x_max *= scale_factor
                        y_min *= scale_factor; y_max *= scale_factor
                        crop_offset = (scaled_height - target_height) // 2
                        y_min -= crop_offset; y_max -= crop_offset
                    current_width, current_height = target_width, target_height

                elif resize_mode == 'fit_within':
                    original_aspect = current_width / current_height
                    target_aspect = target_width / target_height
                    if original_aspect > target_aspect:
                        scale_factor = target_width / current_width
                    else:
                        scale_factor = target_height / current_height
                    x_min *= scale_factor; x_max *= scale_factor
                    y_min *= scale_factor; y_max *= scale_factor

                elif resize_mode in ['fit_reflect_edges', 'fit_black_edges', 'fit_white_edges']:
                    original_aspect = current_width / current_height
                    target_aspect = target_width / target_height
                    if original_aspect > target_aspect:
                        scale_factor = target_width / current_width
                        new_h = int(current_height * scale_factor)
                        x_min *= scale_factor; x_max *= scale_factor
                        y_min *= scale_factor; y_max *= scale_factor
                        paste_y = (target_height - new_h) // 2
                        y_min += paste_y; y_max += paste_y
                    else:
                        scale_factor = target_height / current_height
                        new_w = int(current_width * scale_factor)
                        x_min *= scale_factor; x_max *= scale_factor
                        y_min *= scale_factor; y_max *= scale_factor
                        paste_x = (target_width - new_w) // 2
                        x_min += paste_x; x_max += paste_x
                    current_width, current_height = target_width, target_height

            elif transform_name == 'rotation':
                # Implement rotation coordinate transformation
                angle = params.get('angle', 0)
                if angle != 0:
                    # Convert angle to radians
                    angle_rad = math.radians(angle)
                    cos_a = math.cos(angle_rad)
                    sin_a = math.sin(angle_rad)
                    
                    # Rotation around image center
                    center_x, center_y = current_width / 2, current_height / 2
                    
                    # Transform all 4 corners of bounding box
                    corners = [
                        (x_min - center_x, y_min - center_y),
                        (x_max - center_x, y_min - center_y),
                        (x_min - center_x, y_max - center_y),
                        (x_max - center_x, y_max - center_y)
                    ]
                    
                    rotated_corners = []
                    for (x, y) in corners:
                        # Apply rotation matrix
                        new_x = x * cos_a - y * sin_a + center_x
                        new_y = x * sin_a + y * cos_a + center_y
                        rotated_corners.append((new_x, new_y))
                    
                    # Find new bounding box from rotated corners
                    xs = [corner[0] for corner in rotated_corners]
                    ys = [corner[1] for corner in rotated_corners]
                    x_min, x_max = min(xs), max(xs)
                    y_min, y_max = min(ys), max(ys)

            elif transform_name == 'crop':
                crop_x = params.get('x', 0)
                crop_y = params.get('y', 0)
                x_min -= crop_x; x_max -= crop_x
                y_min -= crop_y; y_max -= crop_y

            elif transform_name == 'random_zoom':
                zoom_factor = params.get('zoom_factor', 1.0)
                center_x, center_y = current_width / 2, current_height / 2
                x_min = center_x + (x_min - center_x) * zoom_factor
                x_max = center_x + (x_max - center_x) * zoom_factor
                y_min = center_y + (y_min - center_y) * zoom_factor
                y_max = center_y + (y_max - center_y) * zoom_factor

            elif transform_name == 'shear':
                # Implement shear coordinate transformation
                shear_angle = params.get('shear_angle', 0) or params.get('angle', 0)
                if shear_angle != 0:
                    # Convert shear angle to shear factor
                    shear_factor = math.tan(math.radians(shear_angle))
                    
                    # Apply horizontal shear transformation
                    # x' = x + shear_factor * y
                    # y' = y (unchanged)
                    corners = [
                        (x_min, y_min),
                        (x_max, y_min),
                        (x_min, y_max),
                        (x_max, y_max)
                    ]
                    
                    sheared_corners = []
                    for (x, y) in corners:
                        new_x = x + shear_factor * y
                        new_y = y
                        sheared_corners.append((new_x, new_y))
                    
                    # Find new bounding box from sheared corners
                    xs = [corner[0] for corner in sheared_corners]
                    ys = [corner[1] for corner in sheared_corners]
                    x_min, x_max = min(xs), max(xs)
                    y_min, y_max = min(ys), max(ys)
            
            elif transform_name == 'affine_transform':
                # Implement basic affine transformation
                scale_x = params.get('scale_x', 1.0)
                scale_y = params.get('scale_y', 1.0)
                translate_x = params.get('translate_x', 0)
                translate_y = params.get('translate_y', 0)
                rotation_angle = params.get('rotation', 0)
                
                if scale_x != 1.0 or scale_y != 1.0 or translate_x != 0 or translate_y != 0 or rotation_angle != 0:
                    # Apply scaling
                    center_x, center_y = current_width / 2, current_height / 2
                    x_min = center_x + (x_min - center_x) * scale_x
                    x_max = center_x + (x_max - center_x) * scale_x
                    y_min = center_y + (y_min - center_y) * scale_y
                    y_max = center_y + (y_max - center_y) * scale_y
                    
                    # Apply translation
                    x_min += translate_x
                    x_max += translate_x
                    y_min += translate_y
                    y_max += translate_y
                    
                    # Apply rotation if specified
                    if rotation_angle != 0:
                        angle_rad = math.radians(rotation_angle)
                        cos_a = math.cos(angle_rad)
                        sin_a = math.sin(angle_rad)
                        
                        corners = [
                            (x_min - center_x, y_min - center_y),
                            (x_max - center_x, y_min - center_y),
                            (x_min - center_x, y_max - center_y),
                            (x_max - center_x, y_max - center_y)
                        ]
                        
                        rotated_corners = []
                        for (x, y) in corners:
                            new_x = x * cos_a - y * sin_a + center_x
                            new_y = x * sin_a + y * cos_a + center_y
                            rotated_corners.append((new_x, new_y))
                        
                        xs = [corner[0] for corner in rotated_corners]
                        ys = [corner[1] for corner in rotated_corners]
                        x_min, x_max = min(xs), max(xs)
                        y_min, y_max = min(ys), max(ys)
            
            elif transform_name == 'perspective_warp':
                # Perspective transformation is complex - use matrix-based approach if available
                # For legacy path, we'll skip precise perspective transformation
                # as it requires solving perspective equations
                logger.warning("operations.transformations", 
                             "Perspective transformation in legacy path not fully supported, use matrix-based path for precision",
                             "perspective_legacy_warning", {
                                 'transform_name': transform_name
                             })
                pass
            
            # Record debug info after this transformation
            if debug_info is not None:
                after_coords = {
                    'x_min': float(x_min),
                    'y_min': float(y_min),
                    'x_max': float(x_max),
                    'y_max': float(y_max)
                }
                
                # Calculate coordinate changes
                coordinate_changes = {
                    'x_min_change': after_coords['x_min'] - before_coords['x_min'],
                    'y_min_change': after_coords['y_min'] - before_coords['y_min'],
                    'x_max_change': after_coords['x_max'] - before_coords['x_max'],
                    'y_max_change': after_coords['y_max'] - before_coords['y_max'],
                    'center_x_change': ((after_coords['x_min'] + after_coords['x_max'])/2) - ((before_coords['x_min'] + before_coords['x_max'])/2),
                    'center_y_change': ((after_coords['y_min'] + after_coords['y_max'])/2) - ((before_coords['y_min'] + before_coords['y_max'])/2)
                }
                
                debug_info['transformation_steps'].append({
                    'step': step_counter,
                    'transformation': transform_name,
                    'parameters': params,
                    'before_coordinates': before_coords,
                    'after_coordinates': after_coords,
                    'coordinate_changes': coordinate_changes,
                    'current_dimensions': {'width': current_width, 'height': current_height}
                })
                
                step_counter += 1

    # clip
    x_min = _clip(x_min, 0, new_width)
    x_max = _clip(x_max, 0, new_width)
    y_min = _clip(y_min, 0, new_height)
    y_max = _clip(y_max, 0, new_height)

    if x_min >= x_max or y_min >= y_max:
        logger.warning("errors.validation", "Invalid bounding box after transformation, skipping", "invalid_bbox_skipped", {
            'bbox_coords': (x_min, y_min, x_max, y_max),
            'original_dims': original_dims,
            'new_dims': new_dims
        })
        return None

    return BoundingBox(x_min, y_min, x_max, y_max, bbox.class_name, bbox.class_id, bbox.confidence)


def _transform_polygon(polygon: Polygon, transformation_config: Dict[str, Any],
                       original_dims: Tuple[int, int], new_dims: Tuple[int, int],
                       debug_info: Optional[Dict] = None) -> Optional[Polygon]:
    """Transform polygon coordinates using sequential transforms with optional debug tracking."""
    points = polygon.points.copy()
    orig_width, orig_height = original_dims
    new_width, new_height = new_dims

    current_width, current_height = orig_width, orig_height
    
    # Updated coordinate_transforms to match transformation_config.py
    # GEOMETRY TOOLS (affect coordinates): resize, rotation, flip, crop, random_zoom, affine_transform, perspective_warp, shear
    # APPEARANCE TOOLS (don't affect coordinates): brightness, contrast, blur, noise, color_jitter, saturation, gamma, clahe, cutout
    coordinate_transforms = {'resize', 'rotation', 'flip', 'crop', 'random_zoom', 'affine_transform', 'perspective_warp', 'shear'}
    
    step_counter = 0

    for transform_name, params in transformation_config.items():
        if transform_name in coordinate_transforms and params.get('enabled', True):
            # Record coordinates before this transformation (for debug tracking)
            if debug_info is not None:
                before_coords = {
                    'type': 'polygon',
                    'points': [(float(x), float(y)) for x, y in points]
                }

            if transform_name == 'flip':
                if params.get('horizontal', False):
                    points = [(current_width - x, y) for x, y in points]
                if params.get('vertical', False):
                    points = [(x, current_height - y) for x, y in points]

            elif transform_name == 'resize':
                target_width = params.get('width', 640)
                target_height = params.get('height', 640)
                resize_mode = params.get('resize_mode', 'stretch_to')

                if resize_mode == 'stretch_to':
                    width_ratio = target_width / current_width
                    height_ratio = target_height / current_height
                    points = [(x * width_ratio, y * height_ratio) for x, y in points]
                    current_width, current_height = target_width, target_height

                elif resize_mode == 'fill_center_crop':
                    original_aspect = current_width / current_height
                    target_aspect = target_width / target_height
                    if original_aspect > target_aspect:
                        scale_factor = target_height / current_height
                        scaled_width = int(current_width * scale_factor)
                        points = [(x * scale_factor, y * scale_factor) for x, y in points]
                        crop_offset = (scaled_width - target_width) // 2
                        points = [(x - crop_offset, y) for x, y in points]
                    else:
                        scale_factor = target_width / current_width
                        scaled_height = int(current_height * scale_factor)
                        points = [(x * scale_factor, y * scale_factor) for x, y in points]
                        crop_offset = (scaled_height - target_height) // 2
                        points = [(x, y - crop_offset) for x, y in points]
                    current_width, current_height = target_width, target_height

                elif resize_mode == 'fit_within':
                    original_aspect = current_width / current_height
                    target_aspect = target_width / target_height
                    if original_aspect > target_aspect:
                        scale_factor = target_width / current_width
                    else:
                        scale_factor = target_height / current_height
                    points = [(x * scale_factor, y * scale_factor) for x, y in points]
                    current_width, current_height = target_width, target_height

                elif resize_mode in ['fit_reflect_edges', 'fit_black_edges', 'fit_white_edges']:
                    original_aspect = current_width / current_height
                    target_aspect = target_width / target_height
                    if original_aspect > target_aspect:
                        scale_factor = target_width / current_width
                        new_h = int(current_height * scale_factor)
                        points = [(x * scale_factor, y * scale_factor) for x, y in points]
                        paste_y = (target_height - new_h) // 2
                        points = [(x, y + paste_y) for x, y in points]
                    else:
                        scale_factor = target_height / current_height
                        new_w = int(current_width * scale_factor)
                        points = [(x * scale_factor, y * scale_factor) for x, y in points]
                        paste_x = (target_width - new_w) // 2
                        points = [(x + paste_x, y) for x, y in points]
                    current_width, current_height = target_width, target_height

            elif transform_name == 'rotation':
                # Implement rotation coordinate transformation for polygons
                angle = params.get('angle', 0)
                if angle != 0:
                    # Convert angle to radians
                    angle_rad = math.radians(angle)
                    cos_a = math.cos(angle_rad)
                    sin_a = math.sin(angle_rad)
                    
                    # Rotation around image center
                    center_x, center_y = current_width / 2, current_height / 2
                    
                    # Transform all polygon points
                    rotated_points = []
                    for (x, y) in points:
                        # Translate to origin, rotate, translate back
                        x_centered = x - center_x
                        y_centered = y - center_y
                        new_x = x_centered * cos_a - y_centered * sin_a + center_x
                        new_y = x_centered * sin_a + y_centered * cos_a + center_y
                        rotated_points.append((new_x, new_y))
                    
                    points = rotated_points

            elif transform_name == 'crop':
                crop_x = params.get('x', 0)
                crop_y = params.get('y', 0)
                points = [(x - crop_x, y - crop_y) for x, y in points]

            elif transform_name == 'random_zoom':
                zoom_factor = params.get('zoom_factor', 1.0)
                center_x, center_y = orig_width / 2, orig_height / 2
                points = [
                    (center_x + (x - center_x) * zoom_factor, center_y + (y - center_y) * zoom_factor)
                    for x, y in points
                ]

            elif transform_name == 'shear':
                # Implement shear coordinate transformation for polygons
                shear_angle = params.get('shear_angle', 0) or params.get('angle', 0)
                if shear_angle != 0:
                    # Convert shear angle to shear factor
                    shear_factor = math.tan(math.radians(shear_angle))
                    
                    # Apply horizontal shear transformation to all points
                    # x' = x + shear_factor * y
                    # y' = y (unchanged)
                    sheared_points = []
                    for (x, y) in points:
                        new_x = x + shear_factor * y
                        new_y = y
                        sheared_points.append((new_x, new_y))
                    
                    points = sheared_points
            
            elif transform_name == 'affine_transform':
                # Implement basic affine transformation for polygons
                scale_x = params.get('scale_x', 1.0)
                scale_y = params.get('scale_y', 1.0)
                translate_x = params.get('translate_x', 0)
                translate_y = params.get('translate_y', 0)
                rotation_angle = params.get('rotation', 0)
                
                if scale_x != 1.0 or scale_y != 1.0 or translate_x != 0 or translate_y != 0 or rotation_angle != 0:
                    center_x, center_y = current_width / 2, current_height / 2
                    
                    # Apply scaling and translation
                    transformed_points = []
                    for (x, y) in points:
                        # Apply scaling around center
                        new_x = center_x + (x - center_x) * scale_x
                        new_y = center_y + (y - center_y) * scale_y
                        
                        # Apply translation
                        new_x += translate_x
                        new_y += translate_y
                        
                        transformed_points.append((new_x, new_y))
                    
                    points = transformed_points
                    
                    # Apply rotation if specified
                    if rotation_angle != 0:
                        angle_rad = math.radians(rotation_angle)
                        cos_a = math.cos(angle_rad)
                        sin_a = math.sin(angle_rad)
                        
                        rotated_points = []
                        for (x, y) in points:
                            x_centered = x - center_x
                            y_centered = y - center_y
                            new_x = x_centered * cos_a - y_centered * sin_a + center_x
                            new_y = x_centered * sin_a + y_centered * cos_a + center_y
                            rotated_points.append((new_x, new_y))
                        
                        points = rotated_points
            
            elif transform_name == 'perspective_warp':
                # Perspective transformation is complex - use matrix-based approach if available
                # For legacy path, we'll skip precise perspective transformation
                # as it requires solving perspective equations
                logger.warning("operations.transformations", 
                             "Perspective transformation in legacy path not fully supported, use matrix-based path for precision",
                             "perspective_legacy_warning", {
                                 'transform_name': transform_name
                             })
                pass
            
            # Record debug info after this transformation
            if debug_info is not None:
                after_coords = {
                    'type': 'polygon',
                    'points': [(float(x), float(y)) for x, y in points]
                }
                
                # Calculate coordinate changes (center point movement)
                before_center_x = sum(p[0] for p in before_coords['points']) / len(before_coords['points'])
                before_center_y = sum(p[1] for p in before_coords['points']) / len(before_coords['points'])
                after_center_x = sum(p[0] for p in after_coords['points']) / len(after_coords['points'])
                after_center_y = sum(p[1] for p in after_coords['points']) / len(after_coords['points'])
                
                coordinate_changes = {
                    'center_x_change': after_center_x - before_center_x,
                    'center_y_change': after_center_y - before_center_y,
                    'point_count': len(after_coords['points'])
                }
                
                debug_info['transformation_steps'].append({
                    'step': step_counter,
                    'transformation': transform_name,
                    'parameters': params,
                    'before_coordinates': before_coords,
                    'after_coordinates': after_coords,
                    'coordinate_changes': coordinate_changes,
                    'current_dimensions': {'width': current_width, 'height': current_height}
                })
                
                step_counter += 1

    # clip points
    valid_points = []
    for x, y in points:
        valid_points.append((_clip(x, 0, new_width), _clip(y, 0, new_height)))

    if len(valid_points) < 3:
        logger.warning("errors.validation", "Polygon has less than 3 valid points after transformation, skipping",
                       "invalid_polygon_skipped", {
                           'valid_points': len(valid_points),
                           'original_points': len(polygon.points)
                       })
        return None

    return Polygon(valid_points, polygon.class_name, polygon.class_id, polygon.confidence)


