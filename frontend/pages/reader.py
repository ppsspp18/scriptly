import streamlit as st

from components.navbar import (
    render_navbar
)

from services.api import (
    get_scene,
    get_settings
)

from components.speech_block import (
    speech_block
)

render_navbar()

st.session_state[
    "settings"
] = get_settings()

scene_id = st.session_state.get(
    "scene_id"
)

if scene_id is None:

    st.error(
        "No scene selected."
    )

    st.stop()

try:

    scene = get_scene(
        scene_id
    )

except Exception as e:

    st.error(
        f"Failed to load scene: {e}"
    )

    st.stop()

st.title(
    f"Act {scene['act']} · Scene {scene['scene']}"
)

st.divider()

for speech in scene["speeches"]:

    speech_block(
        speech
    )
