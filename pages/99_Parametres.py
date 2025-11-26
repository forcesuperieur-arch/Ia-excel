import streamlit as st
from src.ui_components import (
    load_css,
    init_session_state,
    render_header,
    sidebar_config,
    render_settings,
    render_footer,
)

st.set_page_config(page_title="Paramètres - IA Excel Pro", page_icon="⚙️", layout="wide")

load_css()
init_session_state()
render_header()

# Utilise la sidebar sans nav
_ = sidebar_config(disable_nav=True)

render_settings()

render_footer()
