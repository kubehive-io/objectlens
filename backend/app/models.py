from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class Bucket(BaseModel):
    name: str
    creation_date: datetime | None = None


class BucketListResponse(BaseModel):
    buckets: list[Bucket]


class BucketDetailsResponse(BaseModel):
    provider: str
    name: str
    creation_date: datetime | None = None
    indexed_object_count: int = 0
    indexed_total_size: int = 0
    last_indexed_at: datetime | None = None


class ObjectMetadata(BaseModel):
    provider: str
    bucket: str
    key: str
    size: int
    etag: str | None = None
    last_modified: datetime | None = None
    storage_class: str | None = None
    content_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    indexed_at: datetime | None = None


class ObjectListResponse(BaseModel):
    objects: list[ObjectMetadata]
    count: int


class PrefixSummary(BaseModel):
    prefix: str
    object_count: int
    total_size: int


class BucketSummaryResponse(BaseModel):
    bucket: str
    object_count: int
    total_size: int
    last_indexed_at: datetime | None = None
    largest_objects: list[ObjectMetadata]
    recent_objects: list[ObjectMetadata]
    top_prefixes: list[PrefixSummary]


class ScanResponse(BaseModel):
    bucket: str
    scanned: int = Field(description="Number of objects read from object storage")
    indexed: int = Field(description="Number of metadata rows upserted")


class PresignDownloadResponse(BaseModel):
    bucket: str
    key: str
    url: str


class ProviderResponse(BaseModel):
    provider: str
    display_name: str
    endpoint_url: str | None = None
    default_bucket: str | None = None


class ObjectPreviewResponse(BaseModel):
    bucket: str
    key: str
    preview_type: str
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
