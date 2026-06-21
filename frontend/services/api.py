import requests

from config import API_URL

def get_plays():
    response = requests.get(
        f"{API_URL}/plays"
    )
    response.raise_for_status()
    return response.json()

def get_play(play_id):
    response = requests.get(
        f"{API_URL}/plays/{play_id}"
    )
    response.raise_for_status()
    return response.json()

def get_acts(play_id):
    response = requests.get(
        f"{API_URL}/plays/{play_id}/acts"
    )
    response.raise_for_status()
    return response.json()

def get_scenes(play_id, act):
    response = requests.get(
        f"{API_URL}/plays/{play_id}/acts/{act}"
    )
    response.raise_for_status()
    return response.json()

def get_characters(play_id):
    response = requests.get(
        f"{API_URL}/plays/{play_id}/characters"
    )
    response.raise_for_status()
    return response.json()

def get_scene(scene_id):
    response = requests.get(
        f"{API_URL}/reader/scenes/{scene_id}"
    )
    response.raise_for_status()
    return response.json()
