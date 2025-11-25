from fastapi import Depends, HTTPException
from supabase import acreate_client, AsyncClient

from config import get_settings


# CHECK: this is privileged access, only with service role key
async def get_supabase_client():
    settings = get_settings()
    return await acreate_client(
        settings.supabase_url, settings.supabase_service_role_key
    )


async def verify_supabase_auth(
    supabase_client: AsyncClient = Depends(get_supabase_client),
):
    """
    Dependency to verify that the Supabase client is authenticated.
    Raises HTTPException if not authenticated.
    """
    user_response = await supabase_client.auth.get_user()
    if user_response is None or user_response.user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user_response.user
