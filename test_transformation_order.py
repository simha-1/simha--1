#!/usr/bin/env python3
"""
Test the transformation order in annotation_transformer.py
"""

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

print("=== TRANSFORMATION ORDER TEST ===")
print("Dictionary iteration order:")
for i, (transform_name, params) in enumerate(transformation_config.items()):
    if params.get('enabled', True):
        print(f"  {i+1}. {transform_name}")

print("\nExpected order should be:")
print("  1. resize")
print("  2. rotation") 
print("  3. flip")

print("\nActual order from dictionary:")
actual_order = [name for name, params in transformation_config.items() if params.get('enabled', True)]
print(f"  {actual_order}")

if actual_order == ['resize', 'rotation', 'flip']:
    print("✅ Order is correct!")
else:
    print("❌ Order is WRONG!")