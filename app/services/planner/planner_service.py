from msgraph.graph_service_client import GraphServiceClient
from schemas.transcript import (
    MeetingExtractionResult,
    PlanAssociationType,
    TaskAssignment,
    TranscriptionTask,
    PlanAssociation,
    CheckListItem,
)
from msgraph.generated.models.planner_task import PlannerTask
from msgraph.generated.models.planner_task_details import PlannerTaskDetails
from msgraph.generated.models.planner_assignments import PlannerAssignments
from msgraph.generated.models.planner_plan import PlannerPlan
from datetime import datetime
from msgraph.generated.models.planner_plan_container import PlannerPlanContainer
from app.services.planner.planner_formatter import PlannerFormatter


class MicrosoftPlannerService:
    """
    Service to interact with Microsoft Planner via Microsoft Graph API
    """

    def __init__(self, graph_client: GraphServiceClient, container_url: str):
        self.graph_client = graph_client
        self.container_url = container_url

    async def add_tasks(
        self,
        meeting_tasks: MeetingExtractionResult,
    ) -> None:
        """
        Add tasks extracted from meeting transcripts to Microsoft Planner

        Args:
            meeting_tasks: The structured tasks extracted from the meeting transcript
        """
        for task_group in meeting_tasks.task_groups:
            plan_id = await self.get_or_create_plan(task_group.plan_association)
            for task in task_group.tasks:
                task_id = await self.add_task(task, plan_id)
                await self.add_task_details(
                    task_id,
                    description=task.details.description or "",
                    checklist_items=task.details.checklist_items or [],
                )

    async def get_user_assigments(
        self, task_assigments: list[TaskAssignment]
    ) -> PlannerAssignments:
        """Fetch user oids from our database using name-based search and create PlannerAssignments object"""
        # TODO: Implement user lookup and assignment creation based on db
        return PlannerAssignments()

    async def add_task(self, task: TranscriptionTask, plan_id: str) -> str:
        """
        Add a single task to Microsoft Planner

        Args:
            task: The structured task to be added to Planner
        """
        user_assignments = await self.get_user_assigments(task.assignments)

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

    async def get_or_create_plan(self, plan_association: PlanAssociation) -> str:
        """
        Get or create a Planner plan based on the association type

        Args:
            plan_association: The plan association details

        Returns:
            str: The ID of the Planner plan
        """
        if plan_association.association_type == PlanAssociationType.EXISTING:
            if not plan_association.plan_reference:
                raise ValueError(
                    "Plan reference must be provided for existing plan association"
                )
            return plan_association.plan_reference.plan_id
        elif plan_association.association_type == PlanAssociationType.NEW:
            return await self.create_plan(plan_association.plan_title)
        else:
            raise ValueError("Invalid plan association type")

    async def create_plan(self, plan_title: str) -> str:
        """
        Create a new Planner plan

        Args:
            plan_title: The title of the new plan

        Returns:
            str: The ID of the newly created Planner plan
        """

        request_body = PlannerPlan(
            container=PlannerPlanContainer(url=self.container_url),
            title=plan_title,
        )

        created_plan = await self.graph_client.planner.plans.post(request_body)
        if not created_plan or not created_plan.id:
            raise Exception("Failed to create Planner plan")
        return created_plan.id

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
