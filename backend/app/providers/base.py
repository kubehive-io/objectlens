from abc import ABC, abstractmethod

from .types import BucketDetails, BucketInfo, ObjectListResult, ObjectMetadata, ObjectPreview


class ObjectStorageProvider(ABC):
    provider: str
    display_name: str
    endpoint_url: str | None
    default_bucket: str | None

    @abstractmethod
    def list_buckets(self) -> list[BucketInfo]:
        raise NotImplementedError

    @abstractmethod
    def get_bucket_info(self, bucket: str) -> BucketDetails:
        raise NotImplementedError

    @abstractmethod
    def list_objects(
        self,
        bucket: str,
        prefix: str | None = None,
        delimiter: str | None = "/",
        continuation_token: str | None = None,
        limit: int = 50,
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

    @abstractmethod
    def get_object_preview(
        self,
        bucket: str,
        key: str,
        max_bytes: int = 1024 * 1024,
    ) -> ObjectPreview:
        raise NotImplementedError
