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
    
def estimate_jpeg_quality(img):
    """
    Reverse-engineers the JPEG Quality Factor from the quantization tables.
    Returns an integer (1-100) or None if not a JPEG.
    """
    if not img.format == 'JPEG' or not hasattr(img, 'quantization') or img.quantization is None:
        return None

    # Standard JPEG Luminance Quantization Table (Quality 50)
    # Source: JPEG Standard (ITU-T T.81)
    std_luminance_quant_tbl = [
        16, 11, 10, 16, 24, 40, 51, 61,
        12, 12, 14, 19, 26, 58, 60, 55,
        14, 13, 16, 24, 40, 57, 69, 56,
        14, 17, 22, 29, 51, 87, 80, 62,
        18, 22, 37, 56, 68, 109, 103, 77,
        24, 35, 55, 64, 81, 104, 113, 92,
        49, 64, 78, 87, 103, 121, 120, 101,
        72, 92, 95, 98, 112, 100, 103, 99
    ]

    try:
        # Get the image's quantization table (Index 0 = Luminance)
        # PIL returns a dictionary of tables (0, 1, etc) or a flat list depending on version
        # Usually it's {0: [64 ints], 1: [64 ints]}
        qt = img.quantization
        if isinstance(qt, dict):
            curr_table = qt[0]
        else:
            curr_table = qt[:64] # Fallback if flat list

        # Calculate the scaling factor based on the first few coefficients
        # (Averaging all of them is more robust)
        # S = (Current_Table_Value * 100) / Standard_Table_Value
        
        summ = 0
        for i in range(64):
            # Avoid division by zero issues
            val = curr_table[i]
            std = std_luminance_quant_tbl[i]
            summ += (val * 100.0) / std
        
        # Average scaling factor
        avg_scaling_factor = summ / 64.0
        
        # Reverse the JPEG quality formula:
        # If Q >= 50: S = 200 - 2Q  -->  2Q = 200 - S  --> Q = 100 - S/2
        # If Q < 50:  S = 5000/Q    -->  Q = 5000/S
        
        if avg_scaling_factor <= 100:
            quality = 100.0 - (avg_scaling_factor / 2.0)
        else:
            quality = 5000.0 / avg_scaling_factor
            
        return int(round(quality))

    except Exception:
        return None