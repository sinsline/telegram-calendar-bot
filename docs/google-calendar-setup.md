# 📅 Настройка Google Calendar API

Подробное руководство по настройке интеграции с Google Calendar для Telegram Calendar Bot.

## 📋 Содержание

1. [Создание проекта в Google Console](#создание-проекта-в-google-console)
2. [Настройка OAuth2](#настройка-oauth2)
3. [Service Account (рекомендуется)](#service-account-рекомендуется)
4. [Получение credentials.json](#получение-credentialsjson)
5. [Настройка Calendar API](#настройка-calendar-api)
6. [Тестирование интеграции](#тестирование-интеграции)
7. [Устранение неполадок](#устранение-неполадок)

## 🔧 Создание проекта в Google Console

### Шаг 1: Создание проекта
1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Нажмите "Select a project" → "New Project"
3. Введите название проекта: `telegram-calendar-bot`
4. Выберите организацию (если применимо)
5. Нажмите "Create"

### Шаг 2: Включение Calendar API
1. В боковом меню выберите "APIs & Services" → "Library"
2. Найдите "Google Calendar API"
3. Нажмите на API
4. Нажмите "Enable"

## 🔐 Настройка OAuth2

### OAuth2 Consent Screen
1. Перейдите в "APIs & Services" → "OAuth consent screen"
2. Выберите "External" (для персональных проектов)
3. Заполните обязательные поля:
   ```
   App name: Telegram Calendar Bot
   User support email: your@email.com
   Developer contact: your@email.com
   ```
4. Добавьте scopes:
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/calendar.events`
5. Добавьте тестовых пользователей (ваш email)
6. Сохраните и продолжите

### OAuth2 Credentials
1. Перейдите в "APIs & Services" → "Credentials"
2. Нажмите "Create Credentials" → "OAuth 2.0 Client IDs"
3. Выберите "Desktop application"
4. Введите имя: "Telegram Calendar Bot"
5. Нажмите "Create"
6. Скачайте JSON файл (это будет ваш `credentials.json`)

## 🤖 Service Account (рекомендуется)

Service Account обеспечивает более стабильную авторизацию для серверных приложений.

### Создание Service Account
1. Перейдите в "IAM & Admin" → "Service Accounts"
2. Нажмите "Create Service Account"
3. Заполните поля:
   ```
   Service account name: telegram-bot-calendar
   Service account ID: telegram-bot-calendar
   Description: Service account for Telegram Calendar Bot
   ```
4. Нажмите "Create and Continue"
5. Роли не нужны (пропустите)
6. Нажмите "Done"

### Создание ключа
1. Найдите созданный Service Account
2. Нажмите на три точки → "Manage keys"
3. "Add Key" → "Create new key"
4. Выберите "JSON"
5. Нажмите "Create"
6. Сохраните файл как `credentials.json`

### Предоставление доступа к календарю
1. Откройте [Google Calendar](https://calendar.google.com/)
2. В боковом меню найдите ваш календарь
3. Нажмите на три точки рядом с календарем → "Settings and sharing"
4. Прокрутите до "Share with specific people"
5. Нажмите "Add people"
6. Введите email Service Account (из JSON файла, поле "client_email")
7. Выберите permission: "Make changes to events"
8. Нажмите "Send"

## 📄 Получение credentials.json

### Формат OAuth2 credentials.json
```json
{
  "installed": {
    "client_id": "123456789-abc...xyz.apps.googleusercontent.com",
    "project_id": "telegram-calendar-bot",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "GOCSPX-abc...xyz",
    "redirect_uris": ["http://localhost"]
  }
}
```

### Формат Service Account credentials.json
```json
{
  "type": "service_account",
  "project_id": "telegram-calendar-bot",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "telegram-bot-calendar@telegram-calendar-bot.iam.gserviceaccount.com",
  "client_id": "123456789012345678901",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
}
```

## ⚙️ Настройка Calendar API

### Получение Calendar ID
1. Откройте [Google Calendar](https://calendar.google.com/)
2. В боковом меню найдите нужный календарь
3. Нажмите на три точки → "Settings and sharing"
4. Прокрутите до "Calendar ID"
5. Скопируйте ID (например: `your@gmail.com` или `abc123@group.calendar.google.com`)

### Конфигурация в .env
```env
# Основные настройки
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GOOGLE_CALENDAR_ID=your@gmail.com
GOOGLE_CREDENTIALS_FILE=./credentials.json

# Дополнительные настройки
GOOGLE_SCOPES=https://www.googleapis.com/auth/calendar
TIMEZONE=Europe/Berlin
```

### Первичная авторизация (только для OAuth2)

При первом запуске с OAuth2 credentials:
```bash
# Запуск бота в интерактивном режиме
python -m src.cli start

# Бот откроет браузер для авторизации
# Войдите в Google аккаунт и разрешите доступ
# Токен сохранится автоматически
```

## 🧪 Тестирование интеграции

### Скрипт проверки
Создайте файл `test_calendar.py`:
```python
import os
from src.services.calendar_service import CalendarService

async def test_calendar():
    # Загрузка переменных окружения
    from dotenv import load_dotenv
    load_dotenv()
    
    # Создание сервиса
    calendar_service = CalendarService()
    
    try:
        # Получение списка календарей
        calendars = await calendar_service.list_calendars()
        print(f"Найдено календарей: {len(calendars)}")
        
        for calendar in calendars[:3]:  # Показать первые 3
            print(f"- {calendar['summary']} ({calendar['id']})")
        
        # Создание тестового события
        event_data = {
            'summary': 'Тестовое событие',
            'start': '2024-01-01T10:00:00',
            'end': '2024-01-01T11:00:00',
            'description': 'Тест интеграции с Telegram Bot'
        }
        
        event = await calendar_service.create_event(**event_data)
        print(f"Создано событие: {event['id']}")
        
        # Удаление тестового события
        await calendar_service.delete_event(event['id'])
        print("Тестовое событие удалено")
        
        print("✅ Интеграция с Google Calendar работает!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_calendar())
```

Запуск теста:
```bash
python test_calendar.py
```

### Проверка через curl
```bash
# Получение access token (для Service Account)
TOKEN=$(python -c "
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import json

credentials = service_account.Credentials.from_service_account_file(
    'credentials.json',
    scopes=['https://www.googleapis.com/auth/calendar']
)
credentials.refresh(Request())
print(credentials.token)
")

# Тестовый запрос к API
curl -H "Authorization: Bearer $TOKEN" \
  "https://www.googleapis.com/calendar/v3/calendars/primary/events?maxResults=5"
```

## 🔍 Устранение неполадок

### Частые ошибки

#### 403 Forbidden
```json
{
  "error": {
    "code": 403,
    "message": "Forbidden"
  }
}
```
**Решение:**
- Убедитесь, что Calendar API включен
- Проверьте OAuth2 scopes
- Для Service Account: проверьте права доступа к календарю

#### 401 Unauthorized
```json
{
  "error": {
    "code": 401,
    "message": "Unauthorized"
  }
}
```
**Решение:**
- Проверьте credentials.json
- Для OAuth2: пройдите авторизацию заново
- Для Service Account: проверьте формат ключа

#### Calendar not found
```json
{
  "error": {
    "code": 404,
    "message": "Not Found"
  }
}
```
**Решение:**
- Проверьте GOOGLE_CALENDAR_ID
- Убедитесь, что календарь существует
- Для Service Account: проверьте, что bot добавлен в календарь

### Отладка

#### Включение детального логирования
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# В .env файле
LOG_LEVEL=DEBUG
GOOGLE_LOG_LEVEL=DEBUG
```

#### Проверка токенов
```python
# Для OAuth2
import pickle
import os

if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
        print(f"Token valid: {creds.valid}")
        print(f"Token expired: {creds.expired}")
        print(f"Token expiry: {creds.expiry}")
```

#### Валидация credentials.json
```python
import json

def validate_credentials(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if 'type' in data:
            # Service Account
            required_fields = ['client_email', 'private_key', 'project_id']
            print("Type: Service Account")
        else:
            # OAuth2
            required_fields = ['client_id', 'client_secret']
            print("Type: OAuth2")
            data = data.get('installed', data)
        
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing field: {field}")
                return False
            else:
                print(f"✅ {field}: present")
        
        return True
    
    except json.JSONDecodeError:
        print("❌ Invalid JSON format")
        return False
    except FileNotFoundError:
        print("❌ Credentials file not found")
        return False

# Проверка
validate_credentials('credentials.json')
```

### Альтернативные методы аутентификации

#### API ключ (только для чтения)
```python
# Для публичных календарей
GOOGLE_API_KEY = "your_api_key"

# В запросе
url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
params = {"key": GOOGLE_API_KEY}
response = requests.get(url, params=params)
```

#### Domain-wide delegation
Для корпоративных G Suite:
```python
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    'credentials.json',
    scopes=['https://www.googleapis.com/auth/calendar'],
    subject='admin@yourdomain.com'  # Делегирование
)
```

## 📚 Дополнительные ресурсы

### Официальная документация
- [Google Calendar API Documentation](https://developers.google.com/calendar/api)
- [Python Client Library](https://github.com/googleapis/google-api-python-client)
- [OAuth2 Flow](https://developers.google.com/identity/protocols/oauth2)

### Полезные инструменты
- [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)
- [Calendar API Explorer](https://developers.google.com/calendar/api/v3/reference)
- [JSON Viewer](https://jsonviewer.stack.hu/) - для проверки credentials.json

### Примеры кода
```python
# Полный пример с обработкой ошибок
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleCalendarManager:
    def __init__(self, credentials_path, calendar_id):
        self.calendar_id = calendar_id
        self.service = self._authenticate(credentials_path)
    
    def _authenticate(self, credentials_path):
        try:
            # Service Account
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            return build('calendar', 'v3', credentials=credentials)
        
        except Exception as e:
            print(f"Authentication error: {e}")
            raise
    
    def create_event(self, summary, start_time, end_time, description=None):
        event = {
            'summary': summary,
            'start': {'dateTime': start_time, 'timeZone': 'Europe/Berlin'},
            'end': {'dateTime': end_time, 'timeZone': 'Europe/Berlin'},
            'description': description
        }
        
        try:
            result = self.service.events().insert(
                calendarId=self.calendar_id, 
                body=event
            ).execute()
            
            return result['id']
        
        except HttpError as e:
            print(f"HTTP Error: {e}")
            raise
```

---

*Документация обновлена: декабрь 2024*