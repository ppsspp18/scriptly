import streamlit as st

def play_card(play):
    return st.button(
        play["name"],
        use_container_width=True,
        key=f"play_{play['id']}"
    )
