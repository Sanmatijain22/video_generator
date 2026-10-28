"""Tests for input validation module in Property Studio AI."""

import pytest
from pathlib import Path
from PIL import Image

from src.validators import (
    validate_property_details,
    validate_image_file,
    validate_image_count,
    validate_property_input,
    ValidationError
)


def test_required_field_validation():
    """Verify that empty required fields fail validation with clear messages."""
    # Missing name
    valid, msg = validate_property_details(
        name="",
        location="Chandigarh",
        price="₹85 lakh",
        property_type="Apartment",
        features=["Balcony"],
        call_to_action="Call now"
    )
    assert not valid
    assert "Property name is required" in msg

    # Missing location
    valid, msg = validate_property_details(
        name="Green Valley",
        location="",
        price="₹85 lakh",
        property_type="Apartment",
        features=["Balcony"],
        call_to_action="Call now"
    )
    assert not valid
    assert "location is required" in msg

    # Missing price
    valid, msg = validate_property_details(
        name="Green Valley",
        location="Chandigarh",
        price="",
        property_type="Apartment",
        features=["Balcony"],
        call_to_action="Call now"
    )
    assert not valid
    assert "price is required" in msg

    # Missing property type
    valid, msg = validate_property_details(
        name="Green Valley",
        location="Chandigarh",
        price="₹85 lakh",
        property_type="",
        features=["Balcony"],
        call_to_action="Call now"
    )
    assert not valid
    assert "property type is required" in msg.lower()

    # Missing features
    valid, msg = validate_property_details(
        name="Green Valley",
        location="Chandigarh",
        price="₹85 lakh",
        property_type="Apartment",
        features=[],
        call_to_action="Call now"
    )
    assert not valid
    assert "feature" in msg.lower()

    # Missing call to action
    valid, msg = validate_property_details(
        name="Green Valley",
        location="Chandigarh",
        price="₹85 lakh",
        property_type="Apartment",
        features=["Balcony"],
        call_to_action=""
    )
    assert not valid
    assert "call-to-action" in msg.lower() or "contact" in msg.lower()


def test_image_count_validation():
    """Verify constraints: 4 to 8 images allowed."""
    dummy_paths = [Path(f"img_{i}.jpg") for i in range(3)]
    
    # 3 images -> should fail (< 4)
    valid, msg = validate_image_count(dummy_paths, min_count=4, max_count=8)
    assert not valid
    assert "At least 4 images" in msg

    # 4 images -> should pass
    valid, msg = validate_image_count(dummy_paths + [Path("img_3.jpg")], min_count=4, max_count=8)
    assert valid
    assert msg is None

    # 8 images -> should pass
    eight_paths = [Path(f"img_{i}.jpg") for i in range(8)]
    valid, msg = validate_image_count(eight_paths, min_count=4, max_count=8)
    assert valid

    # 9 images -> should fail (> 8)
    nine_paths = [Path(f"img_{i}.jpg") for i in range(9)]
    valid, msg = validate_image_count(nine_paths, min_count=4, max_count=8)
    assert not valid
    assert "At most 8 images" in msg


def test_missing_optional_information(tmp_path):
    """Verify property works smoothly when optional fields (bedrooms, description) are omitted."""
    # Create 4 small valid images
    img_paths = []
    for i in range(4):
        p = tmp_path / f"test_{i}.jpg"
        img = Image.new("RGB", (400, 300), color=(100 + i * 20, 150, 200))
        img.save(p)
        img_paths.append(p)

    prop = validate_property_input(
        name="Sunny Heights",
        location="Pune",
        price="₹60 lakh",
        property_type="Studio",
        features=["Swimming Pool"],
        call_to_action="Contact agent",
        image_paths=img_paths,
        bedrooms=None,      # optional
        description=None    # optional
    )
    assert prop.bedrooms is None
    assert prop.description is None
    assert prop.name == "Sunny Heights"
    assert len(prop.images) == 4


def test_invalid_image_handling(tmp_path):
    """Verify invalid format or corrupted images trigger clear error."""
    # Non-image file
    text_file = tmp_path / "not_an_image.txt"
    text_file.write_text("Hello world")
    valid, msg = validate_image_file(text_file)
    assert not valid
    assert "Unsupported image format" in msg

    # Non-existent file
    valid, msg = validate_image_file(tmp_path / "ghost.jpg")
    assert not valid
    assert "not found" in msg

    # Corrupted image file
    corrupt_file = tmp_path / "corrupt.jpg"
    corrupt_file.write_bytes(b"\x00\x01\x02\x03\x04")
    valid, msg = validate_image_file(corrupt_file)
    assert not valid
    assert "Corrupted or invalid" in msg


def test_full_validation_raises_exception_on_invalid_input(tmp_path):
    """Verify validate_property_input raises ValidationError on bad inputs."""
    with pytest.raises(ValidationError):
        validate_property_input(
            name="",  # invalid
            location="Delhi",
            price="1 Cr",
            property_type="Villa",
            features=["Garden"],
            call_to_action="Inquire now",
            image_paths=[]
        )

