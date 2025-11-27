#!/usr/bin/env python3
"""
Interface web moderne pour le traitement intelligent de catalogues Excel
Version 2.0 - Design repensé avec OpenRouter/OpenAI
"""
import streamlit as st
import os

# Désactiver l'avertissement Streamlit sur les secrets manquants sur Cloud Run
# Les secrets sont stockés dans les variables d'environnement (os.environ)
import warnings
warnings.filterwarnings('ignore', category=FileNotFoundError)

# ✅ Initialiser le logging AVANT tout
from src.logger_config import LoggerConfig
logger_config = LoggerConfig()
logger = logger_config.get_logger(__name__)

from src.ui_components import (
    load_css,
    init_session_state,
    render_header,
    sidebar_config,
    render_stepper,
    render_settings,
    render_footer,
    phase_upload,
    phase_matching,
    phase_seo,
    phase_complete,
    seo_testing_tab
)

# Configuration de la page
st.set_page_config(
    page_title="IA Excel Pro - Catalogs & SEO",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Application principale"""
    load_css()
    init_session_state()
    
    render_header()
    
    # Configuration commune (appelée une seule fois)
    config = sidebar_config()
    
    # Navigation principale via sidebar
    if config["nav"] and config["nav"].startswith("📊"):
        render_stepper()
        
        # Vérification clé API
        if not config["api_key"]:
            st.warning("⚠️ **Clé API manquante** - Configurez-la dans la sidebar pour commencer")
            with st.expander("📖 Comment obtenir une clé ?"):
                st.markdown("""
                **OpenAI:**
                1. [platform.openai.com](https://platform.openai.com/)
                2. Créez un compte et générez une clé API
                3. Format: `sk-...`
                
                **OpenRouter (recommandé):**
                1. [openrouter.ai](https://openrouter.ai/)
                2. Créez un compte et générez une clé
                3. Format: `sk-or-v1-...`
                4. Plus rapide et économique !
                """)
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
    elif config["nav"] and config["nav"].startswith("🧪"):
        if config["api_key"]:
            seo_testing_tab(config)
        else:
            st.warning("⚠️ Configurez votre clé API dans la sidebar pour utiliser le test SEO")
    elif config["nav"] and config["nav"].startswith("⚙️"):
        render_settings()

    # Footer
    render_footer()


if __name__ == "__main__":
    main()
