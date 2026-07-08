# Provider Model

ObjectLens uses a provider abstraction so the API and frontend can stay stable while storage backends vary.

## Why It Exists

Ceph RGW is the first target, but ObjectLens should not be hardcoded to Ceph or AWS naming. A provider boundary keeps object storage access isolated behind a small interface.

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
        continuation_token: str | None = None,
        limit: int = 1000,
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
- Azure Blob
- Google Cloud Storage
- Local filesystem
