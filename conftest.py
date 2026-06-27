"""
Global pytest configuration and fixtures for Telegram Calendar Bot tests
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import tempfile
import json

# Add src to path for all tests
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_environment():
    """Setup mock environment variables for testing"""
    original_env = os.environ.copy()
    
    # Set test environment variables
    test_env = {
        'TELEGRAM_TOKEN': 'test_telegram_token_123',
        'GOOGLE_CREDENTIALS': 'test_credentials.json',
        'OPENAI_API_KEY': 'test_openai_key_123',
        'LOG_LEVEL': 'DEBUG',
        'RATE_LIMIT_REQUESTS': '20',
        'RATE_LIMIT_WINDOW': '60',
        'MAX_FILE_SIZE': '20971520',  # 20MB
        'SUPPORTED_LANGUAGES': 'ru,de,en'
    }
    
    os.environ.update(test_env)
    
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def temp_work_dir():
    """Create temporary working directory for tests"""
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        # Create basic directory structure
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True) 
        os.makedirs('temp', exist_ok=True)
        
        yield Path(temp_dir)
        
        os.chdir(original_cwd)


@pytest.fixture
def mock_google_credentials():
    """Create mock Google credentials file"""
    credentials_data = {
        "type": "service_account",
        "project_id": "test-calendar-bot-123",
        "private_key_id": "test_key_123",
        "private_key": "-----BEGIN PRIVATE KEY-----\nTEST_PRIVATE_KEY_DATA\n-----END PRIVATE KEY-----\n",
        "client_email": "test-bot@test-project.iam.gserviceaccount.com",
        "client_id": "123456789012345678901",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
    }
    
    # Create temporary credentials file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(credentials_data, temp_file, indent=2)
    temp_file.close()
    
    yield temp_file.name
    
    # Cleanup
    os.unlink(temp_file.name)


@pytest.fixture
def mock_telegram_bot():
    """Create mock Telegram bot instance"""
    mock_bot = MagicMock()
    
    # Mock bot methods
    mock_bot.get_file = AsyncMock()
    mock_bot.download_file = AsyncMock()
    mock_bot.send_message = AsyncMock()
    mock_bot.send_photo = AsyncMock()
    mock_bot.send_document = AsyncMock()
    
    # Mock file responses
    mock_bot.get_file.return_value = MagicMock(
        file_id="test_file_123",
        file_unique_id="unique_test_123",
        file_size=12345,
        file_path="test/path/file.jpg"
    )
    
    mock_bot.download_file.return_value = b"fake_file_data"
    
    return mock_bot


@pytest.fixture 
def sample_telegram_messages():
    """Provide sample Telegram message data for testing"""
    return {
        "text_messages": [
            {
                "text": "встреча с клиентом завтра в 15:00",
                "user_id": 12345,
                "chat_id": 12345,
                "expected_summary": "встреча с клиентом"
            },
            {
                "text": "Termin morgen um 14:30", 
                "user_id": 67890,
                "chat_id": 67890,
                "expected_summary": "Termin"
            },
            {
                "text": "meeting tomorrow at 3PM",
                "user_id": 11111,
                "chat_id": 11111, 
                "expected_summary": "meeting"
            }
        ],
        
        "voice_messages": [
            {
                "file_id": "voice_123",
                "duration": 5,
                "transcription": "напомни о звонке завтра в 10 утра",
                "expected_summary": "звонок"
            },
            {  
                "file_id": "voice_456",
                "duration": 8,
                "transcription": "встреча с командой в пятницу в 15:30",
                "expected_summary": "встреча с командой"
            }
        ],
        
        "photo_messages": [
            {
                "file_id": "photo_789",
                "width": 800,
                "height": 600,
                "file_size": 50000,
                "ocr_text": "Конференция\n20 января 2024\n10:00 - 18:00\nОтель Европа",
                "expected_summary": "Конференция"
            }
        ]
    }


@pytest.fixture
def mock_all_services():
    """Create complete set of mocked services"""
    
    # Calendar Service Mock
    calendar_mock = AsyncMock()
    calendar_mock.authenticate = AsyncMock(return_value=True)
    calendar_mock.create_event = AsyncMock(return_value={
        'id': 'test_event_123',
        'summary': 'Test Event',
        'start': {'dateTime': '2024-01-15T15:00:00+01:00'},
        'end': {'dateTime': '2024-01-15T16:00:00+01:00'},
        'htmlLink': 'https://calendar.google.com/event/test_event_123',
        'status': 'confirmed'
    })
    calendar_mock.list_events = AsyncMock(return_value=[])
    calendar_mock.update_event = AsyncMock(return_value={'id': 'updated_123'})
    calendar_mock.delete_event = AsyncMock(return_value=True)
    
    # Speech Service Mock  
    speech_mock = AsyncMock()
    speech_mock.transcribe_audio = AsyncMock(return_value="встреча завтра в 15:00")
    speech_mock.is_audio_valid = AsyncMock(return_value=True)
    speech_mock.convert_audio_format = AsyncMock(return_value=b"converted_audio")
    
    # OCR Service Mock
    ocr_mock = AsyncMock()
    ocr_mock.extract_text = AsyncMock(return_value="встреча завтра в 15:00")
    ocr_mock.is_image_valid = AsyncMock(return_value=True)
    ocr_mock.preprocess_image = AsyncMock(return_value=b"processed_image")
    
    # NLP Service Mock  
    nlp_mock = AsyncMock()
    nlp_mock.parse_event = AsyncMock(return_value={
        'summary': 'встреча',
        'start_time': '2024-01-16T15:00:00+01:00',
        'end_time': '2024-01-16T16:00:00+01:00', 
        'location': '',
        'description': '',
        'confidence': 0.85,
        'language': 'ru'
    })
    nlp_mock.detect_language = AsyncMock(return_value='ru')
    nlp_mock.extract_datetime = AsyncMock(return_value={
        'datetime': '2024-01-16T15:00:00+01:00',
        'confidence': 0.9
    })
    
    return {
        'calendar': calendar_mock,
        'speech': speech_mock,
        'ocr': ocr_mock,
        'nlp': nlp_mock
    }


@pytest.fixture
def test_data_paths():
    """Provide paths to test data files"""
    test_data_dir = Path(__file__).parent / "data"
    
    return {
        'audio_files': test_data_dir / "audio",
        'image_files': test_data_dir / "images", 
        'text_files': test_data_dir / "text"
    }


# Pytest configuration hooks
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"  
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )
    config.addinivalue_line(
        "markers", "google_api: mark test as requiring Google API"
    )
    config.addinivalue_line(
        "markers", "telegram_api: mark test as requiring Telegram API"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    
    for item in items:
        # Add integration marker to integration test files
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
            
        # Add unit marker to unit test files  
        if "services" in str(item.fspath) or "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
            
        # Add slow marker to performance tests
        if "performance" in str(item.fspath):
            item.add_marker(pytest.mark.slow)
            
        # Add API markers based on test names
        if "google" in item.name.lower() or "calendar" in item.name.lower():
            item.add_marker(pytest.mark.google_api)
            
        if "telegram" in item.name.lower() or "bot" in item.name.lower():
            item.add_marker(pytest.mark.telegram_api)


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset any singleton instances between tests"""
    # This ensures test isolation for any singleton services
    yield
    # Cleanup would go here if needed


# Test helper functions available to all tests
def assert_valid_datetime_string(dt_string):
    """Assert that string is valid ISO datetime"""
    from datetime import datetime
    try:
        datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False


def create_mock_telegram_update(message_type="text", **kwargs):
    """Helper to create mock Telegram update objects"""
    from datetime import datetime
    
    update = MagicMock()
    update.message = MagicMock()
    update.message.from_user.id = kwargs.get('user_id', 12345)
    update.message.from_user.first_name = kwargs.get('first_name', 'Test')
    update.message.chat.id = kwargs.get('chat_id', 12345)
    update.message.date = datetime.now()
    update.message.reply_text = AsyncMock()
    
    if message_type == "text":
        update.message.text = kwargs.get('text', 'test message')
        update.message.voice = None
        update.message.photo = None
        
    elif message_type == "voice":
        update.message.text = None  
        update.message.voice = MagicMock()
        update.message.voice.file_id = kwargs.get('file_id', 'voice_123')
        update.message.voice.duration = kwargs.get('duration', 5)
        update.message.photo = None
        
    elif message_type == "photo":
        update.message.text = None
        update.message.voice = None
        update.message.photo = [MagicMock()]
        update.message.photo[-1].file_id = kwargs.get('file_id', 'photo_123')
        update.message.photo[-1].width = kwargs.get('width', 800) 
        update.message.photo[-1].height = kwargs.get('height', 600)
    
    return update