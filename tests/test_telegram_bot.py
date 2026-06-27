"""
Tests for Telegram Bot

Tests for the main Telegram bot functionality including message handlers
and service integration for text, voice, photo, and command messages.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from io import BytesIO

# Import the bot module (which we'll create)
from src.telegram_bot import TelegramBot, create_telegram_bot


class TestTelegramBot:
    """Test cases for TelegramBot class."""

    @pytest.fixture
    def mock_services(self):
        """Mock services for testing."""
        return {
            'nlp_service': MagicMock(),
            'ocr_service': MagicMock(),
            'calendar_service': MagicMock(),
            'speech_service': MagicMock()
        }

    @pytest.fixture
    def telegram_bot(self, mock_services):
        """Create TelegramBot instance with mocked services."""
        return TelegramBot(
            token="test_token",
            nlp_service=mock_services['nlp_service'],
            ocr_service=mock_services['ocr_service'],
            calendar_service=mock_services['calendar_service'],
            speech_service=mock_services['speech_service']
        )

    @pytest.mark.asyncio
    async def test_text_message_handler(self, telegram_bot, mock_services):
        """Test text message processing with NLP parsing and calendar creation."""
        # Setup
        mock_message = MagicMock()
        mock_message.text = "Meeting tomorrow at 2 PM"
        mock_message.from_user.language_code = "en"
        
        # Mock NLP service response
        mock_datetime_info = {
            'datetime': datetime(2026, 6, 28, 14, 0, tzinfo=timezone.utc),
            'date_found': True,
            'time_found': True,
            'original_text': 'Meeting tomorrow at 2 PM',
            'confidence': 0.9
        }
        mock_event_data = {
            'title': 'Meeting',
            'datetime_info': mock_datetime_info,
            'original_text': 'Meeting tomorrow at 2 PM',
            'has_datetime': True
        }
        mock_services['nlp_service'].parse_event_text.return_value = mock_event_data
        
        # Mock calendar service response
        mock_event = {
            'id': 'event123',
            'summary': 'Meeting',
            'start': {'dateTime': '2026-06-28T14:00:00Z'},
            'htmlLink': 'https://calendar.google.com/event?eid=event123'
        }
        mock_services['calendar_service'].create_event.return_value = mock_event
        
        # Test the handler
        await telegram_bot.handle_text_message(mock_message)
        
        # Verify NLP service was called
        mock_services['nlp_service'].parse_event_text.assert_called_once_with("Meeting tomorrow at 2 PM")
        
        # Verify calendar service was called
        mock_services['calendar_service'].create_event.assert_called_once()
        call_args = mock_services['calendar_service'].create_event.call_args[0][0]
        assert call_args['summary'] == 'Meeting'
        assert call_args['start']['dateTime'] == '2026-06-28T14:00:00+00:00'

    @pytest.mark.asyncio
    async def test_voice_message_handler(self, telegram_bot, mock_services):
        """Test voice message processing with speech transcription and NLP parsing."""
        # Setup
        mock_message = MagicMock()
        mock_message.voice.file_id = "voice123"
        mock_message.from_user.language_code = "en"
        
        # Mock file download and speech recognition
        mock_file = MagicMock()
        mock_file.file_path = "voice/file123.ogg"
        
        telegram_bot.bot = MagicMock()
        telegram_bot.bot.get_file.return_value = mock_file
        telegram_bot.bot.download_file.return_value = b"voice_data"
        
        # Mock speech service response
        mock_services['speech_service'].transcribe.return_value = "Schedule meeting for Friday at 3 PM"
        
        # Mock NLP service response
        mock_datetime_info = {
            'datetime': datetime(2026, 7, 4, 15, 0, tzinfo=timezone.utc),
            'date_found': True,
            'time_found': True,
            'original_text': 'Schedule meeting for Friday at 3 PM',
            'confidence': 0.8
        }
        mock_event_data = {
            'title': 'Schedule meeting',
            'datetime_info': mock_datetime_info,
            'original_text': 'Schedule meeting for Friday at 3 PM',
            'has_datetime': True
        }
        mock_services['nlp_service'].parse_event_text.return_value = mock_event_data
        
        # Mock calendar service response
        mock_event = {
            'id': 'event456',
            'summary': 'Schedule meeting',
            'start': {'dateTime': '2026-07-04T15:00:00Z'},
            'htmlLink': 'https://calendar.google.com/event?eid=event456'
        }
        mock_services['calendar_service'].create_event.return_value = mock_event
        
        # Test the handler
        await telegram_bot.handle_voice_message(mock_message)
        
        # Verify speech service was called
        mock_services['speech_service'].transcribe.assert_called_once_with(b"voice_data", "en")
        
        # Verify NLP service was called with transcribed text
        mock_services['nlp_service'].parse_event_text.assert_called_once_with("Schedule meeting for Friday at 3 PM")

    @pytest.mark.asyncio
    async def test_photo_message_handler(self, telegram_bot, mock_services):
        """Test photo message processing with OCR text extraction and NLP parsing."""
        # Setup
        mock_message = MagicMock()
        mock_message.photo = [MagicMock(file_id="photo123")]
        mock_message.from_user.language_code = "en"
        
        # Mock file download
        mock_file = MagicMock()
        mock_file.file_path = "photos/file123.jpg"
        
        telegram_bot.bot = MagicMock()
        telegram_bot.bot.get_file.return_value = mock_file
        telegram_bot.bot.download_file.return_value = b"image_data"
        
        # Mock OCR service response
        mock_services['ocr_service'].extract_text.return_value = "Dentist appointment Monday 10:30 AM"
        
        # Mock NLP service response
        mock_datetime_info = {
            'datetime': datetime(2026, 6, 30, 10, 30, tzinfo=timezone.utc),
            'date_found': True,
            'time_found': True,
            'original_text': 'Dentist appointment Monday 10:30 AM',
            'confidence': 0.85
        }
        mock_event_data = {
            'title': 'Dentist appointment',
            'datetime_info': mock_datetime_info,
            'original_text': 'Dentist appointment Monday 10:30 AM',
            'has_datetime': True
        }
        mock_services['nlp_service'].parse_event_text.return_value = mock_event_data
        
        # Mock calendar service response
        mock_event = {
            'id': 'event789',
            'summary': 'Dentist appointment',
            'start': {'dateTime': '2026-06-30T10:30:00Z'},
            'htmlLink': 'https://calendar.google.com/event?eid=event789'
        }
        mock_services['calendar_service'].create_event.return_value = mock_event
        
        # Test the handler
        await telegram_bot.handle_photo_message(mock_message)
        
        # Verify OCR service was called
        mock_services['ocr_service'].extract_text.assert_called_once_with(b"image_data")
        
        # Verify NLP service was called with extracted text
        mock_services['nlp_service'].parse_event_text.assert_called_once_with("Dentist appointment Monday 10:30 AM")

    @pytest.mark.asyncio
    async def test_start_command_handler(self, telegram_bot):
        """Test /start command handler."""
        # Setup
        mock_message = MagicMock()
        mock_message.from_user.first_name = "John"
        mock_message.from_user.language_code = "en"
        mock_message.reply = AsyncMock()
        
        # Test the handler
        await telegram_bot.handle_start_command(mock_message)
        
        # Verify reply was called with welcome message
        mock_message.reply.assert_called_once()
        reply_text = mock_message.reply.call_args[0][0]
        assert "Hello John" in reply_text
        assert "Telegram Calendar Bot" in reply_text

    @pytest.mark.asyncio
    async def test_help_command_handler(self, telegram_bot):
        """Test /help command handler."""
        # Setup
        mock_message = MagicMock()
        mock_message.from_user.language_code = "en"
        mock_message.reply = AsyncMock()
        
        # Test the handler
        await telegram_bot.handle_help_command(mock_message)
        
        # Verify reply was called with help message
        mock_message.reply.assert_called_once()
        reply_text = mock_message.reply.call_args[0][0]
        assert "Available commands:" in reply_text
        assert "/start" in reply_text
        assert "/help" in reply_text

    @pytest.mark.asyncio
    async def test_events_command_handler(self, telegram_bot, mock_services):
        """Test /events command handler."""
        # Setup
        mock_message = MagicMock()
        mock_message.from_user.language_code = "en"
        mock_message.reply = AsyncMock()
        
        # Mock calendar service response
        mock_events = [
            {
                'id': 'event1',
                'summary': 'Meeting',
                'start': {'dateTime': '2026-06-28T14:00:00Z'},
                'htmlLink': 'https://calendar.google.com/event?eid=event1'
            },
            {
                'id': 'event2',
                'summary': 'Dentist',
                'start': {'dateTime': '2026-06-30T10:30:00Z'},
                'htmlLink': 'https://calendar.google.com/event?eid=event2'
            }
        ]
        mock_services['calendar_service'].get_upcoming_events.return_value = mock_events
        
        # Test the handler
        await telegram_bot.handle_events_command(mock_message)
        
        # Verify calendar service was called
        mock_services['calendar_service'].get_upcoming_events.assert_called_once()
        
        # Verify reply was called with events list
        mock_message.reply.assert_called_once()
        reply_text = mock_message.reply.call_args[0][0]
        assert "Upcoming events:" in reply_text
        assert "Meeting" in reply_text
        assert "Dentist" in reply_text

    @pytest.mark.asyncio
    async def test_cancel_command_handler(self, telegram_bot):
        """Test /cancel command handler."""
        # Setup
        mock_message = MagicMock()
        mock_message.from_user.language_code = "en"
        mock_message.reply = AsyncMock()
        
        # Test the handler
        await telegram_bot.handle_cancel_command(mock_message)
        
        # Verify reply was called with cancellation message
        mock_message.reply.assert_called_once()
        reply_text = mock_message.reply.call_args[0][0]
        assert "Operation cancelled" in reply_text or "Cancelled" in reply_text

    def test_get_user_language(self, telegram_bot):
        """Test user language detection."""
        # Test English
        mock_user = MagicMock()
        mock_user.language_code = "en"
        assert telegram_bot._get_user_language(mock_user) == "en"
        
        # Test Russian
        mock_user.language_code = "ru"
        assert telegram_bot._get_user_language(mock_user) == "ru"
        
        # Test German
        mock_user.language_code = "de"
        assert telegram_bot._get_user_language(mock_user) == "de"
        
        # Test unsupported language (fallback to English)
        mock_user.language_code = "fr"
        assert telegram_bot._get_user_language(mock_user) == "en"
        
        # Test no language code
        mock_user.language_code = None
        assert telegram_bot._get_user_language(mock_user) == "en"

    @pytest.mark.asyncio
    async def test_error_handling_nlp_failure(self, telegram_bot, mock_services):
        """Test error handling when NLP service fails."""
        # Setup
        mock_message = MagicMock()
        mock_message.text = "Invalid text"
        mock_message.from_user.language_code = "en"
        mock_message.reply = AsyncMock()
        
        # Mock NLP service to raise exception
        mock_services['nlp_service'].parse_event_text.side_effect = Exception("NLP failed")
        
        # Test the handler
        await telegram_bot.handle_text_message(mock_message)
        
        # Verify error message was sent
        mock_message.reply.assert_called_once()
        reply_text = mock_message.reply.call_args[0][0]
        assert "error" in reply_text.lower() or "failed" in reply_text.lower()

    @pytest.mark.asyncio
    async def test_error_handling_calendar_failure(self, telegram_bot, mock_services):
        """Test error handling when calendar service fails."""
        # Setup
        mock_message = MagicMock()
        mock_message.text = "Meeting tomorrow"
        mock_message.from_user.language_code = "en"
        mock_message.reply = AsyncMock()
        
        # Mock successful NLP but failed calendar
        mock_datetime_info = {
            'datetime': datetime(2026, 6, 28, 14, 0, tzinfo=timezone.utc),
            'date_found': True,
            'time_found': True,
            'original_text': 'Meeting tomorrow',
            'confidence': 0.9
        }
        mock_event_data = {
            'title': 'Meeting',
            'datetime_info': mock_datetime_info,
            'original_text': 'Meeting tomorrow',
            'has_datetime': True
        }
        mock_services['nlp_service'].parse_event_text.return_value = mock_event_data
        mock_services['calendar_service'].create_event.side_effect = Exception("Calendar failed")
        
        # Test the handler
        await telegram_bot.handle_text_message(mock_message)
        
        # Verify error message was sent
        mock_message.reply.assert_called_once()
        reply_text = mock_message.reply.call_args[0][0]
        assert "error" in reply_text.lower() or "failed" in reply_text.lower()

    def test_format_event_for_display(self, telegram_bot):
        """Test event formatting for display."""
        event = {
            'id': 'event123',
            'summary': 'Team Meeting',
            'start': {'dateTime': '2026-06-28T14:00:00Z'},
            'htmlLink': 'https://calendar.google.com/event?eid=event123'
        }
        
        formatted = telegram_bot._format_event_for_display(event)
        
        assert "Team Meeting" in formatted
        assert "Jun 28" in formatted or "28" in formatted
        assert "14:00" in formatted or "2:00" in formatted


class TestCreateTelegramBot:
    """Test cases for create_telegram_bot factory function."""

    @patch('src.telegram_bot.create_nlp_service')
    @patch('src.telegram_bot.create_ocr_service')  
    @patch('src.telegram_bot.create_calendar_service')
    @patch('src.telegram_bot.create_speech_service')
    def test_create_telegram_bot_with_services(self, mock_speech, mock_calendar, mock_ocr, mock_nlp):
        """Test creating telegram bot with all services."""
        # Setup mocks
        mock_nlp.return_value = MagicMock()
        mock_ocr.return_value = MagicMock()
        mock_calendar.return_value = MagicMock()
        mock_speech.return_value = MagicMock()
        
        # Test creation
        bot = create_telegram_bot("test_token")
        
        assert isinstance(bot, TelegramBot)
        assert bot.token == "test_token"
        
        # Verify services were created
        mock_nlp.assert_called_once()
        mock_ocr.assert_called_once()
        mock_calendar.assert_called_once()
        mock_speech.assert_called_once()

    def test_create_telegram_bot_missing_token(self):
        """Test creating telegram bot without token raises error."""
        with pytest.raises(ValueError, match="Token is required"):
            create_telegram_bot("")

    def test_create_telegram_bot_none_token(self):
        """Test creating telegram bot with None token raises error."""
        with pytest.raises(ValueError, match="Token is required"):
            create_telegram_bot(None)


if __name__ == "__main__":
    pytest.main([__file__])