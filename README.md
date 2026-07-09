# ObjectLens

ObjectLens is a Kubernetes-native object storage interface for fast access to Ceph RGW and S3-compatible object data.

ObjectLens is documented with MkDocs Material.

## Features

### Storage Providers
- **Ceph RGW & AWS S3**: High-performance object storage integration.
- **Garage**: Simple, lightweight provider optimized for local, air-gapped, or self-hosted environments.
- **Dynamic Discovery**: Automatic discovery and listing of buckets based on active credentials.

### Navigation & Search
- **S3-Style Pathing**: Native folder/prefix browsing.
- **Search Capabilities**: Supports scoped prefix searches, glob-style matching, and fast indexed search.
- **Detailed Insights**: Paginated bucket browsing complete with indexed storage statistics.

### Previews & Actions
- **Rich File Previews**: Built-in viewing for CSV, JSON, Parquet, and image files.
- **Direct Operations**: Rename, move, delete single objects, or recursively clean up entire prefixes.
- **Safe Merges**: Merge prefixes with conflict protection to prevent overwrites.
- **Presigned Downloads**: Instantly generate shareable download links.

### Uploads & Batch Actions
- **Drag-and-Drop**: Easy uploading coupled with a dedicated verification/review queue and progress tracking.
- **Multi-Selection**: Multi-row selection to process operations on multiple items simultaneously.

### Interface
- **Dynamic Theming**: Easily switch between light, dark, and system-matched theme modes.

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
