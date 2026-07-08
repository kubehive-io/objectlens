# Provider Model

ObjectLens uses a provider abstraction so the API and frontend can stay stable while storage backends vary.

## Why It Exists

Ceph RGW is the first target, but ObjectLens should not be hardcoded to Ceph or AWS naming. A provider boundary keeps object storage access isolated behind a small interface.

## Provider Interface

A provider must implement:

```python
class ObjectStorageProvider:
    def list_buckets(self) -> list[BucketInfo]:
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
```

Shared provider types include:

- `BucketInfo`
- `ObjectInfo`
- `ObjectMetadata`
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
