from collections import defaultdict

from core.data_loader import plays
from core.indexes import (
    scenes_by_play,
    characters_by_play
)


def get_all_plays():

    return [
        {
            "id": play["_id"],
            "name": play["name"]
        }
        for play in plays
    ]


def get_play(play_id: int):

    play_scenes = scenes_by_play.get(play_id, [])
    play_characters = characters_by_play.get(play_id, [])

    acts = {
        scene["act"]
        for scene in play_scenes
    }

    return {
        "id": play_id,
        "acts": len(acts),
        "scenes": len(play_scenes),
        "characters": len(play_characters)
    }


def get_acts(play_id: int):

    play_scenes = scenes_by_play.get(play_id, [])

    act_counts = defaultdict(int)

    for scene in play_scenes:
        act_counts[scene["act"]] += 1

    return [
        {
            "act": act,
            "scene_count": count
        }
        for act, count in sorted(act_counts.items())
    ]


def get_scenes(play_id: int, act: int):

    play_scenes = scenes_by_play.get(play_id, [])

    return [
        {
            "scene_id": scene["_id"],
            "scene": scene["scene"]
        }
        for scene in play_scenes
        if scene["act"] == act
    ]


def get_characters(play_id: int):

    return [
        {
            "id": character["_id"],
            "name": character["name"]
        }
        for character in characters_by_play.get(
            play_id,
            []
        )
    ]
