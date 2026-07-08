# Getting Started

## Requirements

Install only:

- Git
- Devbox

Devbox provides Python, uv, Node.js, Just, MkDocs, and the other local tools used by the project.

## Run Locally

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

## One Command

After dependencies are installed, you can also run:

```bash
devbox run dev
```

## Local Ceph-Compatible Endpoint

The default `.env.example` points at a local S3-compatible endpoint:

```env
OBJECTLENS_PROVIDER=ceph
CEPH_S3_ENDPOINT_URL=http://localhost:9000
CEPH_S3_REGION=us-east-1
CEPH_S3_ACCESS_KEY_ID=minioadmin
CEPH_S3_SECRET_ACCESS_KEY=minioadmin
CEPH_S3_DEFAULT_BUCKET=objectlens-demo
CEPH_S3_VERIFY_SSL=false
```

For Docker Compose, this endpoint is provided by MinIO so the Ceph provider can be exercised without a real Ceph cluster.
