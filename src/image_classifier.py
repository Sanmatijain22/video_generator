"""Intelligent room and scene classification for Property Studio AI.

Identifies room types and property spaces from:
1. Explicit user-assigned categories (from UI or metadata).
2. Filename and metadata keyword heuristics.
3. Computer vision color and spatial layout analysis (OpenCV / PIL / NumPy).

Ensures that photographs (e.g. bedrooms, kitchens, balconies) are accurately
classified and mapped to their corresponding descriptive captions.
"""

from pathlib import Path
from typing import Tuple, Optional, Dict
import numpy as np
from PIL import Image
import cv2

# Supported categories
CATEGORY_EXTERIOR = "exterior"
CATEGORY_LIVING_ROOM = "living_room"
CATEGORY_KITCHEN = "kitchen"
CATEGORY_BEDROOM = "bedroom"
CATEGORY_BALCONY = "balcony"
CATEGORY_BATHROOM = "bathroom"
CATEGORY_PARKING = "parking"
CATEGORY_AMENITY = "amenity"
CATEGORY_GENERAL = "general"

DISPLAY_NAMES: Dict[str, str] = {
    CATEGORY_EXTERIOR: "Property Exterior",
    CATEGORY_LIVING_ROOM: "Living Room",
    CATEGORY_KITCHEN: "Modular Kitchen",
    CATEGORY_BEDROOM: "Bedroom",
    CATEGORY_BALCONY: "Balcony View",
    CATEGORY_BATHROOM: "Designer Bathroom",
    CATEGORY_PARKING: "Parking & Garage",
    CATEGORY_AMENITY: "Key Amenity",
    CATEGORY_GENERAL: "Property Space"
}

# Keyword mappings for filenames and metadata
KEYWORD_MAPPINGS = {
    CATEGORY_EXTERIOR: ["exterior", "facade", "building", "front", "outside", "aerial", "elevation", "architecture"],
    CATEGORY_LIVING_ROOM: ["living", "hall", "lounge", "drawing", "sitting", "family_room"],
    CATEGORY_KITCHEN: ["kitchen", "modular_kitchen", "culinary", "cook", "pantry", "dining"],
    CATEGORY_BEDROOM: ["bedroom", "bed", "master", "suite", "sleeping"],
    CATEGORY_BALCONY: ["balcony", "terrace", "deck", "patio", "veranda", "view", "balcony_view", "scenic"],
    CATEGORY_BATHROOM: ["bathroom", "bath", "washroom", "toilet", "shower", "powder_room"],
    CATEGORY_PARKING: ["parking", "garage", "carport", "driveway"],
    CATEGORY_AMENITY: ["pool", "swimming", "gym", "fitness", "garden", "clubhouse", "lawn"]
}


def classify_by_filename(filename: str) -> Optional[Tuple[str, float]]:
    """Inspect filename stem for reliable property keywords."""
    clean_name = filename.lower().replace("-", "_").replace(" ", "_")
    
    # Check exact keywords in order of specificity
    for category, keywords in KEYWORD_MAPPINGS.items():
        for kw in keywords:
            if kw in clean_name:
                return category, 0.95

    return None


def classify_by_visual_features(image_path: Path) -> Tuple[str, float]:
    """Analyze image colors, spatial gradients, and edge geometry using OpenCV & NumPy.
    
    Provides reliable fallback classification when uploaded filenames are arbitrary
    (e.g., IMG_4821.jpg, photo_1.png).
    """
    if not image_path.exists():
        return CATEGORY_GENERAL, 0.3

    try:
        # Load image via cv2
        img_bgr = cv2.imread(str(image_path))
        if img_bgr is None:
            return CATEGORY_GENERAL, 0.3

        h, w = img_bgr.shape[:2]
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        # Region slices
        top_third = img_hsv[: h // 3, :]
        bottom_third = img_hsv[2 * (h // 3) :, :]
        mid_region = img_hsv[h // 4 : 3 * (h // 4), :]

        # 1. Sky & Outdoor Detection (Blue/Cyan in upper region)
        # Blue/Cyan Hue in OpenCV is ~90-135
        sky_mask = (top_third[:, :, 0] >= 90) & (top_third[:, :, 0] <= 135) & (top_third[:, :, 1] >= 40)
        sky_ratio = np.mean(sky_mask)

        # 2. Vegetation / Greenery Detection (Green Hue in OpenCV is ~35-85)
        green_mask = (img_hsv[:, :, 0] >= 35) & (img_hsv[:, :, 0] <= 85) & (img_hsv[:, :, 1] >= 40)
        green_ratio = np.mean(green_mask)

        # 3. Warm Interior Tones (Warm wood / interior lamps: Hue 8-28, moderate saturation)
        warm_mask = (img_hsv[:, :, 0] >= 8) & (img_hsv[:, :, 0] <= 28) & (img_hsv[:, :, 1] >= 50)
        warm_ratio = np.mean(warm_mask)

        # 4. Straight edge / structural line detection
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.mean(edges > 0)

        # Decision Heuristics:
        # Case A: High sky and green foliage -> Exterior or Balcony
        if sky_ratio > 0.12 or (green_ratio > 0.18 and sky_ratio > 0.05):
            # Check for balcony railing / framing lines in lower-to-middle half
            lower_edges = edges[h // 2 :, :]
            lower_edge_density = np.mean(lower_edges > 0)
            if lower_edge_density > 0.04 and green_ratio > 0.20:
                return CATEGORY_BALCONY, 0.78
            return CATEGORY_EXTERIOR, 0.82

        # Case B: Significant green vegetation with railing / terrace view
        if green_ratio > 0.22:
            return CATEGORY_BALCONY, 0.75

        # Case C: High warm interior tones & low edge complexity (soft bedding / headboards)
        if warm_ratio > 0.15 and edge_density < 0.06:
            return CATEGORY_BEDROOM, 0.70

        # Case D: High edge density and grid structure (cabinets, tiles, countertops)
        if edge_density > 0.065:
            # Check upper half for cabinet edges
            upper_edges = np.mean(edges[: h // 2, :] > 0)
            if upper_edges > 0.06:
                return CATEGORY_KITCHEN, 0.72

        # Case E: Moderate warm interior, open space -> Living Room
        if warm_ratio > 0.10:
            return CATEGORY_LIVING_ROOM, 0.65

        # Default interior living space
        return CATEGORY_LIVING_ROOM, 0.50

    except Exception:
        return CATEGORY_GENERAL, 0.30


def detect_image_category(
    image_path: Path,
    user_override: Optional[str] = None
) -> Tuple[str, str, float]:
    """Detect image category from user override, filename hints, or visual features.
    
    Returns:
    - category_key: e.g. 'kitchen', 'bedroom', 'balcony'
    - display_name: e.g. 'Modular Kitchen', 'Bedroom', 'Balcony View'
    - confidence: float between 0.0 and 1.0
    """
    # 1. User manual override takes highest priority
    if user_override and user_override.strip() and user_override.strip().lower() != "auto-detect":
        clean_override = user_override.strip().lower().replace(" ", "_")
        for cat_key in DISPLAY_NAMES:
            if cat_key in clean_override or clean_override in cat_key:
                return cat_key, DISPLAY_NAMES[cat_key], 1.0
        # Check display names
        for cat_key, disp in DISPLAY_NAMES.items():
            if disp.lower() == user_override.strip().lower():
                return cat_key, disp, 1.0
        return CATEGORY_GENERAL, user_override.strip().title(), 1.0

    # 2. Filename keyword heuristics
    file_hint = classify_by_filename(image_path.name)
    if file_hint:
        cat_key, conf = file_hint
        return cat_key, DISPLAY_NAMES.get(cat_key, cat_key.title()), conf

    # 3. Computer Vision feature analysis
    cat_key, conf = classify_by_visual_features(image_path)
    return cat_key, DISPLAY_NAMES.get(cat_key, cat_key.title()), conf
