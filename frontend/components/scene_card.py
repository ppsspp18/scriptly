import streamlit as st

def scene_card(scene):
    return st.button(
        f"Scene {scene['scene']}",
        use_container_width=True,
        key=f"scene_{scene['scene_id']}"
    )
