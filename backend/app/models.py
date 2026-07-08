from datetime import datetime

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
    bucket: str
    key: str
    size: int
    etag: str | None = None
    last_modified: datetime | None = None
    storage_class: str | None = None
    content_type: str | None = None
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
