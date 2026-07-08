# Architecture

ObjectLens is split into a Nuxt frontend, FastAPI backend, provider abstraction, provider implementations, and a metadata index.

```mermaid
flowchart LR
  Browser[Browser] --> Frontend[Nuxt 4 Frontend]
  Frontend --> Backend[FastAPI Backend]
  Backend --> Provider[ObjectStorageProvider]
  Provider --> Ceph[CephObjectStorageProvider]
  Ceph --> RGW[Ceph RGW]
  Backend --> SQLite[(SQLite Metadata Index)]
```

## Frontend

The frontend is a Nuxt 4 application under `frontend/app`. It renders the ObjectLens dashboard, reads the public API base URL from runtime config, and uses provider-neutral language while showing the active provider as Ceph RGW.

## Backend API

The FastAPI backend exposes stable endpoints:

- `GET /health`
- `GET /provider`
- `GET /buckets`
- `GET /objects`
- `POST /index/scan`
- `GET /objects/presign-download`

Routes depend on the provider interface rather than boto3 directly.

## Provider Abstraction

The provider layer lives in `backend/app/providers`. It defines shared types, an abstract provider interface, a Ceph provider, and a factory.

```mermaid
classDiagram
  class ObjectStorageProvider {
    +list_buckets()
    +list_objects(bucket, prefix, continuation_token, limit)
    +get_presigned_download_url(bucket, key, expires_in)
    +get_object_metadata(bucket, key)
  }
  class CephObjectStorageProvider
  ObjectStorageProvider <|-- CephObjectStorageProvider
```

## Ceph Provider

The first provider is `CephObjectStorageProvider`. It uses boto3 against a Ceph RGW S3-compatible endpoint with path-style addressing.

## Metadata Index

SQLite stores indexed object metadata for the PoC. Rows include the provider name, bucket, key, size, etag, last modified time, storage class, content type, provider metadata, and indexed timestamp.

Future deployments should move this to Postgres for shared use.

## Index Scanner

The scan endpoint pages through provider objects and upserts metadata into SQLite. The current scanner is synchronous. A later phase should move scanning into background workers.

## Future Search and Deployment

OpenSearch can take over full-text and large-scale object search. Kubernetes manifests exist today, and the project is shaped to move toward Helm and Flux without source code changes.

## Preview Flow

```mermaid
sequenceDiagram
  participant User
  participant UI as Nuxt Frontend
  participant API as FastAPI Backend
  participant Provider as Provider Interface
  participant Ceph as Ceph RGW

  User->>UI: Open object preview
  UI->>API: GET /objects/preview?bucket=&key=
  API->>Provider: get_object_preview(bucket, key)
  Provider->>Ceph: Get object range / metadata
  Ceph-->>Provider: Object bytes or metadata
  Provider-->>API: Preview result
  API-->>UI: JSON / CSV / Parquet / Image preview
  UI-->>User: Render preview
```

## Bucket Visibility

```mermaid
flowchart TD
  User[User opens ObjectLens] --> UI[Frontend]
  UI --> API[GET /buckets]
  API --> Provider[Provider Interface]
  Provider --> Ceph[Ceph RGW list_buckets]
  Ceph --> Allowed[Only buckets allowed by credentials]
  Allowed --> UI
```
