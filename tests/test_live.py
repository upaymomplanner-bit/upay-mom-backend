import pytest
from app.schemas.transcript import MeetingDetails

@pytest.mark.asyncio
async def test_live_process_transcript(live_client):
    # Prepare request data
    meeting_details = MeetingDetails(
        meeting_date="2023-10-27T10:00:00Z",
        meeting_type="Live Test Meeting",
        attendees=["Alice", "Bob"]
    )

    # Use a real file (we will create this)
    with open("tests/sample_transcript.txt", "rb") as f:
        files = {"file": ("sample_transcript.txt", f, "text/plain")}
        data = {"meeting_details": meeting_details.model_dump_json()}

        response = live_client.post("/transcripts/process", files=files, data=data)

    if response.status_code != 200:
        pytest.fail(f"Error Response: {response.text}")

    assert response.status_code == 200
    result = response.json()

    # Basic validation of structure
    assert "meeting_summary" in result
    assert "task_groups" in result
    assert result["meeting_date"] == "2023-10-27T10:00:00Z"

    # Print result for manual inspection if needed
    print("\nLive Gemini Response Summary:", result["meeting_summary"])

# NOTE: We are skipping the upload_tasks test by default to avoid creating junk in Planner
# Uncomment to run if you really want to test Planner creation
# @pytest.mark.asyncio
# async def test_live_upload_tasks(live_client):
#     ...
