from google import genai
from google.genai import types
from pydantic import ValidationError

from app.schemas.transcript import GeminiExtractionResponse


class GeminiClient:
    """Reusable client for interacting with Google Gemini API."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        """Initialize Gemini client with API key and model configuration."""
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def get_system_prompt(self) -> str:
        """
        Get the system prompt for transcript analysis.
        This prompt instructs Gemini to extract structured information from meeting transcripts.
        """
        return """You are an expert meeting transcription analysis AI. Your task is to process a given meeting transcript and generate a structured JSON output. The output must strictly adhere to the provided JSON schema.

**Instructions:**

1.  **Analyze the Transcript:** Thoroughly read the entire transcript to understand the key discussion points, decisions, and action items.

2.  **Generate Meeting Summary:** Create a concise, factual summary of the meeting's purpose and key discussions. This will populate the `meeting_summary` field.

3.  **Identify and Group Tasks:**
    *   Identify all clear, actionable tasks mentioned during the meeting.
    *   Group related tasks under a common theme or project. Each theme will be an object in the `task_groups` array.
    *   For each group, provide a brief `group_description`.
    *   The `plan_association` object is for linking to plans. For this exercise, you can create a placeholder `plan_title` based on the group's theme and leave other fields in `plan_reference` as placeholders or derived from the title. Set `confidence_score` to whatever you deem appropriate. The `rationale` should briefly explain why the tasks are grouped. In case the user sends any existing plans as input, evaluate if the group matches with any of these plans and give appopriate confidence score. If this score is below 0.5, then create a new plan that best fits the task group and set the confidence score to 1. The reference field is not needed if you create new plan. Otherwise reference the existing plan and fill out necessary details.

4.  **Extract Detailed Task Information for Each Task:**
    *   **title**: A concise, action-oriented title.
    *   **description**: A detailed description of the task based on the conversation.
    *   **assignments**: Identify the person(s) or team(s) responsible. Populate the `assignee_name`. If no email is available, use `null`. If no one is assigned, the array can be empty.
    *   **due_date**: Extract any specified deadline. Use the meeting date present in the transcript as a reference for relative terms like "this week" or "next month". Format as "YYYY-MM-DD". If no date is mentioned, use `null`.
    *   **checklist_items**: If the conversation breaks the task down into smaller, distinct steps, list them here.
    *   **priority**: Set task priority depending on urgency or importance mentioned in the transcript. Use 1 for urgent, 3 for high, 5 for medium, and 9 for low. If no priority is mentioned, use a default value of "5".
    *   **startDateTime**: Use the meeting date "2025-09-04T09:38:00Z" as the default start time unless otherwise specified.

5.  **Output Format:**
    *   Generate a single JSON object as the final output.
    *   Do not add any explanations or text outside of the JSON object.
    *   Ensure the output is a valid JSON that perfectly matches the required schema. Do not invent information not present in the transcript.

```json
{
  "task_groups": [
    {
      "plan_association": {
        "association_type": "existing",
        "plan_title": "Data and Document Management Improvement",
        "plan_reference": {
          "plan_id": "DM-001",
          "plan_title": "Data and Document Management Improvement",
          "confidence_score": 1
        },
        "rationale": "Multiple tasks were discussed to centralize and streamline the organization's data and document handling processes."
      },
      "tasks": [
        {
          "details": {
            "description": "Create a comprehensive and centralized list of all program and support documents. This list should specify where each document is maintained (center, zonal, central), its format (hard/soft copy), update frequency, and the last updated date.",
            "checklist_items": [
              {
                "title": "Identify all existing documents across departments."
              },
              {
                "title": "Log the location and format for each document."
              },
              {
                "title": "Define and record the update frequency and last updated date."
              }
            ]
          },
          "assignments": [
            {
              "assignee_name": "Program Support Team (Pankaj, Friends, Yashvi, Sneh)",
              "assignee_email": null
            }
          ],
          "due_date": "2025-09-12",
          "title": "Compile Centralized List of All Documents",
          "startDateTime": "2025-09-04T09:38:00Z",
          "priority": "5"
        },
        {
          "details": {
            "description": "Establish a system to maintain all collaboration data, including MOUs, partnerships, and activities, in a centralized location. The goal is to move away from scattered sheets to a single, common Google Sheet for better tracking and reporting.",
            "checklist_items": []
          },
          "assignments": [
            {
              "assignee_name": "Executive Director (review process)",
              "assignee_email": null
            }
          ],
          "due_date": null,
          "title": "Centralize Collaboration and Partnership Data",
          "startDateTime": "2025-09-04T09:38:00Z",
          "priority": "5"
        },
        {
          "details": {
            "description": "The monthly MIS report for program support was not submitted for the last month. The report needs to be completed and mailed.",
            "checklist_items": []
          },
          "assignments": [
            {
              "assignee_name": "Program Support Team",
              "assignee_email": null
            }
          ],
          "due_date": null,
          "title": "Submit Monthly MIS Report for Program Support",
          "startDateTime": "2025-09-04T09:38:00Z",
          "priority": "5"
        }
      ],
      "group_description": "Tasks related to improving the structure, accessibility, and accuracy of organizational documents and data."
    },
    {
      "plan_association": {
        "association_type": "existing",
        "plan_title": "Outreach and Volunteer Management",
        "plan_reference": {
          "plan_id": "OVM-001",
          "plan_title": "Outreach and Volunteer Management",
          "confidence_score": 1
        },
        "rationale": "Tasks focused on analyzing volunteer data and improving outreach strategies to boost engagement."
      },
      "tasks": [
        {
          "details": {
            "description": "Analyze volunteer data from April to August to identify the 3-4 zones with the lowest conversion rates. Investigate the reasons for the low conversion and prepare to discuss potential outreach activities to improve performance.",
            "checklist_items": [
              {
                "title": "Pull volunteer conversion data from April to August 2025."
              },
              {
                "title": "Identify the 3-4 zones with the lowest conversion percentages."
              },
              {
                "title": "Investigate potential reasons for low performance in those zones."
              }
            ]
          },
          "assignments": [
            {
              "assignee_name": "Yash",
              "assignee_email": null
            }
          ],
          "due_date": null,
          "title": "Analyze and Report on Low Volunteer Conversion Zones",
          "startDateTime": "2025-09-04T09:38:00Z",
          "priority": "5"
        }
      ],
      "group_description": "Strategic tasks to analyze volunteer data and improve outreach effectiveness."
    },
    {
      "plan_association": {
        "association_type": "existing",
        "plan_title": "HR and Team Coordination",
        "plan_reference": {
          "plan_id": "HR-001",
          "plan_title": "HR and Team Coordination",
          "confidence_score": 1
        },
        "rationale": "Tasks related to internal team meetings and coordination."
      },
      "tasks": [
        {
          "details": {
            "description": "Arrange a meeting for all full-time associates with the Director of HR. This meeting is to be held every alternate month to discuss challenges and HR-related issues.",
            "checklist_items": []
          },
          "assignments": [
            {
              "assignee_name": "Operations Manager",
              "assignee_email": null
            }
          ],
          "due_date": null,
          "title": "Schedule Bi-Monthly Meeting for Full-Time Associates",
          "startDateTime": "2025-09-04T09:38:00Z",
          "priority": "5"
        }
      ],
      "group_description": "Tasks focused on internal team management and communication."
    }
  ],
  "meeting_summary": "The meeting focused on streamlining data and document management within UPAY. Key issues discussed included the lack of centralized access to documents, inconsistent data maintenance, and the need for a better system for tracking collaborations and partnerships. Action items include creating a centralized document list, consolidating collaboration data, and analyzing volunteer conversion rates to improve outreach. The team also decided to implement regular bi-monthly meetings for all full-time associates to address challenges."
}
```"""

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
                    "Create tasks based on the attached file and make sure to extract relevant information only",
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
