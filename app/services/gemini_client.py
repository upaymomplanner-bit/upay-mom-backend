from google import genai
from google.genai import types
from pydantic import ValidationError

from app.schemas.transcript import GeminiExtractionResponse


class GeminiClient:
    """Reusable client for interacting with Google Gemini API."""

    def __init__(self, model: str = "gemini-2.5-flash") -> None:
        """Initialize Gemini client with API key and model configuration."""
        self.client = genai.Client()
        self.model = model

    def get_system_prompt(self) -> str:
        """
        Get the system prompt for transcript analysis.
        This prompt instructs Gemini to extract structured information from meeting transcripts.
        """
        return """You are an expert meeting transcript analyst. Your task is to analyze meeting transcripts and extract structured information.

Analyze the provided transcript and extract the following information in a structured JSON format:

1. **meeting_title**: A concise title for the meeting based on the content
2. **meeting_date**: The date of the meeting if mentioned (format: YYYY-MM-DD)
3. **participants**: List of meeting participants with their names and roles (if mentioned)
4. **summary**: A comprehensive summary of the meeting (2-3 paragraphs)
5. **key_topics**: List of main topics discussed
6. **action_items**: List of action items with:
   - task: Description of the task
   - assignee: Person responsible (if mentioned)
   - due_date: Deadline (if mentioned)
   - priority: High/Medium/Low (if mentioned or inferred)
7. **decisions**: List of decisions made with description and rationale
8. **next_steps**: Overall next steps or follow-up actions

Return ONLY a valid JSON object matching this structure. Do not include any markdown formatting or code blocks.

Example JSON structure:
{
    "meeting_title": "Q4 Product Planning Meeting",
    "meeting_date": "2025-10-31",
    "participants": [
        {"name": "John Doe", "role": "Product Manager"},
        {"name": "Jane Smith", "role": "Engineer"}
    ],
    "summary": "The team discussed the Q4 product roadmap...",
    "key_topics": ["Product roadmap", "Budget allocation", "Team resources"],
    "action_items": [
        {
            "task": "Prepare budget proposal",
            "assignee": "John Doe",
            "due_date": "2025-11-15",
            "priority": "High"
        }
    ],
    "decisions": [
        {
            "description": "Approved new feature development",
            "rationale": "High customer demand and competitive advantage"
        }
    ],
    "next_steps": "Follow up on action items in next week's meeting"
}"""

    async def analyze_transcript(
        self, file_data: bytes, mime_type: str
    ) -> GeminiExtractionResponse:
        """
        Analyze transcript file using Gemini API and return structured output.
        Gemini handles file content extraction directly (supports PDF, TXT, etc.)

        Args:
            file_data: Raw file bytes
            mime_type: MIME type of the file (e.g., 'application/pdf', 'text/plain')

        Returns:
            TranscriptAnalysis: Structured analysis of the transcript

        Raises:
            Exception: If API call fails or response parsing fails
        """
        try:
            # Upload file to Gemini (Gemini will handle text extraction)

            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(data=file_data, mime_type=mime_type),
                    "List a few popular cookie recipes, and include the amounts of ingredients.",
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiExtractionResponse,
                    system_instruction=self.get_system_prompt(),
                ),
            )

            response_text = response.text

            if response_text is None:
                raise Exception(
                    "Gemini response parsing returned None for transcript analysis"
                )

            response_parsed: GeminiExtractionResponse = (
                GeminiExtractionResponse.model_validate_json(response_text)
            )
            return response_parsed

        except ValidationError as e:
            raise Exception(f"Failed to parse Gemini response as JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to analyze transcript with Gemini: {str(e)}")
