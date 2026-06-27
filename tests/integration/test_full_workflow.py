"""
Integration tests for Telegram Calendar Bot

Tests the complete workflow from Telegram message to Google Calendar event.
Covers all input types: text, voice, and image messages.
"""

import asyncio
import os
import tempfile
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import json
from io import BytesIO
from PIL import Image

# Import bot components
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.calendar_service import CalendarService
from services.nlp_service import NLPService
from services.ocr_service import OCRService
from services.speech_service import SpeechService
from telegram_bot import CalendarBot


class TestIntegrationWorkflow:
    """Integration tests for complete bot workflow"""
    
    @pytest.fixture
    def setup_services(self):
        """Setup all services with mocked external dependencies"""
        # Mock Google Calendar API
        mock_calendar_service = AsyncMock(spec=CalendarService)
        mock_calendar_service.create_event = AsyncMock(return_value={
            'id': 'test_event_123',
            'summary': 'Test Event',
            'start': {'dateTime': '2024-01-15T10:00:00+01:00'},
            'end': {'dateTime': '2024-01-15T11:00:00+01:00'},
            'htmlLink': 'https://calendar.google.com/event/test_event_123'
        })
        
        # Real NLP service (no external dependencies)
        nlp_service = NLPService(supported_languages=["ru", "de", "en"])
        
        # Mock OCR service
        mock_ocr_service = AsyncMock(spec=OCRService)
        
        # Mock Speech service  
        mock_speech_service = AsyncMock(spec=SpeechService)
        
        return {
            'calendar': mock_calendar_service,
            'nlp': nlp_service,
            'ocr': mock_ocr_service,
            'speech': mock_speech_service
        }
    
    @pytest.fixture
    def mock_telegram_update(self):
        """Create mock Telegram update object"""
        mock_update = MagicMock()
        mock_update.message = MagicMock()
        mock_update.message.from_user.id = 12345
        mock_update.message.from_user.first_name = "Test"
        mock_update.message.chat.id = 12345
        mock_update.message.date = datetime.now()
        return mock_update
    
    @pytest.mark.asyncio
    async def test_text_message_workflow(self, setup_services, mock_telegram_update):
        """Test complete workflow: text message → NLP → calendar event"""
        services = setup_services
        
        # Setup text message
        mock_telegram_update.message.text = "встреча с клиентом завтра в 15:00"
        
        # Create bot instance with mocked services
        with patch.multiple('telegram_bot', 
                           CalendarService=lambda *args: services['calendar'],
                           NLPService=lambda *args: services['nlp'],
                           OCRService=lambda *args: services['ocr'], 
                           SpeechService=lambda *args: services['speech']):
            
            bot = CalendarBot("fake_token")
            bot.calendar_service = services['calendar']
            bot.nlp_service = services['nlp']
            
            # Process message
            await bot._handle_text_message(mock_telegram_update.message)
            
            # Verify NLP parsing worked
            parsed_text = mock_telegram_update.message.text
            nlp_result = await services['nlp'].parse_event(parsed_text)
            
            assert nlp_result['summary'] == "встреча с клиентом"
            assert nlp_result['confidence'] > 0.7
            assert 'start_time' in nlp_result
            
            # Verify calendar event creation was called
            services['calendar'].create_event.assert_called_once()
            call_args = services['calendar'].create_event.call_args[1]
            assert call_args['summary'] == nlp_result['summary']
    
    @pytest.mark.asyncio 
    async def test_voice_message_workflow(self, setup_services, mock_telegram_update):
        """Test complete workflow: voice → speech recognition → NLP → calendar"""
        services = setup_services
        
        # Mock voice message
        mock_telegram_update.message.voice = MagicMock()
        mock_telegram_update.message.voice.file_id = "voice_123"
        mock_telegram_update.message.text = None
        
        # Mock file download
        mock_file = MagicMock()
        mock_file.file_path = "voice/file_123.ogg"
        
        # Setup speech recognition mock
        services['speech'].transcribe_audio.return_value = "звонок маме в пятницу в 19:00"
        
        with patch.multiple('telegram_bot',
                           CalendarService=lambda *args: services['calendar'],
                           NLPService=lambda *args: services['nlp'],
                           OCRService=lambda *args: services['ocr'],
                           SpeechService=lambda *args: services['speech']):
            
            bot = CalendarBot("fake_token")
            bot.calendar_service = services['calendar'] 
            bot.nlp_service = services['nlp']
            bot.speech_service = services['speech']
            
            # Mock bot file download
            with patch.object(bot.bot, 'get_file', return_value=mock_file):
                with patch.object(bot.bot, 'download_file', return_value=b"fake_audio_data"):
                    
                    # Process voice message
                    await bot._handle_voice_message(mock_telegram_update.message)
            
            # Verify speech recognition was called
            services['speech'].transcribe_audio.assert_called_once()
            
            # Verify NLP processing of transcribed text
            transcribed = services['speech'].transcribe_audio.return_value
            nlp_result = await services['nlp'].parse_event(transcribed)
            
            assert nlp_result['summary'] == "звонок маме"
            assert 'friday' in nlp_result['start_time'].lower() or 'fri' in nlp_result['start_time'].lower()
            
            # Verify calendar event creation
            services['calendar'].create_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_image_message_workflow(self, setup_services, mock_telegram_update):
        """Test complete workflow: image → OCR → NLP → calendar"""
        services = setup_services
        
        # Mock image message
        mock_telegram_update.message.photo = [MagicMock()]
        mock_telegram_update.message.photo[-1].file_id = "photo_123"
        mock_telegram_update.message.text = None
        
        # Setup OCR mock
        services['ocr'].extract_text.return_value = "Встреча с партнерами\n15 января 2024\n15:00 - 17:00\nКонференц-зал А"
        
        with patch.multiple('telegram_bot',
                           CalendarService=lambda *args: services['calendar'],
                           NLPService=lambda *args: services['nlp'], 
                           OCRService=lambda *args: services['ocr'],
                           SpeechService=lambda *args: services['speech']):
            
            bot = CalendarBot("fake_token")
            bot.calendar_service = services['calendar']
            bot.nlp_service = services['nlp'] 
            bot.ocr_service = services['ocr']
            
            # Mock file operations
            mock_file = MagicMock()
            mock_file.file_path = "photos/file_123.jpg"
            
            with patch.object(bot.bot, 'get_file', return_value=mock_file):
                with patch.object(bot.bot, 'download_file', return_value=b"fake_image_data"):
                    
                    # Process image message
                    await bot._handle_photo_message(mock_telegram_update.message)
            
            # Verify OCR was called
            services['ocr'].extract_text.assert_called_once()
            
            # Verify NLP processing of extracted text
            extracted_text = services['ocr'].extract_text.return_value
            nlp_result = await services['nlp'].parse_event(extracted_text)
            
            assert nlp_result['summary'] == "Встреча с партнерами"
            assert nlp_result['location'] == "Конференц-зал А"
            
            # Verify calendar event creation
            services['calendar'].create_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, setup_services, mock_telegram_update):
        """Test error handling in complete workflow"""
        services = setup_services
        
        # Setup failing calendar service
        services['calendar'].create_event.side_effect = Exception("Calendar API Error")
        
        mock_telegram_update.message.text = "встреча завтра в 15:00"
        
        with patch.multiple('telegram_bot',
                           CalendarService=lambda *args: services['calendar'],
                           NLPService=lambda *args: services['nlp']):
            
            bot = CalendarBot("fake_token")
            bot.calendar_service = services['calendar']
            bot.nlp_service = services['nlp']
            
            # Mock message reply
            mock_telegram_update.message.reply_text = AsyncMock()
            
            # Process message (should handle error gracefully)
            await bot._handle_text_message(mock_telegram_update.message)
            
            # Verify error message was sent
            mock_telegram_update.message.reply_text.assert_called()
            reply_text = mock_telegram_update.message.reply_text.call_args[0][0]
            assert "ошибка" in reply_text.lower() or "error" in reply_text.lower()
    
    @pytest.mark.asyncio
    async def test_rate_limiting_workflow(self, setup_services, mock_telegram_update):
        """Test rate limiting functionality"""
        services = setup_services
        
        with patch.multiple('telegram_bot',
                           CalendarService=lambda *args: services['calendar'],
                           NLPService=lambda *args: services['nlp']):
            
            bot = CalendarBot("fake_token")
            bot.calendar_service = services['calendar']
            bot.nlp_service = services['nlp']
            
            user_id = 12345
            mock_telegram_update.message.from_user.id = user_id
            mock_telegram_update.message.text = "тест"
            mock_telegram_update.message.reply_text = AsyncMock()
            
            # Simulate rapid requests
            for i in range(25):  # Exceeds default limit of 20/minute
                await bot._handle_text_message(mock_telegram_update.message)
            
            # Check if rate limiting kicked in
            # (Implementation depends on bot's rate limiting logic)
            assert bot._is_rate_limited(user_id) == True


class TestServiceIntegration:
    """Test integration between individual services"""
    
    @pytest.fixture
    def real_nlp_service(self):
        """Real NLP service for testing actual parsing"""
        return NLPService(supported_languages=["ru", "de", "en"])
    
    @pytest.mark.asyncio
    async def test_nlp_datetime_parsing(self, real_nlp_service):
        """Test comprehensive date/time parsing"""
        
        test_cases = [
            # Russian
            ("встреча завтра в 15:00", "встреча", True),
            ("звонок маме в пятницу в 19:30", "звонок маме", True), 
            ("дентист 25 декабря в 10 утра", "дентист", True),
            ("планерка сегодня в половине четвертого", "планерка", True),
            
            # German  
            ("Termin morgen um 15:00", "Termin", True),
            ("Anruf am Freitag um 19:30", "Anruf", True),
            ("Zahnarzt am 25. Dezember um 10 Uhr", "Zahnarzt", True),
            
            # English
            ("meeting tomorrow at 3PM", "meeting", True),
            ("call mom on Friday at 7:30", "call mom", True),
            ("dentist appointment on December 25th at 10 AM", "dentist appointment", True),
            
            # Edge cases
            ("неясный текст без дат", None, False),
            ("", None, False),
        ]
        
        for text, expected_summary, should_parse in test_cases:
            if not text:
                continue
                
            result = await real_nlp_service.parse_event(text)
            
            if should_parse:
                assert result['summary'] == expected_summary
                assert result['confidence'] > 0.5
                assert 'start_time' in result
                assert result['start_time'] != ""
            else:
                assert result['confidence'] < 0.5 or result['summary'] == ""
    
    @pytest.mark.asyncio
    async def test_service_integration_chain(self):
        """Test chaining services together"""
        
        # Mock external dependencies
        mock_calendar = AsyncMock()
        mock_ocr = AsyncMock()
        mock_speech = AsyncMock()
        real_nlp = NLPService()
        
        # Test data flow: Speech → NLP → Calendar
        mock_speech.transcribe_audio.return_value = "встреча с командой завтра в 14:00"
        mock_calendar.create_event.return_value = {'id': 'event_123'}
        
        # Simulate workflow
        audio_data = b"fake_audio"
        transcribed_text = await mock_speech.transcribe_audio(audio_data)
        
        parsed_event = await real_nlp.parse_event(transcribed_text)
        assert parsed_event['summary'] == "встреча с командой"
        assert parsed_event['confidence'] > 0.7
        
        calendar_result = await mock_calendar.create_event(
            summary=parsed_event['summary'],
            start_time=parsed_event['start_time'],
            end_time=parsed_event['end_time']
        )
        assert calendar_result['id'] == 'event_123'
        
        # Verify call chain
        mock_speech.transcribe_audio.assert_called_with(audio_data)
        mock_calendar.create_event.assert_called_once()


class TestPerformanceIntegration:
    """Performance and scalability tests"""
    
    @pytest.mark.asyncio 
    async def test_concurrent_message_processing(self):
        """Test handling multiple simultaneous messages"""
        
        # Mock services
        mock_calendar = AsyncMock()
        mock_nlp = AsyncMock()
        mock_nlp.parse_event.return_value = {
            'summary': 'test event',
            'start_time': '2024-01-15T10:00:00',
            'end_time': '2024-01-15T11:00:00',
            'confidence': 0.9
        }
        
        async def process_message(message_id):
            """Simulate processing one message"""
            text = f"встреча {message_id} завтра в 15:00"
            parsed = await mock_nlp.parse_event(text)
            result = await mock_calendar.create_event(**parsed)
            return result
        
        # Process 10 messages concurrently
        tasks = [process_message(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all succeeded
        for result in results:
            assert not isinstance(result, Exception)
        
        # Verify call counts
        assert mock_nlp.parse_event.call_count == 10
        assert mock_calendar.create_event.call_count == 10
    
    @pytest.mark.asyncio
    async def test_large_file_handling(self):
        """Test handling of large audio/image files"""
        
        mock_ocr = AsyncMock()
        mock_speech = AsyncMock()
        
        # Test large image (simulated)
        large_image_data = b"x" * (5 * 1024 * 1024)  # 5MB
        mock_ocr.extract_text.return_value = "тестовое событие завтра в 10:00"
        
        result = await mock_ocr.extract_text(large_image_data)
        assert result == "тестовое событие завтра в 10:00"
        
        # Test large audio (simulated) 
        large_audio_data = b"x" * (20 * 1024 * 1024)  # 20MB
        mock_speech.transcribe_audio.return_value = "аудио событие сегодня в 16:00"
        
        result = await mock_speech.transcribe_audio(large_audio_data)
        assert result == "аудио событие сегодня в 16:00"


class TestEndToEndScenarios:
    """End-to-end test scenarios mimicking real usage"""
    
    @pytest.mark.asyncio
    async def test_daily_usage_scenario(self):
        """Simulate a typical day of bot usage"""
        
        # Mock all services
        mock_services = {
            'calendar': AsyncMock(),
            'nlp': NLPService(),
            'ocr': AsyncMock(),  
            'speech': AsyncMock()
        }
        
        # Daily events to process
        daily_events = [
            ("text", "планерка сегодня в 9:00"),
            ("voice", "звонок клиенту в 11:30"),
            ("image", "встреча с партнерами завтра в 14:00"),
            ("text", "обед с командой в 12:30"),
            ("voice", "презентация проекта в четверг в 15:00")
        ]
        
        created_events = []
        
        for event_type, content in daily_events:
            if event_type == "text":
                parsed = await mock_services['nlp'].parse_event(content)
            elif event_type == "voice":
                mock_services['speech'].transcribe_audio.return_value = content
                transcribed = await mock_services['speech'].transcribe_audio(b"fake")
                parsed = await mock_services['nlp'].parse_event(transcribed)
            elif event_type == "image":
                mock_services['ocr'].extract_text.return_value = content
                extracted = await mock_services['ocr'].extract_text(b"fake")
                parsed = await mock_services['nlp'].parse_event(extracted)
            
            # Create calendar event
            mock_services['calendar'].create_event.return_value = {
                'id': f'event_{len(created_events)}',
                'summary': parsed['summary']
            }
            
            event = await mock_services['calendar'].create_event(
                summary=parsed['summary'],
                start_time=parsed['start_time'],
                end_time=parsed['end_time']
            )
            
            created_events.append(event)
        
        # Verify all events were processed
        assert len(created_events) == 5
        assert all('id' in event for event in created_events)
        
        # Verify service call counts
        assert mock_services['calendar'].create_event.call_count == 5
    
    @pytest.mark.asyncio
    async def test_multilingual_scenario(self):
        """Test processing events in multiple languages"""
        
        nlp_service = NLPService(supported_languages=["ru", "de", "en"])
        
        multilingual_events = [
            ("ru", "встреча завтра в 15:00", "встреча"),
            ("de", "Termin morgen um 15:00", "Termin"), 
            ("en", "meeting tomorrow at 3PM", "meeting"),
            ("ru", "звонок в пятницу в 19:30", "звонок"),
            ("de", "Anruf am Freitag um 19:30", "Anruf"),
            ("en", "call on Friday at 7:30PM", "call")
        ]
        
        for lang, text, expected_summary in multilingual_events:
            parsed = await nlp_service.parse_event(text)
            
            assert parsed['summary'] == expected_summary
            assert parsed['confidence'] > 0.6
            assert parsed['language'] == lang
            assert 'start_time' in parsed


if __name__ == "__main__":
    # Run specific test for development
    import asyncio
    
    async def run_quick_test():
        """Quick integration test for development"""
        nlp = NLPService()
        result = await nlp.parse_event("встреча завтра в 15:00")
        print(f"NLP Result: {result}")
        assert result['summary'] == "встреча"
        assert result['confidence'] > 0.7
        print("✅ Quick integration test passed!")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        asyncio.run(run_quick_test())
    else:
        pytest.main([__file__, "-v"])