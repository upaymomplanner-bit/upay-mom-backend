"""
Unit tests for FileProcessor utility class.
Tests file validation and MIME type detection.
"""

import pytest
from unittest.mock import MagicMock
from fastapi import UploadFile, HTTPException


class TestFileProcessor:
    """Tests for FileProcessor utility functions"""

    def test_validate_file_txt_success(self, mock_settings):
        """Test validation succeeds for TXT files"""
        from app.services.file_processor import FileProcessor

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "transcript.txt"

        # Should not raise exception
        FileProcessor.validate_file(mock_file, mock_settings.max_file_size)

    def test_validate_file_pdf_success(self, mock_settings):
        """Test validation succeeds for PDF files"""
        from app.services.file_processor import FileProcessor

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "transcript.pdf"

        # Should not raise exception
        FileProcessor.validate_file(mock_file, mock_settings.max_file_size)

    def test_validate_file_no_filename(self, mock_settings):
        """Test validation fails when no filename"""
        from app.services.file_processor import FileProcessor

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = None

        with pytest.raises(HTTPException) as exc_info:
            FileProcessor.validate_file(mock_file, mock_settings.max_file_size)

        assert exc_info.value.status_code == 400
        assert "No filename provided" in exc_info.value.detail

    def test_validate_file_invalid_extension(self, mock_settings):
        """Test validation fails for unsupported file types"""
        from app.services.file_processor import FileProcessor

        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "transcript.docx"

        with pytest.raises(HTTPException) as exc_info:
            FileProcessor.validate_file(mock_file, mock_settings.max_file_size)

        assert exc_info.value.status_code == 400
        assert "Invalid file type" in exc_info.value.detail

    def test_get_mime_type_txt(self):
        """Test MIME type detection for TXT files"""
        from app.services.file_processor import FileProcessor

        mime_type = FileProcessor.get_mime_type("transcript.txt")
        assert mime_type == "text/plain"

    def test_get_mime_type_pdf(self):
        """Test MIME type detection for PDF files"""
        from app.services.file_processor import FileProcessor

        mime_type = FileProcessor.get_mime_type("transcript.pdf")
        assert mime_type == "application/pdf"

    def test_get_mime_type_unknown(self):
        """Test MIME type for unknown extensions"""
        from app.services.file_processor import FileProcessor

        mime_type = FileProcessor.get_mime_type("file.unknown")
        assert mime_type == "application/octet-stream"

    def test_get_mime_type_case_insensitive(self):
        """Test MIME type detection is case insensitive"""
        from app.services.file_processor import FileProcessor

        assert FileProcessor.get_mime_type("FILE.TXT") == "text/plain"
        assert FileProcessor.get_mime_type("File.PDF") == "application/pdf"
