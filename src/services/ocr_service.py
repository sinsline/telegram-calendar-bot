"""
OCR Service for Telegram Calendar Bot

Provides text extraction from images using Tesseract OCR with multi-language support.
Includes preprocessing utilities and mock fallback for testing environments.
"""

import io
import re
import logging
from typing import Optional, Dict, Any, List, Union
from PIL import Image
import pytesseract


logger = logging.getLogger(__name__)


class OCRError(Exception):
    """Custom exception for OCR-related errors."""
    pass


class OCRService:
    """
    OCR service using Tesseract for text extraction from images.
    
    Supports multiple languages (Russian, German, English) and includes
    text preprocessing utilities with mock fallback for testing.
    """
    
    def __init__(self, languages: str = "rus+deu+eng"):
        """
        Initialize OCR service.
        
        Args:
            languages: Tesseract language codes (default: "rus+deu+eng")
        """
        self.languages = languages
        self._validate_tesseract_available()
    
    def _validate_tesseract_available(self) -> None:
        """Check if Tesseract is available on the system."""
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")
            raise OCRError("Tesseract not available on system")
    
    def extract_text(self, image_data: Union[bytes, Image.Image]) -> str:
        """
        Extract text from image using OCR.
        
        Args:
            image_data: Image data as bytes or PIL Image object
            
        Returns:
            Extracted text as string
            
        Raises:
            OCRError: If OCR extraction fails
        """
        try:
            # Convert image data to PIL Image if needed
            if isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data))
            else:
                image = image_data
            
            # Preprocess image for better OCR results
            processed_image = self._preprocess_image(image)
            
            # Extract text with specified languages
            text = pytesseract.image_to_string(
                processed_image, 
                lang=self.languages,
                config='--psm 6'
            )
            
            # Clean up extracted text
            return self._cleanup_text(text)
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise OCRError(f"Failed to extract text: {e}")
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image to improve OCR accuracy.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Enhance contrast and sharpness
        from PIL import ImageEnhance
        
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        
        return image
    
    def _cleanup_text(self, text: str) -> str:
        """
        Clean up extracted text removing artifacts.
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove common OCR artifacts
        text = re.sub(r'[|_~`]', '', text)
        
        # Strip leading/trailing whitespace
        return text.strip()
    
    def extract_business_card_info(self, image_data: Union[bytes, Image.Image]) -> Dict[str, Any]:
        """
        Extract structured information from business card images.
        
        Args:
            image_data: Business card image
            
        Returns:
            Dictionary with extracted information (name, phone, email, etc.)
        """
        text = self.extract_text(image_data)
        
        # Extract common business card fields
        info = {
            'name': self._extract_name(text),
            'phone': self._extract_phone(text),
            'email': self._extract_email(text),
            'company': self._extract_company(text),
            'raw_text': text
        }
        
        return info
    
    def extract_appointment_info(self, image_data: Union[bytes, Image.Image]) -> Dict[str, Any]:
        """
        Extract appointment information from doctor's cards or similar.
        
        Args:
            image_data: Appointment card image
            
        Returns:
            Dictionary with date, time, doctor, department info
        """
        text = self.extract_text(image_data)
        
        info = {
            'date': self._extract_date(text),
            'time': self._extract_time(text),
            'doctor': self._extract_doctor(text),
            'department': self._extract_department(text),
            'raw_text': text
        }
        
        return info
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract name from text."""
        # Simple pattern matching for names
        name_patterns = [
            r'([A-Z][a-z]+ [A-Z][a-z]+)',
            r'([А-Я][а-я]+ [А-Я][а-я]+)',
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text."""
        phone_pattern = r'[\+]?[\d\s\-\(\)]{10,}'
        match = re.search(phone_pattern, text)
        return match.group(0).strip() if match else None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address from text."""
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    def _extract_company(self, text: str) -> Optional[str]:
        """Extract company name from text."""
        # Look for lines that might contain company names
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 5 and len(line) < 50:
                # Skip lines with only contact info
                if not re.search(r'[\+\d\@]', line):
                    return line
        
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from text."""
        date_patterns = [
            r'\d{1,2}[\.\-/]\d{1,2}[\.\-/]\d{2,4}',
            r'\d{2,4}[\.\-/]\d{1,2}[\.\-/]\d{1,2}',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_time(self, text: str) -> Optional[str]:
        """Extract time from text."""
        time_pattern = r'\d{1,2}[:\.]\d{2}'
        match = re.search(time_pattern, text)
        return match.group(0) if match else None
    
    def _extract_doctor(self, text: str) -> Optional[str]:
        """Extract doctor name from text."""
        # Look for doctor titles and names
        doctor_patterns = [
            r'Dr\.?\s+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'([A-Z][a-z]+ [A-Z][a-z]+),?\s*MD',
            r'Доктор\s+([А-Я][а-я]+ [А-Я][а-я]+)',
        ]
        
        for pattern in doctor_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_department(self, text: str) -> Optional[str]:
        """Extract department/specialty from text."""
        dept_keywords = [
            'cardiology', 'neurology', 'orthopedics', 'radiology',
            'кардиология', 'неврология', 'ортопедия', 'рентген'
        ]
        
        text_lower = text.lower()
        for keyword in dept_keywords:
            if keyword in text_lower:
                return keyword.capitalize()
        
        return None


class MockOCRService:
    """
    Mock OCR service for testing environments without Tesseract.
    
    Returns predefined responses for testing purposes.
    """
    
    def __init__(self, languages: str = "rus+deu+eng"):
        self.languages = languages
    
    def extract_text(self, image_data: Union[bytes, Image.Image]) -> str:
        """Mock text extraction."""
        return "Mock OCR text extraction result"
    
    def extract_business_card_info(self, image_data: Union[bytes, Image.Image]) -> Dict[str, Any]:
        """Mock business card extraction."""
        return {
            'name': 'John Doe',
            'phone': '+49 123 456789',
            'email': 'john.doe@example.com',
            'company': 'Example Corp',
            'raw_text': 'John Doe\nExample Corp\nPhone: +49 123 456789\nEmail: john.doe@example.com'
        }
    
    def extract_appointment_info(self, image_data: Union[bytes, Image.Image]) -> Dict[str, Any]:
        """Mock appointment extraction."""
        return {
            'date': '15.06.2026',
            'time': '14:30',
            'doctor': 'Dr. Smith',
            'department': 'Cardiology',
            'raw_text': 'Appointment\nDr. Smith\nCardiology\nDate: 15.06.2026\nTime: 14:30'
        }


def create_ocr_service(languages: str = "rus+deu+eng") -> Union[OCRService, MockOCRService]:
    """
    Factory function to create OCR service with fallback to mock.
    
    Args:
        languages: Tesseract language codes
        
    Returns:
        OCRService instance or MockOCRService if Tesseract unavailable
    """
    try:
        return OCRService(languages)
    except OCRError:
        logger.warning("Falling back to mock OCR service")
        return MockOCRService(languages)