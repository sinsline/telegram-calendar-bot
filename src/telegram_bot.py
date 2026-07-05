"""
Telegram Bot for Calendar Management

Main bot implementation with handlers for text, voice, photo messages and commands.
Integrates with all services: NLP, OCR, Calendar, and Speech services.
"""

import asyncio
import logging
import os
import tempfile
import hashlib
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union
from io import BytesIO

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, FSInputFile, BufferedInputFile
from aiogram.utils.formatting import Text, Bold, Code, Pre
from aiogram.utils.chat_action import ChatActionSender

from .services import (
    create_nlp_service,
    create_ocr_service,
    create_calendar_service,
    create_speech_service
)


logger = logging.getLogger(__name__)


class TelegramBot:
    """
    Main Telegram bot class with message handlers and service integration.
    
    Supports:
    - Text messages (NLP parsing + calendar creation)
    - Voice messages (speech transcription + NLP + calendar)
    - Photo messages (OCR + NLP + calendar)  
    - Commands: /start, /help, /events, /cancel
    """
    
    def __init__(self, token: str, nlp_service=None, ocr_service=None, 
                 calendar_service=None, speech_service=None, 
                 rate_limit_per_minute: int = 20):
        """
        Initialize Telegram bot.
        
        Args:
            token: Telegram bot token
            nlp_service: NLP service instance (optional, will create if None)
            ocr_service: OCR service instance (optional, will create if None)
            calendar_service: Calendar service instance (optional, will create if None)
            speech_service: Speech service instance (optional, will create if None)
            rate_limit_per_minute: Max requests per user per minute
        """
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        
        # Rate limiting
        self.rate_limit_per_minute = rate_limit_per_minute
        self.user_requests = {}  # user_id -> list of timestamps
        
        # Initialize services with fallbacks
        self.nlp_service = nlp_service or create_nlp_service()
        self.ocr_service = ocr_service or create_ocr_service()
        self.calendar_service = calendar_service or create_calendar_service()
        self.speech_service = speech_service or create_speech_service()
        
        self._setup_handlers()
        self.calendar_service = calendar_service or create_calendar_service()
        self.speech_service = speech_service or create_speech_service()
        
        # Setup handlers
        self._setup_handlers()
        
        # Multi-language messages
        self.messages = {
            'en': {
                'welcome': "Hello {name}! 👋\\n\\nWelcome to **Telegram Calendar Bot**. I can help you create calendar events from your messages.\\n\\n📝 Send me text, 🎤 voice messages, or 📸 photos containing event information, and I'll add them to your calendar!\\n\\nUse /help to see all available commands.",
                'help': "**Available commands:**\\n\\n/start - Start the bot\\n/help - Show this help message\\n/events - Show upcoming events\\n/cancel - Cancel current operation\\n\\n**How to use:**\\n\\n📝 **Text:** Send event details like 'Meeting tomorrow at 2 PM'\\n🎤 **Voice:** Record voice messages with event information\\n📸 **Photos:** Send photos of schedules, notes, or text with event details\\n\\nI support multiple languages: English, Russian, German.",
                'events_header': "📅 **Upcoming events:**\\n\\n",
                'no_events': "No upcoming events found.",
                'event_created': "✅ **Event created successfully!**\\n\\n📝 **Title:** {title}\\n📅 **Date:** {date}\\n🔗 [View in Calendar]({link})",
                'operation_cancelled': "❌ Operation cancelled.",
                'error': "❌ **Error:** {error}\\n\\nPlease try again or contact support.",
                'no_datetime_found': "⚠️ No date/time information found in your message. Please include when the event should happen.",
                'processing': "🔄 Processing your request...",
                'transcribing': "🎤 Transcribing voice message...",
                'extracting_text': "📸 Extracting text from image...",
                'parsing_event': "📝 Analyzing event details..."
            },
            'ru': {
                'welcome': "Привет {name}! 👋\\n\\nДобро пожаловать в **Telegram Calendar Bot**. Я помогу вам создавать события календаря из ваших сообщений.\\n\\n📝 Отправьте мне текст, 🎤 голосовые сообщения или 📸 фотографии с информацией о событиях, и я добавлю их в ваш календарь!\\n\\nИспользуйте /help для просмотра всех доступных команд.",
                'help': "**Доступные команды:**\\n\\n/start - Запустить бота\\n/help - Показать это сообщение справки\\n/events - Показать предстоящие события\\n/cancel - Отменить текущую операцию\\n\\n**Как использовать:**\\n\\n📝 **Текст:** Отправьте детали события, например 'Встреча завтра в 14:00'\\n🎤 **Голос:** Запишите голосовые сообщения с информацией о событии\\n📸 **Фото:** Отправьте фотографии расписаний, заметок или текста с деталями события\\n\\nЯ поддерживаю несколько языков: английский, русский, немецкий.",
                'events_header': "📅 **Предстоящие события:**\\n\\n",
                'no_events': "Предстоящих событий не найдено.",
                'event_created': "✅ **Событие успешно создано!**\\n\\n📝 **Название:** {title}\\n📅 **Дата:** {date}\\n🔗 [Посмотреть в календаре]({link})",
                'operation_cancelled': "❌ Операция отменена.",
                'error': "❌ **Ошибка:** {error}\\n\\nПожалуйста, попробуйте еще раз или обратитесь в поддержку.",
                'no_datetime_found': "⚠️ В вашем сообщении не найдена информация о дате/времени. Пожалуйста, укажите, когда должно произойти событие.",
                'processing': "🔄 Обработка вашего запроса...",
                'transcribing': "🎤 Расшифровка голосового сообщения...",
                'extracting_text': "📸 Извлечение текста из изображения...",
                'parsing_event': "📝 Анализ деталей события..."
            },
            'de': {
                'welcome': "Hallo {name}! 👋\\n\\nWillkommen bei **Telegram Calendar Bot**. Ich helfe dir dabei, Kalenderereignisse aus deinen Nachrichten zu erstellen.\\n\\n📝 Sende mir Text, 🎤 Sprachnachrichten oder 📸 Fotos mit Ereignisinformationen, und ich füge sie zu deinem Kalender hinzu!\\n\\nVerwende /help, um alle verfügbaren Befehle zu sehen.",
                'help': "**Verfügbare Befehle:**\\n\\n/start - Bot starten\\n/help - Diese Hilfemeldung anzeigen\\n/events - Kommende Termine anzeigen\\n/cancel - Aktuelle Operation abbrechen\\n\\n**Verwendung:**\\n\\n📝 **Text:** Sende Ereignisdetails wie 'Besprechung morgen um 14 Uhr'\\n🎤 **Sprache:** Nimm Sprachnachrichten mit Ereignisinformationen auf\\n📸 **Fotos:** Sende Fotos von Terminplänen, Notizen oder Text mit Ereignisdetails\\n\\nIch unterstütze mehrere Sprachen: Englisch, Russisch, Deutsch.",
                'events_header': "📅 **Kommende Termine:**\\n\\n",
                'no_events': "Keine kommenden Termine gefunden.",
                'event_created': "✅ **Ereignis erfolgreich erstellt!**\\n\\n📝 **Titel:** {title}\\n📅 **Datum:** {date}\\n🔗 [Im Kalender anzeigen]({link})",
                'operation_cancelled': "❌ Operation abgebrochen.",
                'error': "❌ **Fehler:** {error}\\n\\nBitte versuche es erneut oder wende dich an den Support.",
                'no_datetime_found': "⚠️ Keine Datum-/Zeitinformationen in deiner Nachricht gefunden. Bitte gib an, wann das Ereignis stattfinden soll.",
                'processing': "🔄 Verarbeite deine Anfrage...",
                'transcribing': "🎤 Transkribiere Sprachnachricht...",
                'extracting_text': "📸 Extrahiere Text aus dem Bild...",
                'parsing_event': "📝 Analysiere Ereignisdetails..."
            }
        }
    
    def _setup_handlers(self) -> None:
        """Setup message and command handlers."""
        # Command handlers
        self.dp.message.register(self.handle_start_command, CommandStart())
        self.dp.message.register(self.handle_help_command, Command('help'))
        self.dp.message.register(self.handle_events_command, Command('events'))
        self.dp.message.register(self.handle_cancel_command, Command('cancel'))
        
        # Message handlers
        self.dp.message.register(self.handle_voice_message, F.voice)
        self.dp.message.register(self.handle_photo_message, F.photo)
        self.dp.message.register(self.handle_document_message, F.document)
        self.dp.message.register(self.handle_text_message, F.text)
    
    async def handle_start_command(self, message: Message) -> None:
        """Handle /start command."""
        try:
            user_lang = self._get_user_language(message.from_user)
            user_name = message.from_user.first_name or "there"
            
            welcome_message = self._get_message(user_lang, 'welcome').format(name=user_name)
            await message.reply(welcome_message, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await message.reply("❌ An error occurred. Please try again.")
    
    async def handle_help_command(self, message: Message) -> None:
        """Handle /help command."""
        try:
            user_lang = self._get_user_language(message.from_user)
            help_message = self._get_message(user_lang, 'help')
            
            await message.reply(help_message, parse_mode="Markdown")
            
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await message.reply("❌ An error occurred. Please try again.")
    
    async def handle_events_command(self, message: Message) -> None:
        """Handle /events command."""
        try:
            user_lang = self._get_user_language(message.from_user)
            
            # Fetch upcoming events
            events = self.calendar_service.get_upcoming_events()
            
            if not events:
                no_events_msg = self._get_message(user_lang, 'no_events')
                await message.reply(no_events_msg)
                return
            
            # Format events for display
            events_header = self._get_message(user_lang, 'events_header')
            events_text = events_header
            
            for i, event in enumerate(events[:10], 1):  # Limit to 10 events
                formatted_event = self._format_event_for_display(event)
                events_text += f"{i}. {formatted_event}\\n\\n"
            
            await message.reply(events_text, parse_mode="Markdown", disable_web_page_preview=True)
            
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            user_lang = self._get_user_language(message.from_user)
            error_msg = self._get_message(user_lang, 'error').format(error=str(e))
            await message.reply(error_msg)
    
    async def handle_cancel_command(self, message: Message) -> None:
        """Handle /cancel command."""
        try:
            user_lang = self._get_user_language(message.from_user)
            cancel_message = self._get_message(user_lang, 'operation_cancelled')
            
            await message.reply(cancel_message)
            
        except Exception as e:
            logger.error(f"Error in cancel command: {e}")
            await message.reply("❌ An error occurred. Please try again.")
    
    async def handle_text_message(self, message: Message) -> None:
        """Handle text messages with NLP parsing and calendar creation."""
        try:
            # Check rate limiting
            if self._is_rate_limited(message.from_user.id):
                await message.reply("⏰ Too many requests. Please wait a moment.")
                return
                
            # Sanitize input
            sanitized_text = self._sanitize_input(message.text or "")
            if not sanitized_text:
                await message.reply("❌ Invalid input.")
                return
                
            user_lang = self._get_user_language(message.from_user)
            
            # Show processing message
            processing_msg = self._get_message(user_lang, 'processing')
            status_message = await message.reply(processing_msg)
            
            # Parse event with NLP service
            await self._update_status(status_message, user_lang, 'parsing_event')
            event_data = self.nlp_service.parse_event_text(sanitized_text)
            
            if not event_data.get('has_datetime'):
                no_datetime_msg = self._get_message(user_lang, 'no_datetime_found')
                await status_message.edit_text(no_datetime_msg)
                return
            
            # Create calendar event
            calendar_event = await self._create_calendar_event(event_data, user_lang)
            
            # Send success message
            success_msg = await self._format_success_message(calendar_event, user_lang)
            await status_message.edit_text(success_msg, parse_mode="Markdown", disable_web_page_preview=True)
            
        except Exception as e:
            logger.error(f"Error processing text message: {e}")
            user_lang = self._get_user_language(message.from_user)
            error_msg = self._get_message(user_lang, 'error').format(error=str(e))
            await message.reply(error_msg)
    
    async def handle_voice_message(self, message: Message) -> None:
        """Handle voice messages with speech transcription, NLP parsing and calendar creation."""
        try:
            user_lang = self._get_user_language(message.from_user)
            
            # Show processing message
            processing_msg = self._get_message(user_lang, 'processing')
            status_message = await message.reply(processing_msg)
            
            # Download voice file
            file = await self.bot.get_file(message.voice.file_id)
            voice_file = await self.bot.download_file(file.file_path)
            voice_data = voice_file.read()
            
            # Transcribe speech
            await self._update_status(status_message, user_lang, 'transcribing')
            transcribed_text = self.speech_service.transcribe(voice_data, user_lang)
            
            if not transcribed_text:
                await status_message.edit_text("❌ Could not transcribe voice message.")
                return
            
            # Parse event with NLP service
            await self._update_status(status_message, user_lang, 'parsing_event')
            event_data = self.nlp_service.parse_event_text(transcribed_text)
            
            if not event_data.get('has_datetime'):
                no_datetime_msg = self._get_message(user_lang, 'no_datetime_found')
                await status_message.edit_text(no_datetime_msg)
                return
            
            # Create calendar event
            calendar_event = await self._create_calendar_event(event_data, user_lang)
            
            # Send success message with transcribed text
            success_msg = await self._format_success_message(calendar_event, user_lang)
            success_msg += f"\\n\\n🎤 **Transcribed:** {transcribed_text}"
            
            await status_message.edit_text(success_msg, parse_mode="Markdown", disable_web_page_preview=True)
            
        except Exception as e:
            logger.error(f"Error processing voice message: {e}")
            user_lang = self._get_user_language(message.from_user)
            error_msg = self._get_message(user_lang, 'error').format(error=str(e))
            await message.reply(error_msg)
    
    async def handle_photo_message(self, message: Message) -> None:
        """Handle photo messages with OCR text extraction, NLP parsing and calendar creation."""
        try:
            user_lang = self._get_user_language(message.from_user)
            
            # Show processing message
            processing_msg = self._get_message(user_lang, 'processing')
            status_message = await message.reply(processing_msg)
            
            # Download photo (get the largest size)
            photo = message.photo[-1]
            file = await self.bot.get_file(photo.file_id)
            photo_data = await self.bot.download_file(file.file_path)
            
            # Extract text with OCR
            await self._update_status(status_message, user_lang, 'extracting_text')
            extracted_text = self.ocr_service.extract_text(photo_data)
            
            if not extracted_text:
                await status_message.edit_text("❌ Could not extract text from image.")
                return
            
            # Parse event with NLP service
            await self._update_status(status_message, user_lang, 'parsing_event')
            event_data = self.nlp_service.parse_event_text(extracted_text)
            
            if not event_data.get('has_datetime'):
                no_datetime_msg = self._get_message(user_lang, 'no_datetime_found')
                await status_message.edit_text(no_datetime_msg)
                return
            
            # Create calendar event
            calendar_event = await self._create_calendar_event(event_data, user_lang)
            
            # Send success message with extracted text
            success_msg = await self._format_success_message(calendar_event, user_lang)
            success_msg += f"\\n\\n📸 **Extracted text:** {extracted_text[:100]}{'...' if len(extracted_text) > 100 else ''}"
            
            await status_message.edit_text(success_msg, parse_mode="Markdown", disable_web_page_preview=True)
            
        except Exception as e:
            logger.error(f"Error processing photo message: {e}")
            user_lang = self._get_user_language(message.from_user)
            error_msg = self._get_message(user_lang, 'error').format(error=str(e))
            await message.reply(error_msg)
    
    async def handle_document_message(self, message: Message) -> None:
        """Handle document messages (treat as photos if they are images)."""
        try:
            if message.document.mime_type and message.document.mime_type.startswith('image/'):
                # Process as image
                await self.handle_photo_message(message)
            else:
                await message.reply("📄 Document processing not yet supported. Please send images as photos.")
                
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            await message.reply("❌ Error processing document.")
    
    async def _create_calendar_event(self, event_data: Dict[str, Any], user_lang: str) -> Dict[str, Any]:
        """Create calendar event from parsed data."""
        datetime_info = event_data['datetime_info']
        
        # Prepare event for calendar service
        calendar_event_data = {
            'summary': event_data['title'],
            'start': datetime_info['datetime'],
            'description': f"Created from Telegram by Calendar Bot\\n\\nOriginal text: {event_data['original_text']}"
        }
        
        # Create event
        return self.calendar_service.create_event(calendar_event_data)
    
    async def _format_success_message(self, calendar_event: Dict[str, Any], user_lang: str) -> str:
        """Format success message for event creation."""
        title = calendar_event.get('summary', 'Event')
        
        # Format datetime
        start_time = calendar_event.get('start', {})
        if isinstance(start_time, dict):
            date_str = start_time.get('dateTime', 'Unknown time')
        else:
            date_str = str(start_time)
        
        # Try to parse and format date nicely
        try:
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                date_str = dt.strftime('%B %d, %Y at %H:%M')
        except:
            pass  # Keep original string if parsing fails
        
        link = calendar_event.get('htmlLink', '#')
        
        return self._get_message(user_lang, 'event_created').format(
            title=title,
            date=date_str,
            link=link
        )
    
    async def _update_status(self, status_message: Message, user_lang: str, status_key: str) -> None:
        """Update status message."""
        try:
            status_text = self._get_message(user_lang, status_key)
            await status_message.edit_text(status_text)
        except Exception:
            pass  # Ignore edit failures
    
    def _get_user_language(self, user: types.User) -> str:
        """Get user language with fallback to English."""
        if not user or not user.language_code:
            return 'en'
        
        lang = user.language_code.lower()
        
        # Support main languages
        if lang in ['ru', 'de']:
            return lang
        else:
            return 'en'  # Default to English
    
    def _is_rate_limited(self, user_id: int) -> bool:
        """Check if user is rate limited."""
        now = datetime.now()
        minute_ago = now.timestamp() - 60
        
        # Clean old requests 
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
            
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id] 
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.user_requests[user_id]) >= self.rate_limit_per_minute:
            return True
            
        # Add current request
        self.user_requests[user_id].append(now.timestamp())
        return False
    
    def _sanitize_input(self, text: str) -> str:
        """Sanitize user input to prevent injection attacks."""
        if not text:
            return ""
            
        # Remove potentially dangerous characters
        sanitized = text.replace('<script', '').replace('</script>', '')
        sanitized = sanitized.replace('javascript:', '').replace('data:', '')
        
        # Limit length
        max_length = 4000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            
        return sanitized.strip()
    
    def _get_message(self, language: str, key: str) -> str:
        """Get localized message."""
        return self.messages.get(language, self.messages['en']).get(key, key)
    
    def _format_event_for_display(self, event: Dict[str, Any]) -> str:
        """Format event for display in list."""
        title = event.get('summary', 'Untitled Event')
        start_time = event.get('start', {})
        
        # Extract datetime
        if isinstance(start_time, dict):
            date_str = start_time.get('dateTime') or start_time.get('date', 'Unknown time')
        else:
            date_str = str(start_time)
        
        # Try to format nicely
        try:
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                formatted_date = dt.strftime('%b %d, %H:%M')
            else:
                formatted_date = date_str
        except:
            formatted_date = date_str
        
        return f"**{title}** - {formatted_date}"
    
    async def start_polling(self) -> None:
        """Start bot polling."""
        logger.info("Starting Telegram bot polling...")
        await self.dp.start_polling(self.bot)
    
    async def stop(self) -> None:
        """Stop the bot."""
        await self.bot.session.close()


def create_telegram_bot(token: str, **kwargs) -> TelegramBot:
    """
    Factory function to create Telegram bot instance.
    
    Args:
        token: Telegram bot token
        **kwargs: Additional arguments for TelegramBot
        
    Returns:
        TelegramBot instance
    """
    if not token:
        raise ValueError("Token is required")
    
    return TelegramBot(token, **kwargs)


# Main function for running the bot
async def main():
    """Main function to run the bot."""
    # Get token from environment
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    
    # Create and start bot
    bot = create_telegram_bot(token)
    
    try:
        await bot.start_polling()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        await bot.stop()


if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the bot
    asyncio.run(main())