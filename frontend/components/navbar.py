import streamlit as st

def render_navbar():
    with st.sidebar:
        st.title("📖 Scriptly")
        st.divider()

        play_name = st.session_state.get(
            "play_name"
        )
        if play_name:
            st.markdown(
                f"**Play:** {play_name}"
            )

        act = st.session_state.get("act")
        if act:
            st.markdown(
                f"**Act:** {act}"
            )

        st.divider()

        if st.button(
            "🏠 Home",
            use_container_width=True
        ):
            st.switch_page(
                "app.py"
            )
