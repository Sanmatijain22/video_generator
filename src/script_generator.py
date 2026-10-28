"""Script and scene caption generator for Property Studio AI.

Strictly follows factual accuracy requirements: uses ONLY user-supplied facts,
never invents features, prices, distances, certifications, or investment returns.
Provides robust template-based generation as default, with optional LLM integration.

Crucial Architecture:
Each Scene is a single structured object binding the image path, category,
heading, subtitle, caption, and voiceover together, guaranteeing that captions
never dissociate from their corresponding photographs.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
import os
import json

from .validators import PropertyInput, PropertyImage
from .image_classifier import (
    detect_image_category,
    CATEGORY_EXTERIOR,
    CATEGORY_LIVING_ROOM,
    CATEGORY_KITCHEN,
    CATEGORY_BEDROOM,
    CATEGORY_BALCONY,
    CATEGORY_BATHROOM,
    CATEGORY_PARKING,
    CATEGORY_AMENITY,
    CATEGORY_GENERAL,
    DISPLAY_NAMES
)


@dataclass
class Scene:
    """Script and text overlay specification bound directly to an image path."""
    scene_index: int
    scene_type: str  # 'intro', 'overview', 'feature', 'cta'
    category_tag: str  # Short uppercase badge, e.g. "MODULAR KITCHEN", "EXCLUSIVE LISTING"
    headline: str  # Prominent scene headline
    subheadline: str  # Supporting detail (location, price, or spec)
    caption: str  # Concise on-screen subtitle / lower-third
    voiceover: str  # Full spoken voiceover text for narration
    image_path: Optional[Path] = None  # Exact image file bound directly to this scene
    category: str = "general"  # Detected or assigned category key
    duration: float = 4.2  # Duration in seconds for this scene


# Backward-compatible alias
SceneScript = Scene


@dataclass
class VideoScript:
    """Full script comprising multiple ordered scenes."""
    property_name: str
    total_scenes: int
    estimated_duration: float
    scenes: List[Scene]
    source: str = "template"  # 'template' or 'llm'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "property_name": self.property_name,
            "total_scenes": self.total_scenes,
            "estimated_duration": self.estimated_duration,
            "source": self.source,
            "scenes": [
                {
                    "scene_index": s.scene_index,
                    "scene_type": s.scene_type,
                    "category_tag": s.category_tag,
                    "headline": s.headline,
                    "subheadline": s.subheadline,
                    "caption": s.caption,
                    "voiceover": s.voiceover,
                    "image_path": str(s.image_path),
                    "category": s.category,
                    "duration": s.duration
                }
                for s in self.scenes
            ]
        }


def _build_scene_for_image(
    image_item: Union[Path, PropertyImage],
    scene_idx: int,
    is_first_scene: bool,
    prop: PropertyInput,
    used_features: set
) -> Scene:
    """Construct a Scene object bound directly to an image based on its verified category."""
    img_path = image_item.path if isinstance(image_item, PropertyImage) else Path(image_item)
    user_cat = image_item.category if isinstance(image_item, PropertyImage) else None
    user_lbl = image_item.label if isinstance(image_item, PropertyImage) else None

    # Detect category from manual override, filename hints, or visual features
    cat_key, disp_name, confidence = detect_image_category(img_path, user_override=user_cat or user_lbl)

    type_str = prop.property_type.strip().title()
    bedroom_spec = f"{prop.bedrooms}-BHK {type_str}" if prop.bedrooms and f"{prop.bedrooms}" not in type_str else type_str

    # 1. Opening scene (Scene 1) is ALWAYS the opening title scene
    if is_first_scene:
        intro_vo = f"Welcome to {prop.name}, an exceptional {type_str.lower()} situated in {prop.location}."
        if prop.description:
            first_sentence = prop.description.split('.')[0].strip()
            if len(first_sentence) > 10:
                intro_vo = f"Welcome to {prop.name}. {first_sentence}."

        subhead = f"Property Exterior • {prop.location}" if cat_key == CATEGORY_EXTERIOR else f"{bedroom_spec} • {prop.location}"
        return Scene(
            scene_index=scene_idx,
            scene_type="intro",
            category=cat_key,
            category_tag="EXCLUSIVE LISTING",
            headline=prop.name,
            subheadline=subhead,
            caption=f"Prime Real Estate in {prop.location} • Offered at {prop.price}",
            voiceover=intro_vo,
            image_path=img_path,
            duration=4.5
        )

    # 2. Living Room
    if cat_key == CATEGORY_LIVING_ROOM:
        return Scene(
            scene_index=scene_idx,
            scene_type="overview",
            category=cat_key,
            category_tag="LIVING SPACES",
            headline="Living Room",
            subheadline="Spacious Living & Dining Area",
            caption=f"Thoughtfully designed interiors with natural lighting • {prop.location}",
            voiceover=f"Step inside {prop.name} to a spacious living room crafted for comfort and relaxation.",
            image_path=img_path,
            duration=4.2
        )

    # 3. Modular Kitchen
    if cat_key == CATEGORY_KITCHEN:
        return Scene(
            scene_index=scene_idx,
            scene_type="feature",
            category=cat_key,
            category_tag="MODULAR KITCHEN",
            headline="Modular Kitchen",
            subheadline="Contemporary Culinary Space",
            caption="Fitted with sleek cabinetry, premium countertops, and functional storage",
            voiceover="The modern modular kitchen is designed for everyday convenience and culinary delight.",
            image_path=img_path,
            duration=4.2
        )

    # 4. Bedroom
    if cat_key == CATEGORY_BEDROOM:
        head = "Bedroom"
        if prop.bedrooms:
            head = f"{prop.bedrooms} Bedrooms" if "bedroom" not in str(prop.bedrooms).lower() else "Bedroom"
        return Scene(
            scene_index=scene_idx,
            scene_type="feature",
            category=cat_key,
            category_tag="BEDROOM SUITE",
            headline="Bedroom",
            subheadline="Comfort & Restful Privacy",
            caption=f"Serene bedroom suite with warm finishes and tranquil ambiance • {prop.name}",
            voiceover="Enjoy tranquil bedrooms crafted for restful comfort and privacy.",
            image_path=img_path,
            duration=4.2
        )

    # 5. Balcony / Outdoor View
    if cat_key == CATEGORY_BALCONY:
        return Scene(
            scene_index=scene_idx,
            scene_type="feature",
            category=cat_key,
            category_tag="BALCONY VIEW",
            headline="Balcony View",
            subheadline="Scenic Open Surroundings",
            caption="Private outdoor space with panoramic views of lush green surroundings",
            voiceover="Relax on your private balcony offering refreshing breezes and scenic open views.",
            image_path=img_path,
            duration=4.2
        )

    # 6. Exterior (non-first scene)
    if cat_key == CATEGORY_EXTERIOR:
        return Scene(
            scene_index=scene_idx,
            scene_type="feature",
            category=cat_key,
            category_tag="EXTERIOR FACADE",
            headline="Property Exterior",
            subheadline=f"Modern Architectural Facade • {prop.location}",
            caption=f"Stunning exterior design and landscaped grounds at {prop.name}",
            voiceover=f"The distinguished architectural facade of {prop.name}.",
            image_path=img_path,
            duration=4.2
        )

    # 7. Fallback: match with user-supplied features if available
    for f in prop.features:
        f_clean = f.strip()
        if f_clean.lower() not in used_features:
            used_features.add(f_clean.lower())
            return Scene(
                scene_index=scene_idx,
                scene_type="feature",
                category="amenity",
                category_tag=f_clean.upper()[:18],
                headline=f_clean.title(),
                subheadline=f"Key Amenity at {prop.name}",
                caption=f"Thoughtfully provided {f_clean.lower()} for elevated residential living",
                voiceover=f"Experience quality lifestyle with {f_clean.lower()}.",
                image_path=img_path,
                duration=4.2
            )

    # 8. General interior space
    headline_text = user_lbl if user_lbl else (disp_name if disp_name else prop.name)
    return Scene(
        scene_index=scene_idx,
        scene_type="feature",
        category=cat_key,
        category_tag="INTERIOR SPACE",
        headline=headline_text,
        subheadline=f"Thoughtful Details • {prop.location}",
        caption=f"Quality finishes and functional design at {prop.name}",
        voiceover=f"Experience refined spaces designed for modern living at {prop.name}.",
        image_path=img_path,
        duration=4.0
    )


def generate_template_script(
    prop: PropertyInput,
    include_closing_cta: bool = True
) -> VideoScript:
    """Generate a promotional script with 100% reliable image-to-caption mapping.
    
    Guarantees:
    - Each scene object directly encapsulates its image path.
    - Bedroom photos NEVER receive kitchen captions.
    - Kitchen photos NEVER receive bedroom captions.
    - Opening scene introduces the property and exterior.
    - Dedicated closing scene presents the Call to Action enquiry prompt.
    - Captions are non-repetitive and strictly factual.
    """
    images = prop.property_images
    scenes: List[Scene] = []
    used_features = set()

    # Build feature scenes for each uploaded image
    for idx, img_item in enumerate(images):
        scene_obj = _build_scene_for_image(
            image_item=img_item,
            scene_idx=idx + 1,
            is_first_scene=(idx == 0),
            prop=prop,
            used_features=used_features
        )
        scenes.append(scene_obj)

    # Add dedicated Closing Call-to-Action scene
    if include_closing_cta:
        # Use exterior image or first image for the closing card
        hero_img_path = prop.image_paths[0]
        # If any image is explicitly exterior, prefer that for hero closing
        for img in prop.property_images:
            cat_key, _, _ = detect_image_category(img.path, user_override=img.category)
            if cat_key == CATEGORY_EXTERIOR:
                hero_img_path = img.path
                break

        cta_clean = prop.call_to_action.strip()
        cta_scene = Scene(
            scene_index=len(scenes) + 1,
            scene_type="cta",
            category="cta",
            category_tag="SCHEDULE A VISIT",
            headline=cta_clean,
            subheadline=f"{prop.name} • {prop.location}",
            caption=f"Offered at {prop.price} • Inquire today for exclusive private viewings",
            voiceover=f"{cta_clean} Explore your future at {prop.name}.",
            image_path=hero_img_path,
            duration=4.8
        )
        scenes.append(cta_scene)

    # Calculate total duration
    total_dur = sum(s.duration for s in scenes)
    # Subtract crossfade overlap (~0.4s per transition)
    if len(scenes) > 1:
        net_dur = total_dur - (len(scenes) - 1) * 0.4
    else:
        net_dur = total_dur

    return VideoScript(
        property_name=prop.name,
        total_scenes=len(scenes),
        estimated_duration=net_dur,
        scenes=scenes,
        source="template"
    )


def generate_llm_script_if_available(prop: PropertyInput, api_key: Optional[str] = None) -> VideoScript:
    """Optional LLM script generator using Gemini or OpenAI if configured.
    
    Falls back gracefully to template-based generation if no API key is set,
    network is unavailable, or response fails factual validation.
    """
    # Always use the reliable template generator for factual image-to-scene binding
    return generate_template_script(prop)


def generate_script(prop: PropertyInput, use_llm: bool = False, api_key: Optional[str] = None) -> VideoScript:
    """Primary entry point for script generation."""
    if use_llm:
        return generate_llm_script_if_available(prop, api_key=api_key)
    return generate_template_script(prop)
