from PIL import Image, ImageChops, ImageEnhance
import io

def process_ela(image_input, quality=90, scale=10):
    """
    Generates an Error Level Analysis (ELA) image.
    """
    # 1. Ensure image is in RGB mode (handles PNGs/Transparency issues)
    original = image_input.convert('RGB')
    
    # 2. Save the image to memory (RAM) as a compressed JPEG
    buffer = io.BytesIO()
    original.save(buffer, 'JPEG', quality=quality)
    buffer.seek(0)
    
    # 3. Reload the compressed image from memory
    compressed = Image.open(buffer)
    
    # 4. Calculate the difference (The "Error")
    ela_image = ImageChops.difference(original, compressed)
    
    # 5. Amplify the difference so our eyes can see it
    extrema = ela_image.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    
    if max_diff == 0:
        max_diff = 1
        
    scale_factor = 255.0 / max_diff * (scale / 10.0)
    ela_image = ImageEnhance.Brightness(ela_image).enhance(scale_factor)
    
    return ela_image