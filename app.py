"""Property Studio AI — Web Application.

A professional AI property promotional video generator built with Streamlit.
Converts property details and photos into 20-40 second branded marketing videos.
"""

from pathlib import Path
import json
import tempfile
import time
import streamlit as st
from PIL import Image

from src.validators import (
    validate_property_input,
    PropertyImage,
    ValidationError
)
from src.image_classifier import detect_image_category, DISPLAY_NAMES
from src.script_generator import generate_script
from src.video_generator import generate_property_video, VideoGenerationError

PROJECT_ROOT = Path(__file__).resolve().parent
SAMPLE_JSON_PATH = PROJECT_ROOT / "sample_data" / "sample_property.json"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Page configuration
st.set_page_config(
    page_title="Property Studio AI | Video Generator",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .badge-card {
        background-color: #f8fafc;
        border-left: 4px solid #d97706;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 1rem;
    }
    .scene-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def load_sample_property():
    """Load sample property data into session state."""
    if SAMPLE_JSON_PATH.exists():
        with open(SAMPLE_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            st.session_state["name"] = data.get("name", "")
            st.session_state["location"] = data.get("location", "")
            st.session_state["price"] = data.get("price", "")
            st.session_state["property_type"] = data.get("property_type", "")
            st.session_state["bedrooms"] = data.get("bedrooms", 2)
            st.session_state["description"] = data.get("description", "")
            st.session_state["features"] = "\n".join(data.get("features", []))
            st.session_state["cta"] = data.get("call_to_action", "")
            st.session_state["use_sample_images"] = True


# Initialize session state defaults
if "name" not in st.session_state:
    st.session_state["name"] = ""
    st.session_state["location"] = ""
    st.session_state["price"] = ""
    st.session_state["property_type"] = "2-BHK apartment"
    st.session_state["bedrooms"] = 2
    st.session_state["description"] = ""
    st.session_state["features"] = ""
    st.session_state["cta"] = "Contact us today to arrange a visit."
    st.session_state["use_sample_images"] = False
    st.session_state["generated_video"] = None
    st.session_state["generated_script"] = None

# Sidebar: Controls & Presets
with st.sidebar:
    st.title("🏢 Property Studio AI")
    st.caption("AI-Powered Real Estate Promo Generator")
    st.markdown("---")
    
    st.subheader("⚡ Quick Start")
    if st.button("📥 Load Sample Property Data", use_container_width=True, type="secondary"):
        load_sample_property()
        st.success("Sample data loaded: Green Valley Residency")
        st.rerun()

    st.markdown("---")
    st.subheader("⚙️ Video Settings")
    include_narration = st.checkbox("🎙️ Include AI Voice Narration", value=True)
    include_ambient = st.checkbox("🎵 Include Ambient Background Music", value=True)
    use_llm = st.checkbox("🤖 Use LLM Script Enhancement", value=False)
    api_key = None
    if use_llm:
        api_key = st.text_input("Gemini / OpenAI API Key", type="password", help="Leave blank for automatic rule-based generation")

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.caption(
        "Property Studio AI transforms raw property listings and photos into ready-to-publish "
        "promotional videos with typography overlays, automated narration, and ambient audio."
    )

# Main Application Header
col_header, col_status = st.columns([3, 1])
with col_header:
    st.markdown('<div class="main-header">Property Studio AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Automated Promotional Video Studio for Real Estate Listings</div>', unsafe_allow_html=True)

# Tabs
tab_create, tab_preview, tab_docs = st.tabs(["🎬 Create Video", "📺 Video & Script Preview", "📖 Architecture & Info"])

with tab_create:
    st.markdown("#### 1. Property Details")
    
    col1, col2 = st.columns(2)
    with col1:
        name_val = st.text_input("Property Name *", value=st.session_state.get("name", ""), placeholder="e.g. Green Valley Residency")
        location_val = st.text_input("Location *", value=st.session_state.get("location", ""), placeholder="e.g. Chandigarh")
        price_val = st.text_input("Price *", value=st.session_state.get("price", ""), placeholder="e.g. ₹85 lakh")
        
    with col2:
        prop_types = ["2-BHK apartment", "3-BHK apartment", "Luxury Villa", "Penthouse", "Studio", "Commercial Office", "Plot / Land"]
        current_type = st.session_state.get("property_type", "2-BHK apartment")
        type_idx = prop_types.index(current_type) if current_type in prop_types else 0
        property_type_val = st.selectbox("Property Type *", prop_types, index=type_idx)
        bedrooms_val = st.number_input("Bedrooms (optional)", min_value=0, max_value=20, value=int(st.session_state.get("bedrooms", 2)))
        cta_val = st.text_input("Call to Action *", value=st.session_state.get("cta", "Contact us today to arrange a visit."))

    col_desc, col_feat = st.columns(2)
    with col_desc:
        desc_val = st.text_area("Property Description (optional)", value=st.session_state.get("description", ""), placeholder="Brief overview of the property...", height=120)
    with col_feat:
        features_val = st.text_area(
            "Key Features & Amenities * (one per line)",
            value=st.session_state.get("features", ""),
            placeholder="Two bedrooms\nModular kitchen\nBalcony\nParking",
            height=120
        )

    st.markdown("---")
    st.markdown("#### 2. Property Images (4 to 8 required)")
    st.caption("Upload 4 to 8 high-quality landscape or portrait images. They will be automatically framed and cropped to 16:9.")

    uploaded_files = st.file_uploader(
        "Choose property images",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        help="Provide between 4 and 8 images for scene generation."
    )

    # Determine image sources
    selected_image_paths = []
    temp_dir_obj = None

    if uploaded_files:
        temp_dir_obj = tempfile.mkdtemp(prefix="uploaded_imgs_")
        for idx, f in enumerate(uploaded_files):
            p = Path(temp_dir_obj) / f"upload_{idx}_{f.name}"
            with open(p, "wb") as out_f:
                out_f.write(f.getbuffer())
            selected_image_paths.append(p)
    elif st.session_state.get("use_sample_images"):
        # Use bundled sample images
        sample_img_dir = PROJECT_ROOT / "assets" / "sample_images"
        if sample_img_dir.exists():
            selected_image_paths = sorted(list(sample_img_dir.glob("*.jpg")))
            st.info(f"Using {len(selected_image_paths)} bundled sample images for Green Valley Residency.")

    # Image Previews & Category Mapping
    category_choices = [
        "Auto-Detect",
        "Property Exterior",
        "Living Room",
        "Modular Kitchen",
        "Bedroom",
        "Balcony View",
        "Designer Bathroom",
        "Parking & Garage",
        "Key Amenity"
    ]
    image_category_map = {}

    if selected_image_paths:
        st.markdown(f"**Image Gallery & Category Assignment ({len(selected_image_paths)} images)**")
        st.caption("Verify or adjust room categories so each photograph is matched with its accurate caption.")
        img_cols = st.columns(min(len(selected_image_paths), 5))
        for idx, img_p in enumerate(selected_image_paths):
            with img_cols[idx % 5]:
                try:
                    img = Image.open(img_p)
                    st.image(img, use_container_width=True)
                    # Detect default category
                    _, detected_disp, conf = detect_image_category(img_p)
                    def_idx = 0
                    if detected_disp in category_choices:
                        def_idx = category_choices.index(detected_disp)

                    chosen_cat = st.selectbox(
                        f"Image {idx+1}",
                        category_choices,
                        index=def_idx,
                        key=f"img_cat_select_{idx}_{img_p.name}",
                        help=f"Detected: {detected_disp} (conf: {conf:.0%})"
                    )
                    image_category_map[img_p] = chosen_cat
                except Exception:
                    st.error(f"Error loading {img_p.name}")

    st.markdown("---")
    # Action Button
    generate_btn = st.button("🚀 Generate Property Video", type="primary", use_container_width=True)

    if generate_btn:
        feature_list = [f.strip() for f in features_val.split("\n") if f.strip()]
        
        # Build PropertyImage objects with user-selected or detected categories
        property_image_objects = []
        for img_p in selected_image_paths:
            user_choice = image_category_map.get(img_p, "Auto-Detect")
            cat_to_use = None if user_choice == "Auto-Detect" else user_choice
            property_image_objects.append(PropertyImage(path=img_p, category=cat_to_use))

        # Validation
        try:
            prop_input = validate_property_input(
                name=name_val,
                location=location_val,
                price=price_val,
                property_type=property_type_val,
                features=feature_list,
                call_to_action=cta_val,
                image_paths=property_image_objects,
                bedrooms=bedrooms_val if bedrooms_val > 0 else None,
                description=desc_val
            )
        except ValidationError as ve:
            st.error(f"⚠️ Validation Error: {ve}")
            st.stop()

        # Script Generation
        with st.spinner("Generating factual script and captions..."):
            script = generate_script(prop_input, use_llm=use_llm, api_key=api_key)
            st.session_state["generated_script"] = script

        # Video Generation with Progress Bar
        progress_bar = st.progress(0, text="Initializing video renderer...")
        status_box = st.empty()

        def ui_progress(ratio: float, msg: str):
            progress_bar.progress(int(ratio * 100), text=f"[{int(ratio*100)}%] {msg}")
            status_box.info(msg)

        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in prop_input.name if c.isalnum() or c in (' ', '_', '-')).rstrip()
        safe_name = safe_name.replace(" ", "_").lower()
        output_filename = f"{safe_name}_{timestamp_str}.mp4"
        out_mp4_path = OUTPUT_DIR / output_filename

        try:
            res_path = generate_property_video(
                prop=prop_input,
                output_path=out_mp4_path,
                script=script,
                include_narration=include_narration,
                include_background_music=include_ambient,
                fps=24,
                progress_callback=ui_progress
            )
            st.session_state["generated_video"] = res_path
            progress_bar.progress(100, text="Video generation completed!")
            status_box.success("🎉 Promotional video generated successfully! Switch to the 'Video & Script Preview' tab to view and download.")
        except VideoGenerationError as vge:
            st.error(f"❌ Video Generation Error: {vge}")
        except Exception as ex:
            st.error(f"❌ Unexpected error during video generation: {ex}")

with tab_preview:
    st.markdown("#### Video Preview & Downloads")
    
    # Check if a video was just generated or check for the sample video
    current_video = st.session_state.get("generated_video")
    if not current_video or not Path(current_video).exists():
        sample_promo = OUTPUT_DIR / "green_valley_residency_promo.mp4"
        if sample_promo.exists():
            current_video = sample_promo

    if current_video and Path(current_video).exists():
        v_path = Path(current_video)
        col_vid, col_meta = st.columns([3, 2])
        
        with col_vid:
            st.video(str(v_path))
            with open(v_path, "rb") as vid_file:
                st.download_button(
                    label="⬇️ Download Promotional MP4",
                    data=vid_file,
                    file_name=v_path.name,
                    mime="video/mp4",
                    type="primary",
                    use_container_width=True
                )

        with col_meta:
            st.markdown(f"**File Details:**")
            file_mb = v_path.stat().st_size / (1024 * 1024)
            st.write(f"- **Filename:** `{v_path.name}`")
            st.write(f"- **File Size:** {file_mb:.2f} MB")
            st.write(f"- **Resolution:** 1280 x 720 (16:9 Landscape)")
            st.write(f"- **Encoding:** H.264 / AAC")
            st.write(f"- **Status:** Ready to share on social media & client portals")

        # Display Script & Scene Captions
        script_obj = st.session_state.get("generated_script")
        if script_obj:
            st.markdown("---")
            st.markdown("#### 📜 Generated Script & Scene Breakdown")
            st.caption(f"Source: {script_obj.source} • Total Duration: {script_obj.estimated_duration:.1f}s")
            
            for s in script_obj.scenes:
                with st.expander(f"Scene {s.scene_index}: [{s.category_tag}] {s.headline} ({s.duration}s)", expanded=True):
                    sc_col1, sc_col2 = st.columns([1, 2])
                    with sc_col1:
                        st.markdown(f"**Badge:** `{s.category_tag}`")
                        st.markdown(f"**Headline:** {s.headline}")
                        st.markdown(f"**Sub:** {s.subheadline}")
                    with sc_col2:
                        st.markdown(f"**On-Screen Caption:** *\"{s.caption}\"*")
                        st.markdown(f"**Voiceover Script:** *\"{s.voiceover}\"*")
    else:
        st.info("No video generated yet. Go to 'Create Video' tab, enter property details or click 'Load Sample Property Data', and hit 'Generate Property Video'.")

with tab_docs:
    st.markdown("#### Technical Architecture & Implementation")
    st.markdown("""
    **Property Studio AI** is an automated video production system engineered for real estate marketing teams.
    
    ### Pipeline Workflow:
    1. **Input & Validation (`src/validators.py`):**
       - Validates property fields (name, location, price, type, features, CTA).
       - Enforces image requirements (4 to 8 images, min 100x100px, supported JPG/PNG/WEBP).
    2. **Script Generation (`src/script_generator.py`):**
       - **Strict Factual Accuracy:** Rule-based template logic strictly uses user-provided facts. Never hallucinates pricing, amenities, distances, or certifications.
       - Maps property features smoothly across the uploaded image scenes.
    3. **Image & Text Composition (`src/image_processor.py`):**
       - Uses Pillow for fast, standalone typography compositing (no ImageMagick required).
       - Smart cover crop to 1280x720 (16:9 landscape aspect ratio).
       - Safe margins, category pill badges, high-contrast typography, and dark lower-third gradients.
    4. **Audio Synthesis (`src/audio_generator.py`):**
       - TTS voiceover narration generated per scene using gTTS.
       - 100% royalty-free ambient music synthesized procedurally via NumPy (warm chord progression with soft envelope fades).
       - Audio ducking and duration matching.
    5. **Video Compilation (`src/video_generator.py`):**
       - MoviePy 2.x and FFmpeg render H.264 video with smooth crossfades and AAC audio at 24fps.
    """)

