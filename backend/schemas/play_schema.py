from pydantic import BaseModel


class PlaySchema(BaseModel):
    id: int
    name: str


class PlayDetailSchema(BaseModel):
    id: int
    acts: int
    scenes: int
    characters: int


class ActSchema(BaseModel):
    act: int
    scene_count: int


class SceneSchema(BaseModel):
    scene_id: int
    scene: int


class CharacterSchema(BaseModel):
    id: int
    name: str
