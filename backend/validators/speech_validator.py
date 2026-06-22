from core.indexes import speeches_by_id


def validate_speech(speech_id: int):
    speech = speeches_by_id.get(speech_id)
    if not speech:
        raise ValueError(f"Speech with id {speech_id} not found")
    return speech
