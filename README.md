# Property Studio AI — AI Property Video Generator

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![MoviePy](https://img.shields.io/badge/Video-MoviePy%202.x-brightgreen.svg)](https://zulko.github.io/moviepy/)
[![Tests](https://img.shields.io/badge/Tests-12%20Passed-success.svg)](https://docs.pytest.org/)

**Property Studio AI** is an automated video production system engineered for real estate marketing teams. It converts property details and photos into 20–40 second branded promotional MP4 videos featuring scene transitions, typography overlays, text-to-speech voiceovers, and ambient background music — without requiring manual video editing or paid AI subscriptions.

---

## 📋 Features

- **Property Information Intake:** Polished form for property name, location, price, type, bedrooms, description, amenities, and call-to-action.
- **Image Framing & Cropping:** Smart aspect-ratio preserving center-crop to 1280×720 (16:9 widescreen) with Pillow.
- **Factual Script & Caption Generation:** Rule-based template generator strictly using user-provided details (zero hallucinated amenities, prices, or distances).
- **Optional LLM Script Enhancement:** Seamless plug-in for Gemini or OpenAI with automatic fallback.
- **Visual Typography & Badging:** Safe-margin lower-third cards, category pill badges, and branding headers.
- **Voiceover Narration:** High-fidelity TTS speech synthesized per scene via gTTS.
- **Royalty-Free Ambient Music:** Procedurally generated ambient soundtrack synthesized with NumPy/WAV (100% offline, zero copyright risks).
- **H.264 Video Rendering:** High-speed 720p 24fps MP4 compilation with MoviePy and FFmpeg.
- **Interactive UI & In-App Player:** Full preview and one-click MP4 download in Streamlit.
- **1-Click Sample Preset:** Instant loading and generation of the sample listing (*Green Valley Residency, Chandigarh*).

---

## 🏗️ Project Structure

```
ai-property-video-generator/
├── app.py                     # Streamlit web application
├── requirements.txt           # Python dependencies
├── README.md                  # System documentation & setup guide
├── .gitignore                 # Version control exclusions
├── .env.example               # Environment template for optional LLM keys
├── src/
│   ├── __init__.py
│   ├── validators.py          # Input validation & image integrity checks
│   ├── script_generator.py    # Rule-based & optional LLM scene scripting
│   ├── image_processor.py     # Pillow resizing, cropping & card overlays
│   ├── audio_generator.py     # Procedural music synthesis & TTS narration
│   └── video_generator.py     # MoviePy timeline composition & MP4 export
├── assets/
│   ├── README.md
│   ├── audio/
│   └── sample_images/         # 5 bundled 1280x720 property images
├── sample_data/
│   └── sample_property.json   # Green Valley Residency listing data
├── tests/
│   ├── __init__.py
│   ├── test_validators.py     # Validation unit tests
│   ├── test_script_generator.py# Script factual accuracy & scene tests
│   └── test_video_generator.py# Image processing & MP4 integration tests
├── scripts/
│   ├── create_sample_assets.py# Generates sample property images
│   └── generate_sample_video.py# CLI sample promo video generator
└── output/
    ├── README.md
    └── green_valley_residency_promo.mp4 # Generated 23.5s promotional MP4
```

---

## 🚀 Windows Setup & Quick Start

### 1. Prerequisites
- **Python 3.10, 3.11, 3.12, or 3.13** installed.
- **PowerShell** (Windows default terminal).

### 2. Clone / Open Project Folder
```powershell
cd "c:\Users\Sanmati Jain\Desktop\Realty Assistant assignment"
```

### 3. Create & Activate Virtual Environment (Recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

> **Note on FFmpeg:** The project utilizes `imageio-ffmpeg`, which automatically manages and bundles a portable static FFmpeg binary (`ffmpeg-win-x86_64-v7.1.exe`). No manual system PATH modification or external installation is required.

### 5. Launch the Streamlit Web Application
```powershell
python -m streamlit run app.py
```
The application will open in your browser at `http://localhost:8501`.

---

## 🎬 Generating a Promotional Video

### Option A: Using the Streamlit Web App (Recommended)
1. In the sidebar, click **"📥 Load Sample Property Data"** to load the *Green Valley Residency* listing in one click.
2. Review the pre-populated property information and the 5 sample images.
3. Click **"🚀 Generate Property Video"**.
4. Monitor the live progress bar as frames, typography cards, narration, and background audio are synthesized.
5. Switch to the **"📺 Video & Script Preview"** tab to watch the 23.5-second video in the browser and click **"⬇️ Download Promotional MP4"**.

### Option B: Using the CLI Script
You can generate the promotional video directly from PowerShell:
```powershell
python scripts\generate_sample_video.py
```
Output: `output\green_valley_residency_promo.mp4`

---

## 🧪 Automated Testing

Execute the test suite with pytest:
```powershell
python -m pytest -v
```

### Test Coverage Summary:
- `test_required_field_validation`: Verifies missing fields fail with clear error messages.
- `test_image_count_validation`: Confirms strict 4 to 8 image boundary enforcement.
- `test_missing_optional_information`: Confirms clean fallback when optional fields are omitted.
- `test_invalid_image_handling`: Tests non-image files, corrupted images, and small images.
- `test_full_validation_raises_exception_on_invalid_input`: Tests `ValidationError` propagation.
- `test_script_generation_scene_count`: Verifies scene counts match images for 4, 5, 6, and 8 scenes.
- `test_script_generation_factual_accuracy`: Strict enforcement of factual accuracy (zero hallucinated amenities/returns).
- `test_script_generation_handles_missing_optional_fields`: Verifies script creation without bedrooms or description.
- `test_image_resizing_and_cropping`: Tests aspect ratio preservation (portrait & panoramic to 16:9).
- `test_scene_frame_rendering`: Tests Pillow frame compositing and RGB output.
- `test_video_generation_end_to_end`: Synthetic end-to-end MP4 compilation verifying non-zero output.
- `test_video_generation_scene_mismatch_error`: Verifies graceful failure when scenes and images mismatch.

**Result: 12 passed in ~15s.**

---

## 📐 AI Approach, Libraries & Architecture

| Component | Technology | Rationale & Design Choice |
| :--- | :--- | :--- |
| **User Interface** | `Streamlit` | Clean reactive dashboard with live progress updates, audio/video preview, and downloads. |
| **Image Processing** | `Pillow (PIL)` | 100% Python-native, fast center-crop, glassmorphism cards, and high-contrast typography without external ImageMagick. |
| **Video Compilation** | `MoviePy 2.x` + `FFmpeg` | Crossfade scene sequencing, audio-video timeline synchronization, and fast H.264 encoding. |
| **Narration (TTS)** | `gTTS` | Natural Indian-English / Global English vocal delivery with offline fallback. |
| **Ambient Audio** | `NumPy` + `Wave` | 100% royalty-free procedural ambient chord synthesizer with envelope fading. Zero external music licenses needed. |
| **Script Generation** | Rule-Based (Default) / Gemini (Optional) | Rule-based template engine guarantees 100% factual accuracy with zero risk of fabricated property claims. |

### Strict Factual Accuracy Policy
In real estate marketing, fabricated claims (e.g. invented metro proximity, false ROI, fictitious amenities) carry severe legal liability. Property Studio AI strictly uses user-provided information. When information is omitted, the system adapts gracefully rather than inventing details.

---

## 🛠️ Troubleshooting

- **Encoding Error on Windows Console (`charmap`):**  
  Addressed directly in the scripts via `sys.stdout.reconfigure(encoding="utf-8")`.
- **FFmpeg not found:**  
  The project includes `imageio-ffmpeg` which automatically provides a local standalone binary. If running on a minimal system, ensure `imageio-ffmpeg` is installed.
- **Port 8501 already in use:**  
  Run `python -m streamlit run app.py --server.port 8502`.

