import streamlit as st


def render_navbar():

    with st.sidebar:

        st.title("📖 Scriptly")

        st.divider()

        if st.button(
            "🏠 Home",
            use_container_width=True
        ):
            st.switch_page(
                "app.py"
            )

        if st.button(
            "🔍 Search",
            use_container_width=True
        ):
            st.switch_page(
                "pages/search.py"
            )

        if st.button(
            "⭐ Bookmarks",
            use_container_width=True
        ):
            st.switch_page(
                "pages/bookmarks.py"
            )

        if st.button(
            "⚙ Settings",
            use_container_width=True
        ):
            st.switch_page(
                "pages/settings.py"
            )

        st.divider()

        play_name = st.session_state.get(
            "play_name"
        )

        if play_name:

            st.markdown(
                f"**Play:** {play_name}"
            )

        act = st.session_state.get(
            "act"
        )

        if act:

            st.markdown(
                f"**Act:** {act}"
            )

        scene_id = st.session_state.get(
            "scene_id"
        )

        if scene_id:

            st.markdown(
                f"**Scene ID:** {scene_id}"
            )
