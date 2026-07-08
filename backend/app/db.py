from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    and_,
    create_engine,
    desc,
    select,
)
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import Engine

from .config import get_settings

# TODO: Replace SQLite with Postgres for shared production deployments.

metadata = MetaData()

object_metadata = Table(
    "object_metadata",
    metadata,
    Column("bucket", String, primary_key=True),
    Column("key", String, primary_key=True),
    Column("size", Integer, nullable=False),
    Column("etag", String),
    Column("last_modified", DateTime(timezone=True)),
    Column("storage_class", String),
    Column("content_type", String),
    Column("indexed_at", DateTime(timezone=True), nullable=False),
)


def _database_url() -> str:
    database_url = get_settings().database_url
    if not database_url.startswith("sqlite:///"):
        raise ValueError("Only sqlite:/// DATABASE_URL values are supported in the PoC")
    return database_url


@lru_cache
def get_engine() -> Engine:
    return create_engine(_database_url(), future=True)


def init_db() -> None:
    metadata.create_all(get_engine())


def _normalize_dt(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def upsert_objects(bucket: str, objects: list[dict[str, Any]]) -> int:
    indexed_at = datetime.now(UTC)
    rows = [
        {
            "bucket": bucket,
            "key": obj["key"],
            "size": obj["size"],
            "etag": obj.get("etag"),
            "last_modified": _normalize_dt(obj.get("last_modified")),
            "storage_class": obj.get("storage_class"),
            "content_type": obj.get("content_type"),
            "indexed_at": indexed_at,
        }
        for obj in objects
    ]
    if not rows:
        return 0

    insert_stmt = sqlite_insert(object_metadata).values(rows)
    update_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["bucket", "key"],
        set_={
            "size": insert_stmt.excluded.size,
            "etag": insert_stmt.excluded.etag,
            "last_modified": insert_stmt.excluded.last_modified,
            "storage_class": insert_stmt.excluded.storage_class,
            "content_type": insert_stmt.excluded.content_type,
            "indexed_at": insert_stmt.excluded.indexed_at,
        },
    )
    with get_engine().begin() as conn:
        conn.execute(update_stmt)
    return len(rows)


def search_objects(
    bucket: str,
    prefix: str | None = None,
    search: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    clauses = [object_metadata.c.bucket == bucket]
    if prefix:
        clauses.append(object_metadata.c.key.like(f"{prefix}%"))
    if search:
        clauses.append(object_metadata.c.key.like(f"%{search}%"))

    statement = (
        select(object_metadata)
        .where(and_(*clauses))
        .order_by(desc(object_metadata.c.last_modified), object_metadata.c.key.asc())
        .limit(limit)
    )

    with get_engine().connect() as conn:
        rows = conn.execute(statement).mappings().all()
    return [dict(row) for row in rows]
