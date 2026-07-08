# ObjectLens Backend

FastAPI backend for ObjectLens. It talks to object storage through provider implementations, starting with Ceph RGW through the S3-compatible API, and stores indexed object metadata in SQLite for the PoC.

## Development

```bash
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Quality

```bash
uv run ruff check .
uv run ruff format .
uv run pytest
```

## Configuration

Settings use the `OBJECTLENS_` prefix. See the root README for the full environment variable table.
