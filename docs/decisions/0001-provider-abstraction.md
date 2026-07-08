# 0001: Provider Abstraction

## Status

Accepted

## Context

ObjectLens starts with Ceph RGW because the first deployment target is a homelab Ceph cluster. The project should still avoid hardcoding storage access directly into API routes so future providers can be added without rewriting the frontend or endpoint contracts.

## Decision

Backend routes call an `ObjectStorageProvider` interface. Provider implementations own object storage SDK details. The first implementation is `CephObjectStorageProvider`, which uses boto3 against an S3-compatible Ceph RGW endpoint.

Indexed metadata includes `provider`, `bucket`, and `key` as the identity for each object.

## Consequences

- API routes remain provider-neutral.
- The frontend can show provider information without knowing provider SDK details.
- New providers can be added through the factory.
- The PoC carries a little more structure now to avoid larger rewrites later.
