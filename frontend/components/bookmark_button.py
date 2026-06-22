import streamlit as st

from services.api import (
    create_bookmark
)


def bookmark_button(
    speech_id
):

    if st.button(
        "⭐ Bookmark",
        key=f"bookmark_{speech_id}"
    ):

        try:

            create_bookmark(
                speech_id
            )

            st.success(
                "Bookmarked successfully"
            )

        except Exception as e:

            st.error(
                str(e)
            )
