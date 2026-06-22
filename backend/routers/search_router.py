from fastapi import APIRouter, Query
from typing import Optional

from services.search_service import search_speeches

router = APIRouter(
    prefix="/search",
    tags=["Search"]
)


@router.get("")
def search(
    q: str = Query(..., min_length=1),
    play_id: Optional[int] = Query(None),
    character_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    return search_speeches(q, play_id, character_id, limit)
