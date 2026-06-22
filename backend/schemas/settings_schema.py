from pydantic import BaseModel
from typing import Optional


class SettingsSchema(BaseModel):
    theme: str = "light"
    font_size: int = 18
    show_line_numbers: bool = True
    show_character_names: bool = True
    search_limit: int = 50


class SettingsUpdate(BaseModel):
    theme: Optional[str] = None
    font_size: Optional[int] = None
    show_line_numbers: Optional[bool] = None
    show_character_names: Optional[bool] = None
    search_limit: Optional[int] = None
