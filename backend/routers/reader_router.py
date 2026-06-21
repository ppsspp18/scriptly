from fastapi import APIRouter, HTTPException

from services.reader_service import (
    get_scene
)

router = APIRouter(
    prefix="/reader",
    tags=["Reader"]
)


@router.get("/scenes/{scene_id}")
def read_scene(scene_id: int):

    scene = get_scene(scene_id)

    if scene is None:
        raise HTTPException(
            status_code=404,
            detail="Scene not found"
        )

    return scene
