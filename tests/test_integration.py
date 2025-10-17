"""
Integration Tests - Test complete workflow
"""
import pytest
from services.pdf_service import PDFService
from services.chat_service import ChatService

@pytest.mark.integration
def test_complete_pdf_workflow():
    """Test complete PDF processing and query workflow"""
    # This test requires all services to be running
    pytest.skip("Integration test - run manually with all services")
