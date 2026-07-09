from ..config import Settings
from .base import ObjectStorageProvider
from .registry import get_provider_registry


def get_provider(settings: Settings) -> ObjectStorageProvider:
    return get_provider_registry().default()


def get_provider_by_id(provider_id: str) -> ObjectStorageProvider:
    try:
        return get_provider_registry().get(provider_id)
    except KeyError as exc:
        raise ValueError(f"Unknown provider connection: {provider_id}") from exc
