# Development

## Local Workflow

```bash
devbox shell
cp example/.env.example .env
just install
just dev
```

The frontend runs at:

```text
http://localhost:3000
```

The backend Swagger UI runs at:

```text
http://localhost:8000/docs
```

## Commands

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

## Documentation

Serve docs locally:

```bash
just docs
```

Open:

```text
http://localhost:8080
```

Build docs strictly:

```bash
just docs-build
```

## Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
uv run ruff check .
uv run pytest
```

## Frontend

```bash
cd frontend
npm install
npm run dev
npm run build
```

The Nuxt 4 app lives under `frontend/app`.
