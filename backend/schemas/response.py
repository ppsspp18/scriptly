from pydantic import BaseModel


class PlaySchema(BaseModel):
    id: int
    name: str


class ActSchema(BaseModel):
    act: int
    scene_count: int


class SceneSchema(BaseModel):
    scene_id: int
    scene: int


class SpeechSchema(BaseModel):
    character: str
    start_line: int
    end_line: int
    text: str