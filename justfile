set dotenv-load := true
set dotenv-filename := ".env"

install:
    cd backend && uv sync
    cd frontend && npm install

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

format:
    cd backend && uv run ruff format .

test:
    cd backend && uv run pytest

docs:
    mkdocs serve --dev-addr 0.0.0.0:8080

docs-build:
    mkdocs build --strict

clean:
    rm -rf backend/.venv frontend/node_modules frontend/.nuxt frontend/.output .pytest_cache .ruff_cache

docker-up:
    docker compose up --build

docker-down:
    docker compose down

k8s-apply:
    helm upgrade --install objectlens chart/ --namespace objectlens --create-namespace

k8s-delete:
    helm uninstall objectlens --namespace objectlens
