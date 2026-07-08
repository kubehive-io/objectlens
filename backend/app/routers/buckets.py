from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException, Query

from ..config import get_settings
from ..db import bucket_index_stats, largest_objects, recent_objects, search_objects, top_prefixes
from ..models import (
    Bucket,
    BucketDetailsResponse,
    BucketListResponse,
    BucketSummaryResponse,
    ObjectListResponse,
    ObjectMetadata,
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


@router.get("/buckets/{bucket}/objects", response_model=ObjectListResponse)
def bucket_objects(
    bucket: str,
    prefix: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> ObjectListResponse:
    provider = _provider_or_error()
    rows = search_objects(
        provider=provider.provider,
        bucket=bucket,
        prefix=prefix,
        search=search,
        limit=limit,
        offset=offset,
    )
    objects = [ObjectMetadata.model_validate(row) for row in rows]
    return ObjectListResponse(objects=objects, count=len(objects))


@router.get("/buckets/{bucket}/summary", response_model=BucketSummaryResponse)
def bucket_summary(bucket: str) -> BucketSummaryResponse:
    provider = _provider_or_error()
    stats = bucket_index_stats(provider.provider, bucket)
    return BucketSummaryResponse(
        bucket=bucket,
        object_count=stats["object_count"],
        total_size=stats["total_size"],
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
