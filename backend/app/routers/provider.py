from fastapi import APIRouter, HTTPException

from ..config import get_settings
from ..models import ProviderResponse
from ..providers import get_provider

router = APIRouter(tags=["provider"])


@router.get("/provider", response_model=ProviderResponse)
def provider_info() -> ProviderResponse:
    try:
        provider = get_provider(get_settings())
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ProviderResponse(
        provider=provider.provider,
        display_name=provider.display_name,
        endpoint_url=provider.endpoint_url,
        default_bucket=provider.default_bucket,
    )
