from azure.identity.aio import ClientSecretCredential
from msgraph.graph_service_client import GraphServiceClient
from typing import Optional
from ...config import get_settings


# TODO: Replace the default client secret credential with an on behalf of credential flow
def get_graph_client() -> Optional[GraphServiceClient]:
    """
    Initialize and return a Microsoft Graph API client for Planner interactions.
    """

    settings = get_settings()
    microsoft_tenant_id = (
        settings.microsoft_tenant_id if settings.microsoft_tenant_id else ""
    )
    microsoft_client_id = (
        settings.microsoft_client_id if settings.microsoft_client_id else ""
    )
    microsoft_client_secret = (
        settings.microsoft_client_secret if settings.microsoft_client_secret else ""
    )

    if not microsoft_client_secret:
        return None

    credential = ClientSecretCredential(
        tenant_id=microsoft_tenant_id,
        client_id=microsoft_client_id,
        client_secret=microsoft_client_secret,
    )
    scopes = ["https://graph.microsoft.com/.default"]
    client = GraphServiceClient(credentials=credential, scopes=scopes)
    return client
