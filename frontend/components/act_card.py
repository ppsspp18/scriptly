import streamlit as st

def act_card(act):
    return st.button(
        f"Act {act}",
        use_container_width=True,
        key=f"act_{act}"
    )
