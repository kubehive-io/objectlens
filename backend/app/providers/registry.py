import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from ..config import Settings, get_settings
from .aws import AwsObjectStorageProvider
from .base import ObjectStorageProvider
from .ceph import CephObjectStorageProvider
from .garage import GarageObjectStorageProvider
from .types import ProviderConnection, ProviderConnectionPublic


class ProviderRegistry:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.config_source = settings.providers_config_file
        self._connections = self._load_connections()
        self._instances: dict[str, ObjectStorageProvider] = {}
        seen: set[str] = set()
        for connection in self._connections:
            if connection.id in seen:
                raise ValueError(f"Duplicate provider connection id: {connection.id}")
            seen.add(connection.id)

    def _load_connections(self) -> list[ProviderConnection]:
        configured_path = Path(self._settings.providers_config_file)
        candidates = [configured_path]
        if not configured_path.is_absolute():
            candidates.append(Path("..") / configured_path)
        config_path = next((path for path in candidates if path.exists()), configured_path)
        if config_path.exists():
            self.config_source = str(config_path)
            payload = self._expand_env_values(yaml.safe_load(config_path.read_text()) or {})
            connections = [
                ProviderConnection.model_validate(item) for item in payload.get("providers", [])
            ]
            if not connections:
                raise ValueError(f"No providers configured in {config_path}")
            return connections
        return [self._legacy_connection()]

    def _expand_env_values(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._expand_env_values(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._expand_env_values(item) for item in value]
        if not isinstance(value, str):
            return value

        def replace(match: re.Match[str]) -> str:
            env_name = match.group(1)
            if env_name not in os.environ:
                raise ValueError(
                    f"Missing environment variable {env_name} referenced in "
                    f"{self.config_source}"
                )
            return os.environ[env_name]

        return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", replace, value)

    def _legacy_connection(self) -> ProviderConnection:
        provider_type = self._settings.objectlens_provider
        if provider_type == "garage":
            return ProviderConnection(
                id="garage",
                name="Garage",
                type="garage",
                endpoint_url=self._settings.garage_s3_endpoint_url,
                region=self._settings.garage_s3_region,
                access_key_id=self._settings.garage_s3_access_key_id,
                secret_access_key=self._settings.garage_s3_secret_access_key,
                default_bucket=self._settings.garage_s3_default_bucket,
                verify_ssl=self._settings.garage_s3_verify_ssl,
                tags=["garage"],
            )
        return ProviderConnection(
            id="ceph",
            name="Ceph RGW",
            type="ceph",
            endpoint_url=self._settings.ceph_s3_endpoint_url,
            region=self._settings.ceph_s3_region,
            access_key_id=self._settings.ceph_s3_access_key_id,
            secret_access_key=self._settings.ceph_s3_secret_access_key,
            default_bucket=self._settings.ceph_s3_default_bucket,
            verify_ssl=self._settings.ceph_s3_verify_ssl,
            tags=["ceph"],
        )

    def list_connections(self) -> list[ProviderConnectionPublic]:
        return [self.public_connection(connection) for connection in self._connections]

    def public_connection(self, connection: ProviderConnection) -> ProviderConnectionPublic:
        provider = self.get(connection.id)
        return ProviderConnectionPublic(
            id=connection.id,
            name=connection.name,
            type=connection.type,
            display_name=provider.display_name,
            description=connection.description,
            endpoint_url=connection.endpoint_url,
            region=connection.region,
            default_bucket=connection.default_bucket,
            verify_ssl=connection.verify_ssl,
            tags=connection.tags,
        )

    def get_connection(self, provider_id: str) -> ProviderConnection:
        for connection in self._connections:
            if connection.id == provider_id:
                return connection
        raise KeyError(provider_id)

    def get(self, provider_id: str) -> ObjectStorageProvider:
        if provider_id not in self._instances:
            connection = self.get_connection(provider_id)
            self._instances[provider_id] = self._create_provider(connection)
        return self._instances[provider_id]

    def default(self) -> ObjectStorageProvider:
        if not self._connections:
            raise ValueError("No provider connections configured")
        return self.get(self._connections[0].id)

    def _create_provider(self, connection: ProviderConnection) -> ObjectStorageProvider:
        providers: dict[str, Any] = {
            "ceph": CephObjectStorageProvider,
            "garage": GarageObjectStorageProvider,
            "aws": AwsObjectStorageProvider,
        }
        provider_cls = providers.get(connection.type)
        if provider_cls is None:
            raise ValueError(f"Unsupported object storage provider: {connection.type}")
        return provider_cls(settings=self._settings, connection=connection)


@lru_cache
def get_provider_registry() -> ProviderRegistry:
    return ProviderRegistry(get_settings())
