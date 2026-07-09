from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    and_,
    create_engine,
    desc,
    func,
    inspect,
    literal,
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
    Column("provider", String, primary_key=True),
    Column("bucket", String, primary_key=True),
    Column("key", String, primary_key=True),
    Column("size", Integer, nullable=False),
    Column("etag", String),
    Column("last_modified", DateTime(timezone=True)),
    Column("storage_class", String),
    Column("content_type", String),
    Column("metadata", JSON),
    Column("indexed_at", DateTime(timezone=True), nullable=False),
)

prefix_index_state = Table(
    "prefix_index_state",
    metadata,
    Column("provider", String, primary_key=True),
    Column("bucket", String, primary_key=True),
    Column("prefix", String, primary_key=True),
    Column("indexed_at", DateTime(timezone=True), nullable=False),
)

object_prefixes = Table(
    "object_prefixes",
    metadata,
    Column("provider", String, primary_key=True),
    Column("bucket", String, primary_key=True),
    Column("parent_prefix", String, primary_key=True),
    Column("prefix", String, primary_key=True),
    Column("name", String, nullable=False),
    Column("object_count", Integer, nullable=False, default=0),
    Column("indexed_at", DateTime(timezone=True), nullable=False),
)

Index("ix_object_metadata_provider_bucket", object_metadata.c.provider, object_metadata.c.bucket)
Index(
    "ix_object_metadata_provider_bucket_key",
    object_metadata.c.provider,
    object_metadata.c.bucket,
    object_metadata.c.key,
)
Index(
    "ix_object_metadata_provider_bucket_last_modified",
    object_metadata.c.provider,
    object_metadata.c.bucket,
    object_metadata.c.last_modified,
)
Index(
    "ix_object_metadata_provider_bucket_size",
    object_metadata.c.provider,
    object_metadata.c.bucket,
    object_metadata.c.size,
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
    engine = get_engine()
    inspector = inspect(engine)
    if inspector.has_table("object_metadata"):
        primary_key = inspector.get_pk_constraint("object_metadata").get("constrained_columns", [])
        if primary_key != ["provider", "bucket", "key"]:
            object_metadata.drop(engine)
    metadata.create_all(engine)
    for index in object_metadata.indexes:
        index.create(bind=engine, checkfirst=True)


def _normalize_dt(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def upsert_objects(provider: str, bucket: str, objects: list[dict[str, Any]]) -> int:
    indexed_at = datetime.now(UTC)
    rows = [
        {
            "provider": provider,
            "bucket": bucket,
            "key": obj["key"],
            "size": obj["size"],
            "etag": obj.get("etag"),
            "last_modified": _normalize_dt(obj.get("last_modified")),
            "storage_class": obj.get("storage_class"),
            "content_type": obj.get("content_type"),
            "metadata": obj.get("metadata") or {},
            "indexed_at": indexed_at,
        }
        for obj in objects
    ]
    if not rows:
        return 0

    insert_stmt = sqlite_insert(object_metadata).values(rows)
    update_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["provider", "bucket", "key"],
        set_={
            "size": insert_stmt.excluded.size,
            "etag": insert_stmt.excluded.etag,
            "last_modified": insert_stmt.excluded.last_modified,
            "storage_class": insert_stmt.excluded.storage_class,
            "content_type": insert_stmt.excluded.content_type,
            "metadata": insert_stmt.excluded.metadata,
            "indexed_at": insert_stmt.excluded.indexed_at,
        },
    )
    with get_engine().begin() as conn:
        conn.execute(update_stmt)
    return len(rows)


def is_prefix_indexed(provider: str, bucket: str, prefix: str) -> bool:
    statement = (
        select(prefix_index_state.c.indexed_at)
        .where(prefix_index_state.c.provider == provider)
        .where(prefix_index_state.c.bucket == bucket)
        .where(prefix_index_state.c.prefix == prefix)
        .limit(1)
    )
    with get_engine().connect() as conn:
        return conn.execute(statement).first() is not None


def mark_prefix_indexed(provider: str, bucket: str, prefix: str) -> None:
    insert_stmt = sqlite_insert(prefix_index_state).values(
        provider=provider,
        bucket=bucket,
        prefix=prefix,
        indexed_at=datetime.now(UTC),
    )
    update_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["provider", "bucket", "prefix"],
        set_={"indexed_at": insert_stmt.excluded.indexed_at},
    )
    with get_engine().begin() as conn:
        conn.execute(update_stmt)


def upsert_prefixes(
    provider: str,
    bucket: str,
    parent_prefix: str,
    prefixes: list[dict[str, Any]],
) -> int:
    indexed_at = datetime.now(UTC)
    rows = [
        {
            "provider": provider,
            "bucket": bucket,
            "parent_prefix": parent_prefix,
            "prefix": item["prefix"],
            "name": item["name"],
            "object_count": item.get("object_count") or 0,
            "indexed_at": indexed_at,
        }
        for item in prefixes
    ]
    if not rows:
        return 0

    insert_stmt = sqlite_insert(object_prefixes).values(rows)
    update_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["provider", "bucket", "parent_prefix", "prefix"],
        set_={
            "name": insert_stmt.excluded.name,
            "object_count": insert_stmt.excluded.object_count,
            "indexed_at": insert_stmt.excluded.indexed_at,
        },
    )
    with get_engine().begin() as conn:
        conn.execute(update_stmt)
    return len(rows)


def indexed_common_prefixes(provider: str, bucket: str, parent_prefix: str) -> list[dict[str, Any]]:
    statement = (
        select(object_prefixes)
        .where(object_prefixes.c.provider == provider)
        .where(object_prefixes.c.bucket == bucket)
        .where(object_prefixes.c.parent_prefix == parent_prefix)
        .order_by(object_prefixes.c.prefix.asc())
    )
    with get_engine().connect() as conn:
        rows = conn.execute(statement).mappings().all()
    return [dict(row) for row in rows]


def search_objects(
    provider: str,
    bucket: str,
    prefix: str | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    clauses = [object_metadata.c.provider == provider, object_metadata.c.bucket == bucket]
    if prefix:
        clauses.append(object_metadata.c.key.like(f"{prefix}%"))
    if search:
        clauses.append(object_metadata.c.key.like(f"%{search}%"))

    statement = (
        select(object_metadata)
        .where(and_(*clauses))
        .order_by(desc(object_metadata.c.last_modified), object_metadata.c.key.asc())
        .limit(limit)
        .offset(offset)
    )

    with get_engine().connect() as conn:
        rows = conn.execute(statement).mappings().all()
    return [dict(row) for row in rows]


def count_objects(
    provider: str,
    bucket: str,
    prefix: str | None = None,
    search: str | None = None,
    direct_only: bool = False,
    delimiter: str = "/",
) -> int:
    clauses = [object_metadata.c.provider == provider, object_metadata.c.bucket == bucket]
    normalized_prefix = prefix or ""
    if normalized_prefix:
        clauses.append(object_metadata.c.key.like(f"{normalized_prefix}%"))
    if search:
        clauses.append(object_metadata.c.key.like(f"%{search}%"))
    if direct_only:
        suffix = func.substr(object_metadata.c.key, len(normalized_prefix) + 1)
        clauses.append(func.instr(suffix, delimiter) == 0)

    statement = select(func.count()).where(and_(*clauses))
    with get_engine().connect() as conn:
        return int(conn.execute(statement).scalar_one())


def direct_child_objects(
    provider: str,
    bucket: str,
    prefix: str = "",
    delimiter: str = "/",
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    clauses = [object_metadata.c.provider == provider, object_metadata.c.bucket == bucket]
    if prefix:
        clauses.append(object_metadata.c.key.like(f"{prefix}%"))
    suffix = func.substr(object_metadata.c.key, len(prefix) + 1)
    clauses.append(func.instr(suffix, delimiter) == 0)

    statement = (
        select(object_metadata)
        .where(and_(*clauses))
        .order_by(object_metadata.c.key.asc())
        .limit(limit)
        .offset(offset)
    )
    with get_engine().connect() as conn:
        rows = conn.execute(statement).mappings().all()
    return [dict(row) for row in rows]


def common_prefixes(
    provider: str,
    bucket: str,
    prefix: str = "",
    delimiter: str = "/",
) -> list[dict[str, Any]]:
    clauses = [object_metadata.c.provider == provider, object_metadata.c.bucket == bucket]
    if prefix:
        clauses.append(object_metadata.c.key.like(f"{prefix}%"))

    suffix = func.substr(object_metadata.c.key, len(prefix) + 1)
    delimiter_position = func.instr(suffix, delimiter)
    common_prefix = literal(prefix) + func.substr(suffix, 1, delimiter_position)
    statement = (
        select(
            common_prefix.label("prefix"),
            func.count().label("object_count"),
        )
        .where(and_(*clauses))
        .where(delimiter_position > 0)
        .group_by(common_prefix)
        .order_by(common_prefix.asc())
    )

    with get_engine().connect() as conn:
        rows = conn.execute(statement).mappings().all()

    return [
        {
            "name": row["prefix"][len(prefix) :],
            "prefix": row["prefix"],
            "object_count": row["object_count"],
        }
        for row in rows
    ]


def bucket_index_stats(provider: str, bucket: str) -> dict[str, Any]:
    statement = (
        select(
            func.count().label("object_count"),
            func.coalesce(func.sum(object_metadata.c.size), 0).label("total_size"),
            func.max(object_metadata.c.indexed_at).label("last_indexed_at"),
        )
        .where(object_metadata.c.provider == provider)
        .where(object_metadata.c.bucket == bucket)
    )
    with get_engine().connect() as conn:
        row = conn.execute(statement).mappings().one()
    return dict(row)


def recent_objects(provider: str, bucket: str, limit: int = 10) -> list[dict[str, Any]]:
    statement = (
        select(object_metadata)
        .where(object_metadata.c.provider == provider)
        .where(object_metadata.c.bucket == bucket)
        .order_by(desc(object_metadata.c.last_modified), object_metadata.c.key.asc())
        .limit(limit)
    )
    with get_engine().connect() as conn:
        rows = conn.execute(statement).mappings().all()
    return [dict(row) for row in rows]


def largest_objects(provider: str, bucket: str, limit: int = 10) -> list[dict[str, Any]]:
    statement = (
        select(object_metadata)
        .where(object_metadata.c.provider == provider)
        .where(object_metadata.c.bucket == bucket)
        .order_by(desc(object_metadata.c.size), object_metadata.c.key.asc())
        .limit(limit)
    )
    with get_engine().connect() as conn:
        rows = conn.execute(statement).mappings().all()
    return [dict(row) for row in rows]


def top_prefixes(provider: str, bucket: str, limit: int = 10) -> list[dict[str, Any]]:
    rows = search_objects(provider=provider, bucket=bucket, limit=1000)
    summaries: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row["key"]
        prefix = key.split("/", 1)[0] + "/" if "/" in key else "(root)"
        summary = summaries.setdefault(
            prefix,
            {"prefix": prefix, "object_count": 0, "total_size": 0},
        )
        summary["object_count"] += 1
        summary["total_size"] += row["size"]
    return sorted(
        summaries.values(),
        key=lambda item: (item["object_count"], item["total_size"], item["prefix"]),
        reverse=True,
    )[:limit]
