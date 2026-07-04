# Telegram Calendar Bot — Контекст восстановления

Еслиcoder потерял контекст этой разработки, читай этот файл ПЕРВЫМ.

## Что это за проект
Telegram Calendar Bot — умный бот для управления календарём через Telegram.
- Язык: Python, aiogram 3.x
- Разработка велась в профиле `coder` (Proger Darvis, Telegram: @darvis_coder_bot)
- Проект завершён и заархивирован

## Автор и назначение
Сергей Бехтхольд — для личного использования (мотоцикл, бизнес-встречи).

## Функционал
- ✅ Текст → событие календаря (NLP: "встреча завтра в 15:00")
- ✅ Голос → текст (OpenAI Whisper) → событие
- ✅ Фото → OCR (Tesseract) → текст → событие
- ✅ Google Calendar интеграция
- ✅ Inline-клавиатура для выбора дат
- ✅ Мультиязычность: русский, немецкий, английский
- ✅ Docker контейнеризация
- ✅ CLI интерфейс управления

## Структура файлов
```
src/
  telegram_bot.py          # Главный бот с inline-клавиатурой
  services/
    calendar_service.py    # Google Calendar API
    nlp_service.py         # Распознавание дат/времени
    ocr_service.py         # OCR (Tesseract)
    speech_service.py      # Whisper транскрибация
  cli.py                   # CLI management
Dockerfile                 # Docker образ
docker-compose.yml         # Docker Compose
docs/                      # Документация
```

## Где найти предыдущие сессии
База сессий: `/opt/data/profiles/coder/state.db` (38 сессий, 1956 сообщений)
Ключевые сессии: 20260627_181824_c234 (142 сообщения, основная разработка)

## Архивы
- `telegram-calendar-bot.zip` — полный архив проекта
- `telegram-calendar-bot.tar.gz` — tar.gz архив
- `telegram-calendar-bot.bundle` — git bundle
- Все находятся: `/opt/data/profiles/coder/home/projects/`

## Что делать при потере контекста
1. Читай `README.md` в проекте — полное описание
2. Читай `CHANGELOG.md` — история изменений
3. Открой `src/telegram_bot.py` — главный файл для понимания API
4. Проверь `state.db` через `session_search` — там история разработки
5. НЕ спрашивай пользователя "что мы делали" — вся информация есть в файлах

## Последний статус (по memory)
Проект завершён, архив создан, файлы готовы к публикации.
Последние работы: Task 8 (CLI & Docker deployment), тесты, документация.
