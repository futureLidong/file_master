#!/usr/bin/env python3
"""Tests for PDF extraction plugin."""

import pytest
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from file_master.config import Config
from file_master.services.pdf_reader import PDFReader, validate_pdf_file
from file_master.services.extractor import Extractor


class TestPDFReader:
    """Tests for PDF reader service."""
    
    def test_validate_nonexistent_file(self):
        """Test validation of non-existent file."""
        is_valid, error = validate_pdf_file("/nonexistent/file.pdf")
        assert not is_valid
        assert "not found" in error.lower()
    
    def test_validate_non_pdf(self, tmp_path):
        """Test validation of non-PDF file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")
        
        is_valid, error = validate_pdf_file(str(test_file))
        assert not is_valid
        assert "must be a pdf" in error.lower()


class TestExtractor:
    """Tests for AI extractor service."""
    
    def test_clean_json_response(self):
        """Test JSON response cleaning."""
        config = Config(api_key="test")
        extractor = Extractor(config)
        
        # Test with markdown code blocks
        text = '```json\n{"key": "value"}\n```'
        cleaned = extractor._clean_json_response(text)
        assert cleaned == '{"key": "value"}'
        
        # Test plain JSON
        text = '{"key": "value"}'
        cleaned = extractor._clean_json_response(text)
        assert cleaned == '{"key": "value"}'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
