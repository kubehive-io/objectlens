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


class Pagination(BaseModel):
    limit: int
    offset: int
    next_offset: int | None = None
    previous_offset: int | None = None
    has_next: bool
    has_previous: bool


class BucketPrefix(BaseModel):
    name: str
    prefix: str
    object_count: int


class BucketBrowserItem(BaseModel):
    type: str
    name: str
    icon: str
    prefix: str | None = None
    key: str | None = None
    size: int | None = None
    content_type: str | None = None
    storage_class: str | None = None
    last_modified: datetime | None = None


class BucketObjectListing(BaseModel):
    bucket: str
    prefix: str
    delimiter: str | None = None
    mode: str
    limit: int
    offset: int
    total_objects: int
    items: list[BucketBrowserItem]
    pagination: Pagination


class PrefixSummary(BaseModel):
    prefix: str
    object_count: int
    total_size: int


class BucketSummaryResponse(BaseModel):
    provider: str
    bucket: str
    indexed_object_count: int
    indexed_total_size: int
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


class DeleteObjectResponse(BaseModel):
    bucket: str
    key: str
    deleted: bool


class DeletePrefixResponse(BaseModel):
    bucket: str
    prefix: str
    deleted_count: int
    errors: list[str] = Field(default_factory=list)


class UploadObjectResponse(ObjectMetadata):
    pass


class RenameObjectRequest(BaseModel):
    bucket: str
    source_key: str
    target_key: str
    overwrite: bool = False


class RenamePrefixRequest(BaseModel):
    bucket: str
    source_prefix: str
    target_prefix: str
    overwrite: bool = False


class MoveItem(BaseModel):
    type: str
    key: str | None = None
    prefix: str | None = None


class MoveObjectsRequest(BaseModel):
    bucket: str
    items: list[MoveItem]
    target_prefix: str
    overwrite: bool = False


class MergePrefixesRequest(BaseModel):
    bucket: str
    source_prefix: str
    target_prefix: str
    conflict_strategy: str = "fail"


class OperationStatus(BaseModel):
    operation_id: str
    type: str
    status: str
    total: int = 0
    completed: int = 0
    failed: int = 0
    message: str = ""
    errors: list[str] = Field(default_factory=list)


class ObjectOperationSummary(BaseModel):
    operation_id: str
    status: str
    total_objects: int = 0
    moved_objects: int = 0
    skipped_objects: int = 0
    conflicts: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class MergePrefixesResponse(ObjectOperationSummary):
    source_prefix: str
    target_prefix: str


class ProviderResponse(BaseModel):
    id: str | None = None
    name: str | None = None
    type: str | None = None
    provider: str
    display_name: str
    endpoint_url: str | None = None
    region: str | None = None
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
