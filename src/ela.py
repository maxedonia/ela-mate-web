from PIL import Image, ImageChops, ImageEnhance, ImageFilter
import io
import numpy as np
import cv2

def process_ela(image_input, quality=90, scale=10):
    """
    Standard Error Level Analysis.
    """
    original = image_input.convert('RGB')
    
    buffer = io.BytesIO()
    original.save(buffer, 'JPEG', quality=quality)
    buffer.seek(0)
    compressed = Image.open(buffer)
    
    ela_image = ImageChops.difference(original, compressed)
    
    extrema = ela_image.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0: max_diff = 1
    
    scale_factor = 255.0 / max_diff * (scale / 10.0)
    ela_image = ImageEnhance.Brightness(ela_image).enhance(scale_factor)
    
    return ela_image

def process_ela_delta(image_input, quality_high=95, quality_low=85, scale=10, denoise_strength=0):
    """
    Delta Analysis with Static Filtering.
    """
    img = image_input.convert('RGB')
    
    # 1. Generate the two ELA maps
    buff1 = io.BytesIO()
    img.save(buff1, 'JPEG', quality=quality_high)
    buff1.seek(0)
    img1 = Image.open(buff1)
    diff1 = ImageChops.difference(img, img1)
    
    buff2 = io.BytesIO()
    img.save(buff2, 'JPEG', quality=quality_low)
    buff2.seek(0)
    img2 = Image.open(buff2)
    diff2 = ImageChops.difference(img, img2)
    
    # 2. STATIC FILTER (The Fix)
    # If denoise_strength > 0, we blur the ELA maps slightly to kill single-pixel static
    if denoise_strength > 0:
        # Radius of blur increases with strength (0-100 -> 0-5px radius)
        radius = denoise_strength / 20.0
        diff1 = diff1.filter(ImageFilter.GaussianBlur(radius))
        diff2 = diff2.filter(ImageFilter.GaussianBlur(radius))

    # 3. The Delta
    delta = ImageChops.difference(diff1, diff2)
    
    # 4. Enhance
    extrema = delta.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0: max_diff = 1
    
    scale_factor = 255.0 / max_diff * (scale / 5.0)
    delta = ImageEnhance.Brightness(delta).enhance(scale_factor)
    
    return delta

def process_noise_analysis(image_input, intensity=50):
    """
    Noise Residue Analysis (Warp Detector).
    Facetune/Liquify destroys natural noise. This highlights those 'silent' areas.
    """
    # Convert to OpenCV format (grayscale)
    img_cv = np.array(image_input.convert('L'))
    
    # 1. Isolate the Noise: Subtract a smoothed version from the original
    # This leaves ONLY the high-frequency grain.
    denoised = cv2.medianBlur(img_cv, 3)
    noise_map = cv2.absdiff(img_cv, denoised)
    
    # 2. Invert: We want to see where noise is MISSING (Warped areas = Black holes in noise map)
    # But for visualization, let's make the "Missing Noise" areas BRIGHT.
    # So we calculate local variance. Low variance = Edited.
    
    # Calculate local variance (how much noise is in this 5x5 block?)
    local_mean = cv2.blur(noise_map, (5, 5))
    local_sqr_mean = cv2.blur(noise_map**2, (5, 5))
    local_var = local_sqr_mean - local_mean**2
    
    # Normalize to 0-255
    norm_var = cv2.normalize(local_var, None, 0, 255, cv2.NORM_MINMAX)
    norm_var = 255 - norm_var # Invert: Bright = Low Variance (Smoothed/Edited)
    
    # Thresholding to clean it up based on intensity
    # Intensity 50 -> Threshold 128. Higher intensity -> Lower threshold (show more).
    thresh = 255 - int(intensity * 2.0)
    _, result = cv2.threshold(norm_var, thresh, 255, cv2.THRESH_TOZERO)
    
    return Image.fromarray(result.astype('uint8'))