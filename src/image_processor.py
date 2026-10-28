"""Image processing and text overlay composition module for Property Studio AI.

Handles:
- Aspect-ratio preserving smart crop and resize to 1280x720 (16:9 widescreen).
- High-contrast, elegant typography and cards with safe margins.
- Glassmorphism lower-third cards ensuring 100% text readability on any photography.
- Professional category badges and real estate branding.
"""

from pathlib import Path
from typing import Tuple, Optional, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from .script_generator import SceneScript

TARGET_WIDTH = 1280
TARGET_HEIGHT = 720
ASPECT_RATIO = TARGET_WIDTH / TARGET_HEIGHT  # 16:9 (1.777...)


def get_default_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Load an available system font or fall back gracefully."""
    font_candidates = []
    if bold:
        font_candidates = [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "C:/Windows/Fonts/tahomabd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/HelveticaNeue-Bold.otf",
            "arialbd.ttf"
        ]
    else:
        font_candidates = [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "C:/Windows/Fonts/tahoma.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/HelveticaNeue.otf",
            "arial.ttf"
        ]

    for cand in font_candidates:
        try:
            return ImageFont.truetype(cand, size)
        except Exception:
            continue

    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    """Break text into multiple lines that fit within max_width pixels."""
    if not text:
        return []
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        try:
            bbox = font.getbbox(test_line)
            w = bbox[2] - bbox[0]
        except Exception:
            w = len(test_line) * (font.size if hasattr(font, 'size') else 10) * 0.6
            
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))
    return lines


def resize_and_crop_to_16_9(image_path: Path, target_w: int = TARGET_WIDTH, target_h: int = TARGET_HEIGHT) -> Image.Image:
    """Resize and center-crop an image to target dimensions without distortion.
    
    Preserves aspect ratio by scaling to cover target bounds, then center-cropping.
    """
    with Image.open(image_path) as img:
        img = img.convert("RGBA")
        src_w, src_h = img.size
        src_ratio = src_w / src_h
        target_ratio = target_w / target_h

        if src_ratio > target_ratio:
            # Source is wider than target: scale by height, crop width
            new_h = target_h
            new_w = int(src_w * (target_h / src_h))
        else:
            # Source is taller than target: scale by width, crop height
            new_w = target_w
            new_h = int(src_h * (target_w / src_w))

        resample_filter = getattr(Image.Resampling, 'LANCZOS', Image.LANCZOS)
        resized = img.resize((new_w, new_h), resample=resample_filter)

        left = max(0, (new_w - target_w) // 2)
        top = max(0, (new_h - target_h) // 2)
        right = left + target_w
        bottom = top + target_h

        cropped = resized.crop((left, top, right, bottom))
        return cropped


def render_scene_frame(image_path: Path, scene: SceneScript, target_w: int = TARGET_WIDTH, target_h: int = TARGET_HEIGHT) -> Image.Image:
    """Render a complete 1280x720 video frame with photography and professional real estate styling.
    
    Includes:
    - Base cropped photograph
    - Top header watermark: 'PROPERTY STUDIO AI • REAL ESTATE SHOWCASE'
    - Glassmorphism lower-third card with safe margins and gold accent line
    - High-visibility category badge
    - Crisp high-contrast headline, subheadline, and wrapped descriptive caption
    """
    base_img = resize_and_crop_to_16_9(image_path, target_w, target_h)
    
    # Overlay canvas
    overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 1. Top Bar / Watermark Header
    top_bar_height = 55
    for y in range(top_bar_height):
        alpha = int(140 * (1 - (y / top_bar_height) ** 1.8))
        draw.line([(0, y), (target_w, y)], fill=(10, 15, 25, alpha))

    font_brand = get_default_font(16, bold=True)
    draw.text((45, 16), "PROPERTY STUDIO AI", fill=(255, 255, 255, 230), font=font_brand)
    font_brand_sub = get_default_font(14, bold=False)
    draw.text((225, 18), "•  REAL ESTATE SHOWCASE", fill=(218, 165, 32, 220), font=font_brand_sub)

    # 2. Lower-third Glassmorphism Card (safe margins: 45px sides, 35px bottom)
    margin_x = 45
    margin_bottom = 35
    card_height = 205
    card_y0 = target_h - card_height - margin_bottom
    card_y1 = target_h - margin_bottom
    card_width = target_w - 2 * margin_x

    # Rounded rectangle card mask
    card_mask = Image.new("L", (card_width, card_height), 0)
    card_mask_draw = ImageDraw.Draw(card_mask)
    card_mask_draw.rounded_rectangle([(0, 0), (card_width, card_height)], radius=16, fill=255)

    # Semi-transparent deep slate-blue background
    card_bg = Image.new("RGBA", (card_width, card_height), (15, 23, 42, 228))
    
    # Top golden accent highlight bar
    card_draw = ImageDraw.Draw(card_bg)
    card_draw.line([(15, 0), (card_width - 15, 0)], fill=(218, 165, 32, 220), width=3)

    overlay.paste(card_bg, (margin_x, card_y0), card_mask)

    # 3. Card Typography & Content
    card_content_draw = ImageDraw.Draw(overlay)
    text_x = margin_x + 32
    curr_y = card_y0 + 18
    content_max_w = card_width - 64

    # Category Badge (Warm gold pill with dark text)
    font_badge = get_default_font(12, bold=True)
    badge_text = scene.category_tag.upper().strip()
    
    try:
        bbox = font_badge.getbbox(badge_text)
        badge_w = bbox[2] - bbox[0] + 18
        badge_h = bbox[3] - bbox[1] + 10
    except Exception:
        badge_w = len(badge_text) * 8 + 18
        badge_h = 24

    badge_rect = [(text_x, curr_y), (text_x + badge_w, curr_y + badge_h)]
    card_content_draw.rounded_rectangle(badge_rect, radius=5, fill=(218, 165, 32, 245))
    card_content_draw.text((text_x + 9, curr_y + 4), badge_text, fill=(15, 23, 42, 255), font=font_badge)

    curr_y += badge_h + 10

    # Headline (Bold, High Contrast Pure White with subtle shadow)
    font_headline = get_default_font(30, bold=True)
    card_content_draw.text((text_x + 1, curr_y + 1), scene.headline, fill=(0, 0, 0, 180), font=font_headline)
    card_content_draw.text((text_x, curr_y), scene.headline, fill=(255, 255, 255, 255), font=font_headline)
    curr_y += 38

    # Subheadline (Medium, Warm Light Slate)
    font_subhead = get_default_font(18, bold=True)
    card_content_draw.text((text_x, curr_y), scene.subheadline, fill=(226, 232, 240, 240), font=font_subhead)
    curr_y += 26

    # Descriptive Caption (Wrapped smoothly)
    font_cap = get_default_font(15, bold=False)
    caption_lines = wrap_text(scene.caption, font_cap, content_max_w)
    for line in caption_lines[:2]:  # at most 2 lines
        card_content_draw.text((text_x, curr_y), line, fill=(203, 213, 225, 230), font=font_cap)
        curr_y += 20

    # Composite overlay on base photograph
    final_frame = Image.alpha_composite(base_img, overlay).convert("RGB")
    return final_frame


def save_scene_frame(image_path: Path, scene: SceneScript, output_path: Path) -> Path:
    """Render and save a processed scene frame to disk."""
    frame = render_scene_frame(image_path, scene)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.save(output_path, "JPEG", quality=95)
    return output_path
