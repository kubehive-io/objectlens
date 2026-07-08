from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import init_db
from .routers import buckets, health, index, objects

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")

# TODO: Add OIDC login and RBAC enforcement before production use.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


app.include_router(health.router)
app.include_router(buckets.router)
app.include_router(objects.router)
app.include_router(index.router)
