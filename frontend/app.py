import streamlit as st
import requests
from config import PAGE_TITLE, PAGE_ICON

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")

if "play_id" not in st.session_state:
    st.session_state["play_id"] = None
if "play_name" not in st.session_state:
    st.session_state["play_name"] = None
if "act" not in st.session_state:
    st.session_state["act"] = None
if "scene_id" not in st.session_state:
    st.session_state["scene_id"] = None

st.title("📖 Scriptly")
st.subheader("Explore Shakespeare's Plays")

from services.api import get_plays

try:
    plays = get_plays()
except Exception as e:
    st.error(f"Failed to load plays: {e}")
    st.stop()

cols = st.columns(3)

for index, play in enumerate(plays):
    with cols[index % 3]:
        if st.button(play["name"], use_container_width=True, key=f"play_{play['id']}"):
            st.session_state["play_id"] = play["id"]
            st.session_state["play_name"] = play["name"]
            st.switch_page("pages/play.py")
