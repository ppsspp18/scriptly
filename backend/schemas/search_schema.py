from pydantic import BaseModel
from typing import Optional


class SearchQuery(BaseModel):
    q: str
    play_id: Optional[int] = None
    character_id: Optional[int] = None
    limit: int = 20


class SearchResult(BaseModel):
    speech_id: int
    play_id: int
    play_name: str
    character: str
    act: int
    scene: int
    snippet: str
