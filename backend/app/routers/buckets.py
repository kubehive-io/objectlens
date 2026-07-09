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
    BucketSummaryResponse,
    ObjectMetadata,
    Pagination,
    PrefixSummary,
)
from ..providers import get_provider

router = APIRouter(tags=["buckets"])


def _provider_or_error():
    try:
        return get_provider(get_settings())
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


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


def _ensure_prefix_indexed(
    provider,
    bucket: str,
    prefix: str,
    delimiter: str,
    limit: int,
    offset: int,
) -> None:
    if is_prefix_indexed(provider.provider, bucket, prefix):
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
            upsert_objects(provider.provider, bucket, upsertable)
        prefix_rows = [item.model_dump() for item in result.prefixes]
        if prefix_rows:
            upsert_prefixes(provider.provider, bucket, prefix, prefix_rows)
        if not result.next_continuation_token:
            mark_prefix_indexed(provider.provider, bucket, prefix)
            break
        continuation_token = result.next_continuation_token


@router.get("/buckets", response_model=BucketListResponse)
def list_buckets() -> BucketListResponse:
    try:
        provider = _provider_or_error()
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
    provider = _provider_or_error()
    normalized_prefix = prefix or ""
    normalized_delimiter = delimiter or "/"

    if search:
        rows = search_objects(
            provider=provider.provider,
            bucket=bucket,
            prefix=normalized_prefix,
            search=search,
            limit=limit,
            offset=offset,
        )
        total_objects = count_objects(
            provider=provider.provider,
            bucket=bucket,
            prefix=normalized_prefix,
            search=search,
        )
        mode = "search"
        objects = [ObjectMetadata.model_validate(row) for row in rows]
        items = [
            BucketBrowserItem(
                type="object",
                name=_object_name(object_row.key, normalized_prefix),
                key=object_row.key,
                size=object_row.size,
                content_type=object_row.content_type,
                storage_class=object_row.storage_class,
                last_modified=object_row.last_modified,
                icon=_object_icon(object_row.key, object_row.content_type),
            )
            for object_row in objects
        ]
    else:
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

        rows = direct_child_objects(
            provider=provider.provider,
            bucket=bucket,
            prefix=normalized_prefix,
            delimiter=normalized_delimiter,
            limit=limit,
            offset=offset,
        )
        derived_prefix_rows = common_prefixes(
            provider=provider.provider,
            bucket=bucket,
            prefix=normalized_prefix,
            delimiter=normalized_delimiter,
        )
        stored_prefix_rows = indexed_common_prefixes(
            provider.provider,
            bucket,
            normalized_prefix,
        )
        prefix_rows_by_prefix = {
            row["prefix"]: row
            for row in [*stored_prefix_rows, *derived_prefix_rows]
        }
        prefix_rows = sorted(prefix_rows_by_prefix.values(), key=lambda row: row["prefix"])
        total_objects = count_objects(
            provider=provider.provider,
            bucket=bucket,
            prefix=normalized_prefix,
            direct_only=True,
            delimiter=normalized_delimiter,
        )
        mode = "browse"
        objects = [ObjectMetadata.model_validate(row) for row in rows]
        items = [
            BucketBrowserItem(
                type="prefix",
                name=row["name"],
                prefix=row["prefix"],
                icon="folder",
            )
            for row in prefix_rows
        ] + [
            BucketBrowserItem(
                type="object",
                name=_object_name(object_row.key, normalized_prefix),
                key=object_row.key,
                size=object_row.size,
                content_type=object_row.content_type,
                storage_class=object_row.storage_class,
                last_modified=object_row.last_modified,
                icon=_object_icon(object_row.key, object_row.content_type),
            )
            for object_row in objects
        ]

    has_previous = offset > 0
    next_offset = offset + limit if offset + len(objects) < total_objects else None
    previous_offset = max(offset - limit, 0) if has_previous else None
    return BucketObjectListing(
        bucket=bucket,
        prefix=normalized_prefix,
        delimiter=delimiter,
        mode=mode,
        limit=limit,
        offset=offset,
        total_objects=total_objects,
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
    provider = _provider_or_error()
    stats = bucket_index_stats(provider.provider, bucket)
    return BucketSummaryResponse(
        provider=provider.provider,
        bucket=bucket,
        indexed_object_count=stats["object_count"],
        indexed_total_size=stats["total_size"],
        last_indexed_at=stats["last_indexed_at"],
        largest_objects=[
            ObjectMetadata.model_validate(row) for row in largest_objects(provider.provider, bucket)
        ],
        recent_objects=[
            ObjectMetadata.model_validate(row) for row in recent_objects(provider.provider, bucket)
        ],
        top_prefixes=[
            PrefixSummary.model_validate(row) for row in top_prefixes(provider.provider, bucket)
        ],
    )


@router.get("/buckets/{bucket}", response_model=BucketDetailsResponse)
def bucket_details(bucket: str) -> BucketDetailsResponse:
    try:
        provider = _provider_or_error()
        details = provider.get_bucket_info(bucket)
    except (BotoCoreError, ClientError) as exc:
        raise _storage_error(f"Failed to read bucket details for {bucket}", exc) from exc

    stats = bucket_index_stats(provider.provider, bucket)
    return BucketDetailsResponse(
        provider=provider.provider,
        name=details.name,
        creation_date=details.creation_date,
        indexed_object_count=stats["object_count"],
        indexed_total_size=stats["total_size"],
        last_indexed_at=stats["last_indexed_at"],
    )
