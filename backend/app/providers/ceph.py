from typing import Any

import boto3
from botocore.config import Config

from ..config import Settings
from .base import ObjectStorageProvider
from .types import BucketInfo, ObjectInfo, ObjectListResult, ObjectMetadata


class CephObjectStorageProvider(ObjectStorageProvider):
    provider = "ceph"
    display_name = "Ceph RGW"

    def __init__(self, settings: Settings) -> None:
        self.endpoint_url = settings.ceph_s3_endpoint_url
        self.default_bucket = settings.ceph_s3_default_bucket or None
        self._settings = settings
        self._client = self._create_client()

    def _create_client(self):
        kwargs: dict[str, Any] = {
            "service_name": "s3",
            "region_name": self._settings.ceph_s3_region,
            "verify": self._settings.ceph_s3_verify_ssl,
            "config": Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            ),
        }
        if self._settings.ceph_s3_endpoint_url:
            kwargs["endpoint_url"] = self._settings.ceph_s3_endpoint_url
        if self._settings.ceph_s3_access_key_id and self._settings.ceph_s3_secret_access_key:
            kwargs["aws_access_key_id"] = self._settings.ceph_s3_access_key_id
            kwargs["aws_secret_access_key"] = self._settings.ceph_s3_secret_access_key
        return boto3.client(**kwargs)

    def list_buckets(self) -> list[BucketInfo]:
        if self.default_bucket:
            return [BucketInfo(name=self.default_bucket)]

        response = self._client.list_buckets()
        return [
            BucketInfo(name=bucket["Name"], creation_date=bucket.get("CreationDate"))
            for bucket in response.get("Buckets", [])
        ]

    def list_objects(
        self,
        bucket: str,
        prefix: str | None = None,
        continuation_token: str | None = None,
        limit: int = 1000,
    ) -> ObjectListResult:
        kwargs: dict[str, Any] = {
            "Bucket": bucket,
            "MaxKeys": limit,
        }
        if prefix:
            kwargs["Prefix"] = prefix
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token

        response = self._client.list_objects_v2(**kwargs)
        objects = [
            ObjectInfo(
                key=obj["Key"],
                size=obj.get("Size", 0),
                etag=(obj.get("ETag") or "").strip('"') or None,
                last_modified=obj.get("LastModified"),
                storage_class=obj.get("StorageClass"),
            )
            for obj in response.get("Contents", [])
        ]
        return ObjectListResult(
            objects=objects,
            next_continuation_token=response.get("NextContinuationToken"),
            is_truncated=response.get("IsTruncated", False),
        )

    def get_presigned_download_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def get_object_metadata(
        self,
        bucket: str,
        key: str,
    ) -> ObjectMetadata:
        response = self._client.head_object(Bucket=bucket, Key=key)
        return ObjectMetadata(
            key=key,
            size=response.get("ContentLength", 0),
            etag=(response.get("ETag") or "").strip('"') or None,
            last_modified=response.get("LastModified"),
            storage_class=response.get("StorageClass"),
            content_type=response.get("ContentType"),
            metadata=response.get("Metadata", {}),
        )
