from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException

from ..config import get_settings
from ..models import ProviderResponse, ProviderSettingsResponse, ProviderStatusResponse
from ..providers import get_provider, get_provider_registry
from ..providers.types import ProviderConnectionPublic

router = APIRouter(tags=["provider"])


@router.get("/providers", response_model=list[ProviderConnectionPublic])
def list_providers() -> list[ProviderConnectionPublic]:
    return get_provider_registry().list_connections()


@router.get("/providers/{provider_id}", response_model=ProviderConnectionPublic)
def provider_connection(provider_id: str) -> ProviderConnectionPublic:
    registry = get_provider_registry()
    try:
        connection = registry.get_connection(provider_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Provider connection not found.") from exc
    return registry.public_connection(connection)


@router.get("/providers/{provider_id}/status", response_model=ProviderStatusResponse)
def provider_status(provider_id: str) -> ProviderStatusResponse:
    registry = get_provider_registry()
    try:
        provider = registry.get(provider_id)
        buckets = provider.list_buckets()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Provider connection not found.") from exc
    except (BotoCoreError, ClientError) as exc:
        return ProviderStatusResponse(
            provider_id=provider_id,
            status="unhealthy",
            can_list_buckets=False,
            visible_bucket_count=0,
            message=str(exc),
        )
    return ProviderStatusResponse(
        provider_id=provider_id,
        status="healthy",
        can_list_buckets=True,
        visible_bucket_count=len(buckets),
        message="Connected",
    )


@router.get("/providers/{provider_id}/settings", response_model=ProviderSettingsResponse)
def provider_settings(provider_id: str) -> ProviderSettingsResponse:
    registry = get_provider_registry()
    try:
        connection = registry.get_connection(provider_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Provider connection not found.") from exc
    return ProviderSettingsResponse(
        provider_id=provider_id,
        config_source=registry.config_source,
        secrets_loaded=bool(connection.access_key_id and connection.secret_access_key),
        secret_fields=["access_key_id", "secret_access_key"],
        editable=False,
    )


@router.get("/provider", response_model=ProviderResponse)
def provider_info() -> ProviderResponse:
    try:
        provider = get_provider(get_settings())
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ProviderResponse(
        id=getattr(provider, "connection_id", provider.provider),
        name=getattr(provider, "connection_name", provider.display_name),
        type=provider.provider,
        provider=provider.provider,
        display_name=provider.display_name,
        endpoint_url=provider.endpoint_url,
        region=None,
        default_bucket=provider.default_bucket,
    )
