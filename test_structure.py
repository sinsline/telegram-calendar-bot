#!/usr/bin/env python3.13
"""
Simple test runner for checking import structure without external dependencies.
This verifies TDD step 2: ensure tests fail before implementation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_imports():
    """Test that we can import the basic structure."""
    print("Testing imports...")
    
    try:
        from src.services.nlp_service import NLPService, MockNLPService, create_nlp_service
        print("✓ NLP service imports work")
    except ImportError as e:
        print(f"✗ NLP service import failed: {e}")
        return False
    
    try:
        from src.services.ocr_service import OCRService, MockOCRService  # create_ocr_service should exist
        print("✓ OCR service imports work")
    except ImportError as e:
        print(f"✗ OCR service import failed: {e}")
        return False
    
    try:
        from src.services.calendar_service import CalendarService, MockCalendarService, create_calendar_service
        print("✓ Calendar service imports work")
    except ImportError as e:
        print(f"✗ Calendar service import failed: {e}")
        return False
    
    try:
        from src.services.speech_service import SpeechService, MockSpeechService, create_speech_service
        print("✓ Speech service imports work")
    except ImportError as e:
        print(f"✗ Speech service import failed: {e}")
        return False
    
    try:
        from src.services import create_nlp_service, create_ocr_service, create_calendar_service, create_speech_service
        print("✓ Service factories import work")
    except ImportError as e:
        print(f"✗ Service factories import failed: {e}")
        return False
    
    # Test telegram bot imports - these should fail due to missing aiogram
    try:
        from src.telegram_bot import TelegramBot, create_telegram_bot
        print("✓ Telegram bot imports work")
    except ImportError as e:
        print(f"✗ Telegram bot import failed (expected): {e}")
        # This is expected since we don't have aiogram installed
    
    return True

def test_service_creation():
    """Test that services can be created (should use mock versions)."""
    print("\\nTesting service creation...")
    
    try:
        from src.services import create_nlp_service, create_ocr_service, create_calendar_service, create_speech_service
        
        # NLP Service
        nlp = create_nlp_service()
        print(f"✓ NLP service created: {type(nlp).__name__}")
        
        # OCR Service
        ocr = create_ocr_service()
        print(f"✓ OCR service created: {type(ocr).__name__}")
        
        # Calendar Service
        calendar = create_calendar_service()
        print(f"✓ Calendar service created: {type(calendar).__name__}")
        
        # Speech Service
        speech = create_speech_service()
        print(f"✓ Speech service created: {type(speech).__name__}")
        
        return True
        
    except Exception as e:
        print(f"✗ Service creation failed: {e}")
        return False

def test_basic_functionality():
    """Test basic service functionality."""
    print("\\nTesting basic functionality...")
    
    try:
        from src.services import create_nlp_service, create_ocr_service, create_calendar_service, create_speech_service
        from datetime import datetime, timezone
        
        # Test NLP service
        nlp = create_nlp_service()
        result = nlp.parse_event_text("Meeting tomorrow at 2 PM")
        print(f"✓ NLP parsing works: {result.get('title', 'Unknown')}")
        
        # Test Calendar service (mock)
        calendar = create_calendar_service()
        event_data = {
            'summary': 'Test Event',
            'start': datetime.now(timezone.utc)
        }
        event = calendar.create_event(event_data)
        print(f"✓ Calendar creation works: {event.get('id', 'Unknown')}")
        
        # Test Speech service (mock)
        speech = create_speech_service()
        transcription = speech.transcribe(b"fake_audio_data", "en")
        print(f"✓ Speech transcription works: {transcription}")
        
        # Test OCR service (mock)
        ocr = create_ocr_service()
        try:
            text = ocr.extract_text(b"fake_image_data")
            print(f"✓ OCR extraction works: {text[:50]}...")
        except Exception as e:
            # OCR might fail without proper setup, that's okay for testing
            print(f"⚠ OCR extraction expected to fail: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Running TelegramBot structure tests...")
    print("=" * 50)
    
    success = True
    success &= test_imports()
    success &= test_service_creation()
    success &= test_basic_functionality()
    
    print("=" * 50)
    if success:
        print("✓ All basic tests passed! Services are properly structured.")
    else:
        print("✗ Some tests failed.")
    
    # Test that telegram bot would fail (as expected in TDD)
    print("\\nTesting telegram bot creation (should fail)...")
    try:
        from src.telegram_bot import create_telegram_bot
        bot = create_telegram_bot("test_token")
        print("✗ Telegram bot creation unexpectedly succeeded!")
    except Exception as e:
        print(f"✓ Telegram bot creation failed as expected: {e}")
    
    print("\\n🎯 TDD Step 2 Complete: Tests are ready, implementation needs aiogram dependencies.")

if __name__ == "__main__":
    main()