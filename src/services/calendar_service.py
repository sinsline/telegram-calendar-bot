"""
Google Calendar Service for Telegram Calendar Bot

Provides Google Calendar API integration for event creation and management.
Includes mock fallback for testing environments.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Union
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


logger = logging.getLogger(__name__)


class CalendarError(Exception):
    """Custom exception for calendar-related errors."""
    pass


class CalendarService:
    """
    Google Calendar service for event creation and management.
    
    Handles authentication, event creation, and event retrieval
    with proper error handling and timezone support.
    """
    
    # Google Calendar API scopes
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self, credentials_file: Optional[str] = None, token_file: Optional[str] = None):
        """
        Initialize Google Calendar service.
        
        Args:
            credentials_file: Path to Google OAuth2 credentials file
            token_file: Path to store/load user tokens
        """
        self.credentials_file = credentials_file or 'credentials.json'
        self.token_file = token_file or 'token.json'
        self.service = None
        self._authenticate()
    
    def _authenticate(self) -> None:
        """Authenticate with Google Calendar API."""
        try:
            creds = None
            
            # Load existing token
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
            
            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        raise CalendarError(f"Credentials file not found: {self.credentials_file}")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("Successfully authenticated with Google Calendar")
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Calendar: {e}")
            raise CalendarError(f"Authentication failed: {e}")
    
    def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new calendar event.
        
        Args:
            event_data: Event information dictionary with keys:
                - summary: Event title
                - start: Start datetime (datetime object or dict)
                - end: End datetime (optional, defaults to start + 1 hour)
                - description: Event description (optional)
                - location: Event location (optional)
                
        Returns:
            Created event data from Google Calendar API
        """
        try:
            # Format event for Google Calendar API
            formatted_event = self._format_event_for_api(event_data)
            
            # Create the event
            event = self.service.events().insert(
                calendarId='primary',
                body=formatted_event
            ).execute()
            
            logger.info(f"Event created: {event.get('id')} - {event.get('summary')}")
            return event
            
        except HttpError as e:
            logger.error(f"HTTP error creating event: {e}")
            raise CalendarError(f"Failed to create event: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating event: {e}")
            raise CalendarError(f"Event creation failed: {e}")
    
    def get_upcoming_events(self, max_results: int = 10, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get upcoming events from the calendar.
        
        Args:
            max_results: Maximum number of events to return
            days_ahead: Number of days to look ahead
            
        Returns:
            List of upcoming events
        """
        try:
            # Calculate time boundaries
            now = datetime.now(timezone.utc)
            time_max = now + timedelta(days=days_ahead)
            
            # Fetch events
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now.isoformat(),
                timeMax=time_max.isoformat(),
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            logger.info(f"Retrieved {len(events)} upcoming events")
            return events
            
        except HttpError as e:
            logger.error(f"HTTP error fetching events: {e}")
            raise CalendarError(f"Failed to fetch events: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching events: {e}")
            raise CalendarError(f"Event retrieval failed: {e}")
    
    def delete_event(self, event_id: str) -> bool:
        """
        Delete an event from the calendar.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            True if deletion successful
        """
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute()
            
            logger.info(f"Event deleted: {event_id}")
            return True
            
        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Event not found for deletion: {event_id}")
                return False
            logger.error(f"HTTP error deleting event: {e}")
            raise CalendarError(f"Failed to delete event: {e}")
        except Exception as e:
            logger.error(f"Unexpected error deleting event: {e}")
            raise CalendarError(f"Event deletion failed: {e}")
    
    def _format_event_for_api(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format event data for Google Calendar API."""
        
        # Extract datetime information
        start_datetime = event_data.get('start')
        if isinstance(start_datetime, datetime):
            start_time = start_datetime.isoformat()
        elif isinstance(start_datetime, dict):
            start_time = start_datetime.get('dateTime') or start_datetime.get('date')
        else:
            raise CalendarError("Invalid start time format")
        
        # Calculate end time (default to 1 hour later)
        end_datetime = event_data.get('end')
        if end_datetime:
            if isinstance(end_datetime, datetime):
                end_time = end_datetime.isoformat()
            elif isinstance(end_datetime, dict):
                end_time = end_datetime.get('dateTime') or end_datetime.get('date')
            else:
                end_time = start_time  # Fall back to start time
        else:
            # Default to 1 hour duration
            if isinstance(start_datetime, datetime):
                end_dt = start_datetime + timedelta(hours=1)
                end_time = end_dt.isoformat()
            else:
                end_time = start_time
        
        # Build event object
        formatted_event = {
            'summary': event_data.get('summary', 'New Event'),
            'start': {
                'dateTime': start_time,
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'UTC',
            },
        }
        
        # Add optional fields
        if 'description' in event_data:
            formatted_event['description'] = event_data['description']
        
        if 'location' in event_data:
            formatted_event['location'] = event_data['location']
        
        return formatted_event


class MockCalendarService:
    """
    Mock Calendar service for testing environments.
    
    Returns predefined responses for testing purposes without
    requiring actual Google Calendar API authentication.
    """
    
    def __init__(self, credentials_file: Optional[str] = None, token_file: Optional[str] = None):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.mock_events = []
        logger.info("Initialized mock calendar service")
    
    def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock event creation."""
        # Generate mock event response
        event_id = f"mock_event_{len(self.mock_events) + 1}"
        
        mock_event = {
            'id': event_id,
            'summary': event_data.get('summary', 'Mock Event'),
            'description': event_data.get('description', ''),
            'location': event_data.get('location', ''),
            'start': event_data.get('start', {'dateTime': datetime.now(timezone.utc).isoformat()}),
            'end': event_data.get('end', {'dateTime': (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()}),
            'htmlLink': f'https://calendar.google.com/event?eid={event_id}',
            'created': datetime.now(timezone.utc).isoformat(),
            'status': 'confirmed'
        }
        
        self.mock_events.append(mock_event)
        logger.info(f"Mock event created: {event_id}")
        return mock_event
    
    def get_upcoming_events(self, max_results: int = 10, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """Mock upcoming events retrieval."""
        # Return stored mock events or generate some defaults
        if not self.mock_events:
            now = datetime.now(timezone.utc)
            self.mock_events = [
                {
                    'id': 'mock_event_1',
                    'summary': 'Sample Meeting',
                    'start': {'dateTime': (now + timedelta(hours=2)).isoformat()},
                    'end': {'dateTime': (now + timedelta(hours=3)).isoformat()},
                    'htmlLink': 'https://calendar.google.com/event?eid=mock_event_1'
                },
                {
                    'id': 'mock_event_2',
                    'summary': 'Doctor Appointment',
                    'start': {'dateTime': (now + timedelta(days=1)).isoformat()},
                    'end': {'dateTime': (now + timedelta(days=1, hours=1)).isoformat()},
                    'htmlLink': 'https://calendar.google.com/event?eid=mock_event_2'
                }
            ]
        
        return self.mock_events[:max_results]
    
    def delete_event(self, event_id: str) -> bool:
        """Mock event deletion."""
        self.mock_events = [e for e in self.mock_events if e.get('id') != event_id]
        logger.info(f"Mock event deleted: {event_id}")
        return True


def create_calendar_service(credentials_file: Optional[str] = None, 
                          token_file: Optional[str] = None) -> Union[CalendarService, MockCalendarService]:
    """
    Factory function to create calendar service with fallback to mock.
    
    Args:
        credentials_file: Path to Google OAuth2 credentials file
        token_file: Path to store/load user tokens
        
    Returns:
        CalendarService instance or MockCalendarService if credentials unavailable
    """
    try:
        return CalendarService(credentials_file, token_file)
    except (CalendarError, ImportError, FileNotFoundError) as e:
        logger.warning(f"Falling back to mock calendar service: {e}")
        return MockCalendarService(credentials_file, token_file)