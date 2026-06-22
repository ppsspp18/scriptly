from core.indexes import (
    speeches_by_scene,
    characters_by_id,
    scenes_by_id
)


def get_scene(scene_id: int):

    scene = scenes_by_id.get(scene_id)

    if not scene:
        return None

    speeches = []

    for speech in speeches_by_scene.get(scene_id, []):

        character = characters_by_id[
            speech["character_id"]
        ]

        speeches.append(
            {
                "speech_id": speech["_id"],
                "character": character["name"],
                "start_line": speech["start_line"],
                "end_line": speech["end_line"],
                "text": speech["text"]
            }
        )

    return {
        "scene_id": scene_id,
        "play_id": scene["play_id"],
        "act": scene["act"],
        "scene": scene["scene"],
        "speeches": speeches
    }
