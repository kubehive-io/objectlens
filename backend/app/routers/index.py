from typing import Annotated

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import User, require_role
from ..config import get_settings
from ..db import log_activity, upsert_objects
from ..models import ScanResponse
from ..providers import get_provider, get_provider_by_id

router = APIRouter(tags=["index"])


@router.post("/index/scan", response_model=ScanResponse)
def scan_bucket(
    bucket: str = Query(..., min_length=1),
    current_user: Annotated[User, Depends(require_role("admin"))] = None,
) -> ScanResponse:
    return scan_provider_bucket(None, bucket, current_user)


@router.post("/providers/{provider_id}/index/scan", response_model=ScanResponse)
def scan_provider_bucket(
    provider_id: str | None = None,
    bucket: str = Query(..., min_length=1),
    current_user: Annotated[User, Depends(require_role("admin"))] = None,
) -> ScanResponse:
    scanned = 0
    indexed = 0

    try:
        provider = get_provider_by_id(provider_id) if provider_id else get_provider(get_settings())
        provider_key = getattr(provider, "connection_id", provider.provider)
        continuation_token: str | None = None
        while True:
            result = provider.list_objects(
                bucket=bucket,
                delimiter=None,
                continuation_token=continuation_token,
                limit=1000,
            )
            batch = [obj.model_dump() for obj in result.objects]
            scanned += len(batch)
            indexed += upsert_objects(provider_key, bucket, batch)
            if not result.next_continuation_token:
                break
            continuation_token = result.next_continuation_token

        log_activity(
            type="success",
            title="Bucket Metadata Indexed",
            description=(
                f"Scanned connection '{provider_key}' bucket '{bucket}' "
                f"and indexed {indexed} object records successfully."
            ),
        )
    except (BotoCoreError, ClientError) as exc:
        log_activity(
            type="warning",
            title="Bucket Sync Failed",
            description=(
                f"Scan failed on connection '{provider_id or 'default'}' bucket '{bucket}': {exc}"
            ),
        )
        raise HTTPException(status_code=502, detail=f"Failed to scan bucket: {exc}") from exc
    except ValueError as exc:
        log_activity(
            type="error",
            title="Bucket Sync System Error",
            description=f"System error during scan of bucket '{bucket}': {exc}",
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # TODO: Move synchronous scan work to a background worker.
    return ScanResponse(bucket=bucket, scanned=scanned, indexed=indexed)
