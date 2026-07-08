from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException

from ..config import get_settings
from ..models import Bucket, BucketListResponse
from ..providers import get_provider

router = APIRouter(tags=["buckets"])


@router.get("/buckets", response_model=BucketListResponse)
def list_buckets() -> BucketListResponse:
    try:
        provider = get_provider(get_settings())
        buckets = provider.list_buckets()
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(status_code=502, detail=f"Failed to list buckets: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return BucketListResponse(
        buckets=[Bucket(name=bucket.name, creation_date=bucket.creation_date) for bucket in buckets]
    )
