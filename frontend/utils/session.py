import streamlit as st

def initialize_session():
    defaults = {
        "play_id": None,
        "play_name": None,
        "act": None,
        "scene_id": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def clear_navigation():
    st.session_state["play_id"] = None
    st.session_state["play_name"] = None
    st.session_state["act"] = None
    st.session_state["scene_id"] = None
