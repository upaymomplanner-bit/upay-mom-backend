import pytest
from unittest.mock import AsyncMock
from app.schemas.transcript import GeminiExtractionResponse, MeetingDetails

@pytest.mark.asyncio
async def test_process_transcript(client, mock_gemini_client):
    # Setup mock response
    mock_response = GeminiExtractionResponse(
        task_groups=[],
        meeting_summary="Test summary"
    )
    mock_gemini_client.analyze_transcript.return_value = mock_response

    # Prepare request data
    meeting_details = MeetingDetails(
        meeting_date="2023-10-27T10:00:00Z",
        meeting_type="Test Meeting",
        attendees=["Alice", "Bob"]
    )

    files = {"file": ("test.txt", b"test content", "text/plain")}
    data = {"meeting_details": meeting_details.model_dump_json()}

    response = client.post("/transcripts/process", files=files, data=data)

    assert response.status_code == 200
    result = response.json()
    assert result["meeting_summary"] == "Test summary"
    assert result["meeting_date"] == "2023-10-27T10:00:00Z"
    assert result["task_groups"] == []

@pytest.mark.asyncio
async def test_upload_tasks(client, mock_planner_service):
    # Prepare request data
    extraction_result = {
        "meeting_details": {
             "meeting_date": "2023-10-27T10:00:00Z",
             "meeting_type": "Test Meeting",
             "attendees": ["Alice", "Bob"]
        },
        "task_groups": [],
        "meeting_summary": "Test summary",
        "meeting_date": "2023-10-27T10:00:00Z",
        "action_items_count": 0
    }

    response = client.post("/transcripts/upload_tasks", json=extraction_result)

    assert response.status_code == 204
    mock_planner_service.add_tasks.assert_called_once()
