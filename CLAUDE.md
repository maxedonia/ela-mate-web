# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ELA Mate is a Streamlit-based forensic image analysis tool that detects digital image tampering and re-compression artifacts. It uses Error Level Analysis (ELA), Delta ELA, and Noise Variance Analysis to identify suspicious regions in images.

**GitHub repo:** `ela-mate-web` (https://github.com/maxedonia/ela-mate-web)
The local working directory may be named `ELA_MATE_V3` — this is the same project. The canonical name is `ela-mate-web`.

## Commands

### Setup
```bash
python -m venv venv
source venv/Scripts/activate  # Windows (bash)
pip install -r requirements.txt
```

### Run
```bash
streamlit run app.py
```

App runs at `http://localhost:8501`.

## Architecture

```
app.py          — Streamlit UI, sidebar controls, session state, image display
src/ela.py      — Core forensic algorithms (ELA, Delta ELA, noise analysis, quality estimation)
src/analysis.py — Experimental heatmap utility (not currently integrated into app.py)
```

### Processing Pipeline

1. User uploads an image via `app.py`
2. `app.py` reads session state parameters and calls the appropriate function from `src/ela.py`
3. `src/ela.py` returns a PIL Image (analysis result)
4. `app.py` blends the result with the original using opacity, then displays it
5. Optional: interactive before/after comparison slider via `streamlit_image_comparison`

### Session State Pattern

All UI settings are stored in `st.session_state` under a `store` dict. Sliders use `on_change` callbacks to update state. The key names follow the pattern `ela_*`, `delta_*`, `noise_*`, `overlay_*`, `show_*`.

### Core Functions in `src/ela.py`

- `process_ela(image, quality, scale, denoise)` — Standard ELA: compress → diff → enhance
- `process_ela_delta(image, high_q, low_q, scale, denoise)` — Delta ELA: compare two JPEG quality levels
- `process_noise_analysis(image, intensity, denoise)` — Local 3×3 variance map
- `estimate_jpeg_quality(img)` — Reverse-engineers JPEG quality from quantization tables

All three analysis functions accept an optional `denoise` parameter (0–100) that applies OpenCV's `fastNlMeansDenoisingColored` (ELA modes) or `fastNlMeansDenoising` (noise mode) as a final step.

## Dependencies

Key packages: `streamlit`, `Pillow`, `numpy`, `opencv-python-headless`, `scikit-image`, `streamlit_image_comparison`.
