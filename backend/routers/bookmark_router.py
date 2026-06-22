from fastapi import APIRouter, HTTPException

from schemas.bookmark_schema import BookmarkCreate
from services.bookmark_service import add_bookmark, list_bookmarks, delete_bookmark

router = APIRouter(
    prefix="/bookmarks",
    tags=["Bookmarks"]
)


@router.post("")
async def create_bookmark(body: BookmarkCreate):
    try:
        bookmark_id = await add_bookmark(body.speech_id)
        return {"bookmark_id": bookmark_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
async def get_bookmarks():
    return await list_bookmarks()


@router.delete("/{bookmark_id}")
async def remove_bookmark(bookmark_id: str):
    try:
        await delete_bookmark(bookmark_id)
        return {"message": "Bookmark deleted"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
