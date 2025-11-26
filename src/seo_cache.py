"""
Système de cache pour descriptions SEO (SQLite)
Évite les régénérations de produits déjà traités
"""
import hashlib
from typing import Optional, Dict
import logging
from .database import DatabaseManager

logger = logging.getLogger(__name__)


class SEOCache:
    """Cache pour stocker et récupérer descriptions SEO via SQLite"""
    
    def __init__(self):
        """Initialise le cache avec la base de données"""
        self.db = DatabaseManager()
    
    def _get_product_hash(self, product_data: Dict, language: str = "fr") -> str:
        """
        Génère un hash unique pour un produit
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
        """
        product_hash = self._get_product_hash(product_data, language)
        
        rows = self.db.execute_query(
            "SELECT description, seo_title, meta_description FROM cache_seo WHERE hash = ?",
            (product_hash,)
        )
        
        if rows:
            row = rows[0]
            logger.info(f"✅ Cache HIT: {product_data.get('Référence', 'N/A')}")
            return {
                'description': row['description'],
                'seo_title': row['seo_title'],
                'meta_description': row['meta_description'],
                'reference': product_data.get('Référence', 'N/A'),
                'language': language
            }
        
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
        """
        product_hash = self._get_product_hash(product_data, language)
        reference = str(product_data.get('Référence', 'N/A'))
        
        try:
            self.db.execute_update(
                """
                INSERT INTO cache_seo 
                (hash, reference, description, seo_title, meta_description, language)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (hash) DO UPDATE SET
                reference = EXCLUDED.reference,
                description = EXCLUDED.description,
                seo_title = EXCLUDED.seo_title,
                meta_description = EXCLUDED.meta_description,
                language = EXCLUDED.language,
                created_at = CURRENT_TIMESTAMP
                """,
                (product_hash, reference, description, seo_title, meta_description, language)
            )
            logger.debug(f"💾 Cache SET: {reference}")
        except Exception as e:
            logger.error(f"❌ Erreur écriture cache: {e}")
    
    def clear(self):
        """Vide le cache"""
        try:
            self.db.execute_update("DELETE FROM cache_seo")
            logger.info("🗑️ Cache vidé")
        except Exception as e:
            logger.error(f"❌ Erreur vidage cache: {e}")
    
    def stats(self) -> Dict:
        """Retourne des statistiques sur le cache"""
        try:
            count_row = self.db.execute_query("SELECT COUNT(*) as count FROM cache_seo")[0]
            total_entries = count_row['count']
            
            # Taille approximative du fichier DB (pas juste la table, mais bon indicateur)
            db_size = self.db.db_path.stat().st_size / 1024 if self.db.db_path.exists() else 0
            
            return {
                'total_entries': total_entries,
                'cache_file': str(self.db.db_path),
                'cache_size_kb': db_size
            }
        except Exception as e:
            logger.error(f"❌ Erreur stats cache: {e}")
            return {'total_entries': 0, 'cache_size_kb': 0}
