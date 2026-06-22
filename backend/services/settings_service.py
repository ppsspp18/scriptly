from core.database import settings_collection

DEFAULT_SETTINGS = {
    "theme": "light",
    "font_size": 18,
    "show_line_numbers": True,
    "show_character_names": True,
    "search_limit": 50
}


async def get_settings():
    settings = await settings_collection.find_one()
    if not settings:
        settings = DEFAULT_SETTINGS.copy()
        await settings_collection.insert_one(settings)
        settings.pop("_id", None)
        return settings
    settings.pop("_id", None)
    return settings


async def update_settings(update_data: dict):
    settings = await settings_collection.find_one()
    if not settings:
        new_settings = DEFAULT_SETTINGS.copy()
        new_settings.update(update_data)
        await settings_collection.insert_one(new_settings)
        new_settings.pop("_id", None)
        return new_settings

    await settings_collection.update_one({}, {"$set": update_data})
    updated = await settings_collection.find_one()
    updated.pop("_id", None)
    return updated
