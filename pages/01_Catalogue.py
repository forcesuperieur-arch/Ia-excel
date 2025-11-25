import streamlit as st
from app import (
    init_session_state,
    render_header,
    sidebar_config,
    render_stepper,
    phase_upload,
    phase_matching,
    phase_seo,
    phase_complete,
    render_footer,
)

# Page Catalogue
init_session_state()
render_header()

config = sidebar_config(disable_nav=True)

render_stepper()

if not config["api_key"]:
    st.warning("⚠️ **Clé API manquante** - Configurez-la dans la page Paramètres")
else:
    st.divider()
    phase = st.session_state.phase
    if phase == "upload":
        phase_upload(config)
    elif phase == "matching":
        phase_matching(config)
    elif phase == "seo":
        phase_seo(config)
    elif phase == "complete":
        phase_complete()

render_footer()
