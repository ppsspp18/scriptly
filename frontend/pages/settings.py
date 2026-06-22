import streamlit as st

from components.navbar import (
    render_navbar
)

from services.api import (
    get_settings,
    update_settings
)

render_navbar()

st.title(
    "⚙ Settings"
)

settings = get_settings()

theme = st.selectbox(
    "Theme",
    ["light", "dark"],
    index=0 if settings["theme"] == "light" else 1
)

font_size = st.slider(
    "Font Size",
    12,
    30,
    settings["font_size"]
)

show_line_numbers = st.checkbox(
    "Show Line Numbers",
    value=settings["show_line_numbers"]
)

show_character_names = st.checkbox(
    "Show Character Names",
    value=settings["show_character_names"]
)

search_limit = st.selectbox(
    "Search Limit",
    [10, 20, 50, 100],
    index=[10, 20, 50, 100].index(
        settings["search_limit"]
    )
)

if st.button(
    "Save Settings",
    use_container_width=True
):

    payload = {
        "theme": theme,
        "font_size": font_size,
        "show_line_numbers": show_line_numbers,
        "show_character_names": show_character_names,
        "search_limit": search_limit
    }

    update_settings(
        payload
    )

    st.success(
        "Settings updated."
    )
