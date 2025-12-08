"""
FastAPI dependencies for Planner services.
This module provides dependency injection for the Microsoft Planner service hierarchy.
"""

from fastapi import Depends
from typing import Optional
from msgraph.graph_service_client import GraphServiceClient
from app.config import Settings, get_settings
from app.services.auth.planner_auth import get_graph_client
from app.services.planner.user_service import UserService, get_user_service
from app.services.planner.planner_plan_service import (
    get_planner_plan_service,
)
from app.services.planner.planner_task_service import (
    get_planner_task_service,
)
from app.services.planner.planner_service import MicrosoftPlannerService


def get_planner_service(
    graph_client: Optional[GraphServiceClient] = Depends(get_graph_client),
    settings: Settings = Depends(get_settings),
    user_service: UserService = Depends(get_user_service),
) -> MicrosoftPlannerService:
    """
    Dependency to get MicrosoftPlannerService instance with all dependencies injected.

    This orchestrates the creation of the service hierarchy:
    - PlannerPlanService (for plan management)
    - PlannerTaskService (for task management)
      - UserService (for user lookups)
    """
    if not graph_client:
        return MicrosoftPlannerService()

    # Create plan service
    plan_service = get_planner_plan_service(
        graph_client, settings.microsoft_planner_container_url
    )

    # Create task service (with user service dependency)
    task_service = get_planner_task_service(graph_client, user_service)

    # Create and return the orchestrator service
    return MicrosoftPlannerService(plan_service, task_service)
