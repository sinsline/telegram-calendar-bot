# 🔌 API Документация

Документация по внутренним API и сервисам Telegram Calendar Bot.

## 📋 Содержание

1. [Архитектура сервисов](#архитектура-сервисов)
2. [Calendar Service](#calendar-service)
3. [NLP Service](#nlp-service)
4. [OCR Service](#ocr-service)
5. [Speech Service](#speech-service)
6. [Event Formats](#event-formats)
7. [Error Handling](#error-handling)

## 🏗 Архитектура сервисов

### Диаграмма компонентов
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │────│  Input Handler  │────│  Text Processor │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │  Rate Limiter   │    │   NLP Service   │
         │              └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │   OCR Service   │    │ Speech Service  │
         │              └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐    ┌─────────────────┐
         └──────────────│Calendar Service │────│  Google API     │
                        └─────────────────┘    └─────────────────┘
```

### Поток данных
1. **Получение сообщения** → Telegram Bot Handler
2. **Валидация входа** → Rate Limiting + Input Sanitization  
3. **Обработка контента** → OCR/Speech → Text Extraction
4. **Парсинг событий** → NLP Service → Event Data
5. **Создание события** → Calendar Service → Google Calendar
6. **Ответ пользователю** → Confirmation Message

## 📅 Calendar Service

### Класс CalendarService

```python
class CalendarService:
    def __init__(self, credentials_path: str, calendar_id: str)
    async def create_event(self, summary: str, start_time: str, 
                          end_time: str, description: str = None) -> Dict
    async def list_events(self, max_results: int = 10) -> List[Dict]
    async def update_event(self, event_id: str, **kwargs) -> Dict
    async def delete_event(self, event_id: str) -> bool
    async def list_calendars(self) -> List[Dict]
```

### Методы

#### create_event()
Создает новое событие в календаре.

**Параметры:**
- `summary` (str): Название события
- `start_time` (str): Время начала (ISO 8601)
- `end_time` (str): Время окончания (ISO 8601)  
- `description` (str, optional): Описание события

**Возвращает:**
```python
{
    "id": "event_123abc",
    "summary": "Встреча с клиентом", 
    "start": {"dateTime": "2024-01-15T10:00:00+01:00"},
    "end": {"dateTime": "2024-01-15T11:00:00+01:00"},
    "htmlLink": "https://calendar.google.com/event/..."
}
```

**Исключения:**
- `CalendarAPIError`: Ошибка Google Calendar API
- `AuthenticationError`: Проблемы аутентификации
- `ValidationError`: Некорректные данные

#### list_events()
Получает список ближайших событий.

**Параметры:**
- `max_results` (int): Максимальное количество событий (по умолчанию: 10)

**Возвращает:**
```python
[
    {
        "id": "event_123",
        "summary": "Встреча",
        "start": {"dateTime": "2024-01-15T10:00:00+01:00"},
        "end": {"dateTime": "2024-01-15T11:00:00+01:00"}
    }
]
```

#### update_event()
Обновляет существующее событие.

**Параметры:**
- `event_id` (str): ID события
- `**kwargs`: Поля для обновления (summary, start_time, end_time, description)

#### delete_event()
Удаляет событие по ID.

**Параметры:**
- `event_id` (str): ID события для удаления

**Возвращает:**
- `bool`: True если удалено успешно

### Примеры использования

```python
# Инициализация
calendar = CalendarService("credentials.json", "primary")

# Создание события
event = await calendar.create_event(
    summary="Встреча с командой",
    start_time="2024-01-15T14:00:00",
    end_time="2024-01-15T15:00:00",
    description="Обсуждение нового проекта"
)

# Получение событий
events = await calendar.list_events(max_results=5)

# Обновление события  
await calendar.update_event(
    event_id="event_123",
    summary="Обновленное название"
)

# Удаление события
await calendar.delete_event("event_123")
```

## 🧠 NLP Service

### Класс NLPService

```python
class NLPService:
    def __init__(self, supported_languages: List[str] = ["ru", "de", "en"])
    async def parse_event(self, text: str, user_timezone: str = "UTC") -> Dict
    async def extract_datetime(self, text: str, reference_time: datetime = None) -> Dict
    async def detect_language(self, text: str) -> str
    def _normalize_text(self, text: str) -> str
```

### Методы

#### parse_event()
Извлекает данные события из текста на естественном языке.

**Параметры:**
- `text` (str): Входной текст
- `user_timezone` (str): Часовой пояс пользователя

**Возвращает:**
```python
{
    "summary": "Встреча с клиентом",
    "start_time": "2024-01-15T15:00:00+01:00", 
    "end_time": "2024-01-15T16:00:00+01:00",
    "description": "Обсуждение проекта в офисе",
    "confidence": 0.85,
    "language": "ru"
}
```

#### extract_datetime()
Извлекает дату и время из текста.

**Поддерживаемые форматы:**
- **Абсолютные даты**: "15 января 2024", "2024-01-15", "15/01/2024"
- **Относительные**: "завтра", "послезавтра", "в пятницу", "через неделю"
- **Время**: "в 15:00", "в половине четвертого", "утром", "вечером"

**Примеры парсинга:**

| Входной текст | Результат |
|---------------|-----------|
| "встреча завтра в 15:00" | summary: "встреча", start: tomorrow 15:00 |
| "звонок маме в пятницу в 19:30" | summary: "звонок маме", start: next Friday 19:30 |
| "дентист 25 декабря в 10 утра" | summary: "дентист", start: Dec 25 10:00 |

#### detect_language()
Определяет язык текста для правильного парсинга.

**Поддерживаемые языки:**
- `ru`: Русский
- `de`: Немецкий  
- `en`: Английский

## 👁 OCR Service

### Класс OCRService

```python
class OCRService:
    def __init__(self, languages: List[str] = ["rus", "eng", "deu"])
    async def extract_text(self, image_data: bytes) -> str
    async def process_image_file(self, file_path: str) -> str  
    def _preprocess_image(self, image: PIL.Image) -> PIL.Image
    def _is_valid_image(self, image_data: bytes) -> bool
```

### Методы

#### extract_text()
Извлекает текст из изображения.

**Параметры:**
- `image_data` (bytes): Данные изображения

**Возвращает:**
- `str`: Извлеченный текст

**Поддерживаемые форматы:**
- JPEG, PNG, WebP, TIFF, BMP

#### process_image_file()
Обрабатывает изображение из файла.

**Предварительная обработка:**
1. Конвертация в оттенки серого
2. Увеличение контраста
3. Удаление шума  
4. Масштабирование для улучшения точности

### Поддерживаемые языки Tesseract
- `rus`: Русский
- `eng`: Английский
- `deu`: Немецкий
- `fra`: Французский
- `spa`: Испанский

### Примеры использования

```python
# Инициализация
ocr = OCRService(languages=["rus", "eng", "deu"])

# Обработка изображения
with open("business_card.jpg", "rb") as f:
    image_data = f.read()

text = await ocr.extract_text(image_data)
print(f"Извлеченный текст: {text}")

# Результат может быть:
# "Встреча с партнерами
#  15 января 2024
#  15:00 - 17:00
#  Конференц-зал А"
```

## 🎤 Speech Service

### Класс SpeechService

```python
class SpeechService:
    def __init__(self, model: str = "base")
    async def transcribe_audio(self, audio_data: bytes) -> str
    async def transcribe_file(self, file_path: str) -> str
    def _convert_to_wav(self, audio_data: bytes) -> str
```

### Методы

#### transcribe_audio()
Преобразует аудио в текст через OpenAI Whisper.

**Параметры:**
- `audio_data` (bytes): Аудио данные

**Возвращает:**
- `str`: Транскрибированный текст

**Поддерживаемые форматы:**
- OGG, WAV, MP3, M4A, FLAC

#### Модели Whisper
- `tiny`: Быстрая, низкое качество
- `base`: Хороший баланс (по умолчанию) 
- `small`: Хорошее качество
- `medium`: Очень хорошее качество
- `large`: Лучшее качество, медленная

### Примеры использования

```python
# Инициализация
speech = SpeechService(model="base")

# Распознавание голосового сообщения
with open("voice_message.ogg", "rb") as f:
    audio_data = f.read()

text = await speech.transcribe_audio(audio_data)
print(f"Распознанный текст: {text}")

# Результат: "напомни встретиться с андреем завтра в два часа дня"
```

## 📊 Event Formats

### Внутренний формат события

```python
{
    "summary": str,           # Название события
    "start_time": str,        # ISO 8601 дата/время начала
    "end_time": str,          # ISO 8601 дата/время окончания  
    "description": str,       # Описание (опционально)
    "location": str,          # Местоположение (опционально)
    "attendees": List[str],   # Email участников (опционально)
    "reminders": List[int],   # Напоминания в минутах (опционально)
    "timezone": str,          # Часовой пояс
    "all_day": bool,          # Событие на весь день
    "recurring": Dict,        # Правила повторения (опционально)
    "confidence": float,      # Уверенность парсинга (0.0-1.0)
    "source": str,            # Источник: "text", "voice", "image"
    "language": str,          # Язык исходного текста
    "raw_input": str         # Исходный текст
}
```

### Google Calendar Event Format

```python
{
    "id": "event_id_123",
    "summary": "Название события",
    "description": "Описание",
    "start": {
        "dateTime": "2024-01-15T10:00:00+01:00",
        "timeZone": "Europe/Berlin"
    },
    "end": {
        "dateTime": "2024-01-15T11:00:00+01:00", 
        "timeZone": "Europe/Berlin"
    },
    "location": "Конференц-зал А",
    "attendees": [
        {"email": "user@example.com"}
    ],
    "reminders": {
        "useDefault": False,
        "overrides": [
            {"method": "email", "minutes": 30},
            {"method": "popup", "minutes": 10}
        ]
    },
    "status": "confirmed",
    "htmlLink": "https://calendar.google.com/event/...",
    "created": "2024-01-01T12:00:00Z",
    "updated": "2024-01-01T12:00:00Z"
}
```

## ⚠️ Error Handling

### Иерархия исключений

```python
class CalendarBotError(Exception):
    """Базовое исключение для всех ошибок бота"""
    pass

class ServiceError(CalendarBotError):
    """Ошибки сервисов"""
    pass

class CalendarAPIError(ServiceError):
    """Ошибки Google Calendar API"""
    pass

class AuthenticationError(ServiceError):
    """Ошибки аутентификации"""
    pass

class ValidationError(CalendarBotError):
    """Ошибки валидации данных"""
    pass

class RateLimitError(CalendarBotError):
    """Превышение лимита запросов"""
    pass

class ParseError(CalendarBotError):
    """Ошибки парсинга текста/даты"""
    pass
```

### Коды ошибок

| Код | Тип | Описание |
|-----|-----|----------|
| 1001 | CalendarAPIError | Ошибка Google Calendar API |
| 1002 | AuthenticationError | Неверные credentials |
| 1003 | ValidationError | Некорректные входные данные |
| 1004 | RateLimitError | Превышен лимит запросов |
| 1005 | ParseError | Не удалось разобрать текст |
| 1006 | OCRError | Ошибка распознавания изображения |
| 1007 | SpeechError | Ошибка распознавания речи |

### Обработка ошибок в сервисах

```python
# Пример обработки в Calendar Service
async def create_event(self, **kwargs):
    try:
        # Валидация данных
        if not kwargs.get('summary'):
            raise ValidationError("Summary is required")
        
        # Вызов Google Calendar API
        result = await self.service.events().insert(...).execute()
        
        return result
        
    except httplib2.HttpError as e:
        if e.status_code == 401:
            raise AuthenticationError("Invalid credentials")
        elif e.status_code == 403:
            raise CalendarAPIError("Access denied to calendar")
        elif e.status_code == 429:
            raise RateLimitError("Calendar API rate limit exceeded")
        else:
            raise CalendarAPIError(f"Calendar API error: {e}")
            
    except Exception as e:
        logger.error(f"Unexpected error in create_event: {e}")
        raise ServiceError(f"Service error: {e}")
```

### Retry механизм

```python
from functools import wraps
import asyncio

def retry(max_attempts=3, delay=1, backoff=2):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except (CalendarAPIError, ServiceError) as e:
                    if attempt == max_attempts - 1:
                        raise
                    
                    wait_time = delay * (backoff ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. "
                                 f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
            
        return wrapper
    return decorator

# Использование
@retry(max_attempts=3, delay=2)
async def create_event_with_retry(self, **kwargs):
    return await self.create_event(**kwargs)
```

## 🔧 Конфигурация сервисов

### Настройки в environment

```env
# Calendar Service
GOOGLE_CALENDAR_ID=primary
GOOGLE_CREDENTIALS_FILE=./credentials.json
GOOGLE_SCOPES=https://www.googleapis.com/auth/calendar
CALENDAR_TIMEZONE=Europe/Berlin

# NLP Service  
NLP_SUPPORTED_LANGUAGES=ru,de,en
NLP_CONFIDENCE_THRESHOLD=0.7
NLP_DEFAULT_EVENT_DURATION=60  # минут

# OCR Service
OCR_LANGUAGES=rus+eng+deu
OCR_DPI=300
OCR_IMAGE_MAX_SIZE=4096  # пикселей

# Speech Service
SPEECH_MODEL=base
SPEECH_MAX_FILE_SIZE=25000000  # 25MB
SPEECH_TIMEOUT=60  # секунд

# Rate Limiting
RATE_LIMIT_PER_MINUTE=20
RATE_LIMIT_PER_HOUR=200
RATE_LIMIT_PER_DAY=1000
```

### Программная конфигурация

```python
# Настройка сервисов
services_config = {
    "calendar": {
        "credentials_path": os.getenv("GOOGLE_CREDENTIALS_FILE"),
        "calendar_id": os.getenv("GOOGLE_CALENDAR_ID", "primary"),
        "timezone": os.getenv("CALENDAR_TIMEZONE", "UTC")
    },
    "nlp": {
        "languages": ["ru", "de", "en"],
        "confidence_threshold": 0.7,
        "default_duration": 60
    },
    "ocr": {
        "languages": ["rus", "eng", "deu"],
        "max_image_size": 4096,
        "dpi": 300
    },
    "speech": {
        "model": "base",
        "max_file_size": 25 * 1024 * 1024,
        "timeout": 60
    }
}
```

---

*API Documentation v1.0.0*