"""
Service factories for the Telegram Calendar Bot

Provides unified interface for creating all services with proper fallback handling.
"""

from .nlp_service import create_nlp_service
from .ocr_service import create_ocr_service
from .calendar_service import create_calendar_service  
from .speech_service import create_speech_service

__all__ = [
    'create_nlp_service',
    'create_ocr_service', 
    'create_calendar_service',
    'create_speech_service'
]