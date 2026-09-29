"""
Image-to-Text (OCR) Module for Fake News Detection System
Extracts text from images using Tesseract OCR (FREE).
"""
import io
import os
from PIL import Image, ImageEnhance, ImageFilter

# Tesseract language codes
OCR_LANGUAGES = {
    'English': 'eng',
    'Hindi': 'hin',
    'Telugu': 'tel',
    'Tamil': 'tam',
    'Malayalam': 'mal',
    'Kannada': 'kan',
    'Bengali': 'ben',
    'Marathi': 'mar',
}


def preprocess_image(image: Image.Image) -> Image.Image:
    """Enhance image quality for better OCR results.
    
    Applies contrast enhancement, sharpening, and converts to grayscale.
    """
    # Convert to grayscale
    image = image.convert('L')
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    
    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)
    
    # Apply slight blur to remove noise, then sharpen
    image = image.filter(ImageFilter.MedianFilter(size=3))
    
    return image


def extract_text_from_image(image_input, language: str = 'English') -> dict:
    """Extract text from an image using Tesseract OCR.
    
    Args:
        image_input: PIL Image, file path, or bytes
        language: Language of the text in the image
    
    Returns:
        dict: {'success': True/False, 'text': '...', 'error': '...'}
    """
    try:
        import pytesseract
        # Configure path for Windows default installation
        tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    except ImportError:
        return {
            'success': False,
            'text': '',
            'error': 'Tesseract OCR Python bindings not found. Please verify dependencies.'
        }
    
    lang_code = OCR_LANGUAGES.get(language, 'eng')
    
    try:
        # Handle different input types
        if isinstance(image_input, bytes):
            image = Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, str):
            image = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            image = image_input
        else:
            return {
                'success': False,
                'text': '',
                'error': 'Unsupported image input type.'
            }
        
        # Preprocess image for better OCR
        processed_image = preprocess_image(image)
        
        # Extract text using Tesseract
        # Try with the specified language, fall back to English
        try:
            text = pytesseract.image_to_string(processed_image, lang=lang_code)
        except Exception:
            # Fallback to English if language pack not available
            text = pytesseract.image_to_string(processed_image, lang='eng')
            language = 'English (fallback)'
        
        text = text.strip()
        
        if not text:
            return {
                'success': False,
                'text': '',
                'error': 'No text found in the image. Try a clearer image.'
            }
        
        return {
            'success': True,
            'text': text,
            'language': language,
            'error': None
        }
    
    except Exception as e:
        return {
            'success': False,
            'text': '',
            'error': f'Error processing image: {str(e)}'
        }


def get_supported_ocr_languages() -> list:
    """Return list of supported OCR languages."""
    return list(OCR_LANGUAGES.keys())
