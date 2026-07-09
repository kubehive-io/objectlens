# Bucket Details

Bucket details are scoped to a provider connection. The same bucket name can exist in multiple providers without metadata collisions because indexed metadata is keyed by `provider_id`, bucket, and object key.

## Bucket Overview

`GET /providers/{provider_id}/buckets/{bucket}` returns:

- provider ID
- provider name
- bucket name
- creation date when available
- indexed object count
- indexed total size
- last indexed time
- recent objects
- largest objects
- top prefixes

## Bucket Settings

`GET /providers/{provider_id}/buckets/{bucket}/settings` returns safe PoC settings only:

```json
{
  "bucket": "my-bucket",
  "provider_id": "ceph-homelab",
  "versioning": "unknown",
  "lifecycle": "unknown",
  "policy": "not exposed in PoC"
}
```

ObjectLens does not expose bucket policies in the PoC.

## UI

The bucket browser always shows provider name and bucket name. The bucket details page shows indexed statistics, recent objects, largest objects, top prefixes, and safe bucket settings.
