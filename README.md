# ObjectLens

ObjectLens is a Kubernetes-native object storage interface for fast access to Ceph RGW and S3-compatible object data.

ObjectLens is documented with MkDocs Material.

## Features

- Ceph RGW provider
- Garage provider for local, air-gapped, and self-hosted environments
- Visible bucket listing based on provider credentials
- Bucket detail pages
- Bucket details and indexed statistics
- Paginated bucket browsing
- AWS S3-style prefix/folder navigation
- Scoped prefix search
- Glob-style search patterns
- Indexed search
- JSON, CSV, Parquet, and image preview
- Drag-and-drop upload
- Dedicated upload review page
- Single object delete
- Recursive prefix delete
- Multi-row selection
- Object and prefix rename
- Object and prefix move
- Prefix merge with conflict protection
- Operation progress summaries
- Presigned downloads
- Light, dark, and auto theme modes

## Quick Start

```bash
git clone <repo>
cd objectlens

devbox shell
cp .env.example .env
just install
just dev
```

Open:

```text
Frontend: http://localhost:3000
Backend Swagger: http://localhost:8000/docs
```

## Documentation

Run docs locally:

```bash
devbox shell
just docs
```

Open:

```text
http://localhost:8080
```

Build docs:

```bash
just docs-build
```

## Common Commands

```bash
just install
just backend
just frontend
just dev
just lint
just format
just test
just clean
```

Docker support remains available without Devbox:

```bash
docker compose up --build
```
