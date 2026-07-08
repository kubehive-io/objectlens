from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException, Query

from ..db import search_objects
from ..models import ObjectListResponse, ObjectMetadata, PresignDownloadResponse
from ..s3_client import get_s3_client

router = APIRouter(tags=["objects"])


@router.get("/objects", response_model=ObjectListResponse)
def objects(
    bucket: str = Query(..., min_length=1),
    prefix: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
) -> ObjectListResponse:
    # TODO: Add OpenSearch support for large-scale metadata search.
    rows = search_objects(bucket=bucket, prefix=prefix, search=search, limit=limit)
    objects = [ObjectMetadata.model_validate(row) for row in rows]
    return ObjectListResponse(objects=objects, count=len(objects))


@router.get("/objects/presign-download", response_model=PresignDownloadResponse)
def presign_download(
    bucket: str = Query(..., min_length=1),
    key: str = Query(..., min_length=1),
) -> PresignDownloadResponse:
    try:
        url = get_s3_client().generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=3600,
        )
    except (BotoCoreError, ClientError) as exc:
        detail = f"Failed to create download URL: {exc}"
        raise HTTPException(status_code=502, detail=detail) from exc

    return PresignDownloadResponse(bucket=bucket, key=key, url=url)
