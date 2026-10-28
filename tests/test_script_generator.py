"""Tests for script and scene caption generator in Property Studio AI.

Verifies:
- Accurate image-to-caption mapping (bedroom image gets bedroom caption, kitchen gets kitchen).
- Image ordering invariance: changing image list order preserves correct per-image captions.
- Scene structure bindings: every Scene object directly encapsulates its image path.
- Opening and closing scenes do not accidentally reuse feature captions.
- Strict factual accuracy: no hallucinated claims or amenities.
"""

import pytest
from pathlib import Path
from src.validators import PropertyInput, PropertyImage
from src.script_generator import generate_template_script, Scene, VideoScript


def create_dummy_property(num_images=5, features=None) -> PropertyInput:
    features = features or ["Two bedrooms", "Modular kitchen", "Balcony", "Parking"]
    return PropertyInput(
        name="Green Valley Residency",
        location="Chandigarh",
        price="₹85 lakh",
        property_type="2-BHK apartment",
        bedrooms=2,
        description="Spacious apartment in central Chandigarh.",
        features=features,
        call_to_action="Contact us today to arrange a visit.",
        images=[Path(f"img_{i}.jpg") for i in range(num_images)]
    )


def test_script_generation_scene_count():
    """Verify generated script has appropriate scene counts and valid durations."""
    for count in [4, 5, 6, 8]:
        prop = create_dummy_property(num_images=count)
        # Without closing CTA: exactly count scenes
        script_no_cta = generate_template_script(prop, include_closing_cta=False)
        assert len(script_no_cta.scenes) == count
        
        # With closing CTA: count + 1 scenes
        script_with_cta = generate_template_script(prop, include_closing_cta=True)
        assert len(script_with_cta.scenes) == count + 1
        assert 18.0 <= script_with_cta.estimated_duration <= 45.0


def test_script_generation_factual_accuracy():
    """Verify captions and voiceovers ONLY use user-supplied facts and do NOT invent facts."""
    prop = create_dummy_property(num_images=4, features=["Modular kitchen", "Balcony"])
    script = generate_template_script(prop)

    # Check Intro scene
    intro_scene = script.scenes[0]
    assert intro_scene.scene_type == "intro"
    assert "Green Valley Residency" in intro_scene.headline
    assert "Chandigarh" in intro_scene.subheadline
    assert "₹85 lakh" in f"{intro_scene.subheadline} {intro_scene.caption}"

    # Check that forbidden unverified claims never appear
    forbidden_terms = ["guaranteed return", "metro station 200m", "5-star luxury", "roi", "rERA registered 999"]
    for scene in script.scenes:
        text_corpus = f"{scene.headline} {scene.subheadline} {scene.caption} {scene.voiceover}".lower()
        for term in forbidden_terms:
            assert term not in text_corpus, f"Found unsupplied claim: '{term}' in scene {scene.scene_index}"

    # Check CTA scene
    cta_scene = script.scenes[-1]
    assert cta_scene.scene_type == "cta"
    assert "Contact us today" in cta_scene.headline


def test_image_caption_pairing():
    """Verify that each scene object directly encapsulates its image path and correct category."""
    img_exterior = PropertyImage(path=Path("01_exterior.jpg"), category="exterior")
    img_living = PropertyImage(path=Path("02_living_room.jpg"), category="living_room")
    img_kitchen = PropertyImage(path=Path("03_modular_kitchen.jpg"), category="kitchen")
    img_bedroom = PropertyImage(path=Path("04_bedroom.jpg"), category="bedroom")
    img_balcony = PropertyImage(path=Path("05_balcony_view.jpg"), category="balcony")

    prop = PropertyInput(
        name="Green Valley Residency",
        location="Chandigarh",
        price="₹85 lakh",
        property_type="2-BHK apartment",
        features=["Two bedrooms", "Modular kitchen", "Balcony", "Parking"],
        call_to_action="Contact us today to arrange a visit.",
        images=[img_exterior, img_living, img_kitchen, img_bedroom, img_balcony]
    )

    script = generate_template_script(prop)

    # Find scenes by category
    kitchen_scenes = [s for s in script.scenes if s.category == "kitchen"]
    bedroom_scenes = [s for s in script.scenes if s.category == "bedroom"]
    balcony_scenes = [s for s in script.scenes if s.category == "balcony"]

    assert len(kitchen_scenes) == 1
    assert kitchen_scenes[0].image_path == Path("03_modular_kitchen.jpg")
    assert "Kitchen" in kitchen_scenes[0].headline

    assert len(bedroom_scenes) == 1
    assert bedroom_scenes[0].image_path == Path("04_bedroom.jpg")
    assert "Bedroom" in bedroom_scenes[0].headline

    assert len(balcony_scenes) == 1
    assert balcony_scenes[0].image_path == Path("05_balcony_view.jpg")
    assert "Balcony" in balcony_scenes[0].headline


def test_image_ordering_does_not_shift_captions():
    """Verify that reordering uploaded images does NOT scramble captions between rooms."""
    # Order A: Exterior, Living, Kitchen, Bedroom, Balcony
    img_list_a = [
        PropertyImage(path=Path("01_exterior.jpg"), category="exterior"),
        PropertyImage(path=Path("02_living_room.jpg"), category="living_room"),
        PropertyImage(path=Path("03_modular_kitchen.jpg"), category="kitchen"),
        PropertyImage(path=Path("04_bedroom.jpg"), category="bedroom"),
        PropertyImage(path=Path("05_balcony_view.jpg"), category="balcony"),
    ]

    # Order B: Reversed order (Balcony, Bedroom, Kitchen, Living, Exterior)
    img_list_b = list(reversed(img_list_a))

    prop_a = PropertyInput(
        name="Green Valley Residency",
        location="Chandigarh",
        price="₹85 lakh",
        property_type="2-BHK apartment",
        features=["Modular kitchen", "Two bedrooms", "Balcony"],
        call_to_action="Contact us today",
        images=img_list_a
    )

    prop_b = PropertyInput(
        name="Green Valley Residency",
        location="Chandigarh",
        price="₹85 lakh",
        property_type="2-BHK apartment",
        features=["Modular kitchen", "Two bedrooms", "Balcony"],
        call_to_action="Contact us today",
        images=img_list_b
    )

    script_a = generate_template_script(prop_a, include_closing_cta=False)
    script_b = generate_template_script(prop_b, include_closing_cta=False)

    # In both scripts, bedroom image MUST have Bedroom caption
    bedroom_scene_a = next(s for s in script_a.scenes if s.image_path == Path("04_bedroom.jpg"))
    bedroom_scene_b = next(s for s in script_b.scenes if s.image_path == Path("04_bedroom.jpg"))

    assert "Bedroom" in bedroom_scene_a.headline
    assert "Bedroom" in bedroom_scene_b.headline
    assert "Kitchen" not in bedroom_scene_a.headline
    assert "Kitchen" not in bedroom_scene_b.headline

    # Kitchen image MUST have Kitchen caption
    kitchen_scene_a = next(s for s in script_a.scenes if s.image_path == Path("03_modular_kitchen.jpg"))
    kitchen_scene_b = next(s for s in script_b.scenes if s.image_path == Path("03_modular_kitchen.jpg"))

    assert "Kitchen" in kitchen_scene_a.headline
    assert "Kitchen" in kitchen_scene_b.headline
    assert "Bedroom" not in kitchen_scene_a.headline
    assert "Bedroom" not in kitchen_scene_b.headline


def test_bedroom_never_receives_kitchen_caption():
    """Verify that a bedroom scene NEVER receives kitchen headings or culinary subtitles."""
    bedroom_img = PropertyImage(path=Path("bedroom_photo.jpg"), category="bedroom")
    prop = PropertyInput(
        name="Green Valley Residency",
        location="Chandigarh",
        price="₹85 lakh",
        property_type="2-BHK apartment",
        features=["Modular kitchen", "Balcony"],
        call_to_action="Contact us today",
        images=[
            PropertyImage(path=Path("ext.jpg"), category="exterior"),
            PropertyImage(path=Path("liv.jpg"), category="living_room"),
            bedroom_img,
            PropertyImage(path=Path("bal.jpg"), category="balcony"),
        ]
    )
    script = generate_template_script(prop)
    bedroom_scene = next(s for s in script.scenes if s.image_path == Path("bedroom_photo.jpg"))

    assert "bedroom" in bedroom_scene.headline.lower()
    assert "kitchen" not in bedroom_scene.headline.lower()
    assert "culinary" not in bedroom_scene.subheadline.lower()
    assert "cabinetry" not in bedroom_scene.caption.lower()


def test_opening_and_closing_do_not_reuse_feature_captions():
    """Verify opening scene introduces the property and closing scene is dedicated CTA, without reusing features."""
    prop = create_dummy_property(num_images=5, features=["Two bedrooms", "Modular kitchen", "Balcony", "Parking"])
    script = generate_template_script(prop, include_closing_cta=True)

    opening_scene = script.scenes[0]
    closing_scene = script.scenes[-1]

    # Opening scene should be Intro / Property Title
    assert opening_scene.scene_type == "intro"
    assert opening_scene.headline == "Green Valley Residency"
    assert "Modular Kitchen" not in opening_scene.headline

    # Closing scene should be CTA
    assert closing_scene.scene_type == "cta"
    assert "Contact us today" in closing_scene.headline
    assert closing_scene.category_tag == "SCHEDULE A VISIT"
    assert "Modular Kitchen" not in closing_scene.headline
    assert "Bedroom" not in closing_scene.headline
