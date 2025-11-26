from ...schemas.transcript import TaskAssignment
from msgraph.generated.models.planner_assignments import PlannerAssignments


class UserService:
    def __init__(self):
        pass

    async def get_user_assigments(
        self, task_assigments: list[TaskAssignment]
    ) -> PlannerAssignments:
        """Fetch user oids from our database using name-based search and create PlannerAssignments object"""
        # TODO: Implement user lookup and assignment creation based on db
        return PlannerAssignments()


def get_user_service() -> UserService:
    return UserService()
