import pytest
import os
import json
from app.schemas.transcript import MeetingDetails

@pytest.mark.asyncio
async def test_live_process_transcript(live_client):
    # Prepare request data
    meeting_details = MeetingDetails(
        meeting_date="2023-10-27T10:00:00Z",
        meeting_type="Live Test Meeting",
        attendees=["Alice", "Bob"]
    )

    # Use the PDF file
    pdf_path = "tests/sample_transcript.pdf"
    if not os.path.exists(pdf_path):
        pytest.skip(f"PDF file not found at {pdf_path}")

    with open(pdf_path, "rb") as f:
        files = {"file": ("sample_transcript.pdf", f, "application/pdf")}
        data = {"meeting_details": meeting_details.model_dump_json()}

        response = live_client.post("/transcripts/process", files=files, data=data)

    if response.status_code != 200:
        pytest.fail(f"Error Response: {response.text}")

    assert response.status_code == 200
    result = response.json()

    # Save output to file
    with open("gemini_output.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\nSaved Gemini output to gemini_output.json")

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
