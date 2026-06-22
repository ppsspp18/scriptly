import streamlit as st

from components.navbar import (
    render_navbar
)

from services.api import (
    search
)

from utils.highlight import (
    highlight_text
)

render_navbar()

st.title(
    "🔍 Search Shakespeare"
)

query = st.text_input(
    "Search speeches",
    value=st.session_state.get(
        "search_query",
        ""
    )
)

limit = st.selectbox(
    "Limit",
    [10, 20, 50, 100],
    index=2
)

if st.button(
    "Search",
    use_container_width=True
):

    st.session_state[
        "search_query"
    ] = query

    if not query.strip():

        st.warning(
            "Enter a search query."
        )

        st.stop()

    with st.spinner(
        "Searching..."
    ):

        results = search(
            query=query,
            limit=limit
        )

    st.success(
        f"{len(results)} result(s)"
    )

    st.divider()

    for result in results:

        st.markdown(
            f"### {result['character']}"
        )

        st.caption(
            f"{result['play_name']} • "
            f"Act {result['act']} • "
            f"Scene {result['scene']}"
        )

        highlighted = highlight_text(
            result["snippet"],
            query
        )

        st.markdown(
            highlighted,
            unsafe_allow_html=True
        )

        if st.button(
            "Open Speech",
            key=f"speech_{result['speech_id']}"
        ):

            st.session_state[
                "speech_id"
            ] = result["speech_id"]

            st.switch_page(
                "pages/speech.py"
            )

        st.divider()
