import streamlit as st
import pandas as pd
from pathlib import Path
import os
import json
from datetime import datetime
import requests
import re
import time
from io import BytesIO
import logging

# Configuration des logs
LOG_FILE = "app.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger(__name__)

from src.catalog_parser import CatalogParser
from src.ai_matcher import ColumnMatcher
from src.matrix_generator import MatrixGenerator
from src.template_manager import TemplateManager
from src.product_description_generator import ProductDescriptionGenerator
from src.template_injector import TemplateInjector
from src.matching_learning import MatchingLearning


def get_secret(key: str, default: str = "") -> str:
    """
    Récupère un secret depuis:
    1. os.environ (Cloud Run - variables d'environnement)
    2. st.secrets (Streamlit Cloud - secrets.toml)
    3. default (valeur par défaut)
    """
    # 1. D'abord essayer les variables d'environnement (Cloud Run)
    if key in os.environ:
        return os.environ[key]
    
    # 2. Puis st.secrets (Streamlit Cloud) - silence les erreurs
    try:
        import streamlit as st
        # Silencieux - récupère sans déclencher d'avertissement
        if hasattr(st, 'secrets') and isinstance(st.secrets, dict):
            if key in st.secrets:
                return st.secrets[key]
    except Exception:
        # Ignore toute erreur Streamlit
        pass
    
    # 3. Fallback sur la valeur par défaut
    return default
    return default


def load_css():
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* === THEME PRINCIPAL === */
    :root {
        --primary: #6366f1;
        --primary-dark: #4f46e5;
        --secondary: #8b5cf6;
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
        --gray-50: #f9fafb;
        --gray-100: #f3f4f6;
        --gray-200: #e5e7eb;
        --gray-700: #374151;
        --gray-900: #111827;
    }
    
    /* === LAYOUT === */
    .main {
        padding: 1rem 3rem;
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
    }
    
    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
    }
    
    /* === HEADER === */
    .app-header {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        padding: 3rem 2rem;
        border-radius: 1.5rem;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(99, 102, 241, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .app-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -10%;
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        border-radius: 50%;
    }
    
    .app-header h1 {
        font-size: 3.5rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.02em;
        position: relative;
        z-index: 1;
    }
    
    .app-header p {
        font-size: 1.25rem;
        margin: 1rem 0 0 0;
        opacity: 0.95;
        font-weight: 400;
        position: relative;
        z-index: 1;
    }
    
    .app-badge {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        padding: 0.4rem 1rem;
        border-radius: 2rem;
        font-size: 0.9rem;
        font-weight: 600;
        margin-top: 1rem;
        backdrop-filter: blur(10px);
    }
    
    /* === STEPPER === */
    .stepper-container {
        background: white;
        padding: 2rem;
        border-radius: 1.2rem;
        margin: 2rem 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    }
    
    .stepper {
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: relative;
    }
    
    .stepper::before {
        content: '';
        position: absolute;
        top: 20px;
        left: 10%;
        right: 10%;
        height: 3px;
        background: var(--gray-200);
        z-index: 0;
    }
    
    .step {
        flex: 1;
        text-align: center;
        position: relative;
        z-index: 1;
    }
    
    .step-circle {
        width: 42px;
        height: 42px;
        border-radius: 50%;
        background: white;
        border: 3px solid var(--gray-200);
        margin: 0 auto 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 1.1rem;
        color: var(--gray-700);
        transition: all 0.3s ease;
    }
    
    .step.active .step-circle {
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        border-color: var(--primary);
        color: white;
        box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
        transform: scale(1.1);
    }
    
    .step.completed .step-circle {
        background: var(--success);
        border-color: var(--success);
        color: white;
    }
    
    .step-label {
        font-weight: 600;
        font-size: 0.95rem;
        color: var(--gray-700);
        margin-top: 0.5rem;
    }
    
    .step.active .step-label {
        color: var(--primary);
    }
    
    .step-description {
        font-size: 0.85rem;
        color: var(--gray-700);
        margin-top: 0.25rem;
        opacity: 0.7;
    }
    
    /* === CARDS === */
    .metric-card {
        background: white;
        padding: 2rem;
        border-radius: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.06);
        border: 1px solid var(--gray-100);
        transition: all 0.3s ease;
        height: 100%;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 30px rgba(0,0,0,0.1);
    }
    
    .metric-value {
        font-size: 2.8rem;
        font-weight: 800;
        color: var(--gray-900);
        line-height: 1;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: var(--gray-700);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .metric-icon {
        font-size: 2.5rem;
        opacity: 0.15;
        position: absolute;
        right: 1.5rem;
        top: 1.5rem;
    }
    
    /* Cards colorées */
    .card-primary {
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        color: white;
    }
    
    .card-primary .metric-value,
    .card-primary .metric-label {
        color: white;
    }
    
    .card-success {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
    }
    
    .card-success .metric-value,
    .card-success .metric-label {
        color: white;
    }
    
    .card-warning {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
    }
    
    .card-warning .metric-value,
    .card-warning .metric-label {
        color: white;
    }
    
    /* === BOUTONS === */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
        color: white !important;
        border: none;
        padding: 0.9rem 2rem;
        border-radius: 0.75rem;
        font-weight: 600;
        font-size: 1.05rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
        text-transform: none;
        letter-spacing: 0;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.4);
        background: linear-gradient(135deg, var(--secondary) 0%, var(--primary) 100%);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Bouton secondaire */
    .stButton>button[kind="secondary"] {
        background: white;
        color: var(--primary) !important;
        border: 2px solid var(--primary);
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    
    .stButton>button[kind="secondary"]:hover {
        background: var(--gray-50);
    }
    
    /* === UPLOAD ZONE === */
    .uploadedFile {
        background: white;
        border: 2px dashed var(--gray-200);
        border-radius: 1rem;
        padding: 2rem;
        transition: all 0.3s ease;
    }
    
    .uploadedFile:hover {
        border-color: var(--primary);
        background: var(--gray-50);
    }
    
    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: var(--gray-100);
        padding: 0.5rem;
        border-radius: 0.75rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        color: var(--gray-700);
        transition: all 0.2s;
    }
    
    .stTabs [aria-selected="true"] {
        background: white;
        color: var(--primary);
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    
    /* === DATAFRAME === */
    .dataframe {
        border-radius: 0.75rem !important;
        overflow: hidden;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border: 1px solid var(--gray-200);
    }
    
    /* === ALERTS === */
    .stAlert {
        border-radius: 0.75rem;
        border: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        padding: 1rem 1.5rem;
    }
    
    /* === PROGRESS BAR === */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        border-radius: 10px;
        height: 8px;
    }
    
    /* === SIDEBAR === */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fafbfc 0%, #f3f4f6 100%);
    }
    
    [data-testid="stSidebar"] .element-container {
        margin-bottom: 0.5rem;
    }
    
    /* === BADGES === */
    .status-badge {
        display: inline-block;
        padding: 0.4rem 0.9rem;
        border-radius: 2rem;
        font-weight: 600;
        font-size: 0.85rem;
        margin: 0.2rem;
    }
    
    .badge-success {
        background: #d1fae5;
        color: #065f46;
    }
    
    .badge-warning {
        background: #fed7aa;
        color: #92400e;
    }
    
    .badge-error {
        background: #fee2e2;
        color: #991b1b;
    }
    
    .badge-info {
        background: #dbeafe;
        color: #1e40af;
    }
    
    /* === EXPANDER === */
    .streamlit-expanderHeader {
        background: white;
        border-radius: 0.75rem;
        border: 1px solid var(--gray-200);
        font-weight: 600;
        color: var(--gray-900);
        transition: all 0.2s;
    }
    
    .streamlit-expanderHeader:hover {
        background: var(--gray-50);
        border-color: var(--primary);
    }
    
    /* === SELECTBOX === */
    .stSelectbox > div > div {
        border-radius: 0.5rem;
        border-color: var(--gray-200);
    }
    
    /* === TEXT INPUT === */
    .stTextInput > div > div > input {
        border-radius: 0.5rem;
        border-color: var(--gray-200);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary);
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
    }
    
    /* === ANIMATIONS === */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .animate-fade {
        animation: fadeIn 0.5s ease-out;
    }
    
    .animate-slide {
        animation: slideIn 0.5s ease-out;
    }
    
    /* === SEO DASHBOARD === */
    .seo-dashboard {
        background: white;
        padding: 2rem;
        border-radius: 1.2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        margin: 2rem 0;
    }
    
    .seo-stat {
        text-align: center;
        padding: 1.5rem;
        background: var(--gray-50);
        border-radius: 0.75rem;
        border: 1px solid var(--gray-200);
    }
    
    .seo-stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary);
    }
    
    .seo-stat-label {
        font-size: 0.85rem;
        color: var(--gray-700);
        margin-top: 0.5rem;
    }
    
    /* === RESPONSIVITÉ === */
    @media (max-width: 768px) {
        .main {
            padding: 1rem;
        }
        
        .app-header h1 {
            font-size: 2rem;
        }
        
        .metric-value {
            font-size: 2rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def format_description_for_display(text):
    """Convertit Markdown/HTML en format RTF pour Word avec gras réel."""
    if not text:
        return text
    
    # Garder le texte original pour l'affichage
    return text


def format_description_for_word(text):
    """Convertit en RTF (Rich Text Format) pour Word avec formatage gras et encodage UTF-8."""
    if not text:
        return text
    
    # En-tête RTF minimaliste qui supporte l'Unicode via UTF-8 implicite ou \u
    # \ansicpg1252 est standard, mais Word gère bien le contenu mixte si on utilise les bons escapes
    rtf = r"{\rtf1\ansi\ansicpg1252\deff0\nouicompat\deflang1036{\fonttbl{\f0\fnil\fcharset0 Arial;}}" + "\n"
    rtf += r"\viewkind4\uc1\pard\sa200\sl276\slmult1\f0\fs22\lang1036 "
    
    # Échappement des caractères spéciaux RTF
    text_rtf = text.replace('\\', '\\\\').replace('{', '\\{').replace('}', '\\}')
    
    # Remplacer **texte** par \b texte\b0 (gras RTF)
    text_rtf = re.sub(r'\*\*([^*]+)\*\*', r'{\\b \1\\b0}', text_rtf)
    
    # Remplacer <b>texte</b> par \b texte\b0
    text_rtf = re.sub(r'<b>([^<]+)</b>', r'{\\b \1\\b0}', text_rtf, flags=re.IGNORECASE)
    
    # Remplacer les sauts de ligne par \par
    text_rtf = text_rtf.replace('\n', r'\par' + '\n')
    
    # Gestion des caractères Unicode pour RTF (\uN?)
    # On encode tout ce qui n'est pas ASCII standard
    final_rtf = ""
    for char in text_rtf:
        if ord(char) < 128:
            final_rtf += char
        else:
            # \uN? où N est le code décimal unicode (signé pour short, mais ici on utilise unsigned pour simplicité si < 32768)
            code = ord(char)
            final_rtf += f"\\u{code}?"
            
    rtf += final_rtf
    rtf += "}"
    
    return rtf

def init_session_state():
    """Initialise les variables de session"""
    defaults = {
        'phase': 'upload',  # upload, matching, seo, complete
        'catalog_data': None,
        'catalog_headers': None,
        'column_mapping': None,
        'current_file': None,
        'output_path': None,
        'seo_generated': False,
        'seo_results': None,
        'template_manager': TemplateManager(),
        'learning_system': MatchingLearning(),
        'selected_template': None,
        'use_template': False,
        'parser_config': {},
        'seo_progress': {},
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Charger le template par défaut
    if st.session_state.selected_template is None:
        default = st.session_state.template_manager.get_default_template()
        if default:
            st.session_state.selected_template = default["id"]


def _get_brand_config():
    cfg = {
        "brand_name": "IA Excel Pro",
        "brand_primary": "#475569",
        "logo_url": None,
    }
    try:
        cfg_path = Path("templates") / "config.json"
        if cfg_path.exists():
            with open(cfg_path, "r") as f:
                data = json.load(f)
                cfg["brand_name"] = data.get("brand_name", cfg["brand_name"]) or cfg["brand_name"]
                cfg["brand_primary"] = data.get("brand_primary", cfg["brand_primary"]) or cfg["brand_primary"]
                cfg["logo_url"] = data.get("logo_url", cfg["logo_url"]) or cfg["logo_url"]
    except Exception:
        pass
    return cfg


def render_header():
    """Affiche le header moderne"""
    cfg = _get_brand_config()
    logo_html = f'<img src="{cfg["logo_url"]}" alt="logo" style="height:40px; margin-right:10px; vertical-align:middle;">' if cfg["logo_url"] else ""
    st.markdown(f"""
    <div class=\"app-header\" style=\"background: linear-gradient(135deg, {cfg['brand_primary']} 0%, #6b7280 100%);\">
        <div style=\"display:flex; align-items:center; gap:10px;\">{logo_html}<h1 style=\"margin:0;\">🚀 {cfg['brand_name']}</h1></div>
        <p>Transformez vos catalogues avec l'IA • Matching automatique • Génération SEO ultra-rapide</p>
        <span class=\"app-badge\">✨ Powered by OpenRouter & OpenAI</span>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    """Affiche un pied de page professionnel"""
    st.markdown("""
    <hr style="margin:2rem 0; opacity:0.2;" />
    <div style="display:flex; justify-content:space-between; align-items:center; color:#64748B; font-size:0.9rem;">
        <div>© {year} IA Excel Pro — Outils de génération catalogue & SEO</div>
        <div style="opacity:0.9;">Besoin d'aide ? <a href="#" style="text-decoration:none;">Documentation</a></div>
    </div>
    """.format(year=datetime.now().year), unsafe_allow_html=True)


def render_stepper():
    """Affiche le stepper de progression"""
    steps = [
        {"id": "upload", "label": "Upload", "desc": "Chargement"},
        {"id": "matching", "label": "Matching", "desc": "Colonnes"},
        {"id": "seo", "label": "SEO", "desc": "Génération"},
        {"id": "complete", "label": "Terminé", "desc": "Export"}
    ]
    
    current_phase = st.session_state.phase
    current_idx = next((i for i, s in enumerate(steps) if s["id"] == current_phase), 0)
    
    # Générer le HTML complet en une seule chaîne
    html = '<div class="stepper-container"><div class="stepper">'
    
    for i, step in enumerate(steps):
        status = "completed" if i < current_idx else "active" if i == current_idx else ""
        icon = "✓" if i < current_idx else str(i + 1)
        
        html += f'<div class="step {status}"><div class="step-circle">{icon}</div><div class="step-label">{step["label"]}</div><div class="step-description">{step["desc"]}</div></div>'
    
    html += '</div></div>'
    
    st.markdown(html, unsafe_allow_html=True)


def render_settings():
    """Page Paramètres avec tests de connectivité"""
    st.markdown("## ⚙️ Paramètres & Diagnostics")

    # Lecture config rapide
    cfg = _get_brand_config()
    with st.expander("🎨 Branding"):
        st.markdown(f"**Nom de l'app**: {cfg['brand_name']}")
        st.markdown(f"**Couleur primaire**: `{cfg['brand_primary']}`")
        st.markdown(f"**Logo**: {'défini' if cfg['logo_url'] else 'non défini'}")
        st.caption("Modifiez `templates/config.json` pour personnaliser: brand_name, brand_primary, logo_url")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🤖 Test API IA (OpenAI/OpenRouter)")
        if st.button("Tester connexion IA", use_container_width=True):
            try:
                from src.ai_client_factory import AIClientFactory
                
                # Récupérer la clé actuelle (session ou secrets)
                current_api_key = st.session_state.get("api_key") or get_secret("OPENAI_API_KEY")
                
                if not current_api_key:
                    st.error("❌ Aucune clé API configurée")
                else:
                    # Réinitialiser la factory pour forcer une nouvelle connexion avec la clé actuelle
                    AIClientFactory.reset()
                    
                    # Utiliser la factory pour obtenir le client avec la clé actuelle
                    client_wrapper = AIClientFactory.get_client(provider="openai", api_key=current_api_key)
                    
                    if not client_wrapper or not client_wrapper.is_available():
                        st.error("❌ Client IA non disponible (vérifiez la clé API)")
                    else:
                        # Test via le wrapper
                        resp = client_wrapper.generate(
                            prompt="ping",
                            system="Réponds uniquement par: pong",
                            max_tokens=4
                        )
                        
                        if resp and "pong" in resp.lower():
                            st.success(f"✅ Connexion IA OK ({client_wrapper.model})")
                        else:
                            st.warning(f"⚠️ Réponse inattendue: {resp}")
            except Exception as e:
                st.error(f"❌ Échec connexion IA: {e}")

    with col2:
        st.markdown("### 🌐 Test Serper (Google Search)")
        serper_key = get_secret("SERPER_API_KEY")
        if not serper_key:
            st.warning("SERPER_API_KEY non définie dans l'environnement")
        if st.button("Tester Serper", use_container_width=True):
            if not serper_key:
                st.error("❌ Clé manquante")
            else:
                try:
                    headers = {"X-API-KEY": serper_key, "Content-Type": "application/json"}
                    payload = {"q": "Arrow 11005MI motorcycle", "num": 1, "gl": "fr", "hl": "fr"}
                    r = requests.post("https://google.serper.dev/search", headers=headers, json=payload, timeout=8)
                    if r.status_code == 200 and r.json().get("searchParameters"):
                        st.success("✅ Serper opérationnel")
                    else:
                        st.warning(f"⚠️ Réponse inattendue {r.status_code}")
                except Exception as e:
                    st.error(f"❌ Échec Serper: {e}")

    st.divider()
    st.markdown("### 🧪 Outils")
    st.caption("Vous pouvez vider les caches ou réinitialiser l'état si besoin.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("♻️ Réinitialiser l'état", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.success("État réinitialisé. Recharger la page.")
    with c2:
        if st.button("🧹 Vider le cache SEO", use_container_width=True):
            st.session_state.seo_results = None
            st.session_state.seo_generated = False
            st.success("Cache vidée.")

    st.divider()
    st.markdown("### 📜 Logs Serveur")
    st.caption("Consultez les logs pour le débogage.")
    
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            # Lire les dernières lignes pour ne pas surcharger
            lines = f.readlines()
            last_lines = "".join(lines[-500:]) # 500 dernières lignes
            
        st.text_area("Derniers logs", last_lines, height=300, key="log_viewer")
        
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            st.download_button("⬇️ Télécharger les logs complets", "".join(lines), "app.log", mime="text/plain", use_container_width=True)
        with col_l2:
            if st.button("🗑️ Effacer les logs", use_container_width=True):
                with open(LOG_FILE, "w") as f:
                    f.write(f"Log cleared at {datetime.now()}\n")
                st.rerun()
    else:
        st.info("Aucun fichier de log trouvé.")



def sidebar_config(disable_nav: bool = False):
    """Configuration dans la sidebar moderne + (option) Navigation.
    disable_nav=True pour masquer la nav quand utilisé en pages.
    """
    with st.sidebar:
        # Navigation principale
        nav = None
        if not disable_nav:
            st.markdown("### 🧭 Navigation")
            nav = st.radio(
                label="Navigation",
                options=["📊 Traitement Catalogue", "🧪 Test SEO", "⚙️ Paramètres"],
                index=0,
                label_visibility="collapsed",
            )
            st.divider()
        st.markdown("## ⚙️ Configuration")
        
        # API Key (Gestion sécurisée en mémoire/session uniquement)
        # Ne jamais stocker la clé sur le disque dans config.json
        
        # Récupérer depuis st.secrets (Streamlit Cloud), l'environnement ou la session
        env_key = get_secret("OPENAI_API_KEY", "")
        session_key = st.session_state.get("api_key", "")
        current_key = session_key or env_key
        
        api_key = st.text_input(
            "🔑 Clé API",
            type="password",
            value=current_key,
            help="Votre clé OpenAI ou OpenRouter (non stockée sur disque)"
        )
        
        # Validation visuelle de la clé
        if api_key:
            if api_key.startswith("sk-or-"):
                st.success("✅ OpenRouter")
            elif api_key.startswith("sk-proj-"):
                st.success("✅ OpenAI Project")
            elif api_key.startswith("sk-"):
                st.success("✅ OpenAI")
            else:
                st.info("🔑 Clé API configurée")
            
            # Mettre à jour l'environnement et la session pour cette exécution
            os.environ["OPENAI_API_KEY"] = api_key
            st.session_state["api_key"] = api_key
        
        st.divider()
        
        # Templates
        st.markdown("### 📋 Templates")
        
        templates = st.session_state.template_manager.list_templates()
        
        if templates:
            options = ["Aucun"] + [t["name"] for t in templates]
            selected_name = st.selectbox(
                "Template actif",
                options,
                index=0 if not st.session_state.selected_template else 
                      next((i+1 for i, t in enumerate(templates) 
                            if t["id"] == st.session_state.selected_template), 0)
            )
            
            if selected_name != "Aucun":
                template = next(t for t in templates if t["name"] == selected_name)
                st.session_state.selected_template = template["id"]
                st.session_state.use_template = True
                st.success(f"✅ {selected_name}")
            else:
                st.session_state.selected_template = None
                st.session_state.use_template = False
        
        # Upload nouveau template
        with st.expander("➕ Ajouter template"):
            uploaded = st.file_uploader("Fichier Excel", type=["xlsx", "xls"], key="template_upload")
            if uploaded:
                name = st.text_input("Nom", value=Path(uploaded.name).stem)
                if st.button("💾 Sauvegarder", use_container_width=True):
                    temp_path = Path("templates") / f"temp_{uploaded.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded.getbuffer())
                    
                    try:
                        st.session_state.template_manager.add_template(
                            str(temp_path),
                            name=name,
                            set_as_default=not templates
                        )
                        st.success(f"✅ {name} ajouté !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ {e}")
                    finally:
                        if temp_path.exists():
                            temp_path.unlink()
        
        st.divider()
        
        # Statistiques d'apprentissage
        st.markdown("### 📊 Apprentissage")
        
        stats = st.session_state.learning_system.get_statistics()
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Corrections", stats["total_corrections"])
        with col2:
            st.metric("Patterns", stats["unique_patterns"])
        
        if stats["total_corrections"] > 0:
            with st.expander("📜 Historique"):
                history = st.session_state.learning_system.history
                corrections = history.get("corrections", [])
                for corr in corrections[-5:]:  # 5 dernières
                    st.caption(f"• `{corr['source']}` → `{corr['target']}`")
        
        st.divider()
        
        # Paramètres avancés
        with st.expander("🔧 Avancé"):
            model = st.selectbox(
                "Modèle",
                ["openai/gpt-4o-mini", "openai/gpt-4o", "gpt-4o", "gpt-4o-mini"],
                help="Modèle pour le matching et le SEO"
            )
            
            confidence = st.slider(
                "Confiance minimale",
                0.0, 1.0, 0.6, 0.05,
                help="Seuil de confiance pour le matching"
            )
        
        return {
            "api_key": api_key,
            "model": model,
            "confidence": confidence,
            "use_template": st.session_state.use_template,
            "nav": nav,
        }


def phase_upload(config):
    """Phase 1: Upload du catalogue"""
    st.markdown("## 📁 Upload du catalogue")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Glissez-déposez votre fichier Excel",
            type=["xlsx", "xls"],
            help="Format: .xlsx ou .xls"
        )
    
    with col2:
        if config["use_template"] and st.session_state.selected_template:
            template = next(
                (t for t in st.session_state.template_manager.list_templates() 
                 if t["id"] == st.session_state.selected_template),
                None
            )
            if template:
                st.info(f"📋 **Template**\n\n{template['name']}")
    
    if uploaded_file:
        st.divider()
        
        # Infos fichier avec cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card card-primary">
                <div class="metric-value">{len(uploaded_file.name[:20])}</div>
                <div class="metric-label">📄 {uploaded_file.name}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            size_kb = uploaded_file.size / 1024
            st.markdown(f"""
            <div class="metric-card card-success">
                <div class="metric-value">{size_kb:.1f}</div>
                <div class="metric-label">📦 KB</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            if st.button("🔍 **Analyser**", type="primary", use_container_width=True):
                with st.spinner("Analyse en cours..."):
                    result = analyze_catalog(uploaded_file, config)
                    
                    if result:
                        st.session_state.catalog_data = result['data']
                        st.session_state.catalog_headers = result['headers']
                        st.session_state.column_mapping = result['mapping']
                        st.session_state.current_file = uploaded_file
                        st.session_state.parser_config = result['parser_config']
                        st.session_state.phase = "matching"
                        
                        st.success("✅ Analyse terminée !")
                        st.balloons()
                        time.sleep(0.5)
                        st.rerun()


def analyze_catalog(uploaded_file, config):
    """Analyse le catalogue et fait le matching"""
    # Sauvegarder temporairement
    temp_path = Path("catalogues") / uploaded_file.name
    temp_path.parent.mkdir(exist_ok=True)
    
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    analyze_start = time.time()
    try:
        # Parser le catalogue
        logger.info(f"📂 Parsing catalogue: {uploaded_file.name}")
        parser = CatalogParser(str(temp_path))
        header_row = parser.detect_header_row()
        
        if not parser.load(header_row=header_row):
            logger.error("❌ Impossible de charger le catalogue")
            st.error("❌ Impossible de charger le catalogue")
            return None
        
        headers = parser.get_headers()
        logger.info(f"✓ Catalogue chargé: {len(headers)} colonnes, {len(parser.df)} lignes")
        
        # Déterminer les colonnes cibles
        target_columns = []
        if st.session_state.use_template and st.session_state.selected_template:
            logger.info(f"📋 Utilisation template: {st.session_state.selected_template}")
            template_path = st.session_state.template_manager.get_template_path(
                st.session_state.selected_template
            )
            if template_path:
                injector = TemplateInjector(template_path)
                injector.select_sheet()
                target_columns = injector.get_headers_from_row(row=1)
                logger.info(f"✓ Template: {len(target_columns)} colonnes cibles")
        
        if not target_columns:
            target_columns = headers  # Prendre toutes les colonnes du catalogue
            logger.info("⚠️ Pas de template, utilisation des colonnes du catalogue")
        
        logger.info(f"📊 Headers catalogue: {headers[:5]}...")
        logger.info(f"🎯 Colonnes cibles: {target_columns[:5]}...")
        
        # Matching intelligent
        logger.info("🔄 Démarrage du matching intelligent...")
        matcher_start = time.time()
        matcher = ColumnMatcher()
        
        column_mapping = matcher.match_with_fallback(
            column_headers=headers,
            target_columns=target_columns,
            use_ai=bool(config.get("api_key")),
            learning_system=st.session_state.learning_system
        )
        
        matcher_elapsed = time.time() - matcher_start
        matched = sum(1 for v in column_mapping.values() if v.get('column'))
        logger.info(f"✅ Matching terminé: {matched}/{len(column_mapping)} en {matcher_elapsed:.1f}s")
        
        temp_path.unlink()
        
        total_elapsed = time.time() - analyze_start
        logger.info(f"🎉 Analyse complète en {total_elapsed:.1f}s")
        
        return {
            "data": parser.df,
            "headers": headers,
            "mapping": column_mapping,
            "parser_config": {"header_row": header_row}
        }
        
    except Exception as e:
        elapsed = time.time() - analyze_start
        logger.error(f"❌ Erreur analyse après {elapsed:.1f}s: {str(e)}", exc_info=True)
        st.error(f"❌ Erreur: {str(e)}")
        if temp_path.exists():
            temp_path.unlink()
        return None


def phase_matching(config):
    """Phase 2: Validation du matching"""
    st.markdown("## 🔗 Validation des correspondances")
    
    mapping = st.session_state.column_mapping
    catalog_data = st.session_state.catalog_data
    
    # Stats
    matched = sum(1 for v in mapping.values() if v.get('column'))
    total = len(mapping)
    percent = (matched / total * 100) if total > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(catalog_data)}</div>
            <div class="metric-label">📊 LIGNES</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card card-success">
            <div class="metric-value">{matched}/{total}</div>
            <div class="metric-label">✓ MATCHÉES</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        color = "card-success" if percent > 70 else "card-warning"
        st.markdown(f"""
        <div class="metric-card {color}">
            <div class="metric-value">{percent:.0f}%</div>
            <div class="metric-label">📈 TAUX</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Interface de validation
    st.markdown("### 🔧 Ajuster les correspondances")
    
    catalog_cols = list(catalog_data.columns)
    corrections = {}
    
    # Filtrer pour ne montrer que les colonnes importantes
    for template_col, info in mapping.items():
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.markdown(f"**{template_col}**")
        
        with col2:
            current = info.get('column', '')
            options = [''] + catalog_cols
            
            selected = st.selectbox(
                f"mapping_{template_col}",
                options,
                index=catalog_cols.index(current) + 1 if current in catalog_cols else 0,
                key=f"select_{template_col}",
                label_visibility="collapsed"
            )
            
            if selected != current:
                corrections[template_col] = selected
        
        with col3:
            conf = info.get('confidence', 0)
            method = info.get('method', '?')
            
            if conf >= 0.8:
                st.success(f"✓ {conf:.0%}")
            elif conf >= 0.5:
                st.warning(f"⚠ {conf:.0%}")
            else:
                st.error(f"✗ {method}")
    
    # Appliquer corrections
    if corrections:
        for template_col, catalog_col in corrections.items():
            mapping[template_col] = {
                'column': catalog_col,
                'confidence': 1.0,
                'method': 'manual'
            }
    
    st.divider()
    
    # Preview
    st.markdown("### 👁️ Aperçu")
    preview_mapping = {k: v['column'] for k, v in mapping.items() if v['column']}
    
    if preview_mapping:
        preview_df = catalog_data[[col for col in preview_mapping.values() if col in catalog_data.columns]].head(5)
        preview_df.columns = [k for k, v in preview_mapping.items() if v in catalog_data.columns]
        st.dataframe(preview_df, use_container_width=True)
    
    st.divider()
    
    # Actions
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("↩️ Retour", use_container_width=True):
            st.session_state.phase = "upload"
            st.rerun()
    
    with col2:
        if st.button("✅ Valider et continuer", type="primary", use_container_width=True):
            # Sauvegarder corrections
            if corrections:
                for template_col, catalog_col in corrections.items():
                    st.session_state.learning_system.add_correction(catalog_col, template_col)
            
            # Générer le fichier
            result = generate_output(st.session_state.current_file, config, mapping)
            
            if result:
                st.session_state.output_path = str(result['output_path'])
                st.session_state.phase = "seo"
                st.success("✅ Fichier généré !")
                time.sleep(0.5)
                st.rerun()


def generate_output(uploaded_file, config, validated_mapping):
    """Génère le fichier Excel avec le mapping validé"""
    temp_path = Path("catalogues") / uploaded_file.name
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    template_path = None
    if config.get("use_template") and st.session_state.selected_template:
        template_path = st.session_state.template_manager.get_template_path(
            st.session_state.selected_template
        )
    
    try:
        parser = CatalogParser(str(temp_path))
        header_row = st.session_state.parser_config.get('header_row', 0)
        parser.load(header_row=header_row)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path("output") / f"resultat_{timestamp}.xlsx"
        output_path.parent.mkdir(exist_ok=True)
        
        if template_path:
            # Mode template
            extracted_df = parser.df.copy()
            injector = TemplateInjector(str(template_path))
            injector.select_sheet()
            
            template_mapping = {k: v['column'] for k, v in validated_mapping.items() if v.get('column')}
            
            if template_mapping:
                injector.inject_with_column_mapping(extracted_df, template_mapping, header_row=1)
            else:
                injector.inject_data(extracted_df, include_headers=True, start_row=2, start_col=1)
            
            injector.save(str(output_path))
        else:
            # Mode standard
            simple_mapping = {k: v['column'] for k, v in validated_mapping.items()}
            extracted_df = parser.extract_data(simple_mapping)
            
            summary_data = {
                "Fichier source": uploaded_file.name,
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Lignes": len(extracted_df),
            }
            
            MatrixGenerator.create_matrix_excel(
                df=extracted_df,
                output_path=str(output_path),
                column_mapping=validated_mapping,
                summary_data=summary_data
            )
        
        temp_path.unlink()
        
        return {"output_path": output_path}
        
    except Exception as e:
        st.error(f"❌ Erreur génération: {str(e)}")
        if temp_path.exists():
            temp_path.unlink()
        return None


def phase_seo(config):
    """Phase 3: Génération SEO"""
    st.markdown("## ✨ Génération de descriptions SEO")
    
    output_path = st.session_state.output_path
    
    # Dashboard SEO
    st.markdown("""
    <div class="seo-dashboard">
        <h3 style="margin-top: 0;">🚀 Génération ultra-rapide avec OpenRouter</h3>
        <p style="color: var(--gray-700); margin-bottom: 2rem;">
            Descriptions SEO optimisées • Technique • Multilingue • ~3-5 sec/produit
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Vérifier si déjà généré
    if st.session_state.seo_generated:
        st.success(f"✅ Descriptions générées avec succès !")
        
        # Stats
        results = st.session_state.seo_results
        if results:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("""
                <div class="seo-stat">
                    <div class="seo-stat-value">{}</div>
                    <div class="seo-stat-label">Produits</div>
                </div>
                """.format(len(results)), unsafe_allow_html=True)
            
            with col2:
                avg_words = sum(len(r['description'].split()) for r in results) / len(results)
                st.markdown(f"""
                <div class="seo-stat">
                    <div class="seo-stat-value">{avg_words:.0f}</div>
                    <div class="seo-stat-label">Mots/desc.</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                from_cache = sum(1 for r in results if r.get('from_cache', False))
                st.markdown(f"""
                <div class="seo-stat">
                    <div class="seo-stat-value">{from_cache}</div>
                    <div class="seo-stat-label">Cache hits</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                time_estimate = len(results) * 4  # ~4 sec/produit
                minutes = time_estimate // 60
                st.markdown(f"""
                <div class="seo-stat">
                    <div class="seo-stat-value">{minutes}</div>
                    <div class="seo-stat-label">Minutes</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        
        # Preview
        if st.checkbox("👁️ Prévisualiser les descriptions", value=False):
            try:
                df = pd.read_excel(st.session_state.output_path)
                
                if 'Description SEO' in df.columns:
                    idx = st.slider("Produit", 0, len(df)-1, 0)
                    row = df.iloc[idx]
                    
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.markdown("**📦 Produit**")
                        for col in ['Référence', 'Libellé', 'Marque']:
                            if col in row:
                                st.write(f"**{col}:** {row[col]}")
                    
                    with col2:
                        st.markdown("**📝 SEO**")
                        desc = str(row.get('Description SEO', ''))
                        st.write(f"**Mots:** {len(desc.split())}")
                        st.write(f"**Caractères:** {len(desc)}")
                    
                    st.divider()
                    st.markdown("**🎯 Titre SEO**")
                    st.info(row.get('Titre SEO', 'N/A'))
                    
                    st.markdown("**📝 Description**")
                    st.text_area("Description", desc, height=200, disabled=True, label_visibility="collapsed")
            
            except Exception as e:
                st.error(f"❌ Erreur preview: {e}")
        
        st.divider()
        
        if st.button("➡️ Continuer vers le téléchargement", type="primary", use_container_width=True):
            st.session_state.phase = "complete"
            st.rerun()
    
    else:
        # Bouton de génération
        if st.button("🚀 Générer les descriptions SEO", type="primary", use_container_width=True):
            try:
                df = pd.read_excel(output_path)
                
                generator = ProductDescriptionGenerator(
                    use_cache=True, 
                    provider="openai",
                    use_web_search=True  # Active la recherche web comme pour la génération manuelle
                )
                
                if not generator.is_available():
                    st.error("❌ OpenRouter/OpenAI non disponible. Vérifiez votre clé API.")
                    return
                
                # Progress
                progress_bar = st.progress(0)
                status = st.empty()
                stop_button = st.button("🛑 Arrêter la génération")
                
                total = len(df)
                status.text(f"🤖 Génération en cours... (0/{total})")
                
                # Liste pour stocker les résultats
                results = []
                
                # Boucle séquentielle avec mise à jour UI
                for i, row in df.iterrows():
                    if stop_button:
                        st.warning("⚠️ Génération arrêtée par l'utilisateur.")
                        break
                        
                    product = row.to_dict()
                    
                    # Génération unitaire
                    result = generator.generate_full_seo(product, language='fr')
                    results.append(result)
                    
                    # Mise à jour UI
                    progress = (i + 1) / total
                    progress_bar.progress(progress)
                    status.text(f"🤖 Génération OpenRouter... ({i + 1}/{total})")
                
                # Compléter avec des vides si arrêté
                while len(results) < len(df):
                    results.append({'description': "", 'seo_title': "", 'meta_description': ""})
                
                # Ajouter au DataFrame
                df['Description SEO'] = [r['description'] for r in results]
                df['Titre SEO'] = [r['seo_title'] for r in results]
                df['Meta Description'] = [r['meta_description'] for r in results]
                
                # Sauvegarder
                seo_path = output_path.replace('.xlsx', '_SEO.xlsx')
                df.to_excel(seo_path, index=False)
                
                # Mettre à jour state
                st.session_state.seo_generated = True
                st.session_state.seo_results = results
                st.session_state.output_path = seo_path
                
                progress_bar.progress(1.0)
                status.text(f"✅ {len(results)} descriptions générées !")
                st.balloons()
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Erreur: {str(e)}")


def phase_complete():
    """Phase 4: Téléchargement"""
    st.markdown("## 🎉 Traitement terminé !")
    
    st.success("✅ Votre fichier est prêt au téléchargement")
    
    output_path = st.session_state.output_path
    
    if os.path.exists(output_path):
        # Vue catalogue avant téléchargement
        with st.expander("📊 Aperçu & Filtres du catalogue généré", expanded=False):
            try:
                df = pd.read_excel(output_path)
                
                # Filtres
                col_search, col_filter = st.columns([2, 1])
                with col_search:
                    search_term = st.text_input("🔍 Rechercher (Référence, Libellé, Marque...)", "", key="catalog_search")
                with col_filter:
                    filter_col = st.selectbox("Filtrer par colonne", ["Toutes"] + list(df.columns), key="catalog_filter_col")
                
                # Appliquer recherche
                df_filtered = df.copy()
                if search_term:
                    mask = df_filtered.astype(str).apply(lambda row: row.str.contains(search_term, case=False, na=False).any(), axis=1)
                    df_filtered = df_filtered[mask]
                
                st.caption(f"📄 {len(df_filtered)} produits affichés sur {len(df)}")
                
                # Tableau interactif
                st.dataframe(
                    df_filtered,
                    use_container_width=True,
                    hide_index=True,
                    height=400,
                )
                
                # Export CSV filtré
                if len(df_filtered) < len(df):
                    csv_bytes = BytesIO(df_filtered.to_csv(index=False).encode("utf-8"))
                    st.download_button(
                        "⬇️ Télécharger la sélection filtrée (CSV)",
                        data=csv_bytes,
                        file_name=f"catalogue_filtre_{len(df_filtered)}_produits.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"❌ Erreur d'affichage: {e}")
        
        st.divider()
        
        col_dl1, col_dl2 = st.columns(2)
        
        with col_dl1:
            with open(output_path, "rb") as f:
                st.download_button(
                    label="📥 Télécharger le fichier Excel",
                    data=f,
                    file_name=os.path.basename(output_path),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        with col_dl2:
            # Export ZIP des RTF
            if st.button("📦 Télécharger tout (ZIP Word)", use_container_width=True):
                try:
                    import zipfile
                    
                    df = pd.read_excel(output_path)
                    zip_buffer = BytesIO()
                    
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for _, row in df.iterrows():
                            if 'Description SEO' in row and pd.notna(row['Description SEO']):
                                # Nom du fichier: Marque_Reference.rtf
                                ref = str(row.get('Référence', 'REF')).replace('/', '-')
                                marque = str(row.get('Marque', 'MARQUE')).replace('/', '-')
                                filename = f"{marque}_{ref}.rtf"
                                
                                # Contenu RTF
                                rtf_content = format_description_for_word(row['Description SEO'])
                                zip_file.writestr(filename, rtf_content)
                    
                    st.download_button(
                        label="⬇️ Cliquer pour télécharger le ZIP",
                        data=zip_buffer.getvalue(),
                        file_name="descriptions_word.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Erreur ZIP: {e}")
        
        st.info(f"💾 **Fichier:** `{os.path.basename(output_path)}`")
        st.caption(f"📍 **Emplacement:** `{output_path}`")


def seo_testing_tab(config):
    """Onglet de test SEO pour un seul produit"""
    st.markdown("## 🧪 Test de génération SEO")
    
    # Mode sélection
    mode = st.radio(
        "Mode",
        ["🤖 Générer avec IA", "📝 Coller une description existante", "🎨 Appliquer le format à un nouveau produit"],
        horizontal=True,
        key="seo_test_mode"
    )
    
    st.divider()
    
    if mode == "📝 Coller une description existante":
        st.markdown("### 📝 Description personnalisée")
        st.markdown("Collez une description existante et l'IA la retravaillera au style Motoblouz")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            custom_description = st.text_area(
                "Description originale",
                "",
                height=200,
                key="seo_test_custom_desc",
                placeholder="Collez votre description ici..."
            )
            
            if custom_description:
                st.markdown("---")
                
                # Paramètres de réécriture
                col_a, col_b = st.columns(2)
                with col_a:
                    rewrite_language = st.selectbox("Langue", ["fr", "en", "it", "es", "de"], index=0, key="rewrite_lang")
                with col_b:
                    rewrite_temp = st.slider("Créativité", 0.0, 1.0, 0.7, 0.1, key="rewrite_temp")
                
                rewrite_instructions = st.text_input(
                    "Instructions supplémentaires (optionnel)",
                    "",
                    key="rewrite_instructions",
                    placeholder="Ex: Insister sur la sécurité, mentionner la garantie"
                )
        
        with col2:
            st.markdown("### 📊 Statistiques")
            if custom_description:
                words = len(custom_description.split())
                chars = len(custom_description)
                sentences = custom_description.count('.') + custom_description.count('!') + custom_description.count('?')
                
                st.metric("Mots", words)
                st.metric("Caractères", chars)
                st.metric("Phrases", sentences)
                
                # Analyse
                if words < 80:
                    st.warning("⚠️ Trop court")
                elif words > 200:
                    st.warning("⚠️ Trop long")
                else:
                    st.success("✅ Longueur OK")
            else:
                st.info("Aucune description")
        
        if custom_description:
            st.divider()
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("✨ Réécrire style Motoblouz", type="primary", use_container_width=True, key="rewrite_btn"):
                    # Réécriture avec IA
                    with st.spinner("🤖 Réécriture en cours..."):
                        generator = ProductDescriptionGenerator(
                            use_cache=False,
                            provider="openai",
                            use_web_search=False
                        )
                        
                        if not generator.is_available():
                            st.error("❌ Service IA non disponible")
                        else:
                            # Créer un produit fictif pour la réécriture
                            rewrite_prompt = f"""Réécris cette description de produit moto dans le style exact de Motoblouz.

DESCRIPTION ORIGINALE:
{custom_description}

STYLE MOTOBLOUZ (inspiré du site motoblouz.com):
✨ ACCROCHE PUNCHY:

🔧 CARACTÉRISTIQUES TECHNIQUES:

🏍️ PERFORMANCE ET USAGE:

✅ CONFIANCE:

📏 LONGUEUR: 100-150 mots maximum

🎯 TON:

❌ À ÉVITER:

📏 LONGUEUR: 80-120 mots

📝 FORMATAGE MARKDOWN OBLIGATOIRE:

EXEMPLE DE FORMATAGE:
"Arrow vous propose ce silencieux **Paris-Dakar** pour votre **Yamaha XT 600E**.
Fabriqué en **acier inoxydable**, il offre une construction robuste.

**Caractéristiques principales** :
• Matériau : acier inoxydable
• Design ligne Paris-Dakar
• Construction robuste
• Finition professionnelle

<b>Ce silencieux n'est pas homologué pour un usage routier.</b>"

IMPÉRATIF:

{rewrite_instructions if rewrite_instructions else ''}

Description Motoblouz:"""
                            
                            # Utiliser l'API via la Factory
                            try:
                                from src.ai_client_factory import AIClientFactory
                                client_wrapper = AIClientFactory.get_client(provider="openai")
                                
                                if not client_wrapper:
                                    raise ValueError("Client IA non initialisé")
                                
                                rewritten = client_wrapper.generate(
                                    prompt=rewrite_prompt,
                                    system="Tu es un rédacteur de catalogue professionnel pour Motoblouz. Ton style est factuel, descriptif et technique. Tu présentes les produits de façon informative sans marketing émotionnel. Tu n'utilises JAMAIS d'expressions enthousiastes ou promotionnelles. Tu utilises TOUJOURS le formatage Markdown : **gras** pour les mots-clés importants et • listes à puces pour les caractéristiques. Pour les informations d'homologation importantes (homologué/non homologué), utilise <b>texte</b> pour le mettre en gras HTML.",
                                    temperature=rewrite_temp,
                                    max_tokens=500
                                )
                                
                                if not rewritten:
                                    raise ValueError("Réponse vide de l'IA")
                                
                                st.success("✅ Description réécrite !")
                                
                                # Statistiques comparées
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Mots", len(rewritten.split()), delta=len(rewritten.split()) - words)
                                with col2:
                                    st.metric("Caractères", len(rewritten), delta=len(rewritten) - chars)
                                with col3:
                                    new_sentences = rewritten.count('.') + rewritten.count('!') + rewritten.count('?')
                                    st.metric("Phrases", new_sentences, delta=new_sentences - sentences)
                                
                                st.divider()
                                
                                # Affichage comparatif
                                col_orig, col_new = st.columns(2)
                                
                                with col_orig:
                                    st.markdown("### 📄 Originale")
                                    st.text_area("Description originale", custom_description, height=250, disabled=True, label_visibility="collapsed", key="orig_display")
                                
                                with col_new:
                                    st.markdown("### ✨ Style Motoblouz")
                                    st.markdown(rewritten, unsafe_allow_html=True)
                                
                                st.divider()
                                st.markdown("### 📋 Copier la nouvelle version")
                                st.code(rewritten, language=None)
                                st.info("💡 Sélectionnez et copiez le texte ci-dessus (Ctrl+C)")
                                
                            except Exception as e:
                                st.error(f"❌ Erreur: {str(e)}")
            
            with col_btn2:
                if st.button("📋 Copier l'originale", use_container_width=True, key="copy_original"):
                    st.code(custom_description, language=None)
                    st.info("💡 Sélectionnez et copiez le texte ci-dessus")
    
    elif mode == "🎨 Appliquer le format à un nouveau produit":
        """Mode: Charger un template de format et l'appliquer à un nouveau produit"""
        st.markdown("### 🎨 Appliquer le format d'une description existante à un nouveau produit")
        st.markdown("1. Collez une description **modèle** pour extraire son format")
        st.markdown("2. Fournissez le lien ou la référence du **nouveau produit**")
        st.markdown("3. L'IA génèrera la nouvelle description avec la même structure")
        
        col_template, col_new = st.columns(2)
        
        with col_template:
            st.markdown("#### 📋 Description Modèle")
            template_description = st.text_area(
                "Collez une description existante",
                "",
                height=250,
                key="seo_template_desc",
                placeholder="Collez votre description modèle ici..."
            )
            
            if template_description:
                # Analyser le template
                from src.format_template_analyzer import FormatTemplateAnalyzer
                analyzer = FormatTemplateAnalyzer()
                template_structure = analyzer.analyze_structure(template_description)
                
                st.markdown("**📊 Structure du modèle:**")
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    st.metric("Mots", template_structure['total_words'])
                    st.metric("Phrases", template_structure['total_sentences'])
                with col_t2:
                    st.metric("Lignes", template_structure['total_lines'])
                    st.metric("Caractères", template_structure['total_chars'])
                
                # Afficher les éléments de format
                if template_structure['format_elements']:
                    st.markdown("**🎨 Éléments de formatage détectés:**")
                    for elem in template_structure['format_elements']:
                        st.caption(f"• {elem.replace('_', ' ').title()}")
                
                st.session_state.template_structure = template_structure
        
        with col_new:
            st.markdown("#### 📦 Nouveau Produit")
            
            new_product_url = st.text_input(
                "Lien ou référence du produit",
                "",
                key="seo_new_product_url",
                placeholder="https://example.com/product ou REFERENCE123"
            )
            
            new_product_name = st.text_input(
                "Nom du produit",
                "",
                key="seo_new_product_name",
                placeholder="Ex: Silencieux Paris-Dakar pour Yamaha XT 600"
            )
            
            new_product_description = st.text_area(
                "Informations sur le produit (optionnel)",
                "",
                height=200,
                key="seo_new_product_desc",
                placeholder="Caractéristiques techniques, matériaux, utilisations..."
            )
        
        st.divider()
        
        if template_description and new_product_url:
            if st.button("✨ Générer avec le même format", type="primary", use_container_width=True, key="apply_format_btn"):
                with st.spinner("🤖 Génération en cours..."):
                    try:
                        from src.format_template_analyzer import FormatTemplateAnalyzer
                        from src.ai_client_factory import AIClientFactory
                        
                        analyzer = FormatTemplateAnalyzer()
                        template_structure = st.session_state.get('template_structure', analyzer.analyze_structure(template_description))
                        
                        # Générer le prompt
                        format_prompt = analyzer.generate_format_prompt(
                            template_structure,
                            product_url=new_product_url,
                            product_name=new_product_name
                        )
                        
                        # Ajouter les informations du produit
                        full_prompt = format_prompt + f"\n\nProduit: {new_product_name}\nLien: {new_product_url}"
                        if new_product_description:
                            full_prompt += f"\n\nInformations supplémentaires:\n{new_product_description}"
                        
                        # Utiliser l'IA pour générer
                        client_wrapper = AIClientFactory.get_client(provider="openai")
                        
                        if not client_wrapper:
                            st.error("❌ Client IA non disponible")
                        else:
                            # Déterminer le format et adapter le system prompt
                            format_type = template_structure.get('format_type', 'plain')
                            
                            if format_type == 'html':
                                system_prompt = """Tu es un rédacteur de catalogue professionnel pour Motoblouz spécialisé en formatage HTML.

IMPÉRATIF ABSOLU: Tu dois générer EXACTEMENT du HTML avec:
- <div>...</div> pour les blocs de texte
- <span style="font-weight: bold;">texte important</span> pour les éléments clés
- <ul><li>...</li></ul> pour les listes
- <br> pour les sauts de ligne
- Pas de Markdown (**texte**)

Tu respectes:
1. Le nombre de mots (±10%)
2. La structure HTML exacte
3. Les balises et styles fournis
4. Les sections originales
5. Tu n'inventes JAMAIS de contenu

RÉSULTAT: HTML pur, prêt à afficher."""
                            else:
                                system_prompt = """Tu es un rédacteur de catalogue professionnel pour Motoblouz. Tu respectes EXACTEMENT le format fourni. Tu dois maintenir le même nombre de mots (±10%), les mêmes éléments de formatage (gras, puces, sections). Tu n'inventes JAMAIS de contenu. Tu es factuel et technique."""
                            
                            generated = client_wrapper.generate(
                                prompt=full_prompt,
                                system=system_prompt,
                                temperature=0.6,
                                max_tokens=1000
                            )
                            
                            if not generated:
                                st.error("❌ Réponse vide de l'IA")
                            else:
                                st.success("✅ Description générée avec le même format !")
                                
                                # Comparer les structures
                                comparison = analyzer.compare_structures(template_description, generated)
                                
                                # Afficher le score de conformité
                                col_score1, col_score2, col_score3 = st.columns(3)
                                
                                with col_score1:
                                    compliance_score = comparison['format_compliance_score']
                                    color = "green" if compliance_score > 80 else "orange" if compliance_score > 60 else "red"
                                    st.metric(
                                        "Score de conformité",
                                        f"{compliance_score:.0f}%",
                                        delta=f"{compliance_score - 50:.0f}%" if compliance_score > 50 else None
                                    )
                                
                                with col_score2:
                                    word_diff = comparison['word_count_diff']
                                    word_percent = comparison['word_count_percent']
                                    st.metric("Différence mots", f"{word_diff} ({word_percent:.1f}%)")
                                
                                with col_score3:
                                    match_count = sum(1 for v in comparison['format_match'].values() if v)
                                    st.metric("Format respecté", f"{match_count}/4")
                                
                                # Afficher les recommandations
                                st.markdown("### 📋 Vérification du format")
                                for rec in comparison['recommendations']:
                                    if rec.startswith("✅"):
                                        st.success(rec)
                                    elif rec.startswith("❌"):
                                        st.warning(rec)
                                
                                st.divider()
                                
                                # Affichage comparatif
                                col_modele, col_gen = st.columns(2)
                                
                                with col_modele:
                                    st.markdown("### 📄 Modèle")
                                    st.text_area("Description modèle", template_description, height=300, disabled=True, label_visibility="collapsed", key="model_display")
                                
                                with col_gen:
                                    st.markdown("### ✨ Nouvelle Description")
                                    st.markdown(generated, unsafe_allow_html=True)
                                
                                st.divider()
                                st.markdown("### 📋 Copier la nouvelle version")
                                st.code(generated, language=None)
                                st.info("💡 Sélectionnez et copiez le texte ci-dessus (Ctrl+C)")
                    
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")
                        logger.error(f"Format template error: {str(e)}")
    
    else:
        # Mode génération IA
        st.markdown("Testez la génération de descriptions SEO avec recherche web en temps réel")
        
        st.divider()
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 📦 Informations Produit")
            
            reference = st.text_input("Référence fournisseur", "11005MI", key="seo_test_reference", help="Ex: 11005MI")
            marque = st.text_input("Marque (catalogue)", "ARROW", key="seo_test_marque", help="Ex: ARROW, BMW, AKRAPOVIC")
            libelle = st.text_input("Libellé", "CARBON HEAT SHIELD", key="seo_test_libelle", help="Description courte du produit")
            categorie = st.selectbox("Catégorie", [
                "Pare-chaleur",
                "Échappement",
                "Silencieux",
                "Casque",
                "Blouson",
                "Gants",
                "Bottes",
                "Protection",
                "Accessoire"
            ], key="seo_test_categorie")
            
            use_web_search = st.checkbox("🌐 Activer la recherche web (Serper)", value=True, 
                                        key="seo_test_websearch",
                                        help="Enrichit avec infos trouvées sur Google")
            
            language = st.selectbox("Langue", ["fr", "en", "it", "es", "de"], index=0, key="seo_test_language")
        
        with col2:
            st.markdown("### ⚙️ Paramètres")
            
            temperature = st.slider("Créativité", 0.0, 1.0, 0.7, 0.1, 
                                key="seo_test_temperature",
                                help="Plus élevé = plus créatif")
            
            word_count = st.slider("Nombre de mots cible", 80, 200, 140, 10, key="seo_test_wordcount")
            
            custom_instructions = st.text_area(
                "Instructions personnalisées (optionnel)",
                "",
                height=100,
                key="seo_test_instructions",
                help="Ex: Insister sur la durabilité, mentionner la garantie"
            )
        
        st.divider()
        
        if st.button("🚀 Générer la description", type="primary", use_container_width=True):
            if not reference or not marque:
                st.error("❌ Référence et Marque sont obligatoires")
                return
            
            # Créer les données produit
            product_data = {
                'Référence': reference,
                'Marque': marque,
                'Libellé': libelle,
                'Catégorie': categorie,
                'Désignation': libelle
            }
            
            # Initialiser le générateur
            with st.spinner("🤖 Initialisation de l'IA..."):
                generator = ProductDescriptionGenerator(
                    use_cache=False,
                    provider="openai",
                    use_web_search=use_web_search
                )
                
                if not generator.is_available():
                    st.error("❌ Service IA non disponible. Vérifiez votre clé API.")
                    return
            
            # Recherche web si activée
            if use_web_search:
                with st.spinner("🔍 Recherche sur Google via Serper..."):
                    from src.web_search import WebSearchEnricher
                    
                    serper_key = get_secret('SERPER_API_KEY')
                    if serper_key:
                        searcher = WebSearchEnricher(serper_key)
                        search_result = searcher.search_product_info(product_data)
                        
                        if search_result.get('found'):
                            st.success(f"✅ {len(search_result.get('search_results', []))} résultats trouvés sur le web")
                            
                            with st.expander("🌐 Résultats de recherche web"):
                                for i, result in enumerate(search_result.get('search_results', [])[:3], 1):
                                    st.markdown(f"**{i}. [{result.get('type', '')}]** {result.get('title', '')}")
                                    st.caption(result.get('snippet', '')[:200] + '...')
                                    st.caption(f"🔗 {result.get('source', '')[:60]}...")
                        else:
                            st.info("ℹ️ Aucun résultat web - utilisation du contexte expert")
                    else:
                        st.warning("⚠️ SERPER_API_KEY non configurée - recherche web désactivée")
            
            # Génération
            with st.spinner(f"✨ Génération de la description en {language}..."):
                description = generator.generate_description(
                    product_data=product_data,
                    language=language,
                    category=categorie,
                    temperature=temperature,
                    custom_instructions=custom_instructions if custom_instructions else None
                )
            
            if description:
                st.success("✅ Description générée !")
                
                # Statistiques
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Mots", len(description.split()))
                with col2:
                    st.metric("Caractères", len(description))
                with col3:
                    st.metric("Phrases", description.count('.') + description.count('!') + description.count('?'))
                
                st.divider()
                
                # Description générée avec rendu HTML
                st.markdown("### 📝 Description générée")
                st.markdown(description, unsafe_allow_html=True)
                
                # Historique et exports
                hist = st.session_state.get("seo_history", [])
                hist.append({
                    "timestamp": datetime.now().isoformat(timespec='seconds'),
                    "reference": reference,
                    "marque": marque,
                    "categorie": categorie,
                    "lang": language,
                    "words": len(description.split()),
                    "web": bool(use_web_search),
                })
                st.session_state.seo_history = hist[-50:]

                st.markdown("#### 📥 Export")
                col_dl1, col_dl2, col_dl3 = st.columns(3)
                rtf_content = format_description_for_word(description)
                rtf_bytes = BytesIO(rtf_content.encode("utf-8"))
                txt_bytes = BytesIO(description.encode("utf-8"))
                with col_dl1:
                    st.download_button("⬇️ Word (.rtf)", data=rtf_bytes, file_name=f"seo_{marque}_{reference}.rtf", mime="application/rtf", use_container_width=True)
                with col_dl2:
                    st.download_button("⬇️ Texte brut (.txt)", data=txt_bytes, file_name=f"seo_{marque}_{reference}.txt", mime="text/plain", use_container_width=True)
                with col_dl3:
                    st.info("💡 Sélectionnez le texte ci-dessus et Ctrl+C")

                if st.session_state.get("seo_history"):
                    st.markdown("### 🗂️ Historique des tests")
                    df_hist = pd.DataFrame(st.session_state.seo_history)
                    st.dataframe(df_hist.tail(10), use_container_width=True, hide_index=True)
                    csv_bytes = BytesIO(df_hist.to_csv(index=False).encode("utf-8"))
                    st.download_button("⬇️ Exporter l'historique (CSV)", data=csv_bytes, file_name="seo_history.csv", mime="text/csv", use_container_width=True)
            else:
                st.error("❌ Erreur lors de la génération")
    
    st.divider()
    
    # Stats finales
    if st.session_state.seo_generated and st.session_state.seo_results:
        st.markdown("### 📊 Statistiques")
        
        results = st.session_state.seo_results
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Produits traités", len(results))
        
        with col2:
            total_words = sum(len(r['description'].split()) for r in results)
            st.metric("Mots générés", f"{total_words:,}")
        
        with col3:
            from_cache = sum(1 for r in results if r.get('from_cache', False))
            cache_percent = (from_cache / len(results) * 100) if results else 0
            st.metric("Cache utilisé", f"{cache_percent:.0f}%")
    
    st.divider()
    
    if st.button("🔄 Traiter un nouveau fichier", use_container_width=True):
        # Reset
        st.session_state.phase = "upload"
