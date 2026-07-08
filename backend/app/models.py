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
    indexed_at: datetime


class ObjectListResponse(BaseModel):
    objects: list[ObjectMetadata]
    count: int


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
