from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class BucketInfo(BaseModel):
    name: str
    creation_date: datetime | None = None


class BucketPrefix(BaseModel):
    name: str
    prefix: str
    object_count: int = 0


class BucketDetails(BucketInfo):
    provider: str
    indexed_object_count: int = 0
    indexed_total_size: int = 0
    last_indexed_at: datetime | None = None


class ObjectInfo(BaseModel):
    key: str
    size: int
    etag: str | None = None
    last_modified: datetime | None = None
    storage_class: str | None = None
    content_type: str | None = None


class ObjectMetadata(ObjectInfo):
    metadata: dict[str, Any] = Field(default_factory=dict)


class ObjectPreviewType(StrEnum):
    JSON = "json"
    CSV = "csv"
    PARQUET = "parquet"
    IMAGE = "image"
    TEXT = "text"
    UNSUPPORTED = "unsupported"


class ObjectPreview(BaseModel):
    bucket: str
    key: str
    preview_type: ObjectPreviewType
    content_type: str | None = None
    size: int | None = None
    truncated: bool = False
    text: str | None = None
    headers: list[str] | None = None
    rows: list[dict[str, Any]] | None = None
    schema_fields: list[dict[str, str]] | None = None
    image_url: str | None = None
    download_url: str | None = None
    reason: str | None = None


class ObjectListResult(BaseModel):
    objects: list[ObjectInfo]
    prefixes: list[BucketPrefix] = Field(default_factory=list)
    next_continuation_token: str | None = None
    is_truncated: bool = False


class DeleteObjectResult(BaseModel):
    bucket: str
    key: str
    deleted: bool = True


class DeletePrefixResult(BaseModel):
    bucket: str
    prefix: str
    deleted_count: int = 0
    errors: list[str] = Field(default_factory=list)


class UploadObjectResult(ObjectInfo):
    bucket: str


class ProviderConfig(BaseModel):
    provider: str
    display_name: str
    endpoint_url: str | None = None
    default_bucket: str | None = None


class ProviderConnection(BaseModel):
    id: str
    name: str
    type: str
    description: str | None = None
    endpoint_url: str | None = None
    region: str = "us-east-1"
    access_key_id: str | None = None
    secret_access_key: str | None = None
    verify_ssl: bool = True
    default_bucket: str | None = None
    tags: list[str] = Field(default_factory=list)
    error: str | None = None


class ProviderConnectionPublic(BaseModel):
    id: str
    name: str
    type: str
    display_name: str
    description: str | None = None
    endpoint_url: str | None = None
    region: str
    default_bucket: str | None = None
    verify_ssl: bool
    tags: list[str] = Field(default_factory=list)
    error: str | None = None
