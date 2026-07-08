from collections.abc import Iterator
from typing import Any

import boto3
from botocore.config import Config

from .config import get_settings


def get_s3_client():
    settings = get_settings()
    kwargs = {
        "service_name": "s3",
        "region_name": settings.s3_region,
        "config": Config(
            signature_version="s3v4",
            s3={"addressing_style": "path" if settings.s3_force_path_style else "auto"},
        ),
    }
    if settings.s3_endpoint_url:
        kwargs["endpoint_url"] = settings.s3_endpoint_url
    if settings.s3_access_key_id and settings.s3_secret_access_key:
        kwargs["aws_access_key_id"] = settings.s3_access_key_id
        kwargs["aws_secret_access_key"] = settings.s3_secret_access_key
    return boto3.client(**kwargs)


def configured_bucket() -> str | None:
    return get_settings().s3_bucket


def iter_object_metadata(bucket: str) -> Iterator[list[dict[str, Any]]]:
    client = get_s3_client()
    paginator = client.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=bucket):
        batch: list[dict[str, Any]] = []
        for obj in page.get("Contents", []):
            batch.append(
                {
                    "key": obj["Key"],
                    "size": obj.get("Size", 0),
                    "etag": obj.get("ETag", "").strip('"') or None,
                    "last_modified": obj.get("LastModified"),
                    "storage_class": obj.get("StorageClass"),
                    "content_type": None,
                }
            )
        if batch:
            yield batch
