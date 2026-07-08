from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BucketInfo(BaseModel):
    name: str
    creation_date: datetime | None = None


class ObjectInfo(BaseModel):
    key: str
    size: int
    etag: str | None = None
    last_modified: datetime | None = None
    storage_class: str | None = None
    content_type: str | None = None


class ObjectMetadata(ObjectInfo):
    metadata: dict[str, Any] = Field(default_factory=dict)


class ObjectListResult(BaseModel):
    objects: list[ObjectInfo]
    next_continuation_token: str | None = None
    is_truncated: bool = False


class ProviderConfig(BaseModel):
    provider: str
    display_name: str
    endpoint_url: str | None = None
    default_bucket: str | None = None
