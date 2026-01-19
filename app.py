import streamlit as st
from PIL import Image
from src.ela import process_ela

# 1. Page Configuration
st.set_page_config(page_title="ELA Mate v3", layout="wide")

st.title("🕵️ ELA Mate v3")
st.markdown("Upload an image to detect potential manipulation using Error Level Analysis.")

# 2. Sidebar Controls
with st.sidebar:
    st.header("Settings")
    quality = st.slider("JPEG Quality", min_value=50, max_value=100, value=90, help="Simulate saving the image at this quality level.")
    scale = st.slider("ELA Intensity", min_value=1, max_value=100, value=15, help="Amplify the difference to make artifacts visible.")
    
    st.info("💡 **Tip:** Adjust 'ELA Intensity' if the result is too dark or too bright.")

# 3. Main Interface
uploaded_file = st.file_uploader("Drag & drop an image here", type=['jpg', 'jpeg', 'png'])

if uploaded_file:
    # Load the image
    original_image = Image.open(uploaded_file)
    
    # Create two columns for side-by-side comparison
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Original Image")
        st.image(original_image, use_container_width=True)
        
    with col2:
        st.subheader("ELA Analysis")
        # --- THE MAGIC HAPPENS HERE ---
        # We pass the image to your src/ela.py function
        ela_result = process_ela(original_image, quality=quality, scale=scale)
        
        st.image(ela_result, use_container_width=True)
        
    # Explanation
    st.markdown("---")
    st.caption(f"Analyzing at **{quality}%** JPEG Quality with **{scale}x** Intensity.")