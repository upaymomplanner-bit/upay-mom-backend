"""
Database service for meeting and task persistence.
"""
from supabase import AsyncClient
from datetime import datetime
from uuid import UUID, uuid4
from typing import List, Dict, Any, Optional

from app.schemas.transcript import MeetingExtractionResult, TaskGroup, TranscriptionTask


class MeetingDatabaseService:
    """Service for saving meetings and tasks to Supabase."""

    def __init__(self, supabase_client: AsyncClient):
        self.client = supabase_client

    async def save_meeting(
        self,
        meeting_result: MeetingExtractionResult,
        host_id: Optional[UUID] = None
    ) -> UUID:
        """
        Save meeting to the meetings table.

        Args:
            meeting_result: The extracted meeting data from Gemini
            host_id: Optional host user ID

        Returns:
            UUID of the created meeting
        """
        meeting_id = uuid4()

        meeting_data = {
            "id": str(meeting_id),
            "title": meeting_result.meeting_details.meeting_title or "Untitled Meeting",
            "date": meeting_result.meeting_details.meeting_date,
            "summary": meeting_result.meeting_summary,
            "transcript_path": None,  # Can be added later if storing files
            "host_id": str(host_id) if host_id else None,
            "status": "completed",  # Processing is complete
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        result = await self.client.table("meetings").insert(meeting_data).execute()

        if not result.data:
            raise Exception("Failed to insert meeting into database")

        return meeting_id

    async def save_tasks(
        self,
        meeting_id: UUID,
        task_groups: List[TaskGroup],
        year: int = datetime.utcnow().year,
    ) -> List[UUID]:
        """
        Save tasks to the tasks table.

        Args:
            meeting_id: UUID of the parent meeting
            task_groups: List of task groups from Gemini extraction
            year: Year for the goals (default: current year)

        Returns:
            List of created task UUIDs
        """
        task_ids = []

        for task_group in task_groups:
            # Create goal for this task group
            goal_id = await self._save_goal(task_group, year)

            for task in task_group.tasks:
                task_id = await self._save_single_task(
                    meeting_id=meeting_id,
                    task=task,
                    plan_title=task_group.plan_association.plan_title,
                    goal_id=goal_id
                )
                task_ids.append(task_id)

        return task_ids

    async def _save_goal(self, task_group: TaskGroup, year: int) -> UUID:
        """Save a task group as a goal."""
        goal_id = uuid4()

        goal_data = {
            "id": str(goal_id),
            "title": task_group.plan_association.plan_title,
            "description": task_group.group_description,
            "year": year,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        result = await self.client.table("goals").insert(goal_data).execute()

        if not result.data:
            raise Exception(f"Failed to insert goal '{task_group.plan_association.plan_title}' into database")

        return goal_id

    async def _save_single_task(
        self,
        meeting_id: UUID,
        task: TranscriptionTask,
        plan_title: str,
        goal_id: Optional[UUID] = None,
    ) -> UUID:
        """Save a single task to the database."""
        task_id = uuid4()

        # Map priority string to database format
        priority_map = {
            "1": "urgent",
            "3": "important",
            "5": "medium",
            "9": "low"
        }
        priority = priority_map.get(task.priority, "medium")

        task_data = {
            "id": str(task_id),
            "title": task.title,
            "description": task.details.description,
            "status": "todo",  # Default status
            "priority": priority,
            "due_date": task.due_date,
            "meeting_id": str(meeting_id),
            "assignee_id": None,  # Skipping assignee matching for now
            "department_id": None,  # Can be added later
            "planner_task_id": None,  # Will be updated after Planner sync
            "planner_plan_id": None,  # Can be updated after Planner sync
            "goal_id": str(goal_id) if goal_id else None,
            "metadata": {
                "plan_title": plan_title,
                "assignee_names": [a.assignee_name for a in task.assignments] if task.assignments else [],
                "checklist_items": [
                    {"title": item.title} for item in task.details.checklist_items
                ] if task.details.checklist_items else []
            },
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        result = await self.client.table("tasks").insert(task_data).execute()

        if not result.data:
            raise Exception(f"Failed to insert task '{task.title}' into database")

        return task_id

    async def update_task_planner_id(
        self,
        task_id: UUID,
        planner_task_id: str,
        planner_plan_id: Optional[str] = None
    ) -> None:
        """Update task with Planner sync information."""
        update_data = {
            "planner_task_id": planner_task_id,
            "updated_at": datetime.utcnow().isoformat(),
        }

        if planner_plan_id:
            update_data["planner_plan_id"] = planner_plan_id

        await self.client.table("tasks").update(update_data).eq("id", str(task_id)).execute()
