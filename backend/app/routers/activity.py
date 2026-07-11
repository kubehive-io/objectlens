from typing import Any

from fastapi import APIRouter, Depends

from ..auth import get_current_user
from ..db import count_activities, list_activities

router = APIRouter(tags=["activity"], dependencies=[Depends(get_current_user)])


@router.get("/activity", response_model=list[dict[str, Any]])
def get_activities(limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    return list_activities(limit, offset)


@router.get("/activity/count", response_model=dict[str, int])
def get_activity_count() -> dict[str, int]:
    return {"total": count_activities()}
