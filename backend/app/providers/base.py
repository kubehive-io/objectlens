from abc import ABC, abstractmethod

from .types import (
    BucketDetails,
    BucketInfo,
    DeleteObjectResult,
    DeletePrefixResult,
    ObjectInfo,
    ObjectListResult,
    ObjectMetadata,
    ObjectPreview,
)


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

    @abstractmethod
    def delete_object(self, bucket: str, key: str) -> DeleteObjectResult:
        raise NotImplementedError

    @abstractmethod
    def delete_prefix(self, bucket: str, prefix: str) -> DeletePrefixResult:
        raise NotImplementedError

    @abstractmethod
    def upload_object(
        self,
        bucket: str,
        key: str,
        file_obj,
        content_type: str | None = None,
    ) -> ObjectInfo:
        raise NotImplementedError

    @abstractmethod
    def copy_object(
        self,
        bucket: str,
        source_key: str,
        target_key: str,
    ) -> ObjectInfo:
        raise NotImplementedError
