from collections import defaultdict

from core.data_loader import (
    plays,
    characters,
    scenes,
    speeches
)

plays_by_id = {
    play["_id"]: play
    for play in plays
}

characters_by_id = {
    character["_id"]: character
    for character in characters
}

scenes_by_id = {
    scene["_id"]: scene
    for scene in scenes
}

scenes_by_play = defaultdict(list)

for scene in scenes:
    scenes_by_play[scene["play_id"]].append(scene)

speeches_by_scene = defaultdict(list)

for speech in speeches:
    speeches_by_scene[speech["scene_id"]].append(speech)

characters_by_play = defaultdict(list)

for character in characters:
    characters_by_play[character["play_id"]].append(character)