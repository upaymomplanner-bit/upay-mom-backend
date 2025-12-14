"""
Integration tests for complete workflows.
Tests end-to-end scenarios combining multiple endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO
import os
from pathlib import Path
from supabase import AsyncClient

from conftest import TEST_AUTH_HEADERS
from app.config import get_settings
from app.services.gemini_client import GeminiClient
from app.services.database.meeting_service import MeetingDatabaseService
from app.schemas.transcript import MeetingDetails


class TestEndToEndFlow:
    """Integration tests for complete workflows"""

    def test_complete_workflow_process_and_save(
        self,
        client,
        mock_gemini_client,
        mock_supabase_client,
        mock_planner_service,
        sample_gemini_response,
        sample_meeting_details,
        sample_transcript_txt,
    ):
        """Test complete workflow: process transcript, then save"""
        # Step 1: Process transcript
        mock_gemini_client.analyze_transcript.return_value = sample_gemini_response

        meeting_details_json = sample_meeting_details.model_dump_json()
        files = {
            "file": ("transcript.txt", BytesIO(sample_transcript_txt), "text/plain")
        }
        data = {"meeting_details": meeting_details_json}

        process_response = client.post(
            "/transcripts/process", files=files, data=data, headers=TEST_AUTH_HEADERS
        )
        assert process_response.status_code == 200
        extraction_result = process_response.json()

        # Step 2: Save the result
        mock_db_service = MagicMock()
        mock_db_service.save_meeting = AsyncMock(return_value="meeting_final_123")
        mock_db_service.save_tasks = AsyncMock(return_value=["task_final_1"])

        with patch(
            "app.routers.transcript.MeetingDatabaseService",
            return_value=mock_db_service,
        ):
            save_response = client.post(
                "/transcripts/save", json=extraction_result, headers=TEST_AUTH_HEADERS
            )

        assert save_response.status_code == 201
        save_result = save_response.json()

        assert save_result["meeting_id"] == "meeting_final_123"
        assert save_result["planner_sync_status"] == "success"

    def test_complete_workflow_process_and_upload(
        self,
        client,
        mock_gemini_client,
        mock_planner_service,
        sample_gemini_response,
        sample_meeting_details,
        sample_transcript_txt,
    ):
        """Test complete workflow: process transcript, then upload to Planner"""
        # Step 1: Process transcript
        mock_gemini_client.analyze_transcript.return_value = sample_gemini_response

        meeting_details_json = sample_meeting_details.model_dump_json()
        files = {
            "file": ("transcript.txt", BytesIO(sample_transcript_txt), "text/plain")
        }
        data = {"meeting_details": meeting_details_json}

        process_response = client.post(
            "/transcripts/process", files=files, data=data, headers=TEST_AUTH_HEADERS
        )
        assert process_response.status_code == 200
        extraction_result = process_response.json()

        # Step 2: Upload to Planner
        upload_response = client.post(
            "/transcripts/upload_tasks",
            json=extraction_result,
            headers=TEST_AUTH_HEADERS,
        )
        assert upload_response.status_code == 204

        # Verify planner service was called
        mock_planner_service.add_tasks.assert_called_once()


@pytest.mark.live
class TestLiveIntegration:
    """Live integration tests using real Gemini and Supabase services.

    These tests require:
    - Valid GEMINI_API_KEY in environment
    - Valid SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in environment

    Run with: pytest tests/test_integration.py::TestLiveIntegration -m live -v
    Skip with: pytest tests/test_integration.py -m "not live"
    """

    @pytest.fixture
    def sample_transcript_path(self):
        """Get path to sample transcript file"""
        return Path(__file__).parent / "sample_transcript.txt"

    @pytest.fixture
    def meeting_details(self):
        """Create meeting details for the sample transcript"""
        return MeetingDetails(
            meeting_title="Project Planning Meeting - Q1 2026",
            meeting_date="2025-12-14",
        )

    @pytest.mark.asyncio
    async def test_live_gemini_analysis(self, sample_transcript_path, meeting_details):
        """Test live Gemini API call with sample transcript"""
        settings = get_settings()

        # Skip if API key not configured
        if not settings.gemini_api_key:
            pytest.skip("GEMINI_API_KEY not configured")

        # Read sample transcript
        with open(sample_transcript_path, "r", encoding="utf-8") as f:
            transcript_content = f.read()

        # Initialize Gemini client
        gemini_client = GeminiClient(
            api_key=settings.gemini_api_key, model=settings.gemini_model
        )

        # Call Gemini API
        result = await gemini_client.analyze_transcript(
            file_data=transcript_content.encode("utf-8"), mime_type="text/plain"
        )

        # Verify response structure
        assert result is not None
        assert result.meeting_summary is not None
        assert len(result.meeting_summary) > 0
        assert result.task_groups is not None
        assert len(result.task_groups) > 0

        # Verify at least one task group has tasks
        total_tasks = sum(len(group.tasks) for group in result.task_groups)
        assert total_tasks > 0

        # Print results for manual verification
        print("\n=== Gemini Analysis Results ===")
        print(f"Meeting Summary: {result.meeting_summary[:200]}...")
        print(f"Number of Task Groups: {len(result.task_groups)}")
        print(f"Total Tasks: {total_tasks}")
        for i, group in enumerate(result.task_groups):
            print(f"\nTask Group {i + 1}: {group.group_description}")
            print(f"  Tasks: {len(group.tasks)}")
            for j, task in enumerate(group.tasks[:3]):  # Show first 3 tasks
                print(f"    - {task.title}")

    @pytest.mark.asyncio
    async def test_live_supabase_save_and_delete(
        self, sample_transcript_path, meeting_details
    ):
        """Test live Supabase operations: save tasks and then delete them"""
        settings = get_settings()

        # Skip if Supabase not configured
        if not settings.supabase_url or not settings.supabase_service_role_key:
            pytest.skip("Supabase credentials not configured")

        # Skip if Gemini not configured (needed for analysis)
        if not settings.gemini_api_key:
            pytest.skip("GEMINI_API_KEY not configured")

        # Read sample transcript
        with open(sample_transcript_path, "r", encoding="utf-8") as f:
            transcript_content = f.read()

        # Step 1: Get Gemini analysis
        gemini_client = GeminiClient(
            api_key=settings.gemini_api_key, model=settings.gemini_model
        )

        gemini_result = await gemini_client.analyze_transcript(
            file_data=transcript_content.encode("utf-8"), mime_type="text/plain"
        )

        # Step 2: Initialize Supabase client
        supabase_client = AsyncClient(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_role_key,
        )

        db_service = MeetingDatabaseService(supabase_client)

        # Use None for host_id to avoid foreign key constraint issues
        test_host_id = None

        created_meeting_id = None
        created_task_ids = []

        try:
            # Step 3: Save meeting to Supabase
            print("\n=== Saving to Supabase ===")

            # Only save first 2 tasks from first task group for testing
            test_task_group = gemini_result.task_groups[0]
            test_tasks = test_task_group.tasks[:2]  # Only first 2 tasks

            # Create a modified result with limited tasks
            from app.schemas.transcript import MeetingExtractionResult, TaskGroup

            limited_task_group = TaskGroup(
                group_description=test_task_group.group_description,
                plan_association=test_task_group.plan_association,
                tasks=test_tasks,
            )

            limited_result = MeetingExtractionResult(
                meeting_details=meeting_details,
                meeting_summary=gemini_result.meeting_summary,
                task_groups=[limited_task_group],
                action_items_count=len(test_tasks),
                meeting_date=meeting_details.meeting_date,
            )

            # Save meeting
            created_meeting_id = await db_service.save_meeting(
                meeting_result=limited_result, host_id=test_host_id
            )

            print(f"Created meeting ID: {created_meeting_id}")
            assert created_meeting_id is not None

            # Save tasks
            created_task_ids = await db_service.save_tasks(
                meeting_id=created_meeting_id, task_groups=limited_result.task_groups
            )

            print(f"Created {len(created_task_ids)} tasks")
            assert len(created_task_ids) == 2  # We saved 2 tasks

            for task_id in created_task_ids:
                print(f"  - Task ID: {task_id}")

            # Step 4: Verify data was saved
            # Check meeting exists
            meeting_response = (
                await supabase_client.table("meetings")
                .select("*")
                .eq("id", str(created_meeting_id))
                .execute()
            )
            assert len(meeting_response.data) == 1
            meeting_record = meeting_response.data[0]  # type: ignore
            assert meeting_record["title"] == meeting_details.meeting_title  # type: ignore
            print(f"✓ Meeting verified in database")

            # Check tasks exist
            tasks_response = (
                await supabase_client.table("tasks")
                .select("*")
                .eq("meeting_id", str(created_meeting_id))
                .execute()
            )
            assert len(tasks_response.data) == 2
            print(f"✓ Tasks verified in database")

            print("\n=== Cleanup: Deleting test data ===")

        finally:
            # Step 5: Cleanup - Delete created tasks and meeting
            if created_task_ids:
                for task_id in created_task_ids:
                    try:
                        await (
                            supabase_client.table("tasks")
                            .delete()
                            .eq("id", str(task_id))
                            .execute()
                        )
                        print(f"✓ Deleted task: {task_id}")
                    except Exception as e:
                        print(f"Warning: Could not delete task {task_id}: {e}")

            if created_meeting_id:
                try:
                    await (
                        supabase_client.table("meetings")
                        .delete()
                        .eq("id", str(created_meeting_id))
                        .execute()
                    )
                    print(f"✓ Deleted meeting: {created_meeting_id}")
                except Exception as e:
                    print(
                        f"Warning: Could not delete meeting {created_meeting_id}: {e}"
                    )

            # Verify cleanup
            if created_meeting_id:
                meeting_check = (
                    await supabase_client.table("meetings")
                    .select("*")
                    .eq("id", str(created_meeting_id))
                    .execute()
                )
                assert len(meeting_check.data) == 0, "Meeting was not deleted"
                print(f"✓ Verified meeting deletion")

            if created_task_ids:
                for task_id in created_task_ids:
                    task_check = (
                        await supabase_client.table("tasks")
                        .select("*")
                        .eq("id", str(task_id))
                        .execute()
                    )
                    assert len(task_check.data) == 0, f"Task {task_id} was not deleted"
                print(f"✓ Verified all tasks deleted")

            # Close Supabase client
            await supabase_client.auth.sign_out()
            # Note: AsyncClient doesn't have aclose(), cleanup is automatic

        print("\n=== Live Supabase test completed successfully ===")

    @pytest.mark.asyncio
    async def test_live_complete_gemini_to_supabase_flow(
        self, sample_transcript_path, meeting_details
    ):
        """Complete end-to-end test: Gemini analysis + Supabase save/delete"""
        settings = get_settings()

        # Skip if required services not configured
        if not settings.gemini_api_key:
            pytest.skip("GEMINI_API_KEY not configured")
        if not settings.supabase_url or not settings.supabase_service_role_key:
            pytest.skip("Supabase credentials not configured")

        print("\n=== Complete Live Integration Test ===")
        print("This test performs:")
        print("1. Gemini AI analysis of transcript")
        print("2. Save results to Supabase")
        print("3. Verify data in database")
        print("4. Clean up test data")

        # Read transcript
        with open(sample_transcript_path, "r", encoding="utf-8") as f:
            transcript_content = f.read()

        # Initialize services
        gemini_client = GeminiClient(
            api_key=settings.gemini_api_key, model=settings.gemini_model
        )

        supabase_client = AsyncClient(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_role_key,
        )

        db_service = MeetingDatabaseService(supabase_client)
        # Use None for host_id to avoid foreign key constraint issues
        test_host_id = None

        created_meeting_id = None
        created_task_ids = []

        try:
            # Phase 1: Gemini Analysis
            print("\n[Phase 1] Analyzing transcript with Gemini...")
            gemini_result = await gemini_client.analyze_transcript(
                file_data=transcript_content.encode("utf-8"), mime_type="text/plain"
            )
            print(f"✓ Gemini returned {len(gemini_result.task_groups)} task groups")

            # Phase 2: Save to Supabase (limited to 2 tasks)
            print("\n[Phase 2] Saving to Supabase...")

            # Prepare limited dataset
            from app.schemas.transcript import MeetingExtractionResult, TaskGroup

            test_task_group = gemini_result.task_groups[0]
            limited_task_group = TaskGroup(
                group_description=test_task_group.group_description,
                plan_association=test_task_group.plan_association,
                tasks=test_task_group.tasks[:2],
            )

            limited_result = MeetingExtractionResult(
                meeting_details=meeting_details,
                meeting_summary=gemini_result.meeting_summary,
                task_groups=[limited_task_group],
                action_items_count=2,
                meeting_date=meeting_details.meeting_date,
            )

            created_meeting_id = await db_service.save_meeting(
                meeting_result=limited_result, host_id=test_host_id
            )
            print(f"✓ Meeting saved: {created_meeting_id}")

            created_task_ids = await db_service.save_tasks(
                meeting_id=created_meeting_id, task_groups=limited_result.task_groups
            )
            print(f"✓ {len(created_task_ids)} tasks saved")

            # Phase 3: Verification
            print("\n[Phase 3] Verifying data in database...")
            meeting_data = (
                await supabase_client.table("meetings")
                .select("*")
                .eq("id", str(created_meeting_id))
                .execute()
            )
            assert len(meeting_data.data) == 1
            meeting_record = meeting_data.data[0]  # type: ignore
            print(f"✓ Meeting exists: {meeting_record['title']}")  # type: ignore

            tasks_data = (
                await supabase_client.table("tasks")
                .select("*")
                .eq("meeting_id", str(created_meeting_id))
                .execute()
            )
            assert len(tasks_data.data) == 2
            for task in tasks_data.data:
                print(f"  ✓ Task: {task['title']}")  # type: ignore

        finally:
            # Phase 4: Cleanup
            print("\n[Phase 4] Cleaning up test data...")

            if created_task_ids:
                for task_id in created_task_ids:
                    await (
                        supabase_client.table("tasks")
                        .delete()
                        .eq("id", str(task_id))
                        .execute()
                    )
                print(f"✓ Deleted {len(created_task_ids)} tasks")

            if created_meeting_id:
                await (
                    supabase_client.table("meetings")
                    .delete()
                    .eq("id", str(created_meeting_id))
                    .execute()
                )
                print(f"✓ Deleted meeting")

            await supabase_client.auth.sign_out()
            # Note: AsyncClient doesn't have aclose(), cleanup is automatic

        print("\n=== ✓ Complete live integration test passed ===")
