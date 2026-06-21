from fastapi import APIRouter

from services.play_service import (
    get_all_plays,
    get_play,
    get_acts,
    get_scenes,
    get_characters
)

router = APIRouter(
    prefix="/plays",
    tags=["Plays"]
)


@router.get("")
def list_plays():
    return get_all_plays()


@router.get("/{play_id}")
def play_details(play_id: int):
    return get_play(play_id)


@router.get("/{play_id}/acts")
def acts(play_id: int):
    return get_acts(play_id)


@router.get("/{play_id}/acts/{act}")
def scenes(play_id: int, act: int):
    return get_scenes(play_id, act)


@router.get("/{play_id}/characters")
def characters(play_id: int):
    return get_characters(play_id)
