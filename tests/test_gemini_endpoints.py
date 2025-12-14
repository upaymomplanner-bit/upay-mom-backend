"""
Unit tests for Gemini-related endpoints.
Tests the /transcripts/process endpoint and Gemini client functionality.
"""

import pytest
from io import BytesIO
from unittest.mock import MagicMock

from conftest import TEST_AUTH_HEADERS


# ==================== TESTS FOR /process ENDPOINT ====================


class TestProcessTranscript:
    """Tests for POST /transcripts/process endpoint"""

    def test_process_transcript_txt_success(
        self,
        client,
        mock_gemini_client,
        sample_gemini_response,
        sample_meeting_details,
        sample_transcript_txt,
    ):
        """Test successful processing of TXT transcript"""
        # Setup mock
        mock_gemini_client.analyze_transcript.return_value = sample_gemini_response

        # Prepare request
        meeting_details_json = sample_meeting_details.model_dump_json()
        files = {
            "file": ("transcript.txt", BytesIO(sample_transcript_txt), "text/plain")
        }
        data = {"meeting_details": meeting_details_json}

        # Make request with auth header
        response = client.post(
            "/transcripts/process", files=files, data=data, headers=TEST_AUTH_HEADERS
        )

        # Assertions
        assert response.status_code == 200
        result = response.json()

        assert result["meeting_details"]["meeting_title"] == "Sprint Planning Q1 2025"
        assert (
            result["meeting_summary"]
            == "Discussed Q1 priorities, focusing on user authentication and security features."
        )
        assert len(result["task_groups"]) == 1
        assert (
            result["task_groups"][0]["tasks"][0]["title"]
            == "Implement User Authentication"
        )

        # Verify Gemini was called correctly
        mock_gemini_client.analyze_transcript.assert_called_once()
        call_args = mock_gemini_client.analyze_transcript.call_args
        assert call_args[0][0] == sample_transcript_txt
        assert call_args[0][1] == "text/plain"

    def test_process_transcript_pdf_success(
        self,
        client,
        mock_gemini_client,
        sample_gemini_response,
        sample_meeting_details,
        sample_transcript_pdf,
    ):
        """Test successful processing of PDF transcript"""
        # Setup mock
        mock_gemini_client.analyze_transcript.return_value = sample_gemini_response

        # Prepare request
        meeting_details_json = sample_meeting_details.model_dump_json()
        files = {
            "file": (
                "transcript.pdf",
                BytesIO(sample_transcript_pdf),
                "application/pdf",
            )
        }
        data = {"meeting_details": meeting_details_json}

        # Make request
        response = client.post(
            "/transcripts/process", files=files, data=data, headers=TEST_AUTH_HEADERS
        )

        # Assertions
        assert response.status_code == 200
        result = response.json()
        assert len(result["task_groups"]) == 1

        # Verify MIME type was correct
        call_args = mock_gemini_client.analyze_transcript.call_args
        assert call_args[0][1] == "application/pdf"

    def test_process_transcript_no_filename(self, client, sample_meeting_details):
        """Test error when no filename is provided"""
        meeting_details_json = sample_meeting_details.model_dump_json()

        # Create file with empty filename
        files = {"file": (None, BytesIO(b"content"), "text/plain")}
        data = {"meeting_details": meeting_details_json}

        response = client.post(
            "/transcripts/process", files=files, data=data, headers=TEST_AUTH_HEADERS
        )

        assert response.status_code == 422  # FastAPI validation error
        # Check that error relates to file or validation

    def test_process_transcript_invalid_file_type(self, client, sample_meeting_details):
        """Test error with invalid file type"""
        meeting_details_json = sample_meeting_details.model_dump_json()
        files = {
            "file": (
                "transcript.docx",
                BytesIO(b"content"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
        data = {"meeting_details": meeting_details_json}

        response = client.post(
            "/transcripts/process", files=files, data=data, headers=TEST_AUTH_HEADERS
        )

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_process_transcript_file_too_large(
        self, client, mock_settings, sample_meeting_details
    ):
        """Test error when file exceeds size limit"""
        # Create a file larger than max_file_size
        large_content = b"x" * (mock_settings.max_file_size + 1000)

        meeting_details_json = sample_meeting_details.model_dump_json()
        files = {"file": ("transcript.txt", BytesIO(large_content), "text/plain")}
        data = {"meeting_details": meeting_details_json}

        response = client.post(
            "/transcripts/process", files=files, data=data, headers=TEST_AUTH_HEADERS
        )

        assert response.status_code == 400
        assert "exceeds maximum limit" in response.json()["detail"]

    def test_process_transcript_invalid_meeting_details_json(
        self, client, sample_transcript_txt
    ):
        """Test error with invalid meeting details JSON"""
        files = {
            "file": ("transcript.txt", BytesIO(sample_transcript_txt), "text/plain")
        }
        data = {"meeting_details": "invalid json {"}

        response = client.post(
            "/transcripts/process", files=files, data=data, headers=TEST_AUTH_HEADERS
        )

        assert (
            response.status_code == 500
        )  # Pydantic validation error caught as generic error

    def test_process_transcript_gemini_failure(
        self, client, mock_gemini_client, sample_meeting_details, sample_transcript_txt
    ):
        """Test error handling when Gemini API fails"""
        # Setup mock to raise exception
        mock_gemini_client.analyze_transcript.side_effect = Exception(
            "Gemini API error"
        )

        meeting_details_json = sample_meeting_details.model_dump_json()
        files = {
            "file": ("transcript.txt", BytesIO(sample_transcript_txt), "text/plain")
        }
        data = {"meeting_details": meeting_details_json}

        response = client.post(
            "/transcripts/process", files=files, data=data, headers=TEST_AUTH_HEADERS
        )

        assert response.status_code == 500
        assert "Failed to process transcript" in response.json()["detail"]


# ==================== TESTS FOR GEMINI CLIENT ====================


class TestGeminiClientDependency:
    """Tests for get_gemini_client dependency function"""

    def test_get_gemini_client_creates_instance(self, mock_settings):
        """Test that dependency creates GeminiClient with correct settings"""
        from app.routers.transcript import get_gemini_client

        client = get_gemini_client(mock_settings)

        assert client is not None
        assert hasattr(client, "analyze_transcript")
