"""
Shared test fixtures and configuration for all tests.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so `import app` works when running pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO

from app.main import app
from app.config import get_settings, Settings
from app.routers.transcript import get_gemini_client
from app.services.planner.dependencies import get_planner_service
from app.services.auth.deps import get_supabase_client
from app.schemas.transcript import (
    GeminiExtractionResponse,
    MeetingExtractionResult,
    MeetingDetails,
    TaskGroup,
    TranscriptionTask,
    TaskDetails,
    TaskAssignment,
    CheckListItem,
    TaskPriority,
    PlanAssociation,
    PlanAssociationType,
    PlanReference,
)


# ==================== AUTH CONFIGURATION ====================

# Auth headers for test requests
TEST_AUTH_HEADERS = {"Authorization": "Bearer test_token_123"}


# ==================== MOCK SERVICES ====================


@pytest.fixture
def mock_settings():
    """Mock application settings"""
    return Settings(
        gemini_api_key="test_gemini_key",
        gemini_model="gemini-2.5-flash",
        max_file_size=5 * 1024 * 1024,  # 5MB
        microsoft_tenant_id="test_tenant_id",
        microsoft_client_id="test_client_id",
        microsoft_client_secret="test_secret",
        microsoft_planner_container_url="http://test.planner.url",
        supabase_url="http://test.supabase.url",
        supabase_service_role_key="test_supabase_key",
    )


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini client with analyze_transcript method"""
    mock = MagicMock()
    mock.analyze_transcript = AsyncMock()
    return mock


@pytest.fixture
def mock_planner_service():
    """Mock Microsoft Planner service"""
    mock = MagicMock()
    mock.add_tasks = AsyncMock()
    return mock


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client"""
    mock = MagicMock()
    return mock


@pytest.fixture
def client(
    mock_settings, mock_gemini_client, mock_planner_service, mock_supabase_client
):
    """Test client with dependency overrides and auth middleware bypass"""
    # Setup mock supabase client for auth middleware
    mock_user_response = MagicMock()
    mock_user_response.user = MagicMock(id="test_user_123", email="test@example.com")
    mock_supabase_client.auth.get_user = AsyncMock(return_value=mock_user_response)

    # Patch get_supabase_client used in middleware
    async def mock_get_supabase():
        return mock_supabase_client

    # Override dependencies
    app.dependency_overrides[get_settings] = lambda: mock_settings
    app.dependency_overrides[get_gemini_client] = lambda: mock_gemini_client
    app.dependency_overrides[get_planner_service] = lambda: mock_planner_service
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase_client

    # Patch the get_supabase_client function used in middleware
    with patch("app.main.get_supabase_client", side_effect=mock_get_supabase):
        # Create test client
        test_client = TestClient(app)
        yield test_client

    # Clean up overrides
    app.dependency_overrides.clear()


# ==================== SAMPLE DATA FIXTURES ====================


@pytest.fixture
def sample_meeting_details():
    """Sample meeting details"""
    return MeetingDetails(
        meeting_title="Sprint Planning Q1 2025", meeting_date="2025-01-15T10:00:00Z"
    )


@pytest.fixture
def sample_task_assignment():
    """Sample task assignment"""
    return TaskAssignment(
        assignee_name="John Doe", assignee_email="john.doe@example.com"
    )


@pytest.fixture
def sample_checklist_items():
    """Sample checklist items"""
    return [
        CheckListItem(title="Review requirements"),
        CheckListItem(title="Draft initial design"),
        CheckListItem(title="Get stakeholder approval"),
    ]


@pytest.fixture
def sample_task_details(sample_checklist_items):
    """Sample task details"""
    return TaskDetails(
        description="Implement the user authentication module with OAuth2.0 support",
        checklist_items=sample_checklist_items,
    )


@pytest.fixture
def sample_transcription_task(sample_task_details, sample_task_assignment):
    """Sample transcription task"""
    return TranscriptionTask(
        title="Implement User Authentication",
        details=sample_task_details,
        assignments=[sample_task_assignment],
        due_date="2025-02-01T23:59:59Z",
        startDateTime="2025-01-15T10:00:00Z",
        priority=TaskPriority.IMPORTANT,
    )


@pytest.fixture
def sample_plan_reference():
    """Sample plan reference"""
    return PlanReference(
        plan_id="plan_123", plan_title="Q1 2025 Development", confidence_score=0.95
    )


@pytest.fixture
def sample_plan_association(sample_plan_reference):
    """Sample plan association with existing plan"""
    return PlanAssociation(
        association_type=PlanAssociationType.EXISTING,
        plan_title="Q1 2025 Development",
        plan_reference=sample_plan_reference,
        rationale="Tasks align with Q1 development roadmap",
    )


@pytest.fixture
def sample_task_group(sample_plan_association, sample_transcription_task):
    """Sample task group"""
    return TaskGroup(
        plan_association=sample_plan_association,
        tasks=[sample_transcription_task],
        group_description="Authentication and security tasks for Q1",
    )


@pytest.fixture
def sample_gemini_response(sample_task_group):
    """Sample Gemini extraction response"""
    return GeminiExtractionResponse(
        task_groups=[sample_task_group],
        meeting_summary="Discussed Q1 priorities, focusing on user authentication and security features.",
    )


@pytest.fixture
def sample_meeting_extraction(sample_meeting_details, sample_task_group):
    """Sample meeting extraction result"""
    return MeetingExtractionResult(
        meeting_details=sample_meeting_details,
        task_groups=[sample_task_group],
        meeting_summary="Discussed Q1 priorities, focusing on user authentication and security features.",
        meeting_date="2025-01-15T10:00:00Z",
        action_items_count=1,
    )


@pytest.fixture
def sample_transcript_txt():
    """Sample transcript text file content"""
    return b"""Meeting: Sprint Planning Q1 2025
Date: January 15, 2025

Attendees:
- John Doe (Engineering Lead)
- Jane Smith (Product Manager)
- Bob Wilson (Designer)

Discussion:
Jane: We need to prioritize user authentication for Q1. This is critical for our security roadmap.
John: Agreed. I'll take this on. We should use OAuth2.0 for better integration.
Jane: Can you have this done by end of January?
John: Yes, February 1st works as a deadline.
Jane: Great. Make sure to review requirements, draft initial design, and get stakeholder approval.

Next Steps:
- John to implement user authentication module
- Review session scheduled for Feb 5th
"""


@pytest.fixture
def sample_transcript_pdf():
    """Sample PDF content (mock binary)"""
    return b"%PDF-1.4\n%Mock PDF content for testing\nMeeting transcript..."
