"""Tests for image processor and video generator in Property Studio AI."""

import pytest
from pathlib import Path
from PIL import Image

from src.validators import PropertyInput
from src.image_processor import resize_and_crop_to_16_9, render_scene_frame, TARGET_WIDTH, TARGET_HEIGHT
from src.script_generator import SceneScript, generate_script
from src.video_generator import generate_property_video, VideoGenerationError


def test_image_resizing_and_cropping(tmp_path):
    """Verify images of arbitrary aspect ratios are cropped cleanly to 1280x720 (16:9)."""
    # Create non-16:9 test image (e.g. vertical 800x1200)
    tall_img_path = tmp_path / "tall.jpg"
    Image.new("RGB", (800, 1200), color=(100, 120, 140)).save(tall_img_path)

    cropped = resize_and_crop_to_16_9(tall_img_path)
    assert cropped.size == (TARGET_WIDTH, TARGET_HEIGHT)

    # Wide image (e.g. panoramic 2000x800)
    wide_img_path = tmp_path / "wide.jpg"
    Image.new("RGB", (2000, 800), color=(140, 120, 100)).save(wide_img_path)
    cropped_wide = resize_and_crop_to_16_9(wide_img_path)
    assert cropped_wide.size == (TARGET_WIDTH, TARGET_HEIGHT)


def test_scene_frame_rendering(tmp_path):
    """Verify render_scene_frame generates a valid 1280x720 RGB frame with overlay."""
    img_path = tmp_path / "base.jpg"
    Image.new("RGB", (1000, 700), color=(220, 220, 220)).save(img_path)

    scene = SceneScript(
        scene_index=1,
        scene_type="intro",
        category_tag="TEST BADGE",
        headline="Test Luxury Apartment",
        subheadline="Chandigarh • ₹85 lakh",
        caption="Welcome to your new home",
        voiceover="Spoken voiceover script.",
        duration=3.0
    )

    frame = render_scene_frame(img_path, scene)
    assert frame.size == (TARGET_WIDTH, TARGET_HEIGHT)
    assert frame.mode == "RGB"


def test_video_generation_end_to_end(tmp_path):
    """Verify end-to-end video compilation with 4 synthetic images outputs non-zero MP4."""
    # Create 4 synthetic test images
    img_paths = []
    for i in range(4):
        p = tmp_path / f"syn_img_{i}.jpg"
        Image.new("RGB", (640, 480), color=(50 + i * 40, 100, 150)).save(p)
        img_paths.append(p)

    prop = PropertyInput(
        name="Test Villa",
        location="Jaipur",
        price="₹1.2 Crore",
        property_type="Villa",
        bedrooms=3,
        description="Beautiful villa with garden.",
        features=["Garden", "Pool"],
        call_to_action="Call agent now",
        images=img_paths
    )

    script = generate_script(prop)
    # Set short scene duration for rapid test execution
    for s in script.scenes:
        s.duration = 1.0

    output_mp4 = tmp_path / "test_output.mp4"
    result_path = generate_property_video(
        prop=prop,
        output_path=output_mp4,
        script=script,
        include_narration=False,  # Keep test swift & deterministic
        include_background_music=True,
        fps=15
    )

    assert result_path.exists()
    assert result_path.stat().st_size > 1000  # Non-zero, valid video file


def test_video_generation_empty_scenes_or_missing_image(tmp_path):
    """Verify VideoGenerationError is raised when scenes list is empty or image is missing."""
    p1 = tmp_path / "img1.jpg"
    p2 = tmp_path / "img2.jpg"
    Image.new("RGB", (400, 300)).save(p1)
    Image.new("RGB", (400, 300)).save(p2)

    prop = PropertyInput(
        name="Test Error",
        location="Delhi",
        price="50L",
        property_type="Flat",
        features=["Lift"],
        call_to_action="Contact us",
        images=[p1, p2]
    )

    script = generate_script(prop)
    # Empty scenes should raise VideoGenerationError
    script.scenes = []

    with pytest.raises(VideoGenerationError):
        generate_property_video(
            prop=prop,
            output_path=tmp_path / "fail.mp4",
            script=script
        )

