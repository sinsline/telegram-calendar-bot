# 🤖 Telegram Calendar Bot

Умный Telegram-бот для управления календарем с поддержкой голосовых сообщений, распознавания изображений и интеграции с Google Calendar.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🌟 Возможности

### 📝 **Обработка текста**
- Парсинг естественного языка на **русском**, **немецком** и **английском**
- Автоматическое извлечение дат, времени и описаний событий
- Поддержка относительных дат: "завтра", "послезавтра", "в пятницу"

### 🎤 **Голосовые сообщения**
- Распознавание речи через **OpenAI Whisper**
- Поддержка многих языков
- Автоматическое преобразование речи в календарные события

### 📸 **Распознавание изображений**
- OCR через **Tesseract** для извлечения текста с изображений
- Обработка визиток, расписаний, снимков экрана
- Автоматический парсинг дат и событий из извлеченного текста

### 📅 **Интеграция с Google Calendar**
- OAuth2 авторизация
- Создание, просмотр и управление событиями
- Поддержка множественных календарей
- Автоматическая синхронизация

### 🛡 **Безопасность и производительность**
- Лимит запросов: 20 в минуту на пользователя
- Валидация и санитизация входных данных
- Асинхронная обработка для высокой производительности
- Docker-контейнеризация для изолированного запуска

## 🚀 Быстрый старт

### Требования
- Python 3.11+
- Docker и Docker Compose
- Telegram Bot Token
- Google Calendar API credentials (опционально)

### 1. Клонирование репозитория
```bash
git clone https://github.com/your-username/telegram-calendar-bot.git
cd telegram-calendar-bot
```

### 2. Настройка через Make
```bash
# Установка зависимостей
make install

# Интерактивная настройка
make setup

# Запуск в разработке
make dev
```

### 3. Альтернативная настройка

#### Установка зависимостей
```bash
pip install -r requirements.txt
```

#### Создание конфигурации
```bash
cp .env.example .env
# Отредактируйте .env файл с вашими настройками
```

#### Запуск
```bash
# Через CLI
python -m src.cli start

# Через Docker
docker-compose up -d
```

## 📖 Использование

### Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Запуск бота и приветствие |
| `/help` | Справка по командам |
| `/events` | Показать ближайшие события |
| `/cancel <id>` | Отменить событие |

### Примеры использования

#### 📝 Текстовые сообщения
```
встреча с клиентом завтра в 15:00
звонок маме в пятницу в 19:30
дентист 25 декабря в 10:00 в клинике на Ленина
```

#### 🎤 Голосовые сообщения
Отправьте голосовое сообщение с описанием события:
> *"Напомни мне встретиться с Андреем завтра в два часа дня"*

#### 📸 Изображения
Отправьте фото визитки, расписания или календаря - бот автоматически извлечет событие.

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Описание | Пример |
|------------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | `123456789:ABC...` |
| `GOOGLE_CALENDAR_ID` | ID Google календаря | `your@gmail.com` |
| `GOOGLE_CREDENTIALS_FILE` | Путь к credentials.json | `/app/credentials.json` |
| `RATE_LIMIT_PER_MINUTE` | Лимит запросов в минуту | `20` |
| `LOG_LEVEL` | Уровень логирования | `INFO` |

### Настройка Google Calendar

1. Перейдите в [Google Console](https://console.developers.google.com/)
2. Создайте проект и включите Calendar API
3. Создайте Service Account или OAuth2 credentials
4. Скачайте файл `credentials.json`
5. Укажите путь к файлу в `GOOGLE_CREDENTIALS_FILE`

Подробная инструкция: [docs/google-calendar-setup.md](docs/google-calendar-setup.md)

## 🐳 Docker развертывание

### Разработка
```bash
# Быстрый запуск
make dev

# Или через Docker Compose
docker-compose up -d
```

### Продакшн
```bash
# Продакшн развертывание
make prod

# Или через скрипт
./scripts/deploy.sh prod
```

### Манифест Kubernetes
```bash
# Кубернетес развертывание
kubectl apply -f k8s/
```

## 🔍 Мониторинг

### Проверка статуса
```bash
# Статус контейнера
make status

# Здоровье системы
make health

# Логи в реальном времени
make logs-follow
```

### Метрики
- CPU и память через Docker stats
- Логирование всех событий
- Health check каждые 30 секунд

## 💾 Резервное копирование

```bash
# Создать резервную копию
make backup

# Список копий
make backup-list

# Восстановление
make restore BACKUP=telegram-bot-backup-20231201_143000.tar.gz
```

## 🧪 Тестирование

```bash
# Все тесты
make test

# Только юнит-тесты
make test-unit

# С покрытием
make coverage

# В режиме наблюдения
make test-watch
```

## 📊 Архитектура

```
telegram-calendar-bot/
├── src/                     # Исходный код
│   ├── telegram_bot.py      # Основной бот
│   ├── cli.py              # CLI интерфейс
│   └── services/           # Сервисы
│       ├── calendar_service.py  # Google Calendar
│       ├── nlp_service.py      # NLP парсинг
│       ├── ocr_service.py      # Распознавание текста
│       └── speech_service.py   # Распознавание речи
├── tests/                   # Тесты
├── scripts/                 # Скрипты развертывания
├── docs/                   # Документация
├── docker-compose.yml      # Docker оркестрация
├── Dockerfile             # Контейнер приложения
└── Makefile               # Команды автоматизации
```

### Поток данных
1. **Telegram** → Handler → Input Validation
2. **NLP/OCR/Speech** → Text Extraction → Date Parsing
3. **Google Calendar** → Event Creation → User Confirmation
4. **Logging** → Health Check → Monitoring

## 🤝 Разработка

### Локальная разработка
```bash
# Установка dev зависимостей
make install-dev

# Форматирование кода
make format

# Линтинг
make lint

# Проверка типов
make typecheck

# Все проверки
make check
```

### Перед коммитом
```bash
make pre-commit
```

### Структура коммитов
```
feat: добавить голосовые сообщения
fix: исправить парсинг дат на немецком
docs: обновить README
test: добавить тесты для OCR сервиса
```

## 🐛 Решение проблем

### Частые проблемы

#### Бот не отвечает
1. Проверьте токен: `make config`
2. Проверьте логи: `make logs`
3. Проверьте health check: `make health`

#### Google Calendar не работает
1. Проверьте credentials.json
2. Убедитесь, что Calendar API включен
3. Проверьте права доступа

#### OCR не распознает текст
1. Убедитесь, что Tesseract установлен
2. Проверьте качество изображения
3. Убедитесь в поддержке языка

### Логи и дебаг
```bash
# Подробные логи
LOG_LEVEL=DEBUG make start

# Отслеживание ошибок
make logs-follow | grep ERROR

# Дебаг режим
make debug
```

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE)

## 👥 Авторы

- **Sergej Bechthold** - *Разработчик* - [@telegram_username](https://t.me/telegram_username)

## 🔗 Полезные ссылки

- [Документация API](docs/api.md)
- [Руководство по развертыванию](docs/deployment.md)
- [Конфигурация](docs/configuration.md)
- [FAQ](docs/faq.md)
- [Changelog](CHANGELOG.md)

---

**⭐ Если проект был полезен, поставьте звездочку!**