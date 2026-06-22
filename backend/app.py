from fastapi import FastAPI, HTTPException

from routers.play_router import router as play_router
from routers.reader_router import router as reader_router
from routers.search_router import router as search_router
from routers.bookmark_router import router as bookmark_router
from routers.settings_router import router as settings_router

from core.indexes import speeches_by_id, play_name_by_id, characters_by_id

app = FastAPI(
    title="Scriptly API",
    version="1.0.0"
)

app.include_router(play_router)
app.include_router(reader_router)
app.include_router(search_router)
app.include_router(bookmark_router)
app.include_router(settings_router)


@app.get("/")
def root():
    return {
        "message": "Scriptly API Running"
    }


@app.get("/speeches/{speech_id}")
def get_speech(speech_id: int):
    speech = speeches_by_id.get(speech_id)
    if not speech:
        raise HTTPException(status_code=404, detail="Speech not found")
    return {
        "speech_id": speech["_id"],
        "play_name": play_name_by_id.get(speech["play_id"], "Unknown"),
        "character": characters_by_id.get(speech["character_id"], {}).get("name", "Unknown"),
        "act": speech["act"],
        "scene": speech["scene"],
        "text": speech["text"]
    }
