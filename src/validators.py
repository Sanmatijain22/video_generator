"""Input validation module for Property Studio AI.

Validates property details, image counts, image formats, file integrity,
and supports structured PropertyImage associations with room categories.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union
from pathlib import Path
from PIL import Image
import os


class ValidationError(Exception):
    """Custom exception raised when property input validation fails."""
    pass


@dataclass
class PropertyImage:
    """Structured property image with room category and user label."""
    path: Path
    category: Optional[str] = None  # e.g. 'exterior', 'living_room', 'kitchen', 'bedroom', 'balcony'
    label: Optional[str] = None     # Optional user-specified title

    def __post_init__(self):
        if isinstance(self.path, str):
            self.path = Path(self.path)

    def __fspath__(self):
        return str(self.path)

    @property
    def name(self) -> str:
        return self.path.name


@dataclass
class PropertyInput:
    """Validated property details and associated images."""
    name: str
    location: str
    price: str
    property_type: str
    features: List[str]
    call_to_action: str
    images: List[Union[Path, PropertyImage]]
    bedrooms: Optional[int] = None
    description: Optional[str] = None

    @property
    def image_paths(self) -> List[Path]:
        """Return list of image Paths regardless of whether stored as Path or PropertyImage."""
        return [img.path if isinstance(img, PropertyImage) else Path(img) for img in self.images]

    @property
    def property_images(self) -> List[PropertyImage]:
        """Return list of PropertyImage objects."""
        result = []
        for img in self.images:
            if isinstance(img, PropertyImage):
                result.append(img)
            else:
                result.append(PropertyImage(path=Path(img)))
        return result

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "location": self.location,
            "price": self.price,
            "property_type": self.property_type,
            "bedrooms": self.bedrooms,
            "description": self.description,
            "features": self.features,
            "call_to_action": self.call_to_action,
            "images": [str(p) for p in self.image_paths]
        }


def validate_property_details(
    name: Optional[str],
    location: Optional[str],
    price: Optional[str],
    property_type: Optional[str],
    features: Optional[List[str]],
    call_to_action: Optional[str],
    bedrooms: Optional[int] = None,
    description: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Validate textual fields for property details.
    
    Returns (True, None) if valid, or (False, error_message).
    """
    if not name or not name.strip():
        return False, "Property name is required."
    
    if not location or not location.strip():
        return False, "Property location is required."
    
    if not price or not price.strip():
        return False, "Property price is required."
        
    if not property_type or not property_type.strip():
        return False, "Property type is required."
        
    cleaned_features = [f.strip() for f in (features or []) if f and f.strip()]
    if not cleaned_features:
        return False, "At least one key feature or amenity is required."
        
    if not call_to_action or not call_to_action.strip():
        return False, "Contact information or call-to-action text is required."

    if bedrooms is not None and bedrooms < 0:
        return False, "Number of bedrooms cannot be negative."

    return True, None


def validate_image_file(image_path: Union[Path, PropertyImage]) -> Tuple[bool, Optional[str]]:
    """Validate that a file exists, is an image, and can be opened by PIL.
    
    Returns (True, None) if valid, or (False, error_message).
    """
    path_obj = image_path.path if isinstance(image_path, PropertyImage) else Path(image_path)
    if not path_obj.exists():
        return False, f"Image file not found: {path_obj}"
        
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    if path_obj.suffix.lower() not in allowed_extensions:
        return False, f"Unsupported image format '{path_obj.suffix}'. Allowed formats: JPG, PNG, WEBP."
        
    try:
        with Image.open(path_obj) as img:
            img.verify()
        with Image.open(path_obj) as img:
            width, height = img.size
            if width < 100 or height < 100:
                return False, f"Image {path_obj.name} is too small ({width}x{height}px). Minimum is 100x100px."
    except Exception as e:
        return False, f"Corrupted or invalid image file '{path_obj.name}': {str(e)}"
        
    return True, None


def validate_image_count(images: List[Union[Path, PropertyImage]], min_count: int = 4, max_count: int = 8) -> Tuple[bool, Optional[str]]:
    """Validate image count is within the required range (default 4-8 images)."""
    count = len(images)
    if count < min_count:
        return False, f"At least {min_count} images are required (provided {count})."
    if count > max_count:
        return False, f"At most {max_count} images are allowed (provided {count})."
    return True, None


def validate_property_input(
    name: str,
    location: str,
    price: str,
    property_type: str,
    features: List[str],
    call_to_action: str,
    image_paths: List[Union[Path, PropertyImage]],
    bedrooms: Optional[int] = None,
    description: Optional[str] = None,
    min_images: int = 4,
    max_images: int = 8
) -> PropertyInput:
    """Full end-to-end validation. Returns PropertyInput or raises ValidationError."""
    valid_details, detail_err = validate_property_details(
        name=name,
        location=location,
        price=price,
        property_type=property_type,
        features=features,
        call_to_action=call_to_action,
        bedrooms=bedrooms,
        description=description
    )
    if not valid_details:
        raise ValidationError(detail_err)

    valid_count, count_err = validate_image_count(image_paths, min_count=min_images, max_count=max_images)
    if not valid_count:
        raise ValidationError(count_err)

    for img_item in image_paths:
        valid_img, img_err = validate_image_file(img_item)
        if not valid_img:
            raise ValidationError(img_err)

    cleaned_features = [f.strip() for f in features if f and f.strip()]
    
    # Store images preserving PropertyImage objects if provided
    parsed_images: List[Union[Path, PropertyImage]] = []
    for item in image_paths:
        if isinstance(item, PropertyImage):
            parsed_images.append(item)
        else:
            parsed_images.append(Path(item))

    return PropertyInput(
        name=name.strip(),
        location=location.strip(),
        price=price.strip(),
        property_type=property_type.strip(),
        bedrooms=bedrooms,
        description=description.strip() if description else None,
        features=cleaned_features,
        call_to_action=call_to_action.strip(),
        images=parsed_images
    )
