"""
NLP Service for Telegram Calendar Bot

Provides natural language parsing for dates and times in multiple languages.
Supports Russian, German, and English date/time expressions.
"""

import re
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple, Union
from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta


logger = logging.getLogger(__name__)


class NLPParsingError(Exception):
    """Custom exception for NLP parsing errors."""
    pass


class NLPService:
    """
    NLP service for parsing dates and times from natural language.
    
    Supports multiple languages (Russian, German, English) and various
    date/time formats including relative expressions.
    """
    
    def __init__(self, default_timezone: Optional[timezone] = None):
        """
        Initialize NLP service.
        
        Args:
            default_timezone: Default timezone for parsing (default: UTC)
        """
        self.default_timezone = default_timezone or timezone.utc
        self._init_patterns()
    
    def _init_patterns(self) -> None:
        """Initialize regex patterns for date/time recognition."""
        
        # Date patterns
        self.date_patterns = {
            # Absolute dates
            'date_dmy': r'(\d{1,2})[\.\-/](\d{1,2})[\.\-/](\d{2,4})',  # 15.06.2026, 15-06-26
            'date_ymd': r'(\d{4})[\.\-/](\d{1,2})[\.\-/](\d{1,2})',   # 2026.06.15
            'date_mdy': r'(\d{1,2})[\.\-/](\d{1,2})[\.\-/](\d{2,4})',
            
            # Relative dates - English
            'tomorrow_en': r'\b(tomorrow)\b',
            'today_en': r'\b(today)\b',
            'yesterday_en': r'\b(yesterday)\b',
            'next_week_en': r'\b(next\s+week)\b',
            'next_month_en': r'\b(next\s+month)\b',
            'in_days_en': r'\bin\s+(\d+)\s+days?\b',
            'in_weeks_en': r'\bin\s+(\d+)\s+weeks?\b',
            
            # Relative dates - German
            'tomorrow_de': r'\b(morgen)\b',
            'today_de': r'\b(heute)\b',
            'yesterday_de': r'\b(gestern)\b',
            'next_week_de': r'\b(nächste\s+woche)\b',
            'next_month_de': r'\b(nächster\s+monat)\b',
            'in_days_de': r'\bin\s+(\d+)\s+tagen?\b',
            
            # Relative dates - Russian  
            'tomorrow_ru': r'\b(завтра)\b',
            'today_ru': r'\b(сегодня)\b',
            'yesterday_ru': r'\b(вчера)\b',
            'next_week_ru': r'\b(на\s+следующей\s+неделе|следующую\s+неделю)\b',
            'next_month_ru': r'\b(в\s+следующем\s+месяце|следующий\s+месяц)\b',
            'in_days_ru': r'\b(через\s+(\d+)\s+дн[яей])\b',
            
            # Day names - English
            'weekday_en': r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            'next_weekday_en': r'\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            
            # Day names - German
            'weekday_de': r'\b(montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag)\b',
            'next_weekday_de': r'\bnächsten?\s+(montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag)\b',
            
            # Day names - Russian
            'weekday_ru': r'\b(понедельник|вторник|среда|четверг|пятница|суббота|воскресенье)\b',
            'next_weekday_ru': r'\b(в\s+понедельник|во?\s+вторник|в\s+среду|в\s+четверг|в\s+пятницу|в\s+субботу|в\s+воскресенье)\b',
        }
        
        # Time patterns
        self.time_patterns = {
            # 24-hour format
            'time_24h': r'\b(\d{1,2})[:\.](\d{2})\b',
            'time_24h_detailed': r'\b(\d{1,2})[:\.](\d{2})[:\.](\d{2})\b',
            
            # 12-hour format
            'time_12h_en': r'\b(\d{1,2})[:\.](\d{2})\s*(am|pm)\b',
            'time_12h_hour_en': r'\b(\d{1,2})\s*(am|pm)\b',
            
            # German time
            'time_uhr_de': r'\b(\d{1,2})[:\.]?(\d{2})?\s*uhr\b',
            'time_hour_de': r'\bum\s+(\d{1,2})\s*uhr\b',
            
            # Russian time  
            'time_ru': r'\bв\s+(\d{1,2})[:\.](\d{2})\b',
            'time_hour_ru': r'\bв\s+(\d{1,2})\s*час',
            
            # Relative time
            'in_minutes_en': r'\bin\s+(\d+)\s+minutes?\b',
            'in_hours_en': r'\bin\s+(\d+)\s+hours?\b',
            'in_minutes_de': r'\bin\s+(\d+)\s+minuten?\b',
            'in_hours_de': r'\bin\s+(\d+)\s+stunden?\b',
            'in_minutes_ru': r'\bчерез\s+(\d+)\s+мин',
            'in_hours_ru': r'\bчерез\s+(\d+)\s+час',
        }
        
        # Weekday mappings
        self.weekdays = {
            'en': {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                   'friday': 4, 'saturday': 5, 'sunday': 6},
            'de': {'montag': 0, 'dienstag': 1, 'mittwoch': 2, 'donnerstag': 3,
                   'freitag': 4, 'samstag': 5, 'sonntag': 6},
            'ru': {'понедельник': 0, 'вторник': 1, 'среда': 2, 'четверг': 3,
                   'пятница': 4, 'суббота': 5, 'воскресенье': 6}
        }
    
    def extract_datetime(self, text: str, reference_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Extract date and time information from natural language text.
        
        Args:
            text: Input text to parse
            reference_date: Reference date for relative parsing (default: now)
            
        Returns:
            Dictionary with parsed datetime information or None if no date found
        """
        if not text:
            return None
            
        text = text.lower().strip()
        reference_date = reference_date or datetime.now(self.default_timezone)
        
        try:
            # Extract date and time separately
            date_info = self._extract_date(text, reference_date)
            time_info = self._extract_time(text, reference_date)
            
            if not date_info and not time_info:
                return None
            
            # Combine date and time
            result_datetime = self._combine_datetime(date_info, time_info, reference_date)
            
            return {
                'datetime': result_datetime,
                'date_found': date_info is not None,
                'time_found': time_info is not None,
                'original_text': text,
                'confidence': self._calculate_confidence(date_info, time_info)
            }
            
        except Exception as e:
            logger.error(f"Failed to extract datetime from '{text}': {e}")
            raise NLPParsingError(f"Failed to parse datetime: {e}")
    
    def _extract_date(self, text: str, reference_date: datetime) -> Optional[datetime]:
        """Extract date from text."""
        
        # Try absolute date patterns first
        for pattern_name, pattern in self.date_patterns.items():
            if 'date_' in pattern_name:
                match = re.search(pattern, text)
                if match:
                    return self._parse_absolute_date(match, pattern_name)
        
        # Try relative date patterns
        return self._parse_relative_date(text, reference_date)
    
    def _extract_time(self, text: str, reference_date: datetime) -> Optional[Dict[str, int]]:
        """Extract time from text."""
        
        for pattern_name, pattern in self.time_patterns.items():
            match = re.search(pattern, text)
            if match:
                return self._parse_time_match(match, pattern_name)
        
        return None
    
    def _parse_absolute_date(self, match, pattern_name: str) -> Optional[datetime]:
        """Parse absolute date from regex match."""
        try:
            groups = match.groups()
            
            if pattern_name == 'date_dmy':  # 15.06.2026
                day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                if year < 100:  # Handle 2-digit years
                    year += 2000 if year < 50 else 1900
                    
            elif pattern_name == 'date_ymd':  # 2026.06.15
                year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                
            elif pattern_name == 'date_mdy':  # 06.15.2026 (ambiguous, assume MDY for US format)
                month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                if year < 100:
                    year += 2000 if year < 50 else 1900
            else:
                return None
                
            return datetime(year, month, day, tzinfo=self.default_timezone)
            
        except ValueError:
            return None
    
    def _parse_relative_date(self, text: str, reference_date: datetime) -> Optional[datetime]:
        """Parse relative date expressions."""
        
        # Tomorrow
        if re.search(r'\b(tomorrow|morgen|завтра)\b', text):
            return reference_date + timedelta(days=1)
            
        # Today
        if re.search(r'\b(today|heute|сегодня)\b', text):
            return reference_date
            
        # Yesterday
        if re.search(r'\b(yesterday|gestern|вчера)\b', text):
            return reference_date - timedelta(days=1)
        
        # Next week
        if re.search(r'\b(next\s+week|nächste\s+woche|следующ[^\\s]+\s+недел)\b', text):
            return reference_date + timedelta(weeks=1)
            
        # In X days
        for pattern in [r'\bin\s+(\d+)\s+days?', r'\bin\s+(\d+)\s+tagen?', r'\bчерез\s+(\d+)\s+дн']:
            match = re.search(pattern, text)
            if match:
                days = int(match.group(1))
                return reference_date + timedelta(days=days)
        
        # Weekdays
        for lang, weekdays in self.weekdays.items():
            for weekday_name, weekday_num in weekdays.items():
                if weekday_name in text:
                    days_ahead = weekday_num - reference_date.weekday()
                    if days_ahead <= 0:  # If it's today or in the past, assume next week
                        days_ahead += 7
                    return reference_date + timedelta(days=days_ahead)
        
        return None
    
    def _parse_time_match(self, match, pattern_name: str) -> Optional[Dict[str, int]]:
        """Parse time from regex match."""
        groups = match.groups()
        
        try:
            if pattern_name == 'time_24h':
                hour, minute = int(groups[0]), int(groups[1])
                return {'hour': hour, 'minute': minute, 'second': 0}
                
            elif pattern_name in ['time_12h_en', 'time_12h_hour_en']:
                hour = int(groups[0])
                minute = int(groups[1]) if len(groups) > 1 and groups[1] else 0
                am_pm = groups[-1].lower()
                
                if am_pm == 'pm' and hour != 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0
                    
                return {'hour': hour, 'minute': minute, 'second': 0}
                
            elif pattern_name in ['time_uhr_de', 'time_hour_de']:
                hour = int(groups[0])
                minute = int(groups[1]) if len(groups) > 1 and groups[1] else 0
                return {'hour': hour, 'minute': minute, 'second': 0}
                
            elif pattern_name in ['time_ru', 'time_hour_ru']:
                hour = int(groups[0])
                minute = int(groups[1]) if len(groups) > 1 and groups[1] else 0
                return {'hour': hour, 'minute': minute, 'second': 0}
                
        except (ValueError, IndexError):
            pass
            
        return None
    
    def _combine_datetime(self, date_info: Optional[datetime], 
                         time_info: Optional[Dict[str, int]], 
                         reference_date: datetime) -> datetime:
        """Combine date and time information."""
        
        # Use date_info if available, otherwise use reference date
        base_date = date_info if date_info else reference_date
        
        # Use time_info if available, otherwise keep existing time or set to start of day
        if time_info:
            return base_date.replace(
                hour=time_info['hour'],
                minute=time_info['minute'],
                second=time_info['second'],
                microsecond=0
            )
        else:
            # If no time specified and using reference date, keep the time
            if date_info:
                return base_date.replace(hour=9, minute=0, second=0, microsecond=0)  # Default to 9 AM
            else:
                return base_date
    
    def _calculate_confidence(self, date_info: Optional[datetime], 
                            time_info: Optional[Dict[str, int]]) -> float:
        """Calculate parsing confidence score."""
        confidence = 0.0
        
        if date_info:
            confidence += 0.6
            
        if time_info:
            confidence += 0.4
            
        return min(confidence, 1.0)
    
    def parse_event_text(self, text: str, reference_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Parse event text to extract title, date, time, and description.
        
        Args:
            text: Event description text
            reference_date: Reference date for relative parsing
            
        Returns:
            Dictionary with parsed event information
        """
        datetime_info = self.extract_datetime(text, reference_date)
        
        # Extract event title/description by removing date/time mentions
        cleaned_text = self._remove_datetime_text(text)
        
        return {
            'title': cleaned_text.strip() or 'New Event',
            'datetime_info': datetime_info,
            'original_text': text,
            'has_datetime': datetime_info is not None
        }
    
    def _remove_datetime_text(self, text: str) -> str:
        """Remove date/time expressions from text to extract event title."""
        cleaned = text
        
        # Remove common date/time patterns
        patterns_to_remove = [
            r'\b\d{1,2}[\.\-/]\d{1,2}[\.\-/]\d{2,4}\b',  # Dates
            r'\b\d{1,2}[:\.]\d{2}\b',  # Times
            r'\b(tomorrow|today|yesterday|morgen|heute|gestern|завтра|сегодня|вчера)\b',
            r'\b(next\s+week|nächste\s+woche|следующ[^\\s]+\s+недел)\b',
            r'\bв\s+\d{1,2}[:\.]?\d{2}?\b',  # Russian time
            r'\bum\s+\d{1,2}\s*uhr\b',  # German time
            r'\b\d{1,2}\s*(am|pm)\b',  # 12-hour time
        ]
        
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
            
        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()


class MockNLPService:
    """
    Mock NLP service for testing environments.
    
    Returns predefined responses for testing purposes.
    """
    
    def __init__(self, default_timezone: Optional[timezone] = None):
        self.default_timezone = default_timezone or timezone.utc
    
    def extract_datetime(self, text: str, reference_date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """Mock datetime extraction."""
        reference_date = reference_date or datetime.now(self.default_timezone)
        
        # Simple mock responses based on keywords
        if 'tomorrow' in text.lower() or 'завтра' in text.lower() or 'morgen' in text.lower():
            mock_datetime = reference_date + timedelta(days=1)
            mock_datetime = mock_datetime.replace(hour=14, minute=30, second=0, microsecond=0)
        else:
            mock_datetime = reference_date.replace(hour=15, minute=0, second=0, microsecond=0)
        
        return {
            'datetime': mock_datetime,
            'date_found': True,
            'time_found': True,
            'original_text': text,
            'confidence': 0.8
        }
    
    def parse_event_text(self, text: str, reference_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Mock event parsing."""
        datetime_info = self.extract_datetime(text, reference_date)
        
        return {
            'title': 'Mock Event',
            'datetime_info': datetime_info,
            'original_text': text,
            'has_datetime': True
        }


def create_nlp_service(default_timezone: Optional[timezone] = None) -> Union[NLPService, MockNLPService]:
    """
    Factory function to create NLP service with fallback to mock.
    
    Args:
        default_timezone: Default timezone for parsing
        
    Returns:
        NLPService instance or MockNLPService if dependencies unavailable
    """
    try:
        return NLPService(default_timezone)
    except ImportError as e:
        logger.warning(f"Falling back to mock NLP service: {e}")
        return MockNLPService(default_timezone)