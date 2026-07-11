# Development

This guide covers local development setup, workflow, and instructions for contributing to ObjectLens.

## Requirements

Install only:

- Git
- Devbox

Devbox provides Python, uv, Node.js, Just, MkDocs, and other local tools used by the project.

## Local Setup & Workflow

To set up your local development environment:

```bash
git clone <repo>
cd objectlens

devbox shell
cp example/.env.example .env
just install
just dev
```

Open:
- **Frontend**: `http://localhost:3000`
- **Backend Swagger UI**: `http://localhost:8000/docs`

After dependencies are installed, you can also run the dev environment using a single command:

```bash
devbox run dev
```

## Local S3-Compatible Endpoint

The default `example/.env.example` points at a local S3-compatible endpoint (MinIO):

```env
OBJECTLENS_PROVIDER=ceph
CEPH_S3_ENDPOINT_URL=http://localhost:9000
CEPH_S3_REGION=us-east-1
CEPH_S3_ACCESS_KEY_ID=minioadmin
CEPH_S3_SECRET_ACCESS_KEY=minioadmin
CEPH_S3_DEFAULT_BUCKET=objectlens-demo
CEPH_S3_VERIFY_SSL=false
```

For local development, you can spin up this MinIO service by running the Docker Compose stack (or via the shortcuts below).

---

## Commands

We use `just` for orchestrating development commands:

```bash
just install       # Install frontend and backend dependencies
just dev           # Run frontend and backend servers concurrently
just backend       # Run the FastAPI backend only
just frontend      # Run the Nuxt frontend only
just lint          # Run ruff and frontend typechecks
just format        # Format Python and frontend code
just test          # Run backend unit and integration tests
just clean         # Clean up build/package artifacts
```

## Manual Sub-Project Commands

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
uv run ruff check .
uv run pytest
```

### Frontend

The Nuxt 4 app lives under `frontend/app`.

```bash
cd frontend
npm install
npm run dev
npm run build
```

## Kubernetes & Helm (Local Testing)

To test the Helm chart deployment locally with your in-development files:

```bash
# Apply local Helm chart
helm upgrade --install objectlens chart/ --namespace objectlens --create-namespace

# Or using the 'just' shortcut:
just k8s-apply
```

This deploys the backend and frontend services directly from the local `chart/` directory.

To customize local Helm variables (e.g. override defaults):

```bash
helm upgrade --install objectlens chart/ \
  --namespace objectlens \
  --create-namespace \
  --set backend.env.CEPH_S3_ENDPOINT_URL="http://your-s3-endpoint:9000"
```

To clean up and uninstall the local release:

```bash
helm uninstall objectlens --namespace objectlens

# Or using the 'just' shortcut:
just k8s-delete
```

## Documentation

Serve docs locally:

```bash
just docs
```

Open: `http://localhost:8080`

Build docs strictly:

```bash
just docs-build
```
