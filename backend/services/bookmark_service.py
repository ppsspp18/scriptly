from datetime import datetime, timezone
from bson import ObjectId

from core.database import bookmark_collection
from core.indexes import speeches_by_id, play_name_by_id, characters_by_id
from validators.speech_validator import validate_speech


async def add_bookmark(speech_id: int):
    validate_speech(speech_id)

    existing = await bookmark_collection.find_one({"speech_id": speech_id})
    if existing:
        raise ValueError("Speech already bookmarked")

    bookmark = {
        "speech_id": speech_id,
        "created_at": datetime.now(timezone.utc)
    }
    result = await bookmark_collection.insert_one(bookmark)
    return str(result.inserted_id)


async def list_bookmarks():
    bookmarks = await bookmark_collection.find().sort("created_at", -1).to_list(length=None)
    result = []
    for b in bookmarks:
        speech = speeches_by_id.get(b["speech_id"])
        if not speech:
            continue
        result.append({
            "bookmark_id": str(b["_id"]),
            "speech_id": b["speech_id"],
            "play_name": play_name_by_id.get(speech["play_id"], "Unknown"),
            "character": characters_by_id.get(speech["character_id"], {}).get("name", "Unknown"),
            "snippet": speech["text"][:200],
            "created_at": b["created_at"]
        })
    return result


async def delete_bookmark(bookmark_id: str):
    result = await bookmark_collection.delete_one({"_id": ObjectId(bookmark_id)})
    if result.deleted_count == 0:
        raise ValueError("Bookmark not found")
