from msgraph.graph_service_client import GraphServiceClient
from ...schemas.transcript import TranscriptionTask, CheckListItem
from app.services.planner.user_service import UserService
from datetime import datetime
from msgraph.generated.models.planner_task import PlannerTask
from msgraph.generated.models.planner_task_details import PlannerTaskDetails
from app.services.planner.planner_formatter import PlannerFormatter


class PlannerTaskService:
    def __init__(self, graph_client: GraphServiceClient, user_service: UserService):
        self.graph_client = graph_client
        self.user_service = user_service

    async def add_task(self, task: TranscriptionTask, plan_id: str) -> str:
        """
        Add a new task to a specified Planner plan

        Args:
            plan_id: The ID of the Planner plan
            task_title: The title of the new task

        Returns:
            str: The ID of the newly created Planner task
        """

        user_assignments = await self.user_service.get_user_assigments(task.assignments)

        planner_task = PlannerTask(
            plan_id=plan_id,
            title=task.title,
            assignments=user_assignments,
            due_date_time=datetime.fromisoformat(task.due_date.replace("Z", "+00:00"))
            if task.due_date
            else None,
            start_date_time=datetime.fromisoformat(
                task.startDateTime.replace("Z", "+00:00")
            )
            if task.startDateTime
            else None,
            priority=int(task.priority),
        )
        created_task = await self.graph_client.planner.tasks.post(planner_task)
        if not created_task or not created_task.id:
            raise Exception("Failed to create Planner task")

        return created_task.id

    async def add_task_details(
        self,
        task_id: str,
        description: str,
        checklist_items: list[CheckListItem],
    ) -> None:
        """
        Add details to an existing Planner task

        Args:
            task_id: The ID of the Planner task to update
            description: The description to add to the task
            checklist_items: List of checklist items to add to the task
        """
        formatted_checklist = PlannerFormatter.format_checklist_items(checklist_items)
        task_details = PlannerTaskDetails(
            description=description,
            checklist=formatted_checklist,
        )
        await self.graph_client.planner.tasks.by_planner_task_id(task_id).details.patch(
            task_details
        )


def get_planner_task_service(
    graph_client: GraphServiceClient, user_service: UserService
) -> PlannerTaskService:
    return PlannerTaskService(graph_client, user_service)
