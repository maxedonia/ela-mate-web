# ELA Mate v5.6

A browser-based forensic image analysis tool for detecting digital manipulation and re-compression artifacts.

---

## What is Error Level Analysis?

Digital photo editing diminishes original image characteristics like contrast, sharpness, and compression fidelity. **Error Level Analysis (ELA)** identifies noise patterns that don't reflect normal image compression — making distortion artifacts (warping, facetuning, filtering, cloning) visible. These artifacts persist through resizing and format conversion, with additional manipulations compounding the signal further.

More background: [FotoForensics ELA Tutorial](https://fotoforensics.com/tutorial-ela.php)

---

## Analysis Modes

**Error Level Analysis (ELA)**
- **Standard**: Re-compresses the image at a target JPEG quality, then amplifies the difference. High-error regions indicate potential editing.
- **Delta (Dual-Pass)**: Compares two different JPEG compression levels to identify instability. Useful for localized edit detection that standard ELA may miss.

**Noise Variance (Warp)**
Computes local pixel variance using a 3×3 kernel. Uniform regions (smooth skin, gradients) produce consistent static; dark voids in that static indicate areas of suspicious smoothing or cloning.

**JPEG Quality Detection**
Automatically estimates the original JPEG quality factor from quantization table metadata on upload.

All modes include an optional **Static Filter (Denoise)** slider that applies Non-Local Means smoothing to reduce grain and surface noise, making structural artifacts easier to read.

---

## Setup

Requires Python 3.8+.

```bash
git clone https://github.com/maxedonia/ela-mate-web.git
cd ela-mate-web

python -m venv venv
source venv/Scripts/activate   # Windows (bash)
# or: source venv/bin/activate  (macOS/Linux)

pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. On Windows, you can also use `Launch_ELA_Mate.bat`.

---

## Usage

1. Upload a JPG or PNG via drag-and-drop
2. Select an **Analysis Method** from the sidebar
3. Tune parameters (quality, intensity, denoise, opacity)
4. Toggle **Comparison Slider** for an interactive before/after view, or leave it off for a resizable static view

**Opacity** blends the analysis result with the original image — useful for correlating artifacts with the actual content.

---

## Disclaimer

ELA Mate is intended for digital literacy and educational use only. It is not designed for legal or forensic purposes, and any conclusions drawn are not endorsed by the author. Use responsibly.

---

## Related

- [ELA Mate v2](https://github.com/maxedonia/ela_mate) *(archived)* — the original command-line version, which generates animated GIFs across 99 compression levels
- [29a.ch Photo Forensics](https://29a.ch/photo-forensics/) — a broader suite of forensic analysis tools
