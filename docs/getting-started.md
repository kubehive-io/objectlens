# Getting Started

The quickest way to run ObjectLens is using containerized environments. Run it locally using Docker or Podman, or deploy it to a Kubernetes cluster using the Helm chart.

## Quick Start

### Docker or Podman Compose

Run the entire stack locally with MinIO acting as a mock S3 storage backend:

```bash
# Using Docker Compose
docker compose -f example/docker-compose.yaml up --build

# Using Podman Compose
podman compose -f example/docker-compose.yaml up --build

# Or if you have 'just' installed (automatically detects podman/docker):
just docker-up
```

This starts:
- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **MinIO Console**: `http://localhost:9001` (login with `minioadmin` / `minioadmin`)

To stop all services:

```bash
docker compose -f example/docker-compose.yaml down
# or: just docker-down
```

### Kubernetes via Helm

Deploy ObjectLens into your Kubernetes cluster:

```bash
helm upgrade --install objectlens chart/ --namespace objectlens --create-namespace

# Or using 'just':
just k8s-apply
```

This deploys the backend and frontend to the `objectlens` namespace. Customize S3 connections by editing `chart/values.yaml` or passing variables during install:

```bash
helm upgrade --install objectlens chart/ \
  --namespace objectlens \
  --create-namespace \
  --set backend.env.CEPH_S3_ENDPOINT_URL="http://your-s3-endpoint:9000" \
  --set backend.env.CEPH_S3_ACCESS_KEY_ID="your-access-key" \
  --set backend.env.CEPH_S3_SECRET_ACCESS_KEY="your-secret-key"
```

To delete the deployment:

```bash
helm uninstall objectlens --namespace objectlens
# or: just k8s-delete
```
