from msgraph.graph_service_client import GraphServiceClient
from msgraph.generated.models.planner_plan import PlannerPlan
from msgraph.generated.models.planner_plan_container import PlannerPlanContainer
from ...schemas.transcript import PlanAssociation, PlanAssociationType


class PlannerPlanService:
    """
    Service to interact with Microsoft Planner Plans via Microsoft Graph API
    """

    def __init__(self, graph_client: GraphServiceClient, container_url: str):
        self.graph_client = graph_client
        self.container_url = container_url

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


def get_planner_plan_service(
    graph_client: GraphServiceClient, container_url: str
) -> PlannerPlanService:
    return PlannerPlanService(graph_client, container_url)
