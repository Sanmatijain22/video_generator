"""Video generation engine for Property Studio AI.

Orchestrates:
- Scene frame rendering with readable text overlays and category badges.
- Smooth transitions between property scenes.
- Audio synchronization (voiceover narration and ambient background music).
- H.264 MP4 export at 1280x720 resolution.
- Temporary file management and cleanup.
"""

from pathlib import Path
from typing import Optional, Callable
import tempfile
import shutil
import numpy as np
from PIL import Image

from moviepy import ImageClip, CompositeVideoClip, AudioFileClip
import moviepy.video.fx as vfx

from .validators import PropertyInput
from .script_generator import VideoScript, generate_script
from .image_processor import render_scene_frame
from .audio_generator import generate_full_audio_track


class VideoGenerationError(Exception):
    """Raised when video compilation or encoding fails."""
    pass


def generate_property_video(
    prop: PropertyInput,
    output_path: Path,
    script: Optional[VideoScript] = None,
    include_narration: bool = True,
    include_background_music: bool = True,
    fps: int = 24,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Path:
    """Generate a complete promotional property video MP4.
    
    Parameters:
    - prop: Validated PropertyInput object containing details and image paths
    - output_path: Destination path for the generated MP4 file
    - script: Optional pre-generated VideoScript; if None, generates default template script
    - include_narration: Whether to generate TTS narration
    - include_background_music: Whether to synthesize royalty-free ambient music
    - fps: Output frames per second (default 24)
    - progress_callback: Optional function(progress_ratio: float, status_text: str)
    
    Returns:
    - Path to verified output MP4 file
    """
    def update_progress(ratio: float, text: str):
        if progress_callback:
            progress_callback(ratio, text)

    update_progress(0.05, "Validating input and preparing script...")

    if script is None:
        script = generate_script(prop)

    if not script.scenes:
        raise VideoGenerationError("Script contains no scenes to render.")

    # Use an isolated temporary directory for intermediate files
    temp_dir = Path(tempfile.mkdtemp(prefix="prop_video_"))
    
    try:
        clips = []
        scene_start_times = []
        total_scenes = len(script.scenes)
        transition_duration = 0.4
        curr_start = 0.0

        update_progress(0.15, "Rendering scene overlays and typography...")
        for idx, scene in enumerate(script.scenes):
            update_progress(
                0.15 + (0.35 * (idx / total_scenes)),
                f"Processing scene {idx + 1}/{total_scenes}: {scene.headline}..."
            )
            
            # Use image path directly bound to the scene object
            img_path = scene.image_path if hasattr(scene, "image_path") and scene.image_path else (prop.image_paths[idx % len(prop.image_paths)])
            if not Path(img_path).exists():
                raise VideoGenerationError(f"Image not found for scene {scene.scene_index}: {img_path}")

            # Render composite frame
            frame_img = render_scene_frame(img_path, scene)
            frame_array = np.array(frame_img)
            
            # Create ImageClip
            clip = ImageClip(frame_array)
            if hasattr(clip, "with_duration"):
                clip = clip.with_duration(scene.duration)
            else:
                clip = clip.set_duration(scene.duration)

            scene_start_times.append(curr_start)

            # Smooth crossfade transition directly over the previous scene (eliminating any black frames)
            if idx > 0:
                trans = min(transition_duration, scene.duration * 0.3)
                if hasattr(clip, "with_start"):
                    clip = clip.with_start(curr_start).with_effects([vfx.CrossFadeIn(trans)])
                else:
                    clip = clip.set_start(curr_start).crossfadein(trans)
            else:
                if hasattr(clip, "with_start"):
                    clip = clip.with_start(0.0)
                else:
                    clip = clip.set_start(0.0)

            clips.append(clip)
            
            # Advance start time for subsequent scene by (duration - transition_duration)
            if idx < total_scenes - 1:
                curr_start += scene.duration - transition_duration
            else:
                curr_start += scene.duration

        update_progress(0.55, "Compositing scenes with smooth crossfades...")
        final_video = CompositeVideoClip(clips)
        video_total_duration = final_video.duration

        update_progress(0.65, "Generating synchronized audio track and narration...")
        audio_path = None
        try:
            audio_path = generate_full_audio_track(
                script=script,
                temp_dir=temp_dir,
                include_narration=include_narration,
                include_background_music=include_background_music,
                scene_start_times=scene_start_times,
                total_duration=video_total_duration
            )
        except Exception:
            # Audio is strictly optional and must never crash video generation
            audio_path = None

        if audio_path and audio_path.exists():
            update_progress(0.75, "Muxing audio track with video timeline...")
            try:
                audio_clip = AudioFileClip(str(audio_path))
                if hasattr(final_video, "with_audio"):
                    final_video = final_video.with_audio(audio_clip)
                else:
                    final_video = final_video.set_audio(audio_clip)
            except Exception:
                pass

        update_progress(0.80, "Encoding H.264 MP4 video file...")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        final_video.write_videofile(
            str(output_path),
            fps=fps,
            codec="libx264",
            audio_codec="aac" if audio_path else None,
            preset="fast",
            threads=4,
            logger=None
        )

        # Close all MoviePy clips
        try:
            final_video.close()
            for c in clips:
                c.close()
        except Exception:
            pass

        # Verify output
        if not output_path.exists():
            raise VideoGenerationError(f"Video file was not created at {output_path}")

        file_size = output_path.stat().st_size
        if file_size == 0:
            output_path.unlink(missing_ok=True)
            raise VideoGenerationError("Generated MP4 file is empty (0 bytes).")

        update_progress(1.0, "Video generated successfully!")
        return output_path

    except Exception as e:
        if isinstance(e, VideoGenerationError):
            raise
        raise VideoGenerationError(f"Video encoding failed: {str(e)}") from e

    finally:
        # Safely remove intermediate temp files
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

