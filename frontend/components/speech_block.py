import streamlit as st

def speech_block(speech):
    st.markdown(
        f"### {speech['character']}"
    )
    st.markdown(
        speech["text"]
    )
    st.divider()
