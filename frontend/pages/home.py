import streamlit as st
from services.api import get_plays

st.title("📚 Shakespeare Plays")

plays = get_plays()

if not plays:
    st.warning("No plays found.")
    st.stop()

cols = st.columns(3)

for index, play in enumerate(plays):
    with cols[index % 3]:
        if st.button(play["name"], use_container_width=True, key=f"play_{play['id']}"):
            st.session_state["play_id"] = play["id"]
            st.switch_page("pages/play.py")
