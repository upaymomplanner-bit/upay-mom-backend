from fastapi import HTTPException
import logging
from ...schemas.transcript import MeetingExtractionResult, TaskPriority
from app.services.planner.planner_plan_service import PlannerPlanService
from app.services.planner.planner_task_service import PlannerTaskService
from app.services.auth.deps import get_supabase_client
from typing import Optional

log = logging.getLogger(__name__)


class MicrosoftPlannerService:
    """
    Orchestrator service for Microsoft Planner operations.
    Coordinates interactions between plan and task services.
    """

    def __init__(
        self,
        plan_service: Optional[PlannerPlanService] = None,
        task_service: Optional[PlannerTaskService] = None,
    ):
        self.plan_service = plan_service
        self.task_service = task_service

    def _map_priority(self, priority: TaskPriority) -> str:
        mapping = {
            TaskPriority.URGENT: "urgent",
            TaskPriority.IMPORTANT: "important",
            TaskPriority.MEDIUM: "medium",
            TaskPriority.LOW: "low",
        }
        return mapping.get(priority, "medium")

    async def add_tasks(
        self,
        meeting_tasks: MeetingExtractionResult,
    ) -> None:
        """
        Add tasks extracted from meeting transcripts to Microsoft Planner.
        Orchestrates the workflow of creating/getting plans and adding tasks.

        Args:
            meeting_tasks: The structured tasks extracted from the meeting transcript
        """
        if not self.plan_service or not self.task_service:
            log.warning("Planner services not available. Skipping add_tasks.")
            return

        log.info("Starting add_tasks operation")
        try:
            supabase = await get_supabase_client()

            # TODO: Discuss with UPAY team whether meetings tend to discuss tasks within same project or other way around and then parallelize according to those needs.
            for task_group in meeting_tasks.task_groups:
                plan_id = await self.plan_service.get_or_create_plan(
                    task_group.plan_association
                )

                # Insert plan into DB (upsert)
                # Assuming 'plans' table exists or using 'planner_plan_id' in tasks table directly.
                # The schema provided has 'planner_plan_id' in 'tasks' table, but no 'plans' table in the provided schema snippet?
                # Wait, the schema provided:
                # CREATE TABLE tasks (... planner_plan_id TEXT ... );
                # It does NOT show a 'plans' table. It shows 'goals', 'meetings', 'departments'.
                # So I will NOT insert into a 'plans' table as it wasn't in the provided schema.
                # I will just use plan_id for the task.

                for task in task_group.tasks:
                    task_id = await self.task_service.add_task(task, plan_id)
                    await self.task_service.add_task_details(
                        task_id,
                        description=task.details.description or "",
                        checklist_items=task.details.checklist_items or [],
                    )

                    # Insert task into DB
                    log.info(f"Inserting task {task.title} into database")
                    task_data = {
                        "title": task.title,
                        "description": task.details.description,
                        "status": "todo",
                        "priority": self._map_priority(task.priority),
                        "due_date": task.due_date,
                        "planner_task_id": task_id,
                        "planner_plan_id": plan_id,
                        # "meeting_id": meeting_tasks.meeting_details.meeting_id # Not available in MeetingDetails schema?
                        # "assignee_id": ... # Complex lookup, skipping for now as per plan
                    }

                    # Remove None values to let DB defaults handle them or to avoid errors if columns are not nullable but have defaults
                    task_data = {k: v for k, v in task_data.items() if v is not None}

                    await supabase.table("tasks").insert(task_data).execute()
                    log.info(f"Successfully inserted task {task.title}")

        except Exception as e:
            log.error(f"Error in add_tasks: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

        log.info("Completed add_tasks operation")

    async def get_task(self, task_id: str) -> dict:
        log.info(f"Fetching task with id {task_id}")
        try:
            supabase = await get_supabase_client()
            response = (
                await supabase.table("tasks")
                .select("*")
                .eq("id", task_id)
                .single()
                .execute()
            )
            log.info(f"Successfully fetched task {task_id}")
            return response.data
        except Exception as e:
            log.error(f"Error fetching task {task_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def update_task(self, task_id: str, updates: dict) -> dict:
        log.info(f"Updating task {task_id} with updates: {updates}")
        try:
            supabase = await get_supabase_client()
            response = (
                await supabase.table("tasks")
                .update(updates)
                .eq("id", task_id)
                .execute()
            )
            log.info(f"Successfully updated task {task_id}")
            return response.data
        except Exception as e:
            log.error(f"Error updating task {task_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def delete_task(self, task_id: str) -> None:
        log.info(f"Deleting task {task_id}")
        try:
            supabase = await get_supabase_client()
            await supabase.table("tasks").delete().eq("id", task_id).execute()
            log.info(f"Successfully deleted task {task_id}")
        except Exception as e:
            log.error(f"Error deleting task {task_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
