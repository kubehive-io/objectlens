import csv
import io
import json
from typing import Any

import boto3
from botocore.config import Config

from ..config import Settings
from .base import ObjectStorageProvider
from .types import (
    BucketDetails,
    BucketInfo,
    BucketPrefix,
    DeleteObjectResult,
    DeletePrefixResult,
    ObjectInfo,
    ObjectListResult,
    ObjectMetadata,
    ObjectPreview,
    ObjectPreviewType,
    ProviderConnection,
)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


class CephObjectStorageProvider(ObjectStorageProvider):
    provider = "ceph"
    display_name = "Ceph RGW"

    def __init__(
        self,
        settings: Settings | None = None,
        connection: ProviderConnection | None = None,
    ) -> None:
        self.connection_id = connection.id if connection else self.provider
        self.connection_name = connection.name if connection else self.display_name
        self.endpoint_url = connection.endpoint_url if connection else settings.ceph_s3_endpoint_url
        self.default_bucket = (
            connection.default_bucket if connection else settings.ceph_s3_default_bucket or None
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
        response = self._client.list_buckets()
        return [
            BucketInfo(name=bucket["Name"], creation_date=bucket.get("CreationDate"))
            for bucket in response.get("Buckets", [])
        ]

    def get_bucket_info(self, bucket: str) -> BucketDetails:
        self._client.head_bucket(Bucket=bucket)
        creation_date = None
        for visible_bucket in self.list_buckets():
            if visible_bucket.name == bucket:
                creation_date = visible_bucket.creation_date
                break
        return BucketDetails(provider=self.provider, name=bucket, creation_date=creation_date)

    def list_objects(
        self,
        bucket: str,
        prefix: str | None = None,
        delimiter: str | None = "/",
        continuation_token: str | None = None,
        limit: int = 50,
    ) -> ObjectListResult:
        kwargs: dict[str, Any] = {
            "Bucket": bucket,
            "MaxKeys": limit,
        }
        if prefix:
            kwargs["Prefix"] = prefix
        if delimiter:
            kwargs["Delimiter"] = delimiter
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
        prefixes = [
            BucketPrefix(
                name=common_prefix["Prefix"][len(prefix or "") :],
                prefix=common_prefix["Prefix"],
            )
            for common_prefix in response.get("CommonPrefixes", [])
        ]
        return ObjectListResult(
            objects=objects,
            prefixes=prefixes,
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

    def get_object_preview(
        self,
        bucket: str,
        key: str,
        max_bytes: int = 1024 * 1024,
    ) -> ObjectPreview:
        metadata = self.get_object_metadata(bucket=bucket, key=key)
        content_type = metadata.content_type
        preview_type = self._detect_preview_type(key, content_type)
        download_url = self.get_presigned_download_url(bucket=bucket, key=key)

        if preview_type == ObjectPreviewType.IMAGE:
            return ObjectPreview(
                bucket=bucket,
                key=key,
                preview_type=ObjectPreviewType.IMAGE,
                content_type=content_type,
                size=metadata.size,
                image_url=download_url,
                download_url=download_url,
                reason="Image previews use a presigned URL and do not proxy object bytes.",
            )

        if preview_type == ObjectPreviewType.UNSUPPORTED:
            return ObjectPreview(
                bucket=bucket,
                key=key,
                preview_type=ObjectPreviewType.UNSUPPORTED,
                content_type=content_type,
                size=metadata.size,
                download_url=download_url,
                reason="Object type is not supported for inline preview.",
            )

        content = self._read_preview_bytes(bucket=bucket, key=key, max_bytes=max_bytes)
        truncated = metadata.size > len(content)

        if preview_type == ObjectPreviewType.JSON:
            return self._json_preview(
                bucket,
                key,
                content_type,
                metadata.size,
                content,
                truncated,
                download_url,
            )
        if preview_type == ObjectPreviewType.CSV:
            return self._csv_preview(
                bucket,
                key,
                content_type,
                metadata.size,
                content,
                truncated,
                download_url,
            )
        if preview_type == ObjectPreviewType.PARQUET:
            return self._parquet_preview(
                bucket,
                key,
                content_type,
                metadata.size,
                content,
                truncated,
                download_url,
            )
        if preview_type == ObjectPreviewType.TEXT:
            return self._text_preview(
                bucket,
                key,
                content_type,
                metadata.size,
                content,
                truncated,
                download_url,
            )

        return ObjectPreview(
            bucket=bucket,
            key=key,
            preview_type=ObjectPreviewType.UNSUPPORTED,
            content_type=content_type,
            size=metadata.size,
            download_url=download_url,
            reason="Object type is not supported for inline preview.",
        )

    def delete_object(self, bucket: str, key: str) -> DeleteObjectResult:
        self._client.delete_object(Bucket=bucket, Key=key)
        return DeleteObjectResult(bucket=bucket, key=key)

    def delete_prefix(self, bucket: str, prefix: str) -> DeletePrefixResult:
        deleted_count = 0
        errors: list[str] = []
        continuation_token = None

        while True:
            kwargs: dict[str, Any] = {"Bucket": bucket, "Prefix": prefix, "MaxKeys": 1000}
            if continuation_token:
                kwargs["ContinuationToken"] = continuation_token

            response = self._client.list_objects_v2(**kwargs)
            keys = [{"Key": item["Key"]} for item in response.get("Contents", [])]
            if keys:
                delete_response = self._client.delete_objects(
                    Bucket=bucket,
                    Delete={"Objects": keys, "Quiet": True},
                )
                batch_errors = delete_response.get("Errors", [])
                deleted_count += len(keys) - len(batch_errors)
                errors.extend(
                    f"{error.get('Key')}: {error.get('Code')} {error.get('Message')}"
                    for error in batch_errors
                )

            continuation_token = response.get("NextContinuationToken")
            if not continuation_token:
                break

        return DeletePrefixResult(
            bucket=bucket,
            prefix=prefix,
            deleted_count=deleted_count,
            errors=errors,
        )

    def upload_object(
        self,
        bucket: str,
        key: str,
        file_obj,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
        cache_control: str | None = None,
    ) -> ObjectInfo:
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if cache_control:
            extra_args["CacheControl"] = cache_control
        if metadata:
            extra_args["Metadata"] = metadata

        if extra_args:
            self._client.upload_fileobj(file_obj, bucket, key, ExtraArgs=extra_args)
        else:
            self._client.upload_fileobj(file_obj, bucket, key)
        return self.get_object_metadata(bucket=bucket, key=key)

    def copy_object(
        self,
        bucket: str,
        source_key: str,
        target_key: str,
    ) -> ObjectInfo:
        self._client.copy_object(
            Bucket=bucket,
            Key=target_key,
            CopySource={"Bucket": bucket, "Key": source_key},
        )
        return self.get_object_metadata(bucket=bucket, key=target_key)

    def _read_preview_bytes(self, bucket: str, key: str, max_bytes: int) -> bytes:
        response = self._client.get_object(Bucket=bucket, Key=key, Range=f"bytes=0-{max_bytes - 1}")
        body = response["Body"]
        try:
            return body.read(max_bytes)
        finally:
            body.close()

    def _detect_preview_type(self, key: str, content_type: str | None) -> ObjectPreviewType:
        lower_key = key.lower()
        lower_content_type = (content_type or "").lower()
        is_image = lower_content_type.startswith("image/") or any(
            lower_key.endswith(ext) for ext in IMAGE_EXTENSIONS
        )
        if is_image:
            return ObjectPreviewType.IMAGE
        if "json" in lower_content_type or lower_key.endswith(".json"):
            return ObjectPreviewType.JSON
        if "csv" in lower_content_type or lower_key.endswith(".csv"):
            return ObjectPreviewType.CSV
        if lower_key.endswith(".parquet"):
            return ObjectPreviewType.PARQUET
        
        TEXT_EXTENSIONS = (
            ".txt", ".md", ".log", ".yaml", ".yml", ".toml", ".ini", ".conf",
            ".py", ".js", ".ts", ".go", ".rs", ".sh", ".c", ".cpp", ".h",
            ".hpp", ".css", ".html"
        )
        if lower_content_type.startswith("text/") or any(
            lower_key.endswith(ext) for ext in TEXT_EXTENSIONS
        ):
            return ObjectPreviewType.TEXT

        return ObjectPreviewType.UNSUPPORTED

    def _json_preview(
        self,
        bucket: str,
        key: str,
        content_type: str | None,
        size: int,
        content: bytes,
        truncated: bool,
        download_url: str,
    ) -> ObjectPreview:
        try:
            parsed = json.loads(content.decode("utf-8"))
            text = json.dumps(parsed, indent=2, sort_keys=True)
            reason = "Preview reads only a limited amount of the object." if truncated else None
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return ObjectPreview(
                bucket=bucket,
                key=key,
                preview_type=ObjectPreviewType.UNSUPPORTED,
                content_type=content_type,
                size=size,
                truncated=truncated,
                download_url=download_url,
                reason=f"JSON preview failed: {exc}",
            )
        return ObjectPreview(
            bucket=bucket,
            key=key,
            preview_type=ObjectPreviewType.JSON,
            content_type=content_type,
            size=size,
            truncated=truncated,
            text=text,
            download_url=download_url,
            reason=reason,
        )

    def _text_preview(
        self,
        bucket: str,
        key: str,
        content_type: str | None,
        size: int,
        content: bytes,
        truncated: bool,
        download_url: str,
    ) -> ObjectPreview:
        try:
            text = content.decode("utf-8")
            reason = "Preview reads only a limited amount of the object." if truncated else None
        except UnicodeDecodeError:
            return ObjectPreview(
                bucket=bucket,
                key=key,
                preview_type=ObjectPreviewType.UNSUPPORTED,
                content_type=content_type,
                size=size,
                truncated=truncated,
                download_url=download_url,
                reason="Text preview failed: utf-8 decoding error.",
            )
        return ObjectPreview(
            bucket=bucket,
            key=key,
            preview_type=ObjectPreviewType.TEXT,
            content_type=content_type,
            size=size,
            truncated=truncated,
            text=text,
            download_url=download_url,
            reason=reason,
        )

    def _csv_preview(
        self,
        bucket: str,
        key: str,
        content_type: str | None,
        size: int,
        content: bytes,
        truncated: bool,
        download_url: str,
    ) -> ObjectPreview:
        try:
            sample = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            return ObjectPreview(
                bucket=bucket,
                key=key,
                preview_type=ObjectPreviewType.UNSUPPORTED,
                content_type=content_type,
                size=size,
                truncated=truncated,
                download_url=download_url,
                reason=f"CSV preview failed: {exc}",
            )
        reader = csv.DictReader(io.StringIO(sample))
        rows = [row for _, row in zip(range(25), reader, strict=False)]
        return ObjectPreview(
            bucket=bucket,
            key=key,
            preview_type=ObjectPreviewType.CSV,
            content_type=content_type,
            size=size,
            truncated=truncated,
            headers=reader.fieldnames or [],
            rows=rows,
            download_url=download_url,
            reason="Preview reads only a limited amount of the object." if truncated else None,
        )

    def _parquet_preview(
        self,
        bucket: str,
        key: str,
        content_type: str | None,
        size: int,
        content: bytes,
        truncated: bool,
        download_url: str,
    ) -> ObjectPreview:
        try:
            import pyarrow.parquet as pq
        except ImportError:
            return ObjectPreview(
                bucket=bucket,
                key=key,
                preview_type=ObjectPreviewType.UNSUPPORTED,
                content_type=content_type,
                size=size,
                truncated=truncated,
                download_url=download_url,
                reason="Parquet preview requires optional pyarrow support.",
            )
        if truncated:
            return ObjectPreview(
                bucket=bucket,
                key=key,
                preview_type=ObjectPreviewType.UNSUPPORTED,
                content_type=content_type,
                size=size,
                truncated=truncated,
                download_url=download_url,
                reason=(
                    "Parquet preview needs the full file footer; "
                    "object is larger than the preview limit."
                ),
            )
        table = pq.read_table(io.BytesIO(content))
        rows = table.slice(0, 25).to_pylist()
        schema_fields = [{"name": field.name, "type": str(field.type)} for field in table.schema]
        return ObjectPreview(
            bucket=bucket,
            key=key,
            preview_type=ObjectPreviewType.PARQUET,
            content_type=content_type,
            size=size,
            rows=rows,
            schema_fields=schema_fields,
            download_url=download_url,
        )
