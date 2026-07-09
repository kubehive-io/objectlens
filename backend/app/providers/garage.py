from typing import Any

import boto3
from botocore.config import Config

from ..config import Settings
from .ceph import CephObjectStorageProvider
from .types import ProviderConnection


class GarageObjectStorageProvider(CephObjectStorageProvider):
    provider = "garage"
    display_name = "Garage"

    def __init__(
        self,
        settings: Settings | None = None,
        connection: ProviderConnection | None = None,
    ) -> None:
        self.connection_id = connection.id if connection else self.provider
        self.connection_name = connection.name if connection else self.display_name
        self.endpoint_url = (
            connection.endpoint_url if connection else settings.garage_s3_endpoint_url
        )
        self.default_bucket = (
            connection.default_bucket if connection else settings.garage_s3_default_bucket or None
        )
        self._settings = settings
        self._connection = connection
        self._client = self._create_client()

    def _create_client(self):
        if self._connection:
            kwargs: dict[str, Any] = {
                "service_name": "s3",
                "region_name": self._connection.region,
                "verify": self._connection.verify_ssl,
                "config": Config(
                    signature_version="s3v4",
                    s3={"addressing_style": "path"},
                ),
            }
            if self._connection.endpoint_url:
                kwargs["endpoint_url"] = self._connection.endpoint_url
            if self._connection.access_key_id and self._connection.secret_access_key:
                kwargs["aws_access_key_id"] = self._connection.access_key_id
                kwargs["aws_secret_access_key"] = self._connection.secret_access_key
            return boto3.client(**kwargs)

        kwargs: dict[str, Any] = {
            "service_name": "s3",
            "region_name": self._settings.garage_s3_region,
            "verify": self._settings.garage_s3_verify_ssl,
            "config": Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            ),
        }
        if self._settings.garage_s3_endpoint_url:
            kwargs["endpoint_url"] = self._settings.garage_s3_endpoint_url
        if self._settings.garage_s3_access_key_id and self._settings.garage_s3_secret_access_key:
            kwargs["aws_access_key_id"] = self._settings.garage_s3_access_key_id
            kwargs["aws_secret_access_key"] = self._settings.garage_s3_secret_access_key
        return boto3.client(**kwargs)
