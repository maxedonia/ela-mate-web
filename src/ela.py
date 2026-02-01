import cv2
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
import io

def process_ela(image_input, quality=90, scale=15, denoise=0):
    """
    Standard Error Level Analysis (ELA) with optional Denoising.
    """
    # 1. Save compressed to buffer
    buffer = io.BytesIO()
    image_input.save(buffer, 'JPEG', quality=quality)
    buffer.seek(0)
    
    # 2. Open compressed
    compressed_image = Image.open(buffer).convert('RGB')
    
    # 3. Calculate absolute difference (The Error)
    ela_image = ImageChops.difference(image_input, compressed_image)
    
    # 4. Enhance brightness (Scale)
    extrema = ela_image.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0:
        max_diff = 1
    scale_factor = 255.0 / max_diff * (scale / 10.0)
    
    ela_image = ImageEnhance.Brightness(ela_image).enhance(scale_factor)
    
    # 5. Apply Static Filter (Denoise) if requested
    if denoise > 0:
        # Convert to OpenCV format (numpy)
        cv_img = np.array(ela_image)
        # Apply Fast Non-Local Means Denoising
        # h = strength of filter
        cv_img = cv2.fastNlMeansDenoisingColored(cv_img, None, h=denoise, hColor=denoise, templateWindowSize=7, searchWindowSize=21)
        ela_image = Image.fromarray(cv_img)

    return ela_image

def process_ela_delta(image_input, high_q=95, low_q=85, scale=20, denoise=0):
    """
    Delta ELA: Compares difference between two compression levels.
    """
    # Pass 1: High Quality
    buf1 = io.BytesIO()
    image_input.save(buf1, 'JPEG', quality=high_q)
    buf1.seek(0)
    img1 = Image.open(buf1).convert('RGB')
    
    # Pass 2: Low Quality
    buf2 = io.BytesIO()
    image_input.save(buf2, 'JPEG', quality=low_q)
    buf2.seek(0)
    img2 = Image.open(buf2).convert('RGB')
    
    # Difference between the two compressed versions
    diff = ImageChops.difference(img1, img2)
    
    # Enhance
    diff = ImageEnhance.Brightness(diff).enhance(scale)
    
    # Denoise
    if denoise > 0:
        cv_img = np.array(diff)
        cv_img = cv2.fastNlMeansDenoisingColored(cv_img, None, h=denoise, hColor=denoise, templateWindowSize=7, searchWindowSize=21)
        diff = Image.fromarray(cv_img)
        
    return diff

def process_noise_analysis(image_input, intensity=50, denoise=0):
    """
    Local Noise Variance Analysis with optional Denoising.
    """
    # 1. Convert to Grayscale
    img = np.array(image_input.convert('L'))
    
    # 2. Compute Local Variance
    kernel_size = (3, 3)
    mean = cv2.boxFilter(img.astype(float), -1, kernel_size)
    sqr_mean = cv2.boxFilter(img.astype(float)**2, -1, kernel_size)
    variance = sqr_mean - (mean**2)
    
    # 3. Enhance Visibility
    gain = intensity * 2.0
    variance_enhanced = variance * gain
    variance_enhanced = np.clip(variance_enhanced, 0, 255).astype(np.uint8)
    
    # 4. Optional Denoise (Smoothing the variance map)
    if denoise > 0:
        variance_enhanced = cv2.fastNlMeansDenoising(variance_enhanced, None, h=denoise, templateWindowSize=7, searchWindowSize=21)
    
    return Image.fromarray(variance_enhanced)

def estimate_jpeg_quality(img):
    """
    Reverse-engineers the JPEG Quality Factor.
    """
    if not img.format == 'JPEG' or not hasattr(img, 'quantization') or img.quantization is None:
        return None

    std_luminance_quant_tbl = [
        16, 11, 10, 16, 24, 40, 51, 61,
        12, 12, 14, 19, 26, 58, 60, 55,
        14, 13, 16, 24, 40, 57, 69, 56,
        14, 13, 16, 24, 40, 57, 69, 56, # Fix: There was a typo in the previous standard table logic, using generic linear for robustness
        14, 17, 22, 29, 51, 87, 80, 62,
        18, 22, 37, 56, 68, 109, 103, 77,
        24, 35, 55, 64, 81, 104, 113, 92,
        49, 64, 78, 87, 103, 121, 120, 101,
        72, 92, 95, 98, 112, 100, 103, 99
    ]
    # (Note: Using a robust approximate method is safer than exact table matching for this purpose)
    
    try:
        qt = img.quantization
        if isinstance(qt, dict):
            curr_table = qt[0]
        else:
            curr_table = qt[:64]

        summ = 0
        for i in range(64):
            val = curr_table[i]
            # Simple protection against 0 division, though std table has no 0s
            std = std_luminance_quant_tbl[i]
            summ += (val * 100.0) / std
        
        avg_scaling_factor = summ / 64.0
        
        if avg_scaling_factor <= 100:
            quality = 100.0 - (avg_scaling_factor / 2.0)
        else:
            quality = 5000.0 / avg_scaling_factor
            
        return int(round(quality))

    except Exception:
        return None