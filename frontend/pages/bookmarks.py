import streamlit as st

from components.navbar import (
    render_navbar
)

from services.api import (
    get_bookmarks,
    delete_bookmark
)

render_navbar()

st.title(
    "⭐ Bookmarks"
)

bookmarks = get_bookmarks()

if not bookmarks:

    st.info(
        "No bookmarks yet."
    )

    st.stop()

for bookmark in bookmarks:

    st.markdown(
        f"### {bookmark['character']}"
    )

    st.caption(
        bookmark["play_name"]
    )

    st.markdown(
        bookmark["snippet"]
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "Open",
            key=f"open_{bookmark['bookmark_id']}"
        ):

            st.session_state[
                "speech_id"
            ] = bookmark["speech_id"]

            st.switch_page(
                "pages/speech.py"
            )

    with col2:

        if st.button(
            "Delete",
            key=f"delete_{bookmark['bookmark_id']}"
        ):

            delete_bookmark(
                bookmark["bookmark_id"]
            )

            st.rerun()

    st.divider()
