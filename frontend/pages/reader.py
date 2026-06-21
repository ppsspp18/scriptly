import streamlit as st
from services.api import get_scene

scene_id = st.session_state.get("scene_id")

if scene_id is None:
    st.error("No scene selected.")
    st.stop()

try:
    scene = get_scene(scene_id)
except Exception as e:
    st.error(f"Failed to load scene: {e}")
    st.stop()

st.title(f"Act {scene['act']} · Scene {scene['scene']}")
st.divider()

for speech in scene["speeches"]:
    st.markdown(f"### {speech['character']}")
    st.markdown(speech["text"])
    st.divider()
