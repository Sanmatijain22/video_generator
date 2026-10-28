"""Standalone script to generate sample promotional MP4 video for Green Valley Residency.

Uses sample_data/sample_property.json and assets/sample_images/*.jpg.
Outputs to output/green_valley_residency_promo.mp4.
"""

from pathlib import Path
import json
import sys
import time

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.validators import validate_property_input
from src.script_generator import generate_script
from src.video_generator import generate_property_video


def main():
    print("=" * 65)
    print("  PROPERTY STUDIO AI — SAMPLE PROMOTIONAL VIDEO GENERATION")
    print("=" * 65)

    json_path = PROJECT_ROOT / "sample_data" / "sample_property.json"
    if not json_path.exists():
        print(f"Error: Sample data JSON not found at {json_path}")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Property Name : {data['name']}")
    print(f"Location      : {data['location']}")
    print(f"Price         : {data['price']}")
    print(f"Type          : {data['property_type']}")
    print(f"Features      : {', '.join(data['features'])}")

    # Resolve image paths relative to project root
    resolved_images = []
    for rel_path in data["images"]:
        p = PROJECT_ROOT / rel_path
        if not p.exists():
            print(f"Error: Image not found at {p}")
            sys.exit(1)
        resolved_images.append(p)

    print(f"Images Loaded : {len(resolved_images)} images verified.")

    # Validate input
    print("\n[Step 1/4] Validating property details and images...")
    prop_input = validate_property_input(
        name=data["name"],
        location=data["location"],
        price=data["price"],
        property_type=data["property_type"],
        features=data["features"],
        call_to_action=data["call_to_action"],
        image_paths=resolved_images,
        bedrooms=data.get("bedrooms"),
        description=data.get("description")
    )
    print("  -> Input validation passed successfully.")

    # Generate Script
    print("\n[Step 2/4] Generating promotional scene scripts and captions...")
    script = generate_script(prop_input)
    print(f"  -> Generated {len(script.scenes)} scenes (Est. Duration: {script.estimated_duration:.1f}s)")
    for s in script.scenes:
        print(f"     • Scene {s.scene_index} [{s.category_tag}]: {s.headline} ({s.duration}s)")
        print(f"       Sub: {s.subheadline}")
        print(f"       VO : {s.voiceover}")

    # Generate Video
    print("\n[Step 3/4] Generating MP4 video with overlays and audio...")
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_mp4 = output_dir / "green_valley_residency_promo.mp4"

    def progress_callback(ratio: float, status: str):
        pct = int(ratio * 100)
        bar = "█" * (pct // 5) + "░" * (20 - (pct // 5))
        print(f"\r  [{bar}] {pct:3d}% — {status[:50]:<50}", end="", flush=True)

    start_time = time.time()
    generate_property_video(
        prop=prop_input,
        output_path=output_mp4,
        script=script,
        include_narration=True,
        include_background_music=True,
        fps=24,
        progress_callback=progress_callback
    )
    elapsed = time.time() - start_time
    print(f"\n  -> Video generation completed in {elapsed:.1f} seconds!")

    # Verify output
    print("\n[Step 4/4] Verifying generated MP4 file...")
    if not output_mp4.exists():
        print(f"Error: Output file not found at {output_mp4}")
        sys.exit(1)

    file_size_mb = output_mp4.stat().st_size / (1024 * 1024)
    print(f"  -> Output Path : {output_mp4}")
    print(f"  -> File Size   : {file_size_mb:.2f} MB ({output_mp4.stat().st_size} bytes)")

    # Attempt to read video metadata using moviepy or ffprobe
    try:
        from moviepy import VideoFileClip
        with VideoFileClip(str(output_mp4)) as clip:
            print(f"  -> Resolution  : {clip.w}x{clip.h} (16:9 Landscape)")
            print(f"  -> Duration    : {clip.duration:.2f} seconds")
            print(f"  -> FPS         : {clip.fps}")
            has_audio = clip.audio is not None
            print(f"  -> Audio Track : {'Yes (Narration + Ambient Music)' if has_audio else 'None'}")
    except Exception as e:
        print(f"  -> Metadata check note: {e}")

    print("\n" + "=" * 65)
    print("  SUCCESS: Promo video generated and ready for presentation!")
    print("=" * 65)


if __name__ == "__main__":
    main()
