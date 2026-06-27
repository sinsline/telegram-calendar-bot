"""
Speech Service for Telegram Calendar Bot

Provides speech-to-text conversion using OpenAI Whisper with multi-language support.
Includes mock fallback for testing environments without heavy dependencies.
"""

import io
import logging
import tempfile
import os
from typing import Optional, Union
import whisper


logger = logging.getLogger(__name__)


class SpeechError(Exception):
    """Custom exception for speech-related errors."""
    pass


class SpeechService:
    """
    Speech service using OpenAI Whisper for speech-to-text conversion.
    
    Supports multiple languages (Russian, German, English) and includes
    mock fallback for testing environments.
    """
    
    def __init__(self, model_name: str = "base"):
        """
        Initialize speech service.
        
        Args:
            model_name: Whisper model to use ("tiny", "base", "small", "medium", "large")
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load Whisper model."""
        try:
            self.model = whisper.load_model(self.model_name)
            logger.info(f"Loaded Whisper model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise SpeechError(f"Model loading failed: {e}")
    
    def transcribe(self, audio_data: bytes, language: Optional[str] = None) -> str:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Audio file data in bytes
            language: Language code for better accuracy (optional)
            
        Returns:
            Transcribed text
        """
        if not self.model:
            raise SpeechError("Whisper model not loaded")
        
        try:
            # Write audio data to temporary file
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Map language codes to Whisper format
                whisper_lang = self._map_language_code(language)
                
                # Transcribe audio
                if whisper_lang:
                    result = self.model.transcribe(temp_file_path, language=whisper_lang)
                else:
                    result = self.model.transcribe(temp_file_path)
                
                text = result.get('text', '').strip()
                logger.info(f"Transcription successful: {len(text)} characters")
                return text
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
                    
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise SpeechError(f"Transcription failed: {e}")
    
    def transcribe_file(self, file_path: str, language: Optional[str] = None) -> str:
        """
        Transcribe audio file to text.
        
        Args:
            file_path: Path to audio file
            language: Language code for better accuracy (optional)
            
        Returns:
            Transcribed text
        """
        if not self.model:
            raise SpeechError("Whisper model not loaded")
        
        try:
            # Map language codes to Whisper format
            whisper_lang = self._map_language_code(language)
            
            # Transcribe audio file
            if whisper_lang:
                result = self.model.transcribe(file_path, language=whisper_lang)
            else:
                result = self.model.transcribe(file_path)
            
            text = result.get('text', '').strip()
            logger.info(f"File transcription successful: {len(text)} characters")
            return text
            
        except Exception as e:
            logger.error(f"File transcription failed: {e}")
            raise SpeechError(f"File transcription failed: {e}")
    
    def _map_language_code(self, language: Optional[str]) -> Optional[str]:
        """
        Map Telegram language codes to Whisper language codes.
        
        Args:
            language: Telegram language code (en, ru, de, etc.)
            
        Returns:
            Whisper language code or None for auto-detection
        """
        if not language:
            return None
        
        # Language mapping from Telegram to Whisper
        language_map = {
            'en': 'en',    # English
            'ru': 'ru',    # Russian
            'de': 'de',    # German
            'es': 'es',    # Spanish
            'fr': 'fr',    # French
            'it': 'it',    # Italian
            'pt': 'pt',    # Portuguese
            'pl': 'pl',    # Polish
            'tr': 'tr',    # Turkish
            'nl': 'nl',    # Dutch
            'sv': 'sv',    # Swedish
            'da': 'da',    # Danish
            'no': 'no',    # Norwegian
            'fi': 'fi',    # Finnish
            'cs': 'cs',    # Czech
            'sk': 'sk',    # Slovak
            'hu': 'hu',    # Hungarian
            'ro': 'ro',    # Romanian
            'bg': 'bg',    # Bulgarian
            'hr': 'hr',    # Croatian
            'sr': 'sr',    # Serbian
            'sl': 'sl',    # Slovenian
            'et': 'et',    # Estonian
            'lv': 'lv',    # Latvian
            'lt': 'lt',    # Lithuanian
            'uk': 'uk',    # Ukrainian
            'be': 'be',    # Belarusian
            'ka': 'ka',    # Georgian
            'ar': 'ar',    # Arabic
            'fa': 'fa',    # Persian
            'he': 'he',    # Hebrew
            'hi': 'hi',    # Hindi
            'th': 'th',    # Thai
            'vi': 'vi',    # Vietnamese
            'zh': 'zh',    # Chinese
            'ja': 'ja',    # Japanese
            'ko': 'ko',    # Korean
        }
        
        return language_map.get(language.lower())
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages."""
        return [
            'en', 'ru', 'de', 'es', 'fr', 'it', 'pt', 'pl', 'tr', 'nl',
            'sv', 'da', 'no', 'fi', 'cs', 'sk', 'hu', 'ro', 'bg', 'hr',
            'sr', 'sl', 'et', 'lv', 'lt', 'uk', 'be', 'ka', 'ar', 'fa',
            'he', 'hi', 'th', 'vi', 'zh', 'ja', 'ko'
        ]


class MockSpeechService:
    """
    Mock Speech service for testing environments.
    
    Returns predefined responses for testing purposes without
    requiring heavy Whisper model dependencies.
    """
    
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        logger.info("Initialized mock speech service")
    
    def transcribe(self, audio_data: bytes, language: Optional[str] = None) -> str:
        """Mock speech transcription."""
        # Return mock transcription based on audio data length
        if len(audio_data) > 10000:
            return "This is a longer mock transcription for testing purposes"
        elif len(audio_data) > 5000:
            return "Meeting tomorrow at 2 PM"
        else:
            return "Mock transcription"
    
    def transcribe_file(self, file_path: str, language: Optional[str] = None) -> str:
        """Mock file transcription."""
        # Return mock transcription based on file name or default
        if 'meeting' in file_path.lower():
            return "Schedule meeting for Friday at 3 PM"
        elif 'appointment' in file_path.lower():
            return "Dentist appointment Monday 10:30 AM"
        else:
            return "Mock file transcription"
    
    def get_supported_languages(self) -> list:
        """Return mock supported languages."""
        return ['en', 'ru', 'de']


def create_speech_service(model_name: str = "base") -> Union[SpeechService, MockSpeechService]:
    """
    Factory function to create speech service with fallback to mock.
    
    Args:
        model_name: Whisper model to use
        
    Returns:
        SpeechService instance or MockSpeechService if dependencies unavailable
    """
    try:
        return SpeechService(model_name)
    except (SpeechError, ImportError) as e:
        logger.warning(f"Falling back to mock speech service: {e}")
        return MockSpeechService(model_name)