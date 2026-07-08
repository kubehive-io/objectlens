from abc import ABC, abstractmethod

from .types import BucketInfo, ObjectListResult, ObjectMetadata


class ObjectStorageProvider(ABC):
    provider: str
    display_name: str
    endpoint_url: str | None
    default_bucket: str | None

    @abstractmethod
    def list_buckets(self) -> list[BucketInfo]:
        raise NotImplementedError

    @abstractmethod
    def list_objects(
        self,
        bucket: str,
        prefix: str | None = None,
        continuation_token: str | None = None,
        limit: int = 1000,
    ) -> ObjectListResult:
        raise NotImplementedError

    @abstractmethod
    def get_presigned_download_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_object_metadata(
        self,
        bucket: str,
        key: str,
    ) -> ObjectMetadata:
        raise NotImplementedError
