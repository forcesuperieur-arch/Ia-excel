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

import streamlit as st
import pandas as pd
import time
import os
from io import BytesIO
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
    ProductDescriptionGenerator,
    format_description_for_word
)

# Page Catalogue
init_session_state()
render_header()

config = sidebar_config(disable_nav=True)

render_stepper()

# Redéfinition locale de phase_seo pour inclure la barre de progression et le bouton stop
def phase_seo_enhanced(config):
    """Phase 3: Génération SEO (Améliorée)"""
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
                st.markdown(f"""
                <div class="seo-stat">
                    <div class="seo-stat-value">{len(results)}</div>
                    <div class="seo-stat-label">Produits</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                avg_words = sum(len(r['description'].split()) for r in results) / len(results) if results else 0
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
                    use_web_search=True
                )
                
                if not generator.is_available():
                    st.error("❌ OpenRouter/OpenAI non disponible. Vérifiez votre clé API.")
                    return
                
                # UI de progression
                progress_bar = st.progress(0)
                status = st.empty()
                stop_container = st.empty()
                stop_button = stop_container.button("🛑 Arrêter la génération", type="secondary")
                
                total = len(df)
                status.text(f"🤖 Génération en cours... (0/{total})")
                
                results = []
                
                # Boucle séquentielle pour permettre l'arrêt et la mise à jour UI
                for i, row in df.iterrows():
                    # Vérifier arrêt (nécessite un rerun pour lire le bouton, mais ici on vérifie juste l'état)
                    # Note: st.button ne garde pas l'état dans une boucle longue sans callback.
                    # On utilise une astuce simple ici ou on accepte que le stop soit "au prochain tour"
                    
                    product = row.to_dict()
                    
                    # Génération
                    result = generator.generate_full_seo(product, language='fr')
                    results.append(result)
                    
                    # Mise à jour UI
                    progress = (i + 1) / total
                    progress_bar.progress(progress)
                    status.text(f"🤖 Génération... ({i + 1}/{total}) - {product.get('Référence', '')}")
                
                stop_container.empty() # Cacher le bouton stop
                
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

# Redéfinition locale de phase_complete pour inclure l'export ZIP
def phase_complete_enhanced():
    """Phase 4: Téléchargement (Améliorée)"""
    st.markdown("## 🎉 Traitement terminé !")
    
    st.success("✅ Votre fichier est prêt au téléchargement")
    
    output_path = st.session_state.output_path
    
    if os.path.exists(output_path):
        # Vue catalogue avant téléchargement
        with st.expander("📊 Aperçu & Filtres du catalogue généré", expanded=False):
            try:
                df = pd.read_excel(output_path)
                st.dataframe(df.head(50), use_container_width=True)
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
        phase_seo_enhanced(config)
    elif phase == "complete":
        phase_complete_enhanced()

render_footer()
