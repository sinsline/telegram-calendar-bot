"""
Test fixtures and mock data for integration tests
"""

import pytest
from datetime import datetime, timedelta
import json
import tempfile
import os
from unittest.mock import MagicMock, AsyncMock
from PIL import Image
import io

# Sample test data
SAMPLE_EVENTS = {
    "text_messages": [
        {
            "input": "встреча с клиентом завтра в 15:00",
            "expected": {
                "summary": "встреча с клиентом",
                "contains_time": "15:00",
                "language": "ru"
            }
        },
        {
            "input": "Termin morgen um 14:30",
            "expected": {
                "summary": "Termin", 
                "contains_time": "14:30",
                "language": "de"
            }
        },
        {
            "input": "meeting tomorrow at 3 PM",
            "expected": {
                "summary": "meeting",
                "contains_time": "15:00",
                "language": "en"
            }
        },
        {
            "input": "звонок маме в пятницу в 19:30",
            "expected": {
                "summary": "звонок маме",
                "contains_time": "19:30", 
                "day": "friday",
                "language": "ru"
            }
        },
        {
            "input": "дентист 25 декабря в 10 утра",
            "expected": {
                "summary": "дентист",
                "contains_time": "10:00",
                "month": "december",
                "day": "25",
                "language": "ru"
            }
        }
    ],
    
    "voice_transcriptions": [
        {
            "transcription": "напомни встретиться с андреем завтра в два часа дня",
            "expected": {
                "summary": "встретиться с андреем",
                "contains_time": "14:00",
                "language": "ru"
            }
        },
        {
            "transcription": "записать к врачу на следующей неделе в среду утром",
            "expected": {
                "summary": "записать к врачу",
                "day": "wednesday",
                "time_period": "morning",
                "language": "ru"
            }
        },
        {
            "transcription": "erinnerung anruf kunde freitag fünfzehn uhr",
            "expected": {
                "summary": "anruf kunde",
                "day": "friday",
                "contains_time": "15:00", 
                "language": "de"
            }
        }
    ],
    
    "ocr_extractions": [
        {
            "extracted_text": "Встреча с партнерами\\n15 января 2024\\n15:00 - 17:00\\nКонференц-зал А",
            "expected": {         
                "summary": "Встреча с партнерами",
                "start_time": "15:00",
                "end_time": "17:00",
                "location": "Конференц-зал А",
                "date": "2024-01-15",
                "language": "ru"
            }
        },
        {
            "extracted_text": "Dr. Schmidt\\nTermin: 20.12.2024\\nUhrzeit: 10:30\\nPraxis Hauptstraße 5",
            "expected": {
                "summary": "Dr. Schmidt",
                "date": "2024-12-20",
                "start_time": "10:30",
                "location": "Praxis Hauptstraße 5",
                "language": "de"
            }
        },
        {
            "extracted_text": "Project Meeting\\nJanuary 20, 2024\\n2:30 PM - 4:00 PM\\nConference Room B",
            "expected": {
                "summary": "Project Meeting", 
                "date": "2024-01-20",
                "start_time": "14:30",
                "end_time": "16:00",
                "location": "Conference Room B",
                "language": "en"
            }
        }
    ]
}

GOOGLE_CALENDAR_RESPONSES = {
    "list_events": {
        "items": [
            {
                "id": "test_event_1",
                "summary": "Existing Event 1",
                "start": {"dateTime": "2024-01-15T10:00:00+01:00"},
                "end": {"dateTime": "2024-01-15T11:00:00+01:00"},
                "status": "confirmed"
            },
            {
                "id": "test_event_2", 
                "summary": "Existing Event 2",
                "start": {"dateTime": "2024-01-16T14:00:00+01:00"},
                "end": {"dateTime": "2024-01-16T15:00:00+01:00"},
                "status": "confirmed"
            }
        ]
    },
    
    "create_event": {
        "id": "new_event_12345",
        "summary": "Created Event",
        "start": {"dateTime": "2024-01-17T15:00:00+01:00"},
        "end": {"dateTime": "2024-01-17T16:00:00+01:00"},
        "status": "confirmed",
        "htmlLink": "https://calendar.google.com/event/new_event_12345",
        "created": "2024-01-15T12:00:00Z",
        "updated": "2024-01-15T12:00:00Z"
    }
}

TELEGRAM_API_RESPONSES = {
    "get_file": {
        "file_id": "AgACAgIAAxkBAAIC",
        "file_unique_id": "AQADBAADmLwxG13V",
        "file_size": 12345,
        "file_path": "photos/file_123.jpg"
    }
}

ERROR_SCENARIOS = [
    {
        "name": "calendar_api_error",
        "error_type": "CalendarAPIError",
        "error_message": "Calendar API quota exceeded",
        "expected_user_message": "извините, временные проблемы с календарем"
    },
    {
        "name": "authentication_error", 
        "error_type": "AuthenticationError",
        "error_message": "Invalid credentials",
        "expected_user_message": "проблема с доступом к календарю"
    },
    {
        "name": "ocr_error",
        "error_type": "OCRError", 
        "error_message": "Could not process image",
        "expected_user_message": "не удалось распознать текст на изображении"
    },
    {
        "name": "speech_error",
        "error_type": "SpeechError",
        "error_message": "Audio file too large", 
        "expected_user_message": "файл слишком большой"
    },
    {
        "name": "parse_error",
        "error_type": "ParseError",
        "error_message": "Could not extract date/time",
        "expected_user_message": "не удалось понять дату и время"
    }
]

RATE_LIMIT_SCENARIOS = [
    {
        "user_id": 12345,
        "requests_per_minute": 25,  # Exceeds limit of 20
        "should_be_limited": True
    },
    {
        "user_id": 67890,
        "requests_per_minute": 15,  # Below limit
        "should_be_limited": False
    }
]

PERFORMANCE_TEST_DATA = {
    "concurrent_users": [
        {"user_id": 1000 + i, "message": f"событие {i} завтра в {10+i%8}:00"}
        for i in range(50)  # 50 concurrent users
    ],
    "large_files": {
        "audio_file_sizes": [1024*1024, 5*1024*1024, 15*1024*1024],  # 1MB, 5MB, 15MB
        "image_file_sizes": [500*1024, 2*1024*1024, 8*1024*1024]    # 500KB, 2MB, 8MB
    }
}


@pytest.fixture
def sample_events():
    """Provide sample test events"""
    return SAMPLE_EVENTS


@pytest.fixture  
def google_calendar_mocks():
    """Provide mock Google Calendar responses"""
    return GOOGLE_CALENDAR_RESPONSES


@pytest.fixture
def telegram_api_mocks():
    """Provide mock Telegram API responses"""
    return TELEGRAM_API_RESPONSES


@pytest.fixture
def error_scenarios():
    """Provide error test scenarios"""
    return ERROR_SCENARIOS


@pytest.fixture
def temp_image_file():
    """Create a temporary test image file"""
    # Create a simple test image
    img = Image.new('RGB', (800, 600), color='white')
    
    # Add some text-like rectangles (simulating text)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 750, 100], fill='black')  # Header
    draw.rectangle([50, 150, 400, 180], fill='black') # Date line
    draw.rectangle([50, 200, 500, 230], fill='black') # Time line
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    img.save(temp_file.name, 'JPEG')
    temp_file.close()
    
    yield temp_file.name
    
    # Cleanup
    os.unlink(temp_file.name)


@pytest.fixture
def temp_audio_file():
    """Create a temporary test audio file"""
    # Create minimal OGG file header (fake audio data)
    ogg_header = b'OggS\\x00\\x02\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'
    fake_audio_data = ogg_header + b'x' * 1000  # Fake audio content
    
    temp_file = tempfile.NamedTemporaryFile(suffix='.ogg', delete=False)
    temp_file.write(fake_audio_data)
    temp_file.close()
    
    yield temp_file.name
    
    # Cleanup
    os.unlink(temp_file.name)


@pytest.fixture
def mock_bot_instance():
    """Create a fully mocked bot instance for testing"""
    from unittest.mock import MagicMock, AsyncMock
    
    # Create mock bot  
    mock_bot = MagicMock()
    mock_bot.get_file = AsyncMock(return_value=MagicMock(file_path="test/file/path"))
    mock_bot.download_file = AsyncMock(return_value=b"fake_file_data")
    
    return mock_bot


@pytest.fixture
def mock_telegram_update():
    """Create a mock Telegram update object"""
    mock_update = MagicMock()
    
    # Message mock
    mock_update.message = MagicMock()
    mock_update.message.from_user.id = 12345
    mock_update.message.from_user.first_name = "Test"
    mock_update.message.from_user.username = "testuser"
    mock_update.message.chat.id = 12345
    mock_update.message.date = datetime.now()
    mock_update.message.reply_text = AsyncMock()
    mock_update.message.reply_photo = AsyncMock()
    mock_update.message.reply_document = AsyncMock()
    
    # Default to text message
    mock_update.message.text = "test message"
    mock_update.message.voice = None
    mock_update.message.photo = None
    mock_update.message.document = None
    
    return mock_update


@pytest.fixture
def mock_services():
    """Create all mocked services"""
    return {
        'calendar': AsyncMock(),
        'nlp': AsyncMock(), 
        'ocr': AsyncMock(),
        'speech': AsyncMock()
    }


def create_test_credentials():
    """Create fake Google credentials for testing"""
    return {
        "type": "service_account",
        "project_id": "test-calendar-bot",
        "private_key_id": "test123",
        "private_key": "-----BEGIN PRIVATE KEY-----\\nTEST_KEY_DATA\\n-----END PRIVATE KEY-----\\n",
        "client_email": "test-bot@test-calendar-bot.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }


def save_test_credentials(path):
    """Save test credentials to file"""
    credentials = create_test_credentials()
    with open(path, 'w') as f:
        json.dump(credentials, f, indent=2)


@pytest.fixture 
def test_credentials_file():
    """Create temporary credentials file for testing"""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    credentials = create_test_credentials()
    json.dump(credentials, temp_file, indent=2)
    temp_file.close()
    
    yield temp_file.name
    
    # Cleanup
    os.unlink(temp_file.name)


class MockDatetime:
    """Mock datetime for consistent testing"""
    
    @staticmethod
    def now():
        return datetime(2024, 1, 15, 12, 0, 0)  # Fixed test date
    
    @staticmethod 
    def today():
        return datetime(2024, 1, 15, 0, 0, 0).date()


# Helper functions for assertions
def assert_event_data_valid(event_data):
    """Assert that event data contains required fields"""
    required_fields = ['summary', 'start_time', 'end_time']
    for field in required_fields:
        assert field in event_data, f"Missing required field: {field}"
        assert event_data[field], f"Empty value for field: {field}"


def assert_calendar_api_call_correct(mock_calendar, expected_summary):
    """Assert calendar API was called with correct data"""
    mock_calendar.create_event.assert_called_once()
    call_args = mock_calendar.create_event.call_args
    
    # Check if called with keyword arguments
    if call_args[1]:  # kwargs
        assert call_args[1]['summary'] == expected_summary
    else:  # positional args
        assert expected_summary in str(call_args[0])


def assert_nlp_confidence_acceptable(parsed_result, min_confidence=0.7):
    """Assert NLP parsing confidence is acceptable"""
    assert 'confidence' in parsed_result
    assert parsed_result['confidence'] >= min_confidence, \
           f"NLP confidence {parsed_result['confidence']} below threshold {min_confidence}"


# Performance test helpers
async def measure_processing_time(async_func, *args, **kwargs):
    """Measure execution time of async function"""
    import time
    start_time = time.perf_counter()
    result = await async_func(*args, **kwargs)
    end_time = time.perf_counter()
    return result, (end_time - start_time)


def generate_stress_test_data(num_messages=100):
    """Generate data for stress testing"""
    import random
    
    message_templates = [
        "встреча {num} завтра в {hour}:00",
        "звонок клиенту {num} в {hour}:30", 
        "планерка {num} послезавтра в {hour}:15",
        "обед с командой {num} в {hour}:45"
    ]
    
    messages = []
    for i in range(num_messages):
        template = random.choice(message_templates)
        hour = random.randint(9, 18)
        message = template.format(num=i, hour=hour)
        messages.append({
            'user_id': 10000 + i % 50,  # 50 different users
            'text': message,
            'expected_summary': f"встреча {i}" if "встреча" in message else message.split()[0]
        })
    
    return messages