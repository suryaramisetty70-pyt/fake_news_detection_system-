"""
Speech-to-Text Module for Fake News Detection System
Converts voice input to text using free speech recognition.
"""
import io
import subprocess
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
    recognizer.operation_timeout = 10
    lang_code = SPEECH_LANGUAGES.get(language, 'en-IN')
    
    try:
        try:
            audio_file = sr.AudioFile(io.BytesIO(audio_bytes))
            with audio_file as source:
                audio_data = recognizer.record(source)
        except (ValueError, EOFError):
            # Browsers typically record WebM/Opus or MP4/AAC.
            from imageio_ffmpeg import get_ffmpeg_exe

            converted = subprocess.run(
                [get_ffmpeg_exe(), "-nostdin", "-loglevel", "error",
                 "-i", "pipe:0", "-t", "120", "-ac", "1", "-ar", "16000",
                 "-c:a", "pcm_s16le", "-f", "wav", "pipe:1"],
                input=audio_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                check=True, timeout=15,
            )
            with sr.AudioFile(io.BytesIO(converted.stdout)) as source:
                audio_data = recognizer.record(source)

        # Use Google's free speech recognition
        text = recognizer.recognize_google(audio_data, language=lang_code)
        
        return {
            'success': True,
            'text': text,
            'language': language,
            'error': None
        }
    
    except (subprocess.SubprocessError, ValueError, EOFError):
        return {"success": False, "text": "", "error": "Could not decode this audio recording."}
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
