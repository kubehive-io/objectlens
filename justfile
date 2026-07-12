compose := if `which podman 2>/dev/null` != "" { "podman compose" } else { "docker compose" }

set dotenv-load := true
set dotenv-filename := ".env"

install:
    cd backend && uv sync
    cd frontend && npm install
    cd mcp-server && uv sync

backend:
    cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
    cd frontend && npm run dev

dev:
    @echo "Starting ObjectLens backend and frontend"
    @trap 'kill 0' INT TERM EXIT; just backend & just frontend & wait

lint:
    cd backend && uv run ruff check .
    cd frontend && npm run lint
    cd mcp-server && uv run ruff check .

format:
    cd backend && uv run ruff format .
    cd mcp-server && uv run ruff format .

test:
    cd backend && uv run pytest
    cd mcp-server && uv run pytest

docs:
    mkdocs serve --dev-addr 0.0.0.0:8080

docs-build:
    mkdocs build --strict

docs-multi:
    @echo "=================================================="
    @echo "🎉 Multi-version docs are ready for testing!"
    @echo "🚀 Opening local server..."
    @echo "👉 Preview at: http://localhost:8000"
    @echo "=================================================="
    uv run --with mkdocs-material --with mike mike deploy --branch github-doc dev
    uv run --with mkdocs-material --with mike mike deploy --branch github-doc 0.1.0 latest
    uv run --with mkdocs-material --with mike mike set-default --branch github-doc latest
    uv run --with mkdocs-material --with mike mike serve --branch github-doc

clean:
    rm -rf backend/.venv frontend/node_modules frontend/.nuxt frontend/.output .pytest_cache .ruff_cache

docker-up:
    {{compose}} -f example/development/docker-compose.yaml up --build

docker-down:
    {{compose}} -f example/development/docker-compose.yaml down

docker-garage-up:
    {{compose}} -f example/garage/docker-compose.yaml up --build

init-garage:
    #!/bin/sh
    NODE_ID=$({{compose}} -f example/garage/docker-compose.yaml exec garage /garage status 2>&1 | grep -oE "[0-9a-f]{16}" | head -n 1 | tr -d '\r' | tr -d '\n'); \
    echo "Discovered Garage Node ID: $NODE_ID"; \
    if [ -n "$NODE_ID" ]; then \
        echo "Assigning node $NODE_ID to local zone..."; \
        {{compose}} -f example/garage/docker-compose.yaml exec garage /garage layout assign $NODE_ID -z local -c 10G || true; \
        echo "Applying layout change..."; \
        {{compose}} -f example/garage/docker-compose.yaml exec garage /garage layout apply --version 1 || true; \
    fi
    echo "Importing custom S3 credentials..."
    {{compose}} -f example/garage/docker-compose.yaml exec garage /garage key import my-custom-user my-custom-secret-key --yes || true
    echo "Creating default S3 bucket..."
    {{compose}} -f example/garage/docker-compose.yaml exec garage /garage bucket create objectlens-demo || true
    echo "Authorizing imported S3 key..."
    {{compose}} -f example/garage/docker-compose.yaml exec garage /garage bucket allow objectlens-demo --read --write --key my-custom-user || true
    echo "S3 Garage initialization completed successfully!"

k8s-apply:
    helm upgrade --install objectlens chart/ --namespace objectlens --create-namespace

k8s-delete:
    helm uninstall objectlens --namespace objectlens
