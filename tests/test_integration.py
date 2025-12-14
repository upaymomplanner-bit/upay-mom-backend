"""
Integration tests for complete workflows.
Tests end-to-end scenarios combining multiple endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO

from conftest import TEST_AUTH_HEADERS


class TestEndToEndFlow:
    """Integration tests for complete workflows"""

    def test_complete_workflow_process_and_save(
        self,
        client,
        mock_gemini_client,
        mock_supabase_client,
        mock_planner_service,
        sample_gemini_response,
        sample_meeting_details,
        sample_transcript_txt,
    ):
        """Test complete workflow: process transcript, then save"""
        # Step 1: Process transcript
        mock_gemini_client.analyze_transcript.return_value = sample_gemini_response

        meeting_details_json = sample_meeting_details.model_dump_json()
        files = {
            "file": ("transcript.txt", BytesIO(sample_transcript_txt), "text/plain")
        }
        data = {"meeting_details": meeting_details_json}

        process_response = client.post(
            "/transcripts/process", files=files, data=data, headers=TEST_AUTH_HEADERS
        )
        assert process_response.status_code == 200
        extraction_result = process_response.json()

        # Step 2: Save the result
        mock_db_service = MagicMock()
        mock_db_service.save_meeting = AsyncMock(return_value="meeting_final_123")
        mock_db_service.save_tasks = AsyncMock(return_value=["task_final_1"])

        with patch(
            "app.routers.transcript.MeetingDatabaseService",
            return_value=mock_db_service,
        ):
            save_response = client.post(
                "/transcripts/save", json=extraction_result, headers=TEST_AUTH_HEADERS
            )

        assert save_response.status_code == 201
        save_result = save_response.json()

        assert save_result["meeting_id"] == "meeting_final_123"
        assert save_result["planner_sync_status"] == "success"

    def test_complete_workflow_process_and_upload(
        self,
        client,
        mock_gemini_client,
        mock_planner_service,
        sample_gemini_response,
        sample_meeting_details,
        sample_transcript_txt,
    ):
        """Test complete workflow: process transcript, then upload to Planner"""
        # Step 1: Process transcript
        mock_gemini_client.analyze_transcript.return_value = sample_gemini_response

        meeting_details_json = sample_meeting_details.model_dump_json()
        files = {
            "file": ("transcript.txt", BytesIO(sample_transcript_txt), "text/plain")
        }
        data = {"meeting_details": meeting_details_json}

        process_response = client.post(
            "/transcripts/process", files=files, data=data, headers=TEST_AUTH_HEADERS
        )
        assert process_response.status_code == 200
        extraction_result = process_response.json()

        # Step 2: Upload to Planner
        upload_response = client.post(
            "/transcripts/upload_tasks",
            json=extraction_result,
            headers=TEST_AUTH_HEADERS,
        )
        assert upload_response.status_code == 204

        # Verify planner service was called
        mock_planner_service.add_tasks.assert_called_once()
