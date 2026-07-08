set dotenv-load := false

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
    cd frontend && npm run lint || true

format:
    cd backend && uv run ruff format .

test:
    cd backend && uv run pytest

docker-up:
    docker compose up --build

docker-down:
    docker compose down

k8s-apply:
    kubectl apply -f deploy/kubernetes/

k8s-delete:
    kubectl delete -f deploy/kubernetes/
