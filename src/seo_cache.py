"""
Système de cache pour descriptions SEO
Évite les régénérations de produits déjà traités
"""
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class SEOCache:
    """Cache pour stocker et récupérer descriptions SEO"""
    
    def __init__(self, cache_file: str = "templates/cache_seo.json", max_entries: int = 1000):
        """
        Initialise le cache
        
        Args:
            cache_file: Chemin du fichier cache
            max_entries: Nombre maximum d'entrées (LRU si dépassé)
        """
        self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(exist_ok=True)
        self.max_entries = max_entries
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Charge le cache depuis le fichier"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    logger.info(f"💾 Cache chargé: {len(cache)} entrées")
                    return cache
            except Exception as e:
                logger.warning(f"⚠️ Erreur lecture cache: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Sauvegarde le cache dans le fichier"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            logger.debug(f"💾 Cache sauvegardé: {len(self.cache)} entrées")
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde cache: {e}")
    
    def _get_product_hash(self, product_data: Dict, language: str = "fr") -> str:
        """
        Génère un hash unique pour un produit
        
        Args:
            product_data: Données produit
            language: Langue de génération
            
        Returns:
            Hash MD5 du produit
        """
        # Utilise référence + libellé + marque + langue
        key_fields = [
            str(product_data.get('Référence', '')),
            str(product_data.get('Libellé', '')),
            str(product_data.get('Marque', '')),
            language
        ]
        
        key_string = '|'.join(key_fields).lower()
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, product_data: Dict, language: str = "fr") -> Optional[Dict]:
        """
        Récupère une description depuis le cache
        
        Args:
            product_data: Données produit
            language: Langue
            
        Returns:
            Dict avec description, title, meta ou None si pas en cache
        """
        product_hash = self._get_product_hash(product_data, language)
        
        if product_hash in self.cache:
            logger.info(f"✅ Cache HIT: {product_data.get('Référence', 'N/A')}")
            return self.cache[product_hash]
        
        logger.debug(f"❌ Cache MISS: {product_data.get('Référence', 'N/A')}")
        return None
    
    def set(
        self,
        product_data: Dict,
        description: str,
        seo_title: str,
        meta_description: str,
        language: str = "fr"
    ):
        """
        Stocke une description dans le cache
        
        Args:
            product_data: Données produit
            description: Description générée
            seo_title: Titre SEO
            meta_description: Meta description
            language: Langue
        """
        product_hash = self._get_product_hash(product_data, language)
        
        # Limiter la taille du cache (LRU simple)
        if len(self.cache) >= self.max_entries:
            # Supprimer la première entrée (la plus ancienne)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            logger.warning(f"⚠️ Cache plein, suppression de l'entrée la plus ancienne")
        
        self.cache[product_hash] = {
            'description': description,
            'seo_title': seo_title,
            'meta_description': meta_description,
            'reference': product_data.get('Référence', 'N/A'),
            'language': language
        }
        
        # Sauvegarder toutes les 10 entrées au lieu de chaque fois
        if len(self.cache) % 10 == 0:
            self._save_cache()
        
        logger.debug(f"💾 Cache SET: {product_data.get('Référence', 'N/A')}")
    
    def clear(self):
        """Vide le cache"""
        self.cache = {}
        self._save_cache()
        logger.info("🗑️ Cache vidé")
    
    def stats(self) -> Dict:
        """Retourne des statistiques sur le cache"""
        return {
            'total_entries': len(self.cache),
            'languages': list(set(entry.get('language', 'fr') for entry in self.cache.values())),
            'cache_file': str(self.cache_file),
            'cache_size_kb': self.cache_file.stat().st_size / 1024 if self.cache_file.exists() else 0
        }
