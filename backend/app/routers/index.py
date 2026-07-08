from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException, Query

from ..config import get_settings
from ..db import upsert_objects
from ..models import ScanResponse
from ..providers import get_provider

router = APIRouter(tags=["index"])


@router.post("/index/scan", response_model=ScanResponse)
def scan_bucket(bucket: str = Query(..., min_length=1)) -> ScanResponse:
    scanned = 0
    indexed = 0

    try:
        provider = get_provider(get_settings())
        continuation_token: str | None = None
        while True:
            result = provider.list_objects(
                bucket=bucket,
                continuation_token=continuation_token,
                limit=1000,
            )
            batch = [obj.model_dump() for obj in result.objects]
            scanned += len(batch)
            indexed += upsert_objects(provider.provider, bucket, batch)
            if not result.next_continuation_token:
                break
            continuation_token = result.next_continuation_token
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(status_code=502, detail=f"Failed to scan bucket: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # TODO: Move synchronous scan work to a background worker.
    return ScanResponse(bucket=bucket, scanned=scanned, indexed=indexed)
