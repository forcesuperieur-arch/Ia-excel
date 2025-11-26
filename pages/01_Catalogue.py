import streamlit as st
from src.ui_components import (
    load_css,
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

# Configuration de la page
st.set_page_config(page_title="Catalogue - IA Excel Pro", page_icon="📊", layout="wide")

# Chargement CSS et Session
load_css()
init_session_state()

# Header
render_header()

# Sidebar
config = sidebar_config(disable_nav=True)

# Stepper
render_stepper()

# Vérification API Key
if not config["api_key"]:
    st.warning("⚠️ **Clé API manquante** - Configurez-la dans la sidebar")
else:
    st.divider()
    
    # Routing par phase
    phase = st.session_state.phase
    
    if phase == "upload":
        phase_upload(config)
    elif phase == "matching":
        phase_matching(config)
    elif phase == "seo":
        phase_seo(config)
    elif phase == "complete":
        phase_complete()

# Footer
render_footer()
