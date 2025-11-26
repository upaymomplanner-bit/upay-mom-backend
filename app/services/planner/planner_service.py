from ...schemas.transcript import MeetingExtractionResult
from app.services.planner.planner_plan_service import PlannerPlanService
from app.services.planner.planner_task_service import PlannerTaskService


class MicrosoftPlannerService:
    """
    Orchestrator service for Microsoft Planner operations.
    Coordinates interactions between plan and task services.
    """

    def __init__(
        self,
        plan_service: PlannerPlanService,
        task_service: PlannerTaskService,
    ):
        self.plan_service = plan_service
        self.task_service = task_service

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
        # TODO: Discuss with UPAY team whether meetings tend to discuss tasks within same project or other way around and then parallelize according to those needs.
        for task_group in meeting_tasks.task_groups:
            plan_id = await self.plan_service.get_or_create_plan(
                task_group.plan_association
            )

            for task in task_group.tasks:
                task_id = await self.task_service.add_task(task, plan_id)
                await self.task_service.add_task_details(
                    task_id,
                    description=task.details.description or "",
                    checklist_items=task.details.checklist_items or [],
                )
