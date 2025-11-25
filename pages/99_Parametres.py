import streamlit as st
from app import (
    init_session_state,
    render_header,
    sidebar_config,
    render_settings,
    render_footer,
)

# Page Paramètres
init_session_state()
render_header()

# Utilise la sidebar sans nav
_ = sidebar_config(disable_nav=True)

render_settings()

render_footer()
