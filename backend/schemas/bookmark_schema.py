from pydantic import BaseModel
from datetime import datetime


class BookmarkCreate(BaseModel):
    speech_id: int


class BookmarkResponse(BaseModel):
    bookmark_id: str
    speech_id: int
    play_name: str
    character: str
    snippet: str
    created_at: datetime
