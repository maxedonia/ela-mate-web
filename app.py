import streamlit as st
from PIL import Image
from src.ela import process_ela, process_ela_delta, process_noise_analysis
from src.analysis import generate_heatmap

st.set_page_config(page_title="ELA Mate v3.2", layout="wide")

# --- MEMORY STORE ---
if 'store' not in st.session_state:
    st.session_state.store = {
        'ela_quality': 90, 'ela_scale': 15,
        'delta_high': 95, 'delta_low': 85, 'delta_scale': 20, 'delta_denoise': 25,
        'noise_intensity': 50,
        'hm_sens': 50, 'hm_opac': 0.5,
        'mode': "Standard ELA", 'show_heatmap': False
    }

def update_store(key):
    st.session_state.store[key] = st.session_state[f"_{key}"]

st.title("🕵️ ELA Mate v3.2")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    mode = st.radio(
        "Analysis Mode", 
        ["Standard ELA", "Delta Analysis", "Warp Detector (Noise)"],
        index=["Standard ELA", "Delta Analysis", "Warp Detector (Noise)"].index(st.session_state.store['mode']),
        key="_mode", on_change=update_store, args=('mode',)
    )

    st.markdown("---")
    st.subheader("1. Parameters")
    
    s = st.session_state.store
    
    if s['mode'] == "Standard ELA":
        st.slider("JPEG Quality", 50, 100, value=s['ela_quality'], key="_ela_quality", on_change=update_store, args=('ela_quality',))
        st.slider("Intensity", 1, 100, value=s['ela_scale'], key="_ela_scale", on_change=update_store, args=('ela_scale',))
        
    elif s['mode'] == "Delta Analysis":
        c1, c2 = st.columns(2)
        with c1: st.slider("High Q", 80, 100, value=s['delta_high'], key="_delta_high", on_change=update_store, args=('delta_high',))
        with c2: st.slider("Low Q", 50, 90, value=s['delta_low'], key="_delta_low", on_change=update_store, args=('delta_low',))
        
        st.slider("Delta Intensity", 1, 100, value=s['delta_scale'], key="_delta_scale", on_change=update_store, args=('delta_scale',))
        # THE NEW FEATURE: Static Filter
        st.slider("Static Filter (Denoise)", 0, 100, value=s['delta_denoise'], key="_delta_denoise", on_change=update_store, args=('delta_denoise',), help="Increase this to remove grain/static from high-quality images.")
        
    elif s['mode'] == "Warp Detector (Noise)":
        st.info("Best for finding Facetune/Liquify. Highlights areas that are 'too smooth'.")
        st.slider("Detection Power", 1, 100, value=s['noise_intensity'], key="_noise_intensity", on_change=update_store, args=('noise_intensity',))

    st.markdown("---")
    st.subheader("2. Highlighter")
    
    show_heatmap = st.checkbox("🔥 Show Heatmap", value=s['show_heatmap'], key="_show_heatmap", on_change=update_store, args=('show_heatmap',))
    
    if s['show_heatmap']:
        st.slider("Sensitivity", 1, 100, value=s['hm_sens'], key="_hm_sens", on_change=update_store, args=('hm_sens',))
        st.slider("Opacity", 0.1, 1.0, value=s['hm_opac'], key="_hm_opac", on_change=update_store, args=('hm_opac',))

# --- MAIN WINDOW ---
uploaded_file = st.file_uploader("Drag & drop an image here", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    original_image = Image.open(uploaded_file)
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Original")
        st.image(original_image, width="stretch")
        
    with col2:
        s = st.session_state.store
        
        if s['mode'] == "Standard ELA":
            st.subheader("Standard ELA")
            result = process_ela(original_image, quality=s['ela_quality'], scale=s['ela_scale'])
        elif s['mode'] == "Delta Analysis":
            st.subheader("Delta Analysis")
            result = process_ela_delta(original_image, s['delta_high'], s['delta_low'], s['delta_scale'], s['delta_denoise'])
        else:
            st.subheader("Warp Detector")
            result = process_noise_analysis(original_image, intensity=s['noise_intensity'])
            
        if s['show_heatmap']:
            final = generate_heatmap(original_image, result, s['hm_sens'], s['hm_opac'])
            st.image(final, width="stretch", caption="🔥 Heatmap Active")
        else:
            st.image(result, width="stretch", caption="Analysis Result")