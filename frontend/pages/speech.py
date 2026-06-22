import streamlit as st

from components.navbar import (
    render_navbar
)

from services.api import (
    get_speech
)

from components.bookmark_button import (
    bookmark_button
)

render_navbar()

speech_id = st.session_state.get(
    "speech_id"
)

if speech_id is None:

    st.error(
        "No speech selected."
    )

    st.stop()

speech = get_speech(
    speech_id
)

st.title(
    speech["character"]
)

st.caption(
    f"{speech['play_name']} • "
    f"Act {speech['act']} • "
    f"Scene {speech['scene']}"
)

st.divider()

st.markdown(
    speech["text"]
)

st.divider()

bookmark_button(
    speech_id
)
