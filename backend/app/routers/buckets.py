from fnmatch import fnmatchcase

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException, Query

from ..config import get_settings
from ..db import (
    bucket_index_stats,
    common_prefixes,
    count_objects,
    direct_child_objects,
    indexed_common_prefixes,
    is_prefix_indexed,
    largest_objects,
    mark_prefix_indexed,
    recent_objects,
    search_objects,
    top_prefixes,
    upsert_objects,
    upsert_prefixes,
)
from ..models import (
    Bucket,
    BucketBrowserItem,
    BucketDetailsResponse,
    BucketListResponse,
    BucketObjectListing,
    BucketSettingsResponse,
    BucketSummaryResponse,
    ObjectMetadata,
    Pagination,
    PrefixSummary,
)
from ..providers import get_provider, get_provider_by_id

router = APIRouter(tags=["buckets"])


def _provider_or_error(provider_id: str | None = None):
    try:
        if provider_id:
            return get_provider_by_id(provider_id)
        return get_provider(get_settings())
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _provider_key(provider) -> str:
    return getattr(provider, "connection_id", provider.provider)


def _storage_error(message: str, exc: Exception) -> HTTPException:
    if isinstance(exc, ClientError):
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"AccessDenied", "AllAccessDisabled", "Unauthorized", "Forbidden", "403"}:
            return HTTPException(
                status_code=403,
                detail=f"{message}: credentials are not allowed. {exc}",
            )
    return HTTPException(status_code=502, detail=f"{message}: {exc}")


def _object_icon(key: str, content_type: str | None) -> str:
    lower_key = key.lower()
    lower_content_type = (content_type or "").lower()
    if "json" in lower_content_type or lower_key.endswith(".json"):
        return "json"
    if "csv" in lower_content_type or lower_key.endswith(".csv"):
        return "csv"
    if lower_key.endswith(".parquet"):
        return "parquet"
    is_image = lower_content_type.startswith("image/") or lower_key.endswith(
        (".png", ".jpg", ".jpeg", ".webp", ".gif")
    )
    if is_image:
        return "image"
    return "file"


def _object_name(key: str, prefix: str) -> str:
    return key[len(prefix) :] if prefix and key.startswith(prefix) else key


def _glob_literal(pattern: str) -> str | None:
    tokens = [token for token in pattern.replace("?", "*").split("*") if token]
    if not tokens:
        return None
    return max(tokens, key=len)


def _glob_matches(pattern: str, value: str) -> bool:
    return fnmatchcase(value.casefold(), pattern.casefold())


def _prefix_item(row: dict) -> BucketBrowserItem:
    return BucketBrowserItem(
        type="prefix",
        name=row["name"],
        prefix=row["prefix"],
        icon="folder",
    )


def _object_item(object_row: ObjectMetadata, prefix: str) -> BucketBrowserItem:
    return BucketBrowserItem(
        type="object",
        name=_object_name(object_row.key, prefix),
        key=object_row.key,
        size=object_row.size,
        content_type=object_row.content_type,
        storage_class=object_row.storage_class,
        last_modified=object_row.last_modified,
        icon=_object_icon(object_row.key, object_row.content_type),
    )


def _ensure_prefix_indexed(
    provider,
    bucket: str,
    prefix: str,
    delimiter: str,
    limit: int,
    offset: int,
) -> None:
    provider_key = _provider_key(provider)
    if is_prefix_indexed(provider_key, bucket, prefix):
        return
    continuation_token = None
    pages_to_fetch = max(1, (offset // limit) + 1)
    result = None
    for _ in range(pages_to_fetch):
        result = provider.list_objects(
            bucket=bucket,
            prefix=prefix or None,
            delimiter=delimiter,
            continuation_token=continuation_token,
            limit=limit,
        )
        upsertable = [obj.model_dump() for obj in result.objects]
        if upsertable:
            upsert_objects(provider_key, bucket, upsertable)
        prefix_rows = [item.model_dump() for item in result.prefixes]
        if prefix_rows:
            upsert_prefixes(provider_key, bucket, prefix, prefix_rows)
        if not result.next_continuation_token:
            mark_prefix_indexed(provider_key, bucket, prefix)
            break
        continuation_token = result.next_continuation_token


@router.get("/buckets", response_model=BucketListResponse)
def list_buckets() -> BucketListResponse:
    return list_provider_buckets(None)


@router.get("/providers/{provider_id}/buckets", response_model=BucketListResponse)
def list_provider_buckets(provider_id: str | None = None) -> BucketListResponse:
    try:
        provider = _provider_or_error(provider_id)
        buckets = provider.list_buckets()
    except (BotoCoreError, ClientError) as exc:
        raise _storage_error(
            "Failed to list buckets. The configured provider credentials cannot list "
            "visible buckets",
            exc,
        ) from exc

    return BucketListResponse(
        buckets=[Bucket(name=bucket.name, creation_date=bucket.creation_date) for bucket in buckets]
    )


@router.get("/buckets/{bucket}/objects", response_model=BucketObjectListing)
def bucket_objects(
    bucket: str,
    prefix: str = Query(default=""),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    delimiter: str | None = Query(default="/"),
) -> BucketObjectListing:
    return provider_bucket_objects(None, bucket, prefix, search, limit, offset, delimiter)


@router.get("/providers/{provider_id}/buckets/{bucket}/objects", response_model=BucketObjectListing)
def provider_bucket_objects(
    provider_id: str | None,
    bucket: str,
    prefix: str = Query(default=""),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    delimiter: str | None = Query(default="/"),
) -> BucketObjectListing:
    provider = _provider_or_error(provider_id)
    provider_key = _provider_key(provider)
    normalized_prefix = prefix or ""
    normalized_delimiter = delimiter or "/"

    try:
        _ensure_prefix_indexed(
            provider,
            bucket=bucket,
            prefix=normalized_prefix,
            delimiter=normalized_delimiter,
            limit=limit,
            offset=offset,
        )
    except (BotoCoreError, ClientError) as exc:
        raise _storage_error(f"Failed to lazily index prefix {normalized_prefix}", exc) from exc

    if search:
        pattern = search.strip()
        broad_search = _glob_literal(pattern)
        rows = search_objects(
            provider=provider_key,
            bucket=bucket,
            prefix=normalized_prefix,
            search=broad_search,
            limit=10000,
            offset=0,
        )
        derived_prefix_rows = common_prefixes(
            provider=provider_key,
            bucket=bucket,
            prefix=normalized_prefix,
            delimiter=normalized_delimiter,
        )
        stored_prefix_rows = indexed_common_prefixes(
            provider_key,
            bucket,
            normalized_prefix,
        )

        prefix_rows_by_prefix = {}
        object_rows_by_key = {}
        for row in [*stored_prefix_rows, *derived_prefix_rows]:
            if _glob_matches(pattern, row["name"]) or _glob_matches(
                pattern, row["name"].rstrip(normalized_delimiter)
            ):
                prefix_rows_by_prefix[row["prefix"]] = row

        for row in rows:
            object_row = ObjectMetadata.model_validate(row)
            visible_name = _object_name(object_row.key, normalized_prefix)
            visible_leaf = visible_name.rsplit(normalized_delimiter, 1)[-1]
            if not (_glob_matches(pattern, visible_name) or _glob_matches(pattern, visible_leaf)):
                continue
            if normalized_delimiter in visible_name:
                prefix_name = visible_name.split(normalized_delimiter, 1)[0] + normalized_delimiter
                child_prefix = f"{normalized_prefix}{prefix_name}"
                prefix_rows_by_prefix.setdefault(
                    child_prefix,
                    {"name": prefix_name, "prefix": child_prefix, "object_count": 0},
                )
            else:
                object_rows_by_key[object_row.key] = object_row

        prefix_items = [
            _prefix_item(row)
            for row in sorted(prefix_rows_by_prefix.values(), key=lambda item: item["prefix"])
        ]
        object_items = [
            _object_item(row, normalized_prefix)
            for row in sorted(object_rows_by_key.values(), key=lambda item: item.key)
        ]
        mode = "search"
        all_items = prefix_items + object_items
        total_items = len(all_items)
        items = all_items[offset : offset + limit]
    else:
        derived_prefix_rows = common_prefixes(
            provider=provider_key,
            bucket=bucket,
            prefix=normalized_prefix,
            delimiter=normalized_delimiter,
        )
        stored_prefix_rows = indexed_common_prefixes(
            provider_key,
            bucket,
            normalized_prefix,
        )
        prefix_rows_by_prefix = {
            row["prefix"]: row for row in [*stored_prefix_rows, *derived_prefix_rows]
        }
        prefix_rows = sorted(prefix_rows_by_prefix.values(), key=lambda row: row["prefix"])
        total_direct_objects = count_objects(
            provider=provider_key,
            bucket=bucket,
            prefix=normalized_prefix,
            direct_only=True,
            delimiter=normalized_delimiter,
        )
        prefix_slice = prefix_rows[offset : offset + limit]
        remaining_limit = max(limit - len(prefix_slice), 0)
        object_offset = max(offset - len(prefix_rows), 0)
        rows = (
            direct_child_objects(
                provider=provider_key,
                bucket=bucket,
                prefix=normalized_prefix,
                delimiter=normalized_delimiter,
                limit=remaining_limit,
                offset=object_offset,
            )
            if remaining_limit
            else []
        )
        mode = "browse"
        objects = [ObjectMetadata.model_validate(row) for row in rows]
        items = [_prefix_item(row) for row in prefix_slice] + [
            _object_item(object_row, normalized_prefix) for object_row in objects
        ]
        total_items = len(prefix_rows) + total_direct_objects

    has_previous = offset > 0
    next_offset = offset + limit if offset + len(items) < total_items else None
    previous_offset = max(offset - limit, 0) if has_previous else None
    return BucketObjectListing(
        bucket=bucket,
        prefix=normalized_prefix,
        delimiter=delimiter,
        mode=mode,
        limit=limit,
        offset=offset,
        total_objects=total_items,
        items=items,
        pagination=Pagination(
            limit=limit,
            offset=offset,
            next_offset=next_offset,
            previous_offset=previous_offset,
            has_next=next_offset is not None,
            has_previous=has_previous,
        ),
    )


@router.get("/buckets/{bucket}/summary", response_model=BucketSummaryResponse)
def bucket_summary(bucket: str) -> BucketSummaryResponse:
    return provider_bucket_summary(None, bucket)


@router.get(
    "/providers/{provider_id}/buckets/{bucket}/summary",
    response_model=BucketSummaryResponse,
)
def provider_bucket_summary(provider_id: str | None, bucket: str) -> BucketSummaryResponse:
    provider = _provider_or_error(provider_id)
    provider_key = _provider_key(provider)
    stats = bucket_index_stats(provider_key, bucket)
    return BucketSummaryResponse(
        provider=provider.provider,
        bucket=bucket,
        indexed_object_count=stats["object_count"],
        indexed_total_size=stats["total_size"],
        last_indexed_at=stats["last_indexed_at"],
        largest_objects=[
            ObjectMetadata.model_validate(row) for row in largest_objects(provider_key, bucket)
        ],
        recent_objects=[
            ObjectMetadata.model_validate(row) for row in recent_objects(provider_key, bucket)
        ],
        top_prefixes=[
            PrefixSummary.model_validate(row) for row in top_prefixes(provider_key, bucket)
        ],
    )


@router.get("/buckets/{bucket}", response_model=BucketDetailsResponse)
def bucket_details(bucket: str) -> BucketDetailsResponse:
    return provider_bucket_details(None, bucket)


@router.get("/providers/{provider_id}/buckets/{bucket}", response_model=BucketDetailsResponse)
def provider_bucket_details(provider_id: str | None, bucket: str) -> BucketDetailsResponse:
    try:
        provider = _provider_or_error(provider_id)
        details = provider.get_bucket_info(bucket)
    except (BotoCoreError, ClientError) as exc:
        raise _storage_error(f"Failed to read bucket details for {bucket}", exc) from exc

    stats = bucket_index_stats(_provider_key(provider), bucket)
    provider_key = _provider_key(provider)
    return BucketDetailsResponse(
        provider=provider.provider,
        provider_id=provider_key,
        provider_name=getattr(provider, "connection_name", provider.display_name),
        name=details.name,
        bucket=details.name,
        creation_date=details.creation_date,
        indexed_object_count=stats["object_count"],
        indexed_total_size=stats["total_size"],
        last_indexed_at=stats["last_indexed_at"],
        largest_objects=[
            ObjectMetadata.model_validate(row) for row in largest_objects(provider_key, bucket)
        ],
        recent_objects=[
            ObjectMetadata.model_validate(row) for row in recent_objects(provider_key, bucket)
        ],
        top_prefixes=[
            PrefixSummary.model_validate(row) for row in top_prefixes(provider_key, bucket)
        ],
    )


@router.get(
    "/providers/{provider_id}/buckets/{bucket}/settings",
    response_model=BucketSettingsResponse,
)
def provider_bucket_settings(provider_id: str, bucket: str) -> BucketSettingsResponse:
    _provider_or_error(provider_id)
    return BucketSettingsResponse(bucket=bucket, provider_id=provider_id)
