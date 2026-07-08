from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException, Query

from ..config import get_settings
from ..db import (
    bucket_index_stats,
    common_prefixes,
    count_objects,
    direct_child_objects,
    largest_objects,
    recent_objects,
    search_objects,
    top_prefixes,
)
from ..models import (
    Bucket,
    BucketDetailsResponse,
    BucketListResponse,
    BucketObjectListing,
    BucketPrefix,
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

    if search:
        rows = search_objects(
            provider=provider.provider,
            bucket=bucket,
            prefix=normalized_prefix,
            search=search,
            limit=limit,
            offset=offset,
        )
        prefixes = []
        total_objects = count_objects(
            provider=provider.provider,
            bucket=bucket,
            prefix=normalized_prefix,
            search=search,
        )
        mode = "search"
    else:
        rows = direct_child_objects(
            provider=provider.provider,
            bucket=bucket,
            prefix=normalized_prefix,
            delimiter=delimiter or "/",
            limit=limit,
            offset=offset,
        )
        prefixes = [
            BucketPrefix.model_validate(row)
            for row in common_prefixes(
                provider=provider.provider,
                bucket=bucket,
                prefix=normalized_prefix,
                delimiter=delimiter or "/",
            )
        ]
        total_objects = count_objects(
            provider=provider.provider,
            bucket=bucket,
            prefix=normalized_prefix,
            direct_only=True,
            delimiter=delimiter or "/",
        )
        mode = "browse"

    objects = [ObjectMetadata.model_validate(row) for row in rows]
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
        objects=objects,
        prefixes=prefixes,
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
