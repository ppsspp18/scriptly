from fastapi import APIRouter

from schemas.settings_schema import SettingsUpdate
from services.settings_service import get_settings, update_settings

router = APIRouter(
    prefix="/settings",
    tags=["Settings"]
)


@router.get("")
async def get_user_settings():
    return await get_settings()


@router.put("")
async def update_user_settings(body: SettingsUpdate):
    update_data = body.model_dump(exclude_none=True)
    return await update_settings(update_data)
