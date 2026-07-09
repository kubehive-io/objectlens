# Provider Model

ObjectLens uses a provider abstraction so the API and frontend can stay stable while storage backends vary.

## Why It Exists

Ceph RGW was the first target, and Garage is supported for local and self-hosted development. ObjectLens should not be hardcoded to Ceph, Garage, or AWS naming. A provider boundary keeps object storage access isolated behind a small interface.

## Provider Interface

A provider controls bucket listing, object listing, object metadata, previews, and presigned URLs. A provider must implement:

```python
class ObjectStorageProvider:
    def list_buckets(self) -> list[BucketInfo]:
        ...

    def get_bucket_info(self, bucket: str) -> BucketDetails:
        ...

    def list_objects(
        self,
        bucket: str,
        prefix: str | None = None,
        delimiter: str | None = "/",
        continuation_token: str | None = None,
        limit: int = 50,
    ) -> ObjectListResult:
        ...

    def get_presigned_download_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        ...

    def get_object_metadata(
        self,
        bucket: str,
        key: str,
    ) -> ObjectMetadata:
        ...

    def get_object_preview(
        self,
        bucket: str,
        key: str,
        max_bytes: int = 1024 * 1024,
    ) -> ObjectPreview:
        ...

    def upload_object(
        self,
        bucket: str,
        key: str,
        file_obj,
        content_type: str | None = None,
    ) -> ObjectInfo:
        ...
```

Shared provider types include:

- `BucketInfo`
- `BucketDetails`
- `ObjectInfo`
- `ObjectMetadata`
- `ObjectPreview`
- `ObjectPreviewType`
- `ObjectListResult`
- `ProviderConfig`

## Current Providers

- `ceph`: Ceph RGW through the S3-compatible API.
- `garage`: Garage through the S3-compatible API.

## Adding Providers

To add a provider:

1. Implement `ObjectStorageProvider`.
2. Add provider-specific configuration to settings.
3. Register the provider in `backend/app/providers/factory.py`.
4. Keep routes provider-neutral.
5. Include the provider name in indexed metadata rows.

## Possible Future Providers

- AWS S3
- MinIO
- Garage clusters beyond local development
- Azure Blob
- Google Cloud Storage
- Local filesystem
