"""
Speech-to-Text Module for Fake News Detection System
Converts voice input to text using free speech recognition.
"""
import io
import speech_recognition as sr


# Language codes for Google Speech Recognition
SPEECH_LANGUAGES = {
    'English': 'en-IN',
    'Hindi': 'hi-IN',
    'Telugu': 'te-IN', 
    'Tamil': 'ta-IN',
    'Malayalam': 'ml-IN',
    'Kannada': 'kn-IN',
    'Bengali': 'bn-IN',
    'Marathi': 'mr-IN',
    'Gujarati': 'gu-IN',
}


def convert_audio_to_text(audio_bytes: bytes, language: str = 'English') -> dict:
    """Convert audio bytes to text using Google Speech Recognition (FREE).
    
    Args:
        audio_bytes: Raw audio data in WAV format
        language: Language name (e.g., 'English', 'Hindi', 'Telugu')
    
    Returns:
        dict: {'success': True/False, 'text': '...', 'error': '...'}
    """
    recognizer = sr.Recognizer()
    lang_code = SPEECH_LANGUAGES.get(language, 'en-IN')
    
    try:
        # Convert bytes to AudioData
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
        
        # Use Google's free speech recognition
        text = recognizer.recognize_google(audio_data, language=lang_code)
        
        return {
            'success': True,
            'text': text,
            'language': language,
            'error': None
        }
    
    except sr.UnknownValueError:
        return {
            'success': False,
            'text': '',
            'language': language,
            'error': 'Could not understand audio. Please speak clearly and try again.'
        }
    except sr.RequestError as e:
        return {
            'success': False,
            'text': '',
            'language': language,
            'error': f'Speech recognition service error: {str(e)}. Check your internet connection.'
        }
    except Exception as e:
        return {
            'success': False,
            'text': '',
            'language': language,
            'error': f'Error processing audio: {str(e)}'
        }


def get_supported_languages() -> list:
    """Return list of supported languages for speech recognition."""
    return list(SPEECH_LANGUAGES.keys())
