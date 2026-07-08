from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException, Query

from ..config import get_settings
from ..db import search_objects
from ..models import (
    ObjectListResponse,
    ObjectMetadata,
    ObjectPreviewResponse,
    PresignDownloadResponse,
)
from ..providers import get_provider

router = APIRouter(tags=["objects"])


@router.get("/objects", response_model=ObjectListResponse)
def objects(
    bucket: str = Query(..., min_length=1),
    prefix: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> ObjectListResponse:
    # TODO: Add OpenSearch support for large-scale metadata search.
    provider = get_provider(get_settings())
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


@router.get("/objects/metadata", response_model=ObjectMetadata)
def object_metadata(
    bucket: str = Query(..., min_length=1),
    key: str = Query(..., min_length=1),
) -> ObjectMetadata:
    try:
        provider = get_provider(get_settings())
        metadata = provider.get_object_metadata(bucket=bucket, key=key)
    except (BotoCoreError, ClientError) as exc:
        detail = f"Failed to read object metadata: {exc}"
        raise HTTPException(status_code=502, detail=detail) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ObjectMetadata(
        provider=provider.provider,
        bucket=bucket,
        indexed_at=metadata.last_modified,
        **metadata.model_dump(),
    )


@router.get("/objects/preview", response_model=ObjectPreviewResponse)
def object_preview(
    bucket: str = Query(..., min_length=1),
    key: str = Query(..., min_length=1),
    max_bytes: int = Query(default=1024 * 1024, ge=1024, le=5 * 1024 * 1024),
) -> ObjectPreviewResponse:
    try:
        provider = get_provider(get_settings())
        preview = provider.get_object_preview(bucket=bucket, key=key, max_bytes=max_bytes)
    except (BotoCoreError, ClientError) as exc:
        detail = f"Failed to create object preview: {exc}"
        raise HTTPException(status_code=502, detail=detail) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ObjectPreviewResponse.model_validate(preview.model_dump())


@router.get("/objects/presign-download", response_model=PresignDownloadResponse)
def presign_download(
    bucket: str = Query(..., min_length=1),
    key: str = Query(..., min_length=1),
) -> PresignDownloadResponse:
    try:
        provider = get_provider(get_settings())
        url = provider.get_presigned_download_url(bucket=bucket, key=key)
    except (BotoCoreError, ClientError) as exc:
        detail = f"Failed to create download URL: {exc}"
        raise HTTPException(status_code=502, detail=detail) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return PresignDownloadResponse(bucket=bucket, key=key, url=url)
