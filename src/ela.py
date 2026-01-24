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
    Local Noise Variance Analysis.
    Detects areas where natural sensor noise has been destroyed by warping/smoothing.
    
    Returns:
    A map where BRIGHT = High Noise (Original), DARK = Low Noise (Potentially Warped).
    """
    # 1. Convert to Grayscale
    img = np.array(image_input.convert('L'))
    
    # 2. Compute Local Variance
    # Var(X) = E[X^2] - (E[X])^2
    # We use a 3x3 kernel to look at very fine noise patterns
    kernel_size = (3, 3)
    
    mean = cv2.boxFilter(img.astype(float), -1, kernel_size)
    sqr_mean = cv2.boxFilter(img.astype(float)**2, -1, kernel_size)
    
    variance = sqr_mean - (mean**2)
    
    # 3. Enhance Visibility
    # Variance is usually a very small number, so we need to stretch it to 0-255
    # We use the 'intensity' slider to control the "Gain" of the noise
    gain = intensity * 2.0
    variance_enhanced = variance * gain
    
    # Clip to valid range
    variance_enhanced = np.clip(variance_enhanced, 0, 255).astype(np.uint8)
    
    # 4. Invert? 
    # Standard forensics: White = Noise, Black = Edit. 
    # This feels intuitive (Warped areas look like "voids").
    
    return Image.fromarray(variance_enhanced)