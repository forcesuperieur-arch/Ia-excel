"""
Module de matching intelligent des colonnes Excel avec IA locale
"""
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity
from .column_normalizer import ColumnNormalizer
import logging
import time
import signal
from functools import wraps

# ✅ Utiliser le logger centralisé
from .logger_config import LoggerConfig
logger = LoggerConfig.get_logger(__name__)

def timeout_handler(timeout_seconds=300):
    """Décorateur pour ajouter un timeout à une fonction"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            max_duration = timeout_seconds
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(f"✓ {func.__name__} complété en {elapsed:.1f}s")
                LoggerConfig.log_performance(func.__name__, elapsed, success=True)
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"✗ {func.__name__} échoué après {elapsed:.1f}s: {str(e)}")
                LoggerConfig.log_performance(func.__name__, elapsed, success=False, 
                                            details={'error': str(e)})
                raise
        return wrapper
    return decorator


@st.cache_resource(show_spinner="🔄 Chargement du modèle IA (première fois uniquement)...")
def _load_sentence_transformer(model_name: str):
    """Charge le modèle SentenceTransformer avec cache Streamlit"""
    from sentence_transformers import SentenceTransformer
    import torch
    
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"🔄 Chargement du modèle IA: {model_name} sur {device}")
    
    model = SentenceTransformer(model_name, device=device)
    logger.info(f"✅ Modèle {model_name} chargé")
    return model


class ColumnMatcher:
    """Utilise une IA locale (sentence-transformers) pour matcher les colonnes"""
    
    # Modèle plus léger et rapide pour le cloud
    DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
    
    # Colonnes critiques à matcher EN PREMIER (par priorité décroissante)
    CRITICAL_COLUMNS = {
        "référence": 1,      # Priorité 1 (ESSENTIELLE)
        "designation": 2,    # Priorité 2 (très important)
        "prix": 3,           # Priorité 3
        "quantité": 4,       # Priorité 4
        "description": 2,    # Même priorité que désignation
    }
    
    def __init__(self, model_name: str = None):
        """
        Initialise le matcher avec un modèle local multilingue
        
        Args:
            model_name: Nom du modèle sentence-transformers à utiliser
        """
        model_name = model_name or self.DEFAULT_MODEL
        
        # Utiliser le cache Streamlit pour éviter de recharger le modèle
        self.model = _load_sentence_transformer(model_name)
        self.normalizer = ColumnNormalizer()
        
        # Fichier d'apprentissage pour stocker les correspondances validées
        self.learning_file = Path("learning_data.json")
        self.learned_mappings = self._load_learning_data()
    
    def _get_column_priority(self, column_name: str) -> int:
        """Retourne la priorité d'une colonne (1=très haute, 99=basse)"""
        norm = self.normalizer._normalize(column_name)
        for key, priority in self.CRITICAL_COLUMNS.items():
            if key.lower() in norm:
                return priority
        return 99  # Basse priorité par défaut
        
    def _load_learning_data(self) -> Dict:
        """Charge les données d'apprentissage depuis le fichier JSON"""
        if self.learning_file.exists():
            try:
                with open(self.learning_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"⚠️ Erreur chargement apprentissage: {e}")
                return {}
        return {}
    
    def _save_learning_data(self):
        """Sauvegarde les données d'apprentissage"""
        try:
            with open(self.learning_file, 'w', encoding='utf-8') as f:
                json.dump(self.learned_mappings, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ Apprentissage sauvegardé dans {self.learning_file}")
        except Exception as e:
            logger.error(f"✗ Erreur sauvegarde apprentissage: {e}")
    
    def learn_mapping(self, source_column: str, target_column: str, catalog_context: str = ""):
        """
        Apprend une correspondance validée par l'utilisateur
        
        Args:
            source_column: Nom de la colonne source
            target_column: Nom de la colonne cible
            catalog_context: Contexte optionnel (nom du catalogue)
        """
        key = self.normalizer._normalize(source_column)
        
        if key not in self.learned_mappings:
            self.learned_mappings[key] = []
        
        # Ajoute la correspondance
        self.learned_mappings[key].append({
            "source": source_column,
            "target": target_column,
            "context": catalog_context,
            "normalized_target": self.normalizer._normalize(target_column)
        })
        
        self._save_learning_data()
        logger.info(f"✓ Apprentissage: '{source_column}' → '{target_column}'")
    
    def _compute_similarity_batch(self, sources: List[str], targets: List[str]) -> Dict[tuple, float]:
        """Calcule la similarité entre toutes les paires source-target en batch (ULTRA-OPTIMISÉ)"""
        if not sources or not targets:
            return {}
        
        # Nettoyer et limiter la taille des textes
        max_len = 100  # Réduit à 100 pour économiser mémoire
        sources_clean = [str(s)[:max_len] for s in sources]
        targets_clean = [str(t)[:max_len] for t in targets]
        
        logger.info(f"🔄 Batch encoding: {len(sources_clean)} sources × {len(targets_clean)} cibles")
        start = time.time()
        
        try:
            # ⚠️ ULTRA-LIMITE: Streamlit Cloud ne peut pas gérer beaucoup
            # Max 10 sources par chunk pour éviter OOM
            chunk_size = min(10, max(1, len(sources_clean)))
            
            logger.info(f"  Chunking: max {chunk_size} sources par chunk (limitation mémoire stricte)")
            
            result = {}
            
            # Traiter par chunks TRÈS petits
            for chunk_idx, chunk_start in enumerate(range(0, len(sources_clean), chunk_size)):
                chunk_end = min(chunk_start + chunk_size, len(sources_clean))
                source_chunk = sources_clean[chunk_start:chunk_end]
                
                logger.info(f"  [Chunk {chunk_idx + 1}] sources {chunk_start}-{chunk_end}/{len(sources_clean)}")
                
                try:
                    # Encoder le chunk
                    all_texts = list(source_chunk) + list(targets_clean)
                    all_embeddings = self.model.encode(all_texts, show_progress_bar=False)
                    
                    source_embeddings = all_embeddings[:len(source_chunk)]
                    target_embeddings = all_embeddings[len(source_chunk):]
                    
                    # Calculer similarités pour ce chunk
                    similarities = cosine_similarity(source_embeddings, target_embeddings)
                    
                    for i, source in enumerate(source_chunk):
                        for j, target in enumerate(targets_clean):
                            # Mapper back to original names
                            orig_source = sources[chunk_start + i]
                            orig_target = targets[j]
                            result[(orig_source, orig_target)] = float(similarities[i][j])
                
                except Exception as chunk_err:
                    logger.error(f"  ✗ Chunk {chunk_idx + 1} échoué: {str(chunk_err)}")
                    # Fallback: retourner ce qu'on a
                    elapsed = time.time() - start
                    logger.error(f"✗ Batch encoding échoué après {elapsed:.1f}s et {chunk_idx} chunks")
                    return result  # Retourner les résultats partiels plutôt que crash
            
            elapsed = time.time() - start
            logger.info(f"✅ Batch encoding OK: {len(result)} paires en {elapsed:.1f}s")
            return result
            
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"✗ Batch encoding total échoué après {elapsed:.1f}s: {str(e)}", exc_info=True)
            return {}  # Retourner dict vide plutôt que crash
    
    def _compute_similarity(self, text1: str, text2: str) -> float:
        """Calcule la similarité sémantique entre deux textes"""
        # Embeddings
        emb1 = self.model.encode([text1], show_progress_bar=False)
        emb2 = self.model.encode([text2], show_progress_bar=False)
        
        # Similarité cosine
        similarity = cosine_similarity(emb1, emb2)[0][0]
        return float(similarity)
    
    def _check_learned_mapping(self, source_column: str, target_columns: List[str]) -> Optional[Tuple[str, float]]:
        """Vérifie si une correspondance a été apprise"""
        key = self.normalizer._normalize(source_column)
        
        if key in self.learned_mappings:
            for learned in self.learned_mappings[key]:
                # Cherche si la cible correspond à une des colonnes recherchées
                for target in target_columns:
                    if self.normalizer._normalize(target) == learned["normalized_target"]:
                        return (target, 1.0)  # Confiance maximale pour apprentissage
        
        return None
    
    def identify_columns(
        self, 
        column_headers: List[str],
        target_columns: List[str],
        min_confidence: float = 0.6
    ) -> Dict[str, Optional[str]]:
        """
        Identifie et mappe les colonnes du catalogue vers les colonnes cibles
        
        Args:
            column_headers: Liste des en-têtes de colonnes du catalogue fournisseur
            target_columns: Liste des colonnes cibles recherchées
            min_confidence: Score minimal de confiance
            
        Returns:
            Dict mappant chaque colonne cible vers le nom de colonne trouvé
        """
        mapping = {}
        
        # Enrichir les colonnes avec des variantes multilingues
        target_variants = self._generate_multilingual_variants(target_columns)
        
        for target in target_columns:
            best_match = None
            best_score = min_confidence
            
            # Cherche dans l'apprentissage d'abord
            for source in column_headers:
                learned = self._check_learned_mapping(source, [target])
                if learned:
                    best_match = source
                    best_score = learned[1]
                    break
            
            # Si pas trouvé dans l'apprentissage, utilise l'IA
            if not best_match:
                target_texts = target_variants.get(target, [target])
                
                for source in column_headers:
                    # Teste la similarité avec chaque variante
                    for target_text in target_texts:
                        score = self._compute_similarity(source, target_text)
                        if score > best_score:
                            best_score = score
                            best_match = source
            
            mapping[target] = best_match
        
        return mapping
    
    def _generate_multilingual_variants(self, columns: List[str]) -> Dict[str, List[str]]:
        """Génère des variantes multilingues pour les colonnes"""
        variants = {
            "référence": ["référence", "reference", "ref", "codice", "item", "codigo", "artikel", "code"],
            "désignation": ["désignation", "designation", "description", "descrizione", "descripcion", "bezeichnung", "libellé", "label", "nom", "name"],
            "prix_unitaire": ["prix unitaire", "prix", "price", "prezzo", "precio", "preis", "prix ht", "prix ttc", "prix achat"],
            "quantité": ["quantité", "quantity", "qty", "qté", "quantita", "cantidad", "menge"],
            "unité": ["unité", "unit", "unita", "unidad", "einheit", "u"],
            "famille": ["famille", "family", "categoria", "category", "categorie", "kategorie"],
            "fournisseur": ["fournisseur", "supplier", "marca", "marque", "brand", "hersteller"]
        }
        
        result = {}
        for col in columns:
            normalized = self.normalizer._normalize(col)
            # Cherche dans les variantes
            for key, vals in variants.items():
                if normalized in [self.normalizer._normalize(v) for v in vals]:
                    result[col] = vals
                    break
            
            if col not in result:
                result[col] = [col]
        
        return result

    def get_column_mapping_with_confidence(
        self,
        column_headers: List[str],
        target_columns: List[str],
        min_confidence: float = 0.6
    ) -> Dict[str, Dict[str, any]]:
        """
        Stratégie PRIORITAIRE pour Cloud Run:
        1. Apprentissage
        2. Normalisation
        3. IA seulement pour les colonnes critiques manquantes
        
        Les colonnes critiques (ref, desc, prix) sont traitées EN PREMIER.
        
        Args:
            column_headers: En-têtes du catalogue
            target_columns: Colonnes cibles
            min_confidence: Confiance minimale
            
        Returns:
            Dict avec 'column' et 'confidence' pour chaque cible
        """
        result = {}
        learned_targets = set()
        total_start = time.time()
        
        logger.info(f"🎯 Démarrage matching PRIORITAIRE: {len(column_headers)} sources, {len(target_columns)} cibles")
        
        # ========== ÉTAPE 1: Apprentissage (très rapide) ==========
        learn_start = time.time()
        for target in target_columns:
            for source in column_headers:
                learned = self._check_learned_mapping(source, [target])
                if learned:
                    result[target] = {
                        'column': source,
                        'confidence': 1.0,
                        'method': 'learned'
                    }
                    learned_targets.add(target)
                    break
        learn_elapsed = time.time() - learn_start
        logger.info(f"✓ Étape 1 (apprentissage): {len(learned_targets)}/{len(target_columns)} matchés en {learn_elapsed:.1f}s")
        
        # ========== ÉTAPE 2: Normalisation (rapide, zero mémoire) ==========
        remaining_targets = [t for t in target_columns if t not in learned_targets]
        norm_start = time.time()
        
        unmatched_targets = []
        for target in remaining_targets:
            best_match = None
            best_score = 0.5  # Seuil pour normalisation (bas exprès)
            
            for source in column_headers:
                score = self.normalizer.similarity_score(source, target)
                if score > best_score:
                    best_score = score
                    best_match = source
            
            if best_match:
                result[target] = {
                    'column': best_match,
                    'confidence': best_score,
                    'method': 'normalizer'
                }
            else:
                unmatched_targets.append(target)
        
        norm_elapsed = time.time() - norm_start
        logger.info(f"✓ Étape 2 (normalisation): {len(remaining_targets) - len(unmatched_targets)}/{len(remaining_targets)} matchés en {norm_elapsed:.1f}s")
        
        # ========== ÉTAPE 3: IA seulement pour colonnes CRITIQUES manquantes ==========
        if unmatched_targets and column_headers:
            # Trier par priorité: d'abord les critiques
            critical_unmatched = []
            optional_unmatched = []
            
            for target in unmatched_targets:
                priority = self._get_column_priority(target)
                if priority <= 10:  # Colonnes critiques
                    critical_unmatched.append((target, priority))
                else:
                    optional_unmatched.append((target, priority))
            
            # Trier par priorité
            critical_unmatched.sort(key=lambda x: x[1])
            optional_unmatched.sort(key=lambda x: x[1])
            
            # Traiter critiques EN PREMIER
            to_process_ai = [t for t, _ in critical_unmatched]
            
            # Limiter drastiquement: max 5-10 colonnes en IA pour Cloud Run
            if len(to_process_ai) > 10:
                logger.warning(f"⚠️ Limitation: {len(to_process_ai)} → 10 colonnes critiques (IA)")
                to_process_ai = to_process_ai[:10]
            
            if to_process_ai:
                try:
                    logger.info(f"🔄 Étape 3 (IA critiques): {len(column_headers)} × {len(to_process_ai)} colonnes")
                    batch_start = time.time()
                    
                    similarities = self._compute_similarity_batch(column_headers, to_process_ai)
                    batch_elapsed = time.time() - batch_start
                    logger.info(f"✓ Batch critique computed: {len(similarities)} paires en {batch_elapsed:.1f}s")
                    
                    for target in to_process_ai:
                        best_match = None
                        best_score = min_confidence
                        
                        for source in column_headers:
                            score = similarities.get((source, target), 0)
                            if score > best_score:
                                best_score = score
                                best_match = source
                        
                        result[target] = {
                            'column': best_match,
                            'confidence': best_score,
                            'method': 'ai' if best_match else 'none'
                        }
                        
                except Exception as e:
                    elapsed = time.time() - batch_start
                    logger.error(f"✗ Erreur IA critiques après {elapsed:.1f}s: {str(e)}", exc_info=True)
            
            # Les colonnes optionnelles non matchées: fallback normalisation complète ou None
            for target, _ in optional_unmatched:
                if target not in result:
                    result[target] = {
                        'column': None,
                        'confidence': 0.0,
                        'method': 'skipped_optional'  # Non critiques, on saute
                    }
        
        # Remplir les colonnes non matchées
        for target in target_columns:
            if target not in result:
                result[target] = {
                    'column': None,
                    'confidence': 0.0,
                    'method': 'none'
                }
        
        total_elapsed = time.time() - total_start
        matched_count = sum(1 for v in result.values() if v['column'] is not None)
        logger.info(f"✅ Matching complet: {matched_count}/{len(target_columns)} en {total_elapsed:.1f}s")
        return result
    
    def match_with_fallback(
        self,
        column_headers: List[str],
        target_columns: List[str],
        use_ai: bool = True,
        learning_system = None
    ) -> Dict[str, Dict[str, any]]:
        """
        Matching hybride: apprentissage, IA, puis normalisation
        
        Args:
            column_headers: Colonnes du catalogue
            target_columns: Colonnes du template
            use_ai: Utiliser l'IA (False = normalisation uniquement)
            learning_system: Système d'apprentissage optionnel
            
        Returns:
            Mapping avec confiance et méthode utilisée
        """
        # Étape 1: Utiliser l'historique d'apprentissage en premier
        result = {}
        matched_sources = set()
        matched_targets = set()
        
        if learning_system:
            for target_col in target_columns:
                # Chercher dans l'historique si une colonne source correspond à cette cible
                for source_col in column_headers:
                    suggestion = learning_system.get_suggestion(source_col)
                    if suggestion:
                        normalized_suggestion = self._normalize(suggestion)
                        normalized_target = self._normalize(target_col)
                        if normalized_suggestion == normalized_target:
                            result[target_col] = {
                                'column': source_col,
                                'confidence': 1.0,
                                'method': 'learning'
                            }
                            matched_sources.add(source_col)
                            matched_targets.add(target_col)
                            break
        
        # Étape 2: IA + Normalisation pour les colonnes non matchées
        remaining_headers = [h for h in column_headers if h not in matched_sources]
        remaining_targets = [t for t in target_columns if t not in matched_targets]
        
        if remaining_targets:
            ai_mapping = self.get_column_mapping_with_confidence(
                remaining_headers,
                remaining_targets,
                min_confidence=0.5 if use_ai else 0.55
            )
            result.update(ai_mapping)
        
        # Compléter avec les colonnes non matchées
        for target_col in target_columns:
            if target_col not in result:
                result[target_col] = {
                    'column': None,
                    'confidence': 0.0,
                    'method': 'none'
                }
        
        return result
    
    def _normalize(self, text: str) -> str:
        """Normalise un texte pour la comparaison"""
        return text.lower().strip().replace('_', ' ').replace('-', ' ')
    
    def get_suggestions(
        self,
        source_column: str,
        target_columns: List[str],
        top_n: int = 3
    ) -> List[Tuple[str, float]]:
        """
        Obtient les N meilleures suggestions pour une colonne
        
        Args:
            source_column: Colonne source
            target_columns: Liste des colonnes cibles
            top_n: Nombre de suggestions
            
        Returns:
            Liste de tuples (colonne, score) triée par score
        """
        scores = []
        
        # Combine les scores IA et normalisation
        for target in target_columns:
            # Score IA sémantique
            ai_score = self._compute_similarity(source_column, target)
            
            # Score normalisation
            norm_score = self.normalizer.similarity_score(source_column, target)
            
            # Score combiné (moyenne pondérée)
            combined_score = (ai_score * 0.7) + (norm_score * 0.3)
            
            scores.append((target, combined_score))
        
        # Trier par score décroissant
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:top_n]
    
    def batch_learn_from_mapping(self, mapping: Dict[str, str], catalog_context: str = ""):
        """
        Apprend plusieurs correspondances en batch
        
        Args:
            mapping: Dict {source_column: target_column}
            catalog_context: Contexte du catalogue
        """
        for source, target in mapping.items():
            if target:  # Ignore les mappings None
                self.learn_mapping(source, target, catalog_context)
        
        print(f"✓ {len([v for v in mapping.values() if v])} correspondances apprises")
