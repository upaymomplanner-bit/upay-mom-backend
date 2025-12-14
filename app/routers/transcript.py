from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from datetime import datetime, timezone
from app.schemas.transcript import (
    MeetingExtractionResult,
    MeetingDetails,
)

from app.services.planner.planner_service import MicrosoftPlannerService
from app.services.planner.dependencies import get_planner_service
from app.services.database.meeting_service import MeetingDatabaseService
from app.services.auth.deps import get_supabase_client

from app.services.gemini_client import GeminiClient
from app.services.file_processor import FileProcessor
from app.config import get_settings, Settings

transcript_router = APIRouter(prefix="/transcripts", tags=["transcripts"])


def get_gemini_client(settings: Settings = Depends(get_settings)) -> GeminiClient:
    """Dependency to get GeminiClient instance."""
    return GeminiClient(api_key=settings.gemini_api_key, model=settings.gemini_model)


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


@transcript_router.post("/upload_tasks", status_code=204)
async def upload_transcript_tasks(
    extracted_tasks: MeetingExtractionResult,
    planner_service: MicrosoftPlannerService = Depends(get_planner_service),
) -> None:
    """
    Upload extracted tasks from the transcript to Microsoft Planner

    Args:
        extracted_tasks: The structured tasks extracted from the transcript
        planner_service: Microsoft Planner service (injected)
    """

    try:
        await planner_service.add_tasks(extracted_tasks)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to upload tasks to Planner: {str(e)}"
        )


@transcript_router.post("/save", status_code=201)
async def save_transcript(
    extracted_tasks: MeetingExtractionResult,
    supabase_client=Depends(get_supabase_client),
    planner_service: MicrosoftPlannerService = Depends(get_planner_service),
):
    """
    Save meeting and tasks to database, then optionally upload to Microsoft Planner.

    This endpoint:
    1. Saves the meeting to the 'meetings' table
    2. Saves all tasks to the 'tasks' table
    3. Attempts to sync tasks to Microsoft Planner (non-blocking)

    Args:
        extracted_tasks: The meeting extraction result from Gemini
        supabase_client: Supabase client (injected)
        planner_service: Microsoft Planner service (injected)

    Returns:
        dict: Contains meeting_id and sync status
    """
    try:
        db_service = MeetingDatabaseService(supabase_client)

        # Save to database
        meeting_id = await db_service.save_meeting(extracted_tasks)

        # Extract year from meeting date or use current year
        year = datetime.now(timezone.utc).year
        if extracted_tasks.meeting_date:
            try:
                # Handle ISO format with potential Z
                dt = datetime.fromisoformat(
                    extracted_tasks.meeting_date.replace("Z", "+00:00")
                )
                year = dt.year
            except ValueError:
                pass

        task_ids = await db_service.save_tasks(
            meeting_id, extracted_tasks.task_groups, year=year
        )

        # Try to sync to Planner (non-blocking - errors are logged but not fatal)
        planner_sync_status = "success"
        planner_error = None

        try:
            await planner_service.add_tasks(extracted_tasks)
        except Exception as e:
            planner_sync_status = "failed"
            planner_error = str(e)
            # Log the error but don't fail the request
            print(f"Planner sync failed: {e}")

        return {
            "meeting_id": str(meeting_id),
            "task_count": len(task_ids),
            "planner_sync_status": planner_sync_status,
            "planner_error": planner_error,
            "message": "Meeting and tasks saved successfully"
            if planner_sync_status == "success"
            else "Meeting and tasks saved, but Planner sync failed",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save transcript: {str(e)}"
        )
