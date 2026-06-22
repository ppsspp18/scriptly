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


# -------------------------
# Search
# -------------------------

def search(
    query,
    play_id=None,
    character_id=None,
    limit=None
):
    params = {
        "q": query
    }

    if play_id:
        params["play_id"] = play_id

    if character_id:
        params["character_id"] = character_id

    if limit:
        params["limit"] = limit

    response = requests.get(
        f"{API_URL}/search",
        params=params
    )

    response.raise_for_status()

    return response.json()


# -------------------------
# Single Speech
# -------------------------

def get_speech(
    speech_id
):
    response = requests.get(
        f"{API_URL}/speeches/{speech_id}"
    )

    response.raise_for_status()

    return response.json()


# -------------------------
# Bookmarks
# -------------------------

def create_bookmark(
    speech_id
):
    response = requests.post(
        f"{API_URL}/bookmarks",
        json={
            "speech_id": speech_id
        }
    )

    response.raise_for_status()

    return response.json()


def get_bookmarks():
    response = requests.get(
        f"{API_URL}/bookmarks"
    )

    response.raise_for_status()

    return response.json()


def delete_bookmark(
    bookmark_id
):
    response = requests.delete(
        f"{API_URL}/bookmarks/{bookmark_id}"
    )

    response.raise_for_status()

    return response.json()


# -------------------------
# Settings
# -------------------------

def get_settings():
    response = requests.get(
        f"{API_URL}/settings"
    )

    response.raise_for_status()

    return response.json()


def update_settings(
    payload
):
    response = requests.put(
        f"{API_URL}/settings",
        json=payload
    )

    response.raise_for_status()

    return response.json()
