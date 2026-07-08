from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException

from ..models import Bucket, BucketListResponse
from ..s3_client import configured_bucket, get_s3_client

router = APIRouter(tags=["buckets"])


@router.get("/buckets", response_model=BucketListResponse)
def list_buckets() -> BucketListResponse:
    configured = configured_bucket()
    if configured:
        return BucketListResponse(buckets=[Bucket(name=configured)])

    try:
        response = get_s3_client().list_buckets()
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(status_code=502, detail=f"Failed to list buckets: {exc}") from exc

    return BucketListResponse(
        buckets=[
            Bucket(name=bucket["Name"], creation_date=bucket.get("CreationDate"))
            for bucket in response.get("Buckets", [])
        ]
    )
