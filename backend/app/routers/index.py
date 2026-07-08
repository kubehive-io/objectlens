from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException, Query

from ..db import upsert_objects
from ..models import ScanResponse
from ..s3_client import iter_object_metadata

router = APIRouter(tags=["index"])


@router.post("/index/scan", response_model=ScanResponse)
def scan_bucket(bucket: str = Query(..., min_length=1)) -> ScanResponse:
    scanned = 0
    indexed = 0

    try:
        for batch in iter_object_metadata(bucket):
            scanned += len(batch)
            indexed += upsert_objects(bucket, batch)
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(status_code=502, detail=f"Failed to scan bucket: {exc}") from exc

    # TODO: Move synchronous scan work to a background worker.
    return ScanResponse(bucket=bucket, scanned=scanned, indexed=indexed)
