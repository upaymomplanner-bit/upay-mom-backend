import pytest
from app.services.auth.deps import get_supabase_client

@pytest.mark.asyncio
async def test_supabase_connection():
    """Test Supabase connection by querying the departments table."""
    try:
        supabase = await get_supabase_client()

        # Query the departments table (simple select to verify connection)
        response = await supabase.table("departments").select("id, name").limit(1).execute()

        print(f"\nSupabase Connection Successful.")
        print(f"Response data: {response.data}")
        print(f"Found {len(response.data)} departments (limited to 1).")

        assert response is not None
        assert hasattr(response, 'data')
        # We don't assert > 0 records as the table might be empty

    except Exception as e:
        pytest.fail(f"Supabase connection failed: {str(e)}")

@pytest.mark.asyncio
async def test_supabase_profiles_table():
    """Test querying the profiles table."""
    try:
        supabase = await get_supabase_client()

        # Query the profiles table
        response = await supabase.table("profiles").select("id, email, full_name").limit(1).execute()

        print(f"\nProfiles table query successful.")
        print(f"Found {len(response.data)} profiles (limited to 1).")

        assert response is not None
        assert hasattr(response, 'data')

    except Exception as e:
        pytest.fail(f"Profiles table query failed: {str(e)}")
