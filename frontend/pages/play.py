import streamlit as st

from components.navbar import (
    render_navbar
)

from services.api import (
    get_play,
    get_acts,
    get_characters
)

render_navbar()

play_id = st.session_state.get(
    "play_id"
)

if play_id is None:

    st.error(
        "No play selected."
    )

    st.stop()

play_name = st.session_state.get(
    "play_name"
)

try:

    play = get_play(
        play_id
    )

    acts = get_acts(
        play_id
    )

except Exception as e:

    st.error(
        f"Failed to load play data: {e}"
    )

    st.stop()

st.title(
    play_name
)

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Acts",
        play["acts"]
    )

with col2:

    st.metric(
        "Scenes",
        play["scenes"]
    )

with col3:

    st.metric(
        "Characters",
        play["characters"]
    )

st.divider()

tab1, tab2 = st.tabs(
    [
        "Acts",
        "Characters"
    ]
)

with tab1:

    for act in acts:

        if st.button(
            f"Act {act['act']}",
            key=f"act_{act['act']}",
            use_container_width=True
        ):

            st.session_state["act"] = (
                act["act"]
            )

            st.switch_page(
                "pages/act.py"
            )

with tab2:

    characters = get_characters(
        play_id
    )

    for character in characters:

        st.markdown(
            f"- {character['name']}"
        )
