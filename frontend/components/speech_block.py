import streamlit as st

from components.bookmark_button import (
    bookmark_button
)


def speech_block(
    speech
):

    settings = st.session_state.get(
        "settings",
        {}
    )

    show_character_names = settings.get(
        "show_character_names",
        True
    )

    font_size = settings.get(
        "font_size",
        18
    )

    if show_character_names:

        st.markdown(
            f"### {speech['character']}"
        )

    st.markdown(
        f"""
        <div style="font-size:{font_size}px">
            {speech["text"]}
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:

        bookmark_button(
            speech["speech_id"]
        )

    with col2:

        if st.button(
            "Open",
            key=f"open_{speech['speech_id']}"
        ):

            st.session_state[
                "speech_id"
            ] = speech["speech_id"]

            st.switch_page(
                "pages/speech.py"
            )

    st.divider()
