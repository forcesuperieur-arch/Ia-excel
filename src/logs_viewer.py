"""
Interface Streamlit pour visualiser et gérer les logs
Accessible via la page Paramètres
"""
import streamlit as st
from pathlib import Path
from datetime import datetime, timedelta
import json
import re

from src.logger_config import LoggerConfig


def render_logs_viewer():
    """Affiche le viewer de logs dans l'UI"""
    st.markdown("### 📊 Viewer de Logs")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        log_level = st.selectbox(
            "🔍 Niveau de log",
            ["TOUS", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            key="log_level_filter"
        )
    
    with col2:
        log_type = st.selectbox(
            "📝 Type de log",
            ["TOUS", "USER_ACTIONS", "PERFORMANCE", "CACHE", "DATABASE", "API_CALLS", "ERRORS"],
            key="log_type_filter"
        )
    
    with col3:
        lines_limit = st.slider(
            "📏 Dernières lignes",
            min_value=10,
            max_value=500,
            value=100,
            step=10,
            key="log_lines_limit"
        )
    
    st.divider()
    
    # Récupérer et filtrer les logs
    logs = _get_filtered_logs(
        limit=lines_limit,
        level=log_level,
        log_type=log_type
    )
    
    if logs:
        # Affichage avec couleurs selon le niveau
        log_container = st.container()
        with log_container:
            for log_line in logs:
                _render_log_line(log_line)
    else:
        st.info("ℹ️ Aucun log correspondant aux filtres")
    
    st.divider()
    
    # Actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Rafraîchir", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("💾 Télécharger les logs", use_container_width=True):
            _download_logs(logs)
    
    with col3:
        if st.button("🗑️ Vider les logs", use_container_width=True):
            _clear_logs()
            st.success("✅ Logs vidés")
            st.rerun()


def _get_filtered_logs(limit: int = 100, level: str = "TOUS", log_type: str = "TOUS") -> list:
    """Récupère et filtre les logs"""
    try:
        log_file = LoggerConfig.LOG_FILE
        if not log_file.exists():
            return []
        
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Filtrer par niveau et type
        filtered = []
        for line in lines[-limit*10:]:  # Lire plus pour compenser les filtres
            # Filtrer par niveau
            if level != "TOUS" and level not in line:
                continue
            
            # Filtrer par type
            if log_type != "TOUS" and log_type not in line:
                continue
            
            filtered.append(line.rstrip())
        
        return filtered[-limit:]  # Retourner les N dernières
    
    except Exception as e:
        st.error(f"❌ Erreur lecture logs: {e}")
        return []


def _render_log_line(log_line: str):
    """Affiche une ligne de log avec couleur selon le niveau"""
    if "ERROR" in log_line or "❌" in log_line:
        st.markdown(f"<span style='color: #ff4444'>{log_line}</span>", unsafe_allow_html=True)
    elif "WARNING" in log_line or "⚠️" in log_line:
        st.markdown(f"<span style='color: #ffaa00'>{log_line}</span>", unsafe_allow_html=True)
    elif "DEBUG" in log_line:
        st.markdown(f"<span style='color: #888888'>{log_line}</span>", unsafe_allow_html=True)
    else:
        st.markdown(f"<code>{log_line}</code>")


def _download_logs(logs: list):
    """Prépare le téléchargement des logs"""
    if not logs:
        st.warning("⚠️ Aucun log à télécharger")
        return
    
    content = "\n".join(logs)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logs_{timestamp}.txt"
    
    st.download_button(
        label="📥 Télécharger",
        data=content,
        file_name=filename,
        mime="text/plain",
        key="download_logs_btn"
    )


def _clear_logs():
    """Vide le fichier de logs"""
    try:
        log_file = LoggerConfig.LOG_FILE
        if log_file.exists():
            log_file.unlink()
    except Exception as e:
        st.error(f"❌ Erreur suppression logs: {e}")


def render_logs_statistics():
    """Affiche des statistiques sur les logs"""
    st.markdown("### 📈 Statistiques des Logs")
    
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        log_file = LoggerConfig.LOG_FILE
        if not log_file.exists():
            st.info("ℹ️ Aucun log disponible")
            return
        
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Compter les niveaux
        errors = content.count("ERROR")
        warnings = content.count("WARNING")
        infos = content.count("INFO")
        debugs = content.count("DEBUG")
        
        with col1:
            st.metric("🔴 Erreurs", errors)
        with col2:
            st.metric("🟠 Warnings", warnings)
        with col3:
            st.metric("🟢 Infos", infos)
        with col4:
            st.metric("🔵 Debug", debugs)
        
        # Taille du fichier
        file_size_mb = log_file.stat().st_size / (1024 * 1024)
        st.caption(f"📦 Fichier: {log_file.name} ({file_size_mb:.2f} MB)")
    
    except Exception as e:
        st.error(f"❌ Erreur statistiques: {e}")
