import streamlit as st
from services.api import get_scenes

play_id = st.session_state.get("play_id")
act = st.session_state.get("act")

if play_id is None:
    st.error("No play selected.")
    st.stop()

try:
    scenes = get_scenes(play_id, act)
except Exception as e:
    st.error(f"Failed to load scenes: {e}")
    st.stop()

st.title(f"Act {act}")
st.subheader("Scenes")

for scene in scenes:
    if st.button(f"Scene {scene['scene']}", use_container_width=True, key=f"scene_{scene['scene_id']}"):
        st.session_state["scene_id"] = scene["scene_id"]
        st.switch_page("pages/reader.py")
