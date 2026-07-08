# ObjectLens

ObjectLens is a Kubernetes-native object storage interface for fast access to Ceph RGW and S3-compatible object data.

ObjectLens is documented with MkDocs Material.

## Features

- Ceph RGW provider
- Visible bucket listing based on provider credentials
- Bucket detail pages
- Indexed search
- JSON, CSV, Parquet, and image preview
- Presigned downloads

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
