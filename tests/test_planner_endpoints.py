"""
Unit tests for Planner-related endpoints.
Tests the /transcripts/upload_tasks and /transcripts/save endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from conftest import TEST_AUTH_HEADERS


# ==================== TESTS FOR /upload_tasks ENDPOINT ====================


class TestUploadTranscriptTasks:
    """Tests for POST /transcripts/upload_tasks endpoint"""

    def test_upload_tasks_success(
        self, client, mock_planner_service, sample_meeting_extraction
    ):
        """Test successful task upload to Microsoft Planner"""
        # Setup mock
        mock_planner_service.add_tasks.return_value = None

        # Make request
        response = client.post(
            "/transcripts/upload_tasks",
            json=sample_meeting_extraction.model_dump(mode="json"),
            headers=TEST_AUTH_HEADERS,
        )

        # Assertions
        assert response.status_code == 204
        assert response.content == b""

        # Verify planner service was called
        mock_planner_service.add_tasks.assert_called_once()
        call_args = mock_planner_service.add_tasks.call_args[0][0]
        assert call_args.meeting_details.meeting_title == "Sprint Planning Q1 2025"

    def test_upload_tasks_value_error(
        self, client, mock_planner_service, sample_meeting_extraction
    ):
        """Test handling of ValueError from planner service"""
        # Setup mock to raise ValueError
        mock_planner_service.add_tasks.side_effect = ValueError("Invalid task data")

        response = client.post(
            "/transcripts/upload_tasks",
            json=sample_meeting_extraction.model_dump(mode="json"),
            headers=TEST_AUTH_HEADERS,
        )

        assert response.status_code == 400
        assert "Invalid task data" in response.json()["detail"]

    def test_upload_tasks_planner_service_error(
        self, client, mock_planner_service, sample_meeting_extraction
    ):
        """Test handling of generic planner service error"""
        # Setup mock to raise exception
        mock_planner_service.add_tasks.side_effect = Exception(
            "Planner API unavailable"
        )

        response = client.post(
            "/transcripts/upload_tasks",
            json=sample_meeting_extraction.model_dump(mode="json"),
            headers=TEST_AUTH_HEADERS,
        )

        assert response.status_code == 500
        assert "Failed to upload tasks to Planner" in response.json()["detail"]

    def test_upload_tasks_invalid_payload(self, client):
        """Test upload with invalid request payload"""
        response = client.post(
            "/transcripts/upload_tasks",
            json={"invalid": "data"},
            headers=TEST_AUTH_HEADERS,
        )

        assert response.status_code == 422  # Validation error


# ==================== TESTS FOR /save ENDPOINT ====================


class TestSaveTranscript:
    """Tests for POST /transcripts/save endpoint"""

    def test_save_transcript_success(
        self,
        client,
        mock_supabase_client,
        mock_planner_service,
        sample_meeting_extraction,
    ):
        """Test successful save of transcript to database and Planner sync"""
        # Setup mocks
        mock_db_service = MagicMock()
        mock_db_service.save_meeting = AsyncMock(return_value="meeting_uuid_123")
        mock_db_service.save_tasks = AsyncMock(return_value=["task_1", "task_2"])
        mock_planner_service.add_tasks.return_value = None

        with patch(
            "app.routers.transcript.MeetingDatabaseService",
            return_value=mock_db_service,
        ):
            response = client.post(
                "/transcripts/save",
                json=sample_meeting_extraction.model_dump(mode="json"),
                headers=TEST_AUTH_HEADERS,
            )

        # Assertions
        assert response.status_code == 201
        result = response.json()

        assert result["meeting_id"] == "meeting_uuid_123"
        assert result["task_count"] == 2
        assert result["planner_sync_status"] == "success"
        assert result["planner_error"] is None
        assert "saved successfully" in result["message"]

        # Verify database calls
        mock_db_service.save_meeting.assert_called_once()
        mock_db_service.save_tasks.assert_called_once()

        # Verify planner sync was attempted
        mock_planner_service.add_tasks.assert_called_once()

    def test_save_transcript_with_planner_sync_failure(
        self,
        client,
        mock_supabase_client,
        mock_planner_service,
        sample_meeting_extraction,
    ):
        """Test save succeeds even when Planner sync fails (non-blocking)"""
        # Setup mocks
        mock_db_service = MagicMock()
        mock_db_service.save_meeting = AsyncMock(return_value="meeting_uuid_456")
        mock_db_service.save_tasks = AsyncMock(return_value=["task_1"])
        mock_planner_service.add_tasks.side_effect = Exception("Planner unavailable")

        with patch(
            "app.routers.transcript.MeetingDatabaseService",
            return_value=mock_db_service,
        ):
            response = client.post(
                "/transcripts/save",
                json=sample_meeting_extraction.model_dump(mode="json"),
                headers=TEST_AUTH_HEADERS,
            )

        # Assertions
        assert response.status_code == 201
        result = response.json()

        assert result["meeting_id"] == "meeting_uuid_456"
        assert result["task_count"] == 1
        assert result["planner_sync_status"] == "failed"
        assert "Planner unavailable" in result["planner_error"]
        assert "Planner sync failed" in result["message"]

        # Database operations should still succeed
        mock_db_service.save_meeting.assert_called_once()
        mock_db_service.save_tasks.assert_called_once()

    def test_save_transcript_database_error(
        self, client, mock_supabase_client, sample_meeting_extraction
    ):
        """Test error handling when database save fails"""
        # Setup mock to fail
        mock_db_service = MagicMock()
        mock_db_service.save_meeting = AsyncMock(
            side_effect=Exception("Database connection failed")
        )

        with patch(
            "app.routers.transcript.MeetingDatabaseService",
            return_value=mock_db_service,
        ):
            response = client.post(
                "/transcripts/save",
                json=sample_meeting_extraction.model_dump(mode="json"),
                headers=TEST_AUTH_HEADERS,
            )

        assert response.status_code == 500
        assert "Failed to save transcript" in response.json()["detail"]

    def test_save_transcript_year_extraction(
        self, client, mock_supabase_client, sample_meeting_extraction
    ):
        """Test that year is correctly extracted from meeting date"""
        # Setup mocks
        mock_db_service = MagicMock()
        mock_db_service.save_meeting = AsyncMock(return_value="meeting_uuid_789")
        mock_db_service.save_tasks = AsyncMock(return_value=[])

        # Meeting with specific date
        sample_meeting_extraction.meeting_date = "2024-06-15T14:30:00Z"

        with patch(
            "app.routers.transcript.MeetingDatabaseService",
            return_value=mock_db_service,
        ):
            response = client.post(
                "/transcripts/save",
                json=sample_meeting_extraction.model_dump(mode="json"),
                headers=TEST_AUTH_HEADERS,
            )

        assert response.status_code == 201

        # Verify save_tasks was called with correct year
        call_args = mock_db_service.save_tasks.call_args
        assert call_args[1]["year"] == 2024

    def test_save_transcript_no_meeting_date(
        self, client, mock_supabase_client, sample_meeting_extraction
    ):
        """Test that current year is used when no meeting date provided"""
        # Setup mocks
        mock_db_service = MagicMock()
        mock_db_service.save_meeting = AsyncMock(return_value="meeting_uuid_999")
        mock_db_service.save_tasks = AsyncMock(return_value=[])

        # Remove meeting date
        sample_meeting_extraction.meeting_date = None

        with patch(
            "app.routers.transcript.MeetingDatabaseService",
            return_value=mock_db_service,
        ):
            response = client.post(
                "/transcripts/save",
                json=sample_meeting_extraction.model_dump(mode="json"),
                headers=TEST_AUTH_HEADERS,
            )

        assert response.status_code == 201

        # Verify save_tasks was called with current year (2025 as per context)
        call_args = mock_db_service.save_tasks.call_args
        assert call_args[1]["year"] == 2025
