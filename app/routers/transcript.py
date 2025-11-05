from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from datetime import datetime
from app.schemas.transcript import (
    MeetingExtractionResult,
    MeetingDetails,
)
from app.services.gemini_client import GeminiClient
from app.services.file_processor import FileProcessor
from app.config import get_settings, Settings

transcript_router = APIRouter(prefix="/transcripts", tags=["transcripts"])


def get_gemini_client(settings: Settings = Depends(get_settings)) -> GeminiClient:
    """Dependency to get GeminiClient instance."""
    return GeminiClient(model=settings.gemini_model)


@transcript_router.post("/process", response_model=MeetingExtractionResult)
async def process_transcript(
    file: UploadFile = File(..., description="Transcript file (.txt or .pdf)"),
    meeting_details: str = Form(..., description="JSON string with meeting details"),
    settings: Settings = Depends(get_settings),
    gemini_client: GeminiClient = Depends(get_gemini_client),
) -> MeetingExtractionResult:
    """
    Process a transcript file and extract structured information using Gemini AI.

    This endpoint accepts either a .txt or .pdf file containing a meeting transcript,
    sends it directly to the Gemini API for analysis (Gemini handles text extraction),
    and returns structured information including:
    - Meeting summary
    - Participants
    - Key topics discussed
    - Action items
    - Decisions made
    - Next steps

    Args:
        file: The uploaded transcript file (.txt or .pdf)
        settings: Application settings (injected)
        gemini_client: Gemini API client (injected)

    Returns:
        TranscriptProcessResponse: Structured analysis of the transcript

    Raises:
        HTTPException: If file validation fails or processing errors occur
    """
    try:
        details = MeetingDetails.model_validate_json(meeting_details)
        # Validate file
        FileProcessor.validate_file(file, settings.max_file_size)

        # Read file contents
        file_contents = await file.read()
        file_size = len(file_contents)

        # Get MIME type (validation ensures filename is not None)
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        mime_type = FileProcessor.get_mime_type(file.filename)

        if file_size > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum limit of {settings.max_file_size} bytes",
            )

        # Analyze transcript with Gemini (Gemini handles text extraction from PDF/TXT)
        analysis = await gemini_client.analyze_transcript(file_contents, mime_type)

        # Combine results
        result = MeetingExtractionResult(
            meeting_details=details,
            task_groups=analysis.task_groups,
            meeting_summary=analysis.meeting_summary,
            meeting_date=details.meeting_date,
            action_items_count=0,
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process transcript: {str(e)}"
        )
