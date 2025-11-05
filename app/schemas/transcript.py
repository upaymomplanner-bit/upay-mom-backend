from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum


class TaskAssignment(BaseModel):
    """Assignment information for a task"""

    assignee_name: str = Field(..., description="Full name of the person assigned")
    assignee_email: str | None = Field(None, description="Email address if mentioned")

    @field_validator("assignee_name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return v.strip()


class CheckListItem(BaseModel):
    title: str = Field(..., description="Checklist item description")


class TaskPriority(str, Enum):
    """Priority levels for tasks (0-10 scale in Planner)"""

    URGENT = "1"
    IMPORTANT = "3"
    MEDIUM = "5"
    LOW = "9"


class TaskDetails(BaseModel):
    """Detailed information about a task extracted from the meeting"""

    description: str = Field(..., description="Detailed description of the task")
    checklist_items: list[CheckListItem] = Field(
        default_factory=list, description="Checklist items for the task"
    )


class TranscriptionTask(BaseModel):
    details: TaskDetails = Field(..., description="Details of the task")
    assignments: list[TaskAssignment] = Field(
        default_factory=list, description="People assigned to this task"
    )
    due_date: str | None = Field(
        None, description="Due date in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ"
    )
    title: str = Field(..., description="Clear, concise task title")
    startDateTime: str | None = Field(
        None, description="Start date in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ"
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM, description="Task priority level"
    )

    @field_validator("due_date", "startDateTime")
    @classmethod
    def validate_iso_date(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError(f"Date must be in ISO 8601 format: {v}")
        return v


class PlanAssociationType(str, Enum):
    """How the task relates to a plan"""

    EXISTING = "existing"  # Use an existing plan
    NEW = "new"  # Create a new plan


class PlanReference(BaseModel):
    """Reference to an existing plan"""

    plan_id: str = Field(..., description="ID of the existing plan")
    plan_title: str = Field(..., description="Title of the existing plan")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score for the match (0.0 to 1.0)"
    )


class PlanAssociation(BaseModel):
    """Associates tasks with a plan (existing or new)"""

    association_type: PlanAssociationType = Field(
        ..., description="Whether to use existing plan or create new one"
    )
    plan_title: str = Field(
        ..., description="Title for new plan OR matched title for existing plan"
    )
    plan_reference: PlanReference | None = Field(
        None,
        description="Reference to existing plan (required if association_type is 'existing')",
    )
    rationale: str | None = Field(
        None,
        description="Explanation for why this plan was chosen or should be created",
    )

    @field_validator("plan_reference")
    @classmethod
    def validate_plan_reference(
        cls, v: PlanReference | None, info
    ) -> PlanReference | None:
        association_type = info.data.get("association_type")
        if association_type == PlanAssociationType.EXISTING and v is None:
            raise ValueError(
                "plan_reference is required when association_type is 'existing'"
            )
        if association_type == PlanAssociationType.NEW and v is not None:
            raise ValueError(
                "plan_reference should not be set when association_type is 'new'"
            )
        return v


class TaskGroup(BaseModel):
    """Group of related tasks associated with a plan"""

    plan_association: PlanAssociation = Field(
        ..., description="Plan to associate these tasks with"
    )
    tasks: list[TranscriptionTask] = Field(
        ..., min_length=1, description="list of tasks in this group"
    )
    group_description: str | None = Field(
        None, description="Context about why these tasks are grouped together"
    )


class MeetingDetails(BaseModel):
    """Metadata about the meeting transcript"""

    meeting_title: str | None = Field(
        None, description="Title or subject of the meeting"
    )
    meeting_date: str | None = Field(
        None, description="Date of the meeting in ISO 8601 format"
    )


class GeminiExtractionResponse(BaseModel):
    """Raw response from Gemini API for transcript analysis"""

    task_groups: list[TaskGroup] = Field(
        default_factory=list, description="Groups of tasks associated with plans"
    )
    meeting_summary: str | None = Field(
        None, description="Brief summary of the meeting"
    )


class MeetingExtractionResult(BaseModel):
    """Complete extraction result from meeting transcription"""

    meeting_details: MeetingDetails = Field(
        ..., description="Metadata about the meeting"
    )
    task_groups: list[TaskGroup] = Field(
        ..., description="Groups of tasks associated with plans"
    )
    action_items_count: int = Field(
        0, description="Total number of action items extracted from the meeting"
    )
    meeting_date: str | None = Field(
        None, description="Date of the meeting in ISO 8601 format"
    )
    meeting_summary: str | None = Field(
        None, description="Brief summary of the meeting"
    )

    # TODO: Discuss if the following fields are relevant and need to be discussed:
    # participants: list[str] = Field(
    #     default_factory=list, description="list of meeting participants mentioned"
    # )
    # key_decisions: list[str] = Field(
    #     default_factory=list, description="Important decisions made during the meeting"
    # )

    @field_validator("meeting_date")
    @classmethod
    def validate_meeting_date(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError(f"Meeting date must be in ISO 8601 format: {v}")
        return v

    def model_post_init(self, __context) -> None:
        """Calculate total action items after initialization"""
        total = 0
        for group in self.task_groups:
            total += len(group.tasks)
        self.action_items_count = total
