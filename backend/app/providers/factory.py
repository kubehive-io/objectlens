from ..config import Settings
from .base import ObjectStorageProvider
from .ceph import CephObjectStorageProvider


def get_provider(settings: Settings) -> ObjectStorageProvider:
    if settings.objectlens_provider == "ceph":
        return CephObjectStorageProvider(settings)
    raise ValueError(f"Unsupported object storage provider: {settings.objectlens_provider}")
