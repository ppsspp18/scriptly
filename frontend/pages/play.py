import streamlit as st
from services.api import get_play, get_acts

with st.sidebar:
    st.title("📖 Scriptly")
    st.divider()
    play_name = st.session_state.get("play_name")
    if play_name:
        st.markdown(f"**Play:** {play_name}")
    st.divider()
    if st.button("🏠 Home", use_container_width=True):
        st.switch_page("app.py")

play_id = st.session_state.get("play_id")

if play_id is None:
    st.error("No play selected.")
    st.stop()

play_name = st.session_state.get("play_name")

try:
    play = get_play(play_id)
    acts = get_acts(play_id)
except Exception as e:
    st.error(f"Failed to load play data: {e}")
    st.stop()

st.title(play_name)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Acts", play["acts"])
with col2:
    st.metric("Scenes", play["scenes"])
with col3:
    st.metric("Characters", play["characters"])

st.divider()

for act in acts:
    if st.button(f"Act {act['act']}", use_container_width=True):
        st.session_state["act"] = act["act"]
        st.switch_page("pages/act.py")
