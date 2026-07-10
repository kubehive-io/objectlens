import time

import pytest

from app.config import Settings
from app.providers.registry import ProviderRegistry


def test_provider_registry_loads_valid_single_provider_manifests_from_dir(
    tmp_path, monkeypatch
) -> None:
    # Create test directory for configs
    config_dir = tmp_path / "providers"
    config_dir.mkdir()
    
    # Provider 1
    p1_file = config_dir / "ceph.yaml"
    p1_file.write_text("""
apiVersion: objectlens.kubehive.io/v1alpha1
kind: Provider
metadata:
  name: test-ceph
spec:
  id: mock-ceph
  name: Mock Ceph
  type: ceph
  endpoint_url: http://ceph.example.local
  region: us-east-1
  access_key_id: ${MOCK_ACCESS_KEY_ID}
  secret_access_key: "my-secret"
  verify_ssl: false
  tags:
    - test
""")

    # Provider 2
    p2_file = config_dir / "aws.yaml"
    p2_file.write_text("""
apiVersion: objectlens.kubehive.io/v1alpha1
kind: Provider
metadata:
  name: test-aws
spec:
  id: mock-aws
  name: Mock AWS
  type: aws
  region: us-east-1
  access_key_id: "aws-key"
  secret_access_key: "aws-secret"
  verify_ssl: true
  tags:
    - aws
""")

    monkeypatch.setenv("MOCK_ACCESS_KEY_ID", "expanded-key-123")
    settings = Settings(providers_config_dir=str(config_dir))
    registry = ProviderRegistry(settings)

    connections = registry.list_connections()
    assert len(connections) == 2
    
    # Connections should be sorted by filename (aws, ceph)
    assert connections[0].id == "mock-aws"
    assert connections[1].id == "mock-ceph"
    
    # Check that access_key_id was expanded
    conn = registry.get_connection("mock-ceph")
    assert conn.access_key_id == "expanded-key-123"


def test_provider_registry_raises_on_invalid_apiVersion_or_kind(tmp_path) -> None:
    config_dir = tmp_path / "providers"
    config_dir.mkdir()
    p_file = config_dir / "invalid.yaml"
    p_file.write_text("""
apiVersion: objectlens.io/v1alpha1
kind: ObjectLensProviders
metadata:
  name: bad-config
spec:
  providers: []
""")

    settings = Settings(providers_config_dir=str(config_dir))
    with pytest.raises(ValueError, match="Invalid manifest format"):
        ProviderRegistry(settings)


def test_provider_registry_raises_on_multiple_providers_in_single_file(tmp_path) -> None:
    config_dir = tmp_path / "providers"
    config_dir.mkdir()
    p_file = config_dir / "multiple.yaml"
    p_file.write_text("""
apiVersion: objectlens.kubehive.io/v1alpha1
kind: Provider
metadata:
  name: multiple-config
spec:
  providers:
    - id: ceph
      name: Ceph
""")

    settings = Settings(providers_config_dir=str(config_dir))
    with pytest.raises(ValueError, match="Multiple providers defined"):
        ProviderRegistry(settings)


def test_provider_registry_raises_on_missing_dir() -> None:
    settings = Settings(providers_config_dir="/nonexistent/path/dir")
    with pytest.raises(FileNotFoundError, match="Providers configuration directory not found"):
        ProviderRegistry(settings)


def test_provider_registry_hot_reloading(tmp_path) -> None:
    config_dir = tmp_path / "providers"
    config_dir.mkdir()
    p_file = config_dir / "p1.yaml"
    p_file.write_text("""
apiVersion: objectlens.kubehive.io/v1alpha1
kind: Provider
metadata:
  name: first
spec:
  id: first-provider
  name: First Provider
  type: ceph
  endpoint_url: http://first.local
  region: us-east-1
  access_key_id: "key"
  secret_access_key: "secret"
""")

    # Enable hot reloading every 1 second (to keep test fast)
    settings = Settings(providers_config_dir=str(config_dir), providers_reload_interval=1)
    registry = ProviderRegistry(settings)

    assert len(registry.list_connections()) == 1
    assert registry.list_connections()[0].id == "first-provider"

    # Add a second provider file
    p2_file = config_dir / "p2.yaml"
    p2_file.write_text("""
apiVersion: objectlens.kubehive.io/v1alpha1
kind: Provider
metadata:
  name: second
spec:
  id: second-provider
  name: Second Provider
  type: ceph
  endpoint_url: http://second.local
  region: us-east-1
  access_key_id: "key"
  secret_access_key: "secret"
""")

    # Before the reload interval has elapsed, it should still return only the first one
    assert len(registry.list_connections()) == 1

    # Sleep to trigger reload interval
    time.sleep(1.1)

    # Now it should hot-reload and show both!
    assert len(registry.list_connections()) == 2
    active_ids = {conn.id for conn in registry.list_connections()}
    assert active_ids == {"first-provider", "second-provider"}


def test_provider_registry_gracefully_handles_empty_directory(tmp_path) -> None:
    config_dir = tmp_path / "providers"
    config_dir.mkdir()
    
    settings = Settings(providers_config_dir=str(config_dir))
    registry = ProviderRegistry(settings)
    
    assert registry.list_connections() == []
