import os
import re
import time
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
        self.config_source = settings.providers_config_dir
        self._connections: list[ProviderConnection] = []
        self._instances: dict[str, ObjectStorageProvider] = {}
        self._last_loaded_time = 0.0
        self._load_all()

    def _maybe_reload(self) -> None:
        interval = self._settings.providers_reload_interval
        if interval > 0:
            if time.time() - self._last_loaded_time > interval:
                self._load_all()

    def _load_all(self) -> None:
        connections = self._load_connections()
        seen: set[str] = set()
        for connection in connections:
            if connection.id in seen:
                raise ValueError(f"Duplicate provider connection id: {connection.id}")
            seen.add(connection.id)
        
        self._connections = connections
        self._instances.clear()
        self._last_loaded_time = time.time()

    def _load_connections(self) -> list[ProviderConnection]:
        configured_path = Path(self._settings.providers_config_dir)
        candidates = [configured_path]
        if not configured_path.is_absolute():
            candidates.append(Path("..") / configured_path)
        config_dir = next(
            (path for path in candidates if path.exists() and path.is_dir()),
            configured_path,
        )
        
        if not config_dir.exists() or not config_dir.is_dir():
            raise FileNotFoundError(
                f"Providers configuration directory not found or is not a directory: "
                f"'{self._settings.providers_config_dir}'."
            )
            
        self.config_source = str(config_dir)
        connections: list[ProviderConnection] = []
        
        yaml_files = sorted(list(config_dir.glob("*.yaml")) + list(config_dir.glob("*.yml")))
        if not yaml_files:
            return []
            
        for config_path in yaml_files:
            payload = yaml.safe_load(config_path.read_text()) or {}
            
            api_version = payload.get("apiVersion")
            kind = payload.get("kind")
            if api_version != "objectlens.kubehive.io/v1alpha1" or kind != "Provider":
                raise ValueError(
                    f"Invalid manifest format in {config_path.name}. "
                    f"Expected apiVersion: 'objectlens.kubehive.io/v1alpha1' and kind: 'Provider', "
                    f"got apiVersion: '{api_version}' and kind: '{kind}'"
                )
                
            spec = payload.get("spec")
            if not isinstance(spec, dict):
                raise ValueError(f"Missing or invalid 'spec' block in {config_path.name}")
                
            if "providers" in spec:
                raise ValueError(
                    f"Multiple providers defined in {config_path.name}. "
                    f"Only a single provider is allowed per file under 'spec'."
                )
                
            expanded_spec = self._expand_env_values(spec, str(config_path))
            connection = ProviderConnection.model_validate(expanded_spec)
            connections.append(connection)
            
        return connections

    def _expand_env_values(self, value: Any, file_source: str) -> Any:
        if isinstance(value, dict):
            return {key: self._expand_env_values(item, file_source) for key, item in value.items()}
        if isinstance(value, list):
            return [self._expand_env_values(item, file_source) for item in value]
        if not isinstance(value, str):
            return value

        def replace(match: re.Match[str]) -> str:
            env_name = match.group(1)
            if env_name not in os.environ:
                raise ValueError(
                    f"Missing environment variable {env_name} referenced in "
                    f"{file_source}"
                )
            return os.environ[env_name]

        return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", replace, value)

    def list_connections(self) -> list[ProviderConnectionPublic]:
        self._maybe_reload()
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
        self._maybe_reload()
        for connection in self._connections:
            if connection.id == provider_id:
                return connection
        raise KeyError(provider_id)

    def get(self, provider_id: str) -> ObjectStorageProvider:
        self._maybe_reload()
        if provider_id not in self._instances:
            connection = self.get_connection(provider_id)
            self._instances[provider_id] = self._create_provider(connection)
        return self._instances[provider_id]

    def default(self) -> ObjectStorageProvider:
        self._maybe_reload()
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
