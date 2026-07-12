# ObjectLens

<p align="center">
  <img src="images/objectlens-logo.png" alt="ObjectLens Banner" />
</p>

ObjectLens is a Kubernetes-native object storage interface for fast access to Ceph RGW and S3-compatible object data.

---

## Features

### Storage Providers
- **Ceph RGW & AWS S3**: High-performance object storage integration.
- **Garage**: Simple, lightweight provider optimized for local, air-gapped, or self-hosted environments.
- **Dynamic Discovery**: Automatic discovery and listing of buckets based on active credentials.

### Navigation & Search
- **S3-Style Pathing**: Native folder/prefix browsing.
- **Advanced Global Search**: Features an interactive 3-column workspace masonry grid overview, dynamic file-type color-coded extension badges, formatted file sizes, and `/` and `Escape` keyboard shortcuts.
- **Detailed Insights**: Paginated bucket browsing complete with indexed storage statistics.

### Previews & Actions
- **Rich File Previews**: Built-in viewing for text files, code (Python, Go, JS, etc), CSV, JSON, Parquet, and images.
- **Direct Operations**: Rename, move, delete single objects, or recursively clean up entire prefixes.
- **Safe Merges**: Merge prefixes with conflict protection to prevent overwrites.
- **Presigned Downloads**: Instantly generate shareable download links.

### Uploads & Batch Actions
- **Drag-and-Drop**: Easy uploading coupled with a dedicated verification/review queue and progress tracking.
- **Visual Card Wizards**: Symmetrical visual-card step wizards for selecting storage connections and bucket destinations smoothly.
- **Multi-Selection**: Multi-row selection to process operations on multiple items simultaneously.

### Operations & Audit Logs
- **DB-Backed Auditing**: Real, persistent SQLite `activity_log` tracking of bucket indexing, file uploads, file deletions, and prefix directory deletions.
- **Operations Timeline**: Beautiful paginated audit log timeline supporting default 50-event pages and relative, human-friendly date formatting.

### Security & Access Control
- **Declarative YAML Authentication**: Deploy role permissions by placing clean user manifests (e.g. `data/users/admin.yaml`) with passwords.
- **Granular RBAC Enforcements**: Separates `viewer` (read-only list, search, download, preview) and `admin` (write, upload, recursive delete, move, scan) privileges.
- **HTTP Basic Auth Integration**: Simple stateless S3 security configured dynamically on backend startup.

### Interface
- **Dynamic Theming**: Easily switch between light, dark, and system-matched theme modes.

---

## Deployment via Helm (Recommended)

Deploy ObjectLens into your Kubernetes cluster using the published Helm chart from GitHub Container Registry (GHCR):

```bash
helm upgrade --install objectlens oci://ghcr.io/kubehive-io/objectlens/helm-chart \
  --version 0.1.0 \
  --namespace objectlens \
  --create-namespace
```

### Configuration Overrides

You can customize your deployment (including your Ceph S3 endpoints, credentials, persistence, and ingress) by passing parameters during installation or updating `values.yaml`:

```bash
helm upgrade --install objectlens oci://ghcr.io/kubehive-io/objectlens/helm-chart \
  --version 0.1.0 \
  --namespace objectlens \
  --create-namespace \
  --set backend.env.CEPH_S3_ENDPOINT_URL="https://your-ceph-rgw:9000" \
  --set backend.env.CEPH_S3_ACCESS_KEY_ID="your-access-key" \
  --set backend.env.CEPH_S3_SECRET_ACCESS_KEY="your-secret-key"
```

For more configuration settings, refer to [values.yaml](chart/values.yaml) and the **S3 Connection Settings** guide in our documentation.

---

## Quick Start (Local Docker Compose)

To spin up the entire ObjectLens stack locally with a mock MinIO S3 storage backend:

```bash
docker compose -f example/docker-compose.yaml up --build
```

This starts:
- **Frontend UI**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **MinIO Console**: `http://localhost:9001` (login with `minioadmin` / `minioadmin`)