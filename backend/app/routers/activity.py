from typing import Any

from fastapi import APIRouter

from ..db import list_activities

router = APIRouter(tags=["activity"])


@router.get("/activity", response_model=list[dict[str, Any]])
def get_activities(limit: int = 50) -> list[dict[str, Any]]:
    return list_activities(limit)
