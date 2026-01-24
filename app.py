import streamlit as st
from PIL import Image
import numpy as np
from streamlit_image_coordinates import streamlit_image_coordinates
from src.ela import process_ela, process_ela_delta, process_noise_analysis

# Set page to wide mode
st.set_page_config(page_title="ELA Mate v4.7", layout="wide")

# --- MEMORY STORE ---
default_settings = {
    # Consolidated ELA Params
    'ela_mode': 'Standard', 
    'ela_quality': 90,
    'ela_scale': 15,
    'delta_high': 95, 
    'delta_low': 85, 
    'delta_scale': 20, 
    'delta_denoise': 0,
    
    # Noise Params
    'noise_gain': 25,
    
    # Global Settings
    'mode': "Error Level Analysis",
    'workspace_scale': 0.7, 
    'split_pos': 50,
    'overlay_opacity': 1.0 
}

# Initialize & Heal Store
if 'store' not in st.session_state:
    st.session_state.store = default_settings.copy()
for key, value in default_settings.items():
    if key not in st.session_state.store:
        st.session_state.store[key] = value

def update_store(key):
    st.session_state.store[key] = st.session_state[f"_{key}"]

st.title("🕵️ ELA Mate v4.7")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    # 1. Main Mode Selector
    mode = st.radio(
        "Analysis Method", 
        ["Error Level Analysis", "Noise Variance (Warp)"],
        index=["Error Level Analysis", "Noise Variance (Warp)"].index(st.session_state.store['mode']),
        key="_mode", on_change=update_store, args=('mode',),
        help="Choose the forensic algorithm to apply."
    )

    st.markdown("---")
    
    s = st.session_state.store
    
    # 2. Dynamic Parameters
    if s['mode'] == "Error Level Analysis":
        use_delta = st.checkbox("Enable Delta (Dual-Pass)", 
                                value=(s['ela_mode'] == 'Delta'),
                                help="Check to compare two different compression levels. Good for finding banding artifacts.")
        
        s['ela_mode'] = 'Delta' if use_delta else 'Standard'
        
        if s['ela_mode'] == 'Standard':
            st.info("ℹ️ **Standard ELA:** Highlights high-error blocks.")
            st.slider("JPEG Quality", 50, 100, value=s['ela_quality'], key="_ela_quality", on_change=update_store, args=('ela_quality',),
                      help="Compression level to compare against (50-100).")
            st.slider("Intensity", 1, 100, value=s['ela_scale'], key="_ela_scale", on_change=update_store, args=('ela_scale',),
                      help="Brightness of the error artifacts.")
            
        else: # Delta Mode
            st.info("ℹ️ **Delta ELA:** Highlights instability between qualities.")
            c1, c2 = st.columns(2)
            with c1: st.slider("High Q", 80, 100, value=s['delta_high'], key="_delta_high", on_change=update_store, args=('delta_high',), help="Upper quality reference.")
            with c2: st.slider("Low Q", 50, 90, value=s['delta_low'], key="_delta_low", on_change=update_store, args=('delta_low',), help="Lower quality reference.")
            
            st.slider("Delta Intensity", 1, 100, value=s['delta_scale'], key="_delta_scale", on_change=update_store, args=('delta_scale',), help="Amplification of difference.")
            st.slider("Static Filter (Denoise)", 0, 100, value=s['delta_denoise'], key="_delta_denoise", on_change=update_store, args=('delta_denoise',), help="Blur to remove grain and focus on structure.")

    elif s['mode'] == "Noise Variance (Warp)":
        st.info("ℹ️ **Noise Variance:** Look for DARK voids in the static.")
        st.slider("Noise Gain", 1, 100, value=s['noise_gain'], key="_noise_gain", on_change=update_store, args=('noise_gain',),
                  help="Increases contrast of the noise map.")

    # 3. Opacity Slider
    st.slider(
        "Analysis Overlay Opacity", 0.0, 1.0, value=s['overlay_opacity'], 
        key="_overlay_opacity", on_change=update_store, args=('overlay_opacity',),
        help="0% = Show Original, 100% = Show Analysis. Use this to fade the heatmap over the original photo."
    )

    st.markdown("---")
    
    # 4. Image Size
    st.slider("Image Size", 0.3, 1.0, value=s['workspace_scale'], 
              key="_workspace_scale", on_change=update_store, args=('workspace_scale',),
              help="Adjust the display size of the image.")

# --- MAIN WINDOW ---
uploaded_file = st.file_uploader("Drag & drop an image here", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    original = Image.open(uploaded_file).convert("RGB")
    s = st.session_state.store
    
    # --- 1. PROCESSING ---
    if s['mode'] == "Error Level Analysis":
        if s['ela_mode'] == 'Standard':
            analysis = process_ela(original, s['ela_quality'], s['ela_scale'])
            label_text = "Standard ELA"
        else:
            analysis = process_ela_delta(original, s['delta_high'], s['delta_low'], s['delta_scale'], s['delta_denoise'])
            label_text = "Delta Analysis"
    else:
        analysis = process_noise_analysis(original, intensity=s['noise_gain'])
        analysis = analysis.convert("RGB")
        label_text = "Noise Variance"

    # --- 2. OPACITY BLENDING ---
    opacity = s['overlay_opacity']
    
    if opacity < 1.0:
        analysis_blended = Image.blend(original, analysis, opacity)
    else:
        analysis_blended = analysis

    # --- 3. COMPOSITING ---
    
    scale = s['workspace_scale']
    
    # LAYOUT FIX: Left Alignment
    if scale >= 0.99:
        workspace = st.container()
    else:
        # Create two columns: [Content, Spacer]
        # This pushes the content to the left side
        workspace, _ = st.columns([scale, 1.0 - scale])
    
    with workspace:
        st.markdown("### Interactive Analysis")
        
        # A. INSTRUCTION TEXT
        st.markdown(
            "<div style='text-align: center; color: #888; margin-bottom: 5px;'>"
            "⬇ Click anywhere on the image to move the comparison slider ⬇"
            "</div>", 
            unsafe_allow_html=True
        )

        # B. PREPARE COMPOSITE
        w, h = original.size
        cut_x = int(w * (s['split_pos'] / 100))
        
        arr_a = np.array(original)
        arr_b = np.array(analysis_blended)
        
        composite = arr_b.copy()
        composite[:, :cut_x, :] = arr_a[:, :cut_x, :]
        
        # White Line (2px)
        if cut_x > 0 and cut_x < w:
            composite[:, cut_x-2:cut_x+2, :] = [255, 255, 255]
        
        composite_pil = Image.fromarray(composite)

        # C. RENDER CLICKABLE IMAGE
        value = streamlit_image_coordinates(composite_pil, use_column_width=True)

        # D. HANDLE CLICKS
        if value is not None:
            clicked_x_pixel = value['x']
            original_width = value['width'] 
            
            if original_width > 0:
                new_split = int((clicked_x_pixel / original_width) * 100)
                
                if abs(new_split - s['split_pos']) > 1:
                    st.session_state.store['split_pos'] = new_split
                    st.rerun()
        
        st.caption(f"Original ({s['split_pos']}%) ↔ {label_text} ({100-s['split_pos']}%)")