import streamlit as st
from app import (
    init_session_state,
    render_header,
    sidebar_config,
    seo_testing_tab,
    render_footer,
)

# Page Test SEO
aaa = init_session_state()
render_header()

config = sidebar_config(disable_nav=True)

if config["api_key"]:
    seo_testing_tab(config)
else:
    st.warning("⚠️ Configurez votre clé API dans la page Paramètres pour utiliser le test SEO")

render_footer()
