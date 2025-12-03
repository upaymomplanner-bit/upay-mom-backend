import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from app.main import app
from app.config import get_settings, Settings
from app.routers.transcript import get_gemini_client
from app.services.planner.dependencies import get_planner_service

@pytest.fixture
def mock_settings():
    return Settings(
        gemini_api_key="test_key",
        gemini_model="test_model",
        max_file_size=1024 * 1024,  # 1MB
        microsoft_tenant_id="test_tenant",
        microsoft_client_id="test_client",
        microsoft_client_secret="test_secret",
        microsoft_planner_container_url="http://test.planner",
        supabase_url="http://test.supabase",
        supabase_service_role_key="test_key"
    )

@pytest.fixture
def mock_gemini_client():
    mock = MagicMock()
    mock.analyze_transcript = AsyncMock()
    return mock

@pytest.fixture
def mock_planner_service():
    mock = MagicMock()
    mock.add_tasks = AsyncMock()
    return mock

@pytest.fixture
def client(mock_settings, mock_gemini_client, mock_planner_service):
    app.dependency_overrides[get_settings] = lambda: mock_settings
    app.dependency_overrides[get_gemini_client] = lambda: mock_gemini_client
    app.dependency_overrides[get_planner_service] = lambda: mock_planner_service
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def live_client():
    # Ensure no overrides are active
    app.dependency_overrides.clear()
    return TestClient(app)
