import streamlit as st
from PIL import Image
from streamlit_image_comparison import image_comparison 
from src.ela import process_ela, process_ela_delta, process_noise_analysis

# Set page to wide mode
st.set_page_config(page_title="ELA Mate v5.4", layout="wide")

# --- CUSTOM CSS: COMPACT UI & BORDERS ---
st.markdown("""
    <style>
    /* 1. Reduce the massive top whitespace */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    /* 2. Target Streamlit Images for Border */
    div[data-testid="stImage"] img {
        border: 1px solid #555;
    }
    /* 3. Target the Comparison Component (Iframe) */
    iframe {
        border: 1px solid #555;
    }
    /* 4. Tighten sidebar padding slightly */
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- MEMORY STORE ---
default_settings = {
    'ela_mode': 'Standard', 
    'ela_quality': 90,
    'ela_scale': 15,
    'delta_high': 95, 
    'delta_low': 85, 
    'delta_scale': 20, 
    'delta_denoise': 0,
    'noise_gain': 25,
    'mode': "Error Level Analysis",
    'workspace_scale': 0.7, 
    'overlay_opacity': 1.0,
    'show_slider': True 
}

if 'store' not in st.session_state:
    st.session_state.store = default_settings.copy()
for key, value in default_settings.items():
    if key not in st.session_state.store:
        st.session_state.store[key] = value

def update_store(key):
    st.session_state.store[key] = st.session_state[f"_{key}"]

def toggle_ela_mode():
    is_checked = st.session_state["_use_delta"]
    st.session_state.store['ela_mode'] = 'Delta' if is_checked else 'Standard'

st.title("🕵️ ELA Mate v5.4")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    s = st.session_state.store

    # 1. Image Size (Moved to Top)
    # Logic: Force scale to 1.0 if Slider is ON to prevent bugs
    current_scale = 1.0 if s['show_slider'] else s['workspace_scale']
    
    st.slider(
        "Image Size", 0.3, 1.0, 
        value=current_scale,
        key="_workspace_scale", 
        on_change=update_store, args=('workspace_scale',),
        disabled=s['show_slider'], # Greyed out if active
        help="Adjust display size. (Locked to 100% when Comparison Slider is active)"
    )

    # 2. Enable Comparison Slider (Directly Below)
    st.toggle(
        "Enable Comparison Slider", 
        value=s['show_slider'], 
        key="_show_slider", 
        on_change=update_store, args=('show_slider',),
        help="Toggle ON for interactive slider. OFF allows resizing the image."
    )

    st.markdown("---")
    
    # 3. Analysis Method
    mode = st.radio(
        "Analysis Method", 
        ["Error Level Analysis", "Noise Variance (Warp)"],
        index=["Error Level Analysis", "Noise Variance (Warp)"].index(s['mode']),
        key="_mode", on_change=update_store, args=('mode',),
        help="Choose the forensic algorithm to apply."
    )
    
    # 4. Parameters Section
    if s['mode'] == "Error Level Analysis":
        st.markdown("### Parameters: ELA")
        
        if s['ela_mode'] == 'Standard':
            st.info("ℹ️ **Standard ELA:** Highlights high-error blocks.")
        else:
            st.info("ℹ️ **Delta ELA:** Highlights instability between qualities.")

        st.checkbox("Enable Delta (Dual-Pass)", 
                    value=(s['ela_mode'] == 'Delta'),
                    key="_use_delta", 
                    on_change=toggle_ela_mode,
                    help="Check to compare two different compression levels.")
        
        if s['ela_mode'] == 'Standard':
            st.slider("JPEG Quality", 50, 100, value=s['ela_quality'], key="_ela_quality", on_change=update_store, args=('ela_quality',), help="Compression level to compare against.")
            st.slider("Intensity", 1, 100, value=s['ela_scale'], key="_ela_scale", on_change=update_store, args=('ela_scale',), help="Brightness of the artifacts.")
            
        else: # Delta Mode
            c1, c2 = st.columns(2)
            with c1: st.slider("High Q", 80, 100, value=s['delta_high'], key="_delta_high", on_change=update_store, args=('delta_high',), help="Upper quality reference.")
            with c2: st.slider("Low Q", 50, 90, value=s['delta_low'], key="_delta_low", on_change=update_store, args=('delta_low',), help="Lower quality reference.")
            st.slider("Delta Intensity", 1, 100, value=s['delta_scale'], key="_delta_scale", on_change=update_store, args=('delta_scale',), help="Amplification of difference.")
            st.slider("Static Filter (Denoise)", 0, 100, value=s['delta_denoise'], key="_delta_denoise", on_change=update_store, args=('delta_denoise',), help="Blur to remove grain.")

    elif s['mode'] == "Noise Variance (Warp)":
        st.markdown("### Parameters: Noise")
        st.info("ℹ️ **Noise Variance:** Look for DARK voids in the static.")
        st.slider("Noise Gain", 1, 100, value=s['noise_gain'], key="_noise_gain", on_change=update_store, args=('noise_gain',), help="Increases contrast.")

    st.markdown("---")

    # 5. Opacity
    st.slider(
        "Opacity", 0.0, 1.0, value=s['overlay_opacity'], 
        key="_overlay_opacity", on_change=update_store, args=('overlay_opacity',),
        help="0% = Show Original, 100% = Show Analysis."
    )

# --- MAIN WINDOW ---
uploaded_file = st.file_uploader("Drag & drop an image here", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    original = Image.open(uploaded_file).convert("RGB")
    s = st.session_state.store
    
    # --- PROCESSING ---
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

    # --- OPACITY BLENDING ---
    opacity = s['overlay_opacity']
    if opacity < 1.0:
        analysis_blended = Image.blend(original, analysis, opacity)
    else:
        analysis_blended = analysis

    # --- LAYOUT ---
    scale = 1.0 if s['show_slider'] else s['workspace_scale']
    
    if scale >= 0.99:
        workspace = st.container()
    else:
        workspace, _ = st.columns([scale, 1.0 - scale])
    
    with workspace:
        if s['show_slider']:
            # Interactive Slider (Locked to Full Width)
            image_comparison(
                img1=original,
                img2=analysis_blended, 
                label1="Original",
                label2=label_text,
                starting_position=50,
                show_labels=True,
                make_responsive=True,
                in_memory=True
            )
        else:
            # Static Image (Resizable)
            st.image(analysis_blended, caption=f"{label_text} (Opacity: {int(opacity*100)}%)", use_container_width=True)