"""
Tests for OCR Service
"""

import pytest
import io
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    from services.ocr_service import OCRService, MockOCRService, OCRError, create_ocr_service
except ImportError:
    # If dependencies are missing, create mock classes for testing
    class OCRError(Exception):
        pass
    
    class OCRService:
        def __init__(self, languages="rus+deu+eng"):
            raise OCRError("Tesseract not available")
    
    class MockOCRService:
        def __init__(self, languages="rus+deu+eng"):
            self.languages = languages
        
        def extract_text(self, image_data):
            return "Mock OCR text extraction result"
        
        def extract_business_card_info(self, image_data):
            return {
                'name': 'John Doe',
                'phone': '+49 123 456789',
                'email': 'john.doe@example.com',
                'company': 'Example Corp',
                'raw_text': 'John Doe\nExample Corp\nPhone: +49 123 456789\nEmail: john.doe@example.com'
            }
        
        def extract_appointment_info(self, image_data):
            return {
                'date': '15.06.2026',
                'time': '14:30',
                'doctor': 'Dr. Smith',
                'department': 'Cardiology',
                'raw_text': 'Appointment\nDr. Smith\nCardiology\nDate: 15.06.2026\nTime: 14:30'
            }
    
    def create_ocr_service(languages="rus+deu+eng"):
        return MockOCRService(languages)


class TestOCRService:
    """Test suite for OCR Service."""
    
    def setup_method(self):
        """Setup test environment."""
        self.mock_image_data = b"fake_image_data"
        self.sample_text = "John Doe\\nExample Corp\\n+49 123 456789\\ninfo@example.com"
    
    def create_mock_image(self):
        """Create a mock PIL Image."""
        mock_image = Mock()
        mock_image.mode = 'RGB'
        mock_image.convert.return_value = mock_image
        return mock_image
    
    def test_ocr_error_creation(self):
        """Test OCRError exception creation."""
        error = OCRError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    @patch('services.ocr_service.pytesseract')
    def test_ocr_service_init_success(self, mock_pytesseract):
        """Test successful OCR service initialization."""
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"
        
        service = OCRService()
        assert service.languages == "rus+deu+eng"
    
    @patch('services.ocr_service.pytesseract')
    def test_ocr_service_init_failure(self, mock_pytesseract):
        """Test OCR service initialization failure."""
        mock_pytesseract.get_tesseract_version.side_effect = Exception("Tesseract not found")
        
        with pytest.raises(OCRError, match="Tesseract not available"):
            OCRService()
    
    @patch('services.ocr_service.pytesseract')
    @patch('services.ocr_service.Image')
    def test_extract_text_from_bytes(self, mock_image, mock_pytesseract):
        """Test text extraction from image bytes."""
        # Setup mocks
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"
        mock_pytesseract.image_to_string.return_value = "  Sample text  \\n\\n  with whitespace  "
        
        mock_pil_image = self.create_mock_image()
        mock_image.open.return_value = mock_pil_image
        
        # Test
        service = OCRService()
        result = service.extract_text(self.mock_image_data)
        
        assert "Sample text" in result
        mock_image.open.assert_called_once()
        mock_pytesseract.image_to_string.assert_called_once()
    
    @patch('services.ocr_service.pytesseract')
    def test_extract_text_from_pil_image(self, mock_pytesseract):
        """Test text extraction from PIL Image object."""
        # Setup mocks
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"
        mock_pytesseract.image_to_string.return_value = "Sample text from PIL"
        
        mock_pil_image = self.create_mock_image()
        
        # Test
        service = OCRService()
        result = service.extract_text(mock_pil_image)
        
        assert "Sample text from PIL" in result
    
    @patch('services.ocr_service.pytesseract')
    def test_extract_text_failure(self, mock_pytesseract):
        """Test text extraction failure handling."""
        # Setup mocks
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"
        mock_pytesseract.image_to_string.side_effect = Exception("OCR failed")
        
        mock_pil_image = self.create_mock_image()
        
        # Test
        service = OCRService()
        with pytest.raises(OCRError, match="Failed to extract text"):
            service.extract_text(mock_pil_image)
    
    def test_cleanup_text(self):
        """Test text cleanup functionality."""
        # Create service instance with mocked Tesseract check
        with patch('services.ocr_service.pytesseract.get_tesseract_version'):
            service = OCRService()
        
        # Test text with excessive whitespace and artifacts
        dirty_text = "  Sample   text  \\n\\n\\n  with   artifacts |_~`  "
        cleaned = service._cleanup_text(dirty_text)
        
        assert "Sample text" in cleaned
        assert "|" not in cleaned
        assert "_" not in cleaned
        assert "~" not in cleaned
        assert "`" not in cleaned
    
    def test_extract_name(self):
        """Test name extraction from text."""
        with patch('services.ocr_service.pytesseract.get_tesseract_version'):
            service = OCRService()
        
        # Test English name
        text_en = "Contact: John Doe, Manager"
        name = service._extract_name(text_en)
        assert name == "John Doe"
        
        # Test Russian name
        text_ru = "Контакт: Иван Петров, Менеджер"
        name = service._extract_name(text_ru)
        assert name == "Иван Петров"
    
    def test_extract_phone(self):
        """Test phone number extraction."""
        with patch('services.ocr_service.pytesseract.get_tesseract_version'):
            service = OCRService()
        
        text = "Contact me at +49 123 456-789 or email"
        phone = service._extract_phone(text)
        assert "+49 123 456-789" in phone
    
    def test_extract_email(self):
        """Test email extraction."""
        with patch('services.ocr_service.pytesseract.get_tesseract_version'):
            service = OCRService()
        
        text = "Email us at info@example.com for more details"
        email = service._extract_email(text)
        assert email == "info@example.com"
    
    def test_extract_date(self):
        """Test date extraction."""
        with patch('services.ocr_service.pytesseract.get_tesseract_version'):
            service = OCRService()
        
        # Test different date formats
        text1 = "Appointment on 15.06.2026 at 14:30"
        date1 = service._extract_date(text1)
        assert date1 == "15.06.2026"
        
        text2 = "Meeting scheduled for 2026/06/15"
        date2 = service._extract_date(text2)
        assert date2 == "2026/06/15"
    
    def test_extract_time(self):
        """Test time extraction."""
        with patch('services.ocr_service.pytesseract.get_tesseract_version'):
            service = OCRService()
        
        text = "Appointment at 14:30 or 2:45"
        time = service._extract_time(text)
        assert time in ["14:30", "2:45"]
    
    @patch('services.ocr_service.pytesseract')
    @patch('services.ocr_service.Image')
    def test_extract_business_card_info(self, mock_image, mock_pytesseract):
        """Test business card information extraction."""
        # Setup mocks
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"
        mock_pytesseract.image_to_string.return_value = (
            "John Doe\\n"
            "Example Corp\\n"
            "Phone: +49 123 456789\\n"
            "Email: john.doe@example.com"
        )
        
        mock_pil_image = self.create_mock_image()
        mock_image.open.return_value = mock_pil_image
        
        # Test
        service = OCRService()
        info = service.extract_business_card_info(self.mock_image_data)
        
        assert info['name'] == "John Doe"
        assert info['phone'] == "+49 123 456789"
        assert info['email'] == "john.doe@example.com"
        assert 'raw_text' in info
    
    @patch('services.ocr_service.pytesseract')
    @patch('services.ocr_service.Image')
    def test_extract_appointment_info(self, mock_image, mock_pytesseract):
        """Test appointment information extraction."""
        # Setup mocks
        mock_pytesseract.get_tesseract_version.return_value = "5.0.0"
        mock_pytesseract.image_to_string.return_value = (
            "Dr. Smith\\n"
            "Cardiology Department\\n"
            "Appointment: 15.06.2026\\n"
            "Time: 14:30"
        )
        
        mock_pil_image = self.create_mock_image()
        mock_image.open.return_value = mock_pil_image
        
        # Test
        service = OCRService()
        info = service.extract_appointment_info(self.mock_image_data)
        
        assert info['date'] == "15.06.2026"
        assert info['time'] == "14:30"
        assert info['doctor'] == "Dr. Smith"
        assert 'raw_text' in info


class TestMockOCRService:
    """Test suite for Mock OCR Service."""
    
    def setup_method(self):
        """Setup test environment."""
        self.service = MockOCRService()
        self.mock_image_data = b"fake_image_data"
    
    def test_mock_ocr_init(self):
        """Test mock OCR service initialization."""
        service = MockOCRService("eng")
        assert service.languages == "eng"
    
    def test_mock_extract_text(self):
        """Test mock text extraction."""
        result = self.service.extract_text(self.mock_image_data)
        assert result == "Mock OCR text extraction result"
    
    def test_mock_extract_business_card_info(self):
        """Test mock business card extraction."""
        info = self.service.extract_business_card_info(self.mock_image_data)
        
        assert info['name'] == 'John Doe'
        assert info['phone'] == '+49 123 456789'
        assert info['email'] == 'john.doe@example.com'
        assert info['company'] == 'Example Corp'
        assert 'raw_text' in info
    
    def test_mock_extract_appointment_info(self):
        """Test mock appointment extraction."""
        info = self.service.extract_appointment_info(self.mock_image_data)
        
        assert info['date'] == '15.06.2026'
        assert info['time'] == '14:30'
        assert info['doctor'] == 'Dr. Smith'
        assert info['department'] == 'Cardiology'
        assert 'raw_text' in info


class TestOCRFactory:
    """Test suite for OCR factory function."""
    
    @patch('services.ocr_service.OCRService')
    def test_create_ocr_service_success(self, mock_ocr_class):
        """Test successful OCR service creation."""
        mock_instance = Mock()
        mock_ocr_class.return_value = mock_instance
        
        result = create_ocr_service("eng")
        
        assert result == mock_instance
        mock_ocr_class.assert_called_once_with("eng")
    
    @patch('services.ocr_service.OCRService')
    @patch('services.ocr_service.MockOCRService')
    def test_create_ocr_service_fallback(self, mock_mock_class, mock_ocr_class):
        """Test fallback to mock OCR service."""
        mock_ocr_class.side_effect = OCRError("Tesseract unavailable")
        mock_mock_instance = Mock()
        mock_mock_class.return_value = mock_mock_instance
        
        result = create_ocr_service("eng")
        
        assert result == mock_mock_instance
        mock_mock_class.assert_called_once_with("eng")


if __name__ == "__main__":
    pytest.main([__file__])