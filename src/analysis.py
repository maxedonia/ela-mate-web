import cv2
import numpy as np
from PIL import Image

def generate_heatmap(original_image, ela_image, sensitivity=50, opacity=0.5):
    """
    Creates a heatmap overlay that highlights areas with high ELA error rates.
    """
    # Convert PIL images to NumPy arrays (OpenCV format)
    ela_cv = np.array(ela_image.convert('RGB'))
    original_cv = np.array(original_image.convert('RGB'))

    # 1. Convert ELA to Grayscale (intensity of error)
    gray_ela = cv2.cvtColor(ela_cv, cv2.COLOR_RGB2GRAY)

    # 2. Thresholding: Filter out "normal" background noise
    # High sensitivity in UI means we detect MORE (lower threshold value).
    threshold_value = 255 - int(sensitivity * 2.5) 
    threshold_value = max(10, min(250, threshold_value)) # Clamp safety
    
    _, mask = cv2.threshold(gray_ela, threshold_value, 255, cv2.THRESH_BINARY)

    # 3. Clean up the noise (Morphology)
    # This connects nearby dots into a single "blob"
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel) # Fill holes
    mask = cv2.GaussianBlur(mask, (15, 15), 0) # Smooth edges

    # 4. Create the Heatmap (Red Color)
    heatmap = np.zeros_like(original_cv)
    heatmap[:, :, 0] = 255  # Set Red channel to max

    # 5. Apply Mask to Heatmap
    mask_normalized = mask / 255.0
    mask_3ch = np.stack([mask_normalized]*3, axis=2)

    # 6. Blend: Original + (Heatmap * Opacity * Mask)
    blended = original_cv.astype(float) * (1 - (opacity * mask_3ch)) + \
              heatmap.astype(float) * (opacity * mask_3ch)

    return Image.fromarray(np.uint8(blended))