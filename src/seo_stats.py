"""
Système de statistiques pour les générations SEO (SQLite)
Tracking des performances, qualité, et temps de génération
"""
from datetime import datetime
from typing import Dict, List
import logging
from .database import DatabaseManager

logger = logging.getLogger(__name__)


class SEOStats:
    """Collecte et analyse des statistiques de génération SEO via SQLite"""
    
    def __init__(self):
        """Initialise le système de stats avec la base de données"""
        self.db = DatabaseManager()
    
    def record_generation(
        self,
        category: str,
        language: str,
        time_seconds: float,
        word_count: int,
        char_count: int,
        from_cache: bool = False
    ):
        """
        Enregistre une génération
        """
        try:
            self.db.execute_update(
                """
                INSERT INTO seo_stats 
                (timestamp, category, language, time_seconds, word_count, char_count, from_cache)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(),
                    category,
                    language,
                    time_seconds,
                    word_count,
                    char_count,
                    from_cache
                )
            )
        except Exception as e:
            logger.error(f"❌ Erreur enregistrement stats: {e}")
    
    def get_summary(self) -> Dict:
        """Retourne un résumé des statistiques calculé depuis la DB"""
        try:
            # Total generated
            total = self.db.execute_query("SELECT COUNT(*) as c FROM seo_stats")[0]['c']
            
            if total == 0:
                return {
                    'total_generated': 0,
                    'avg_time': 0,
                    'cache_hit_rate': 0,
                    'avg_word_count': 0,
                    'quality_rate': 0,
                    'by_category': {},
                    'by_language': {}
                }

            # Avg time
            avg_time = self.db.execute_query("SELECT AVG(time_seconds) as a FROM seo_stats")[0]['a'] or 0
            
            # Cache hits
            hits = self.db.execute_query("SELECT COUNT(*) as c FROM seo_stats WHERE from_cache = TRUE")[0]['c']
            
            # Avg word count
            avg_words = self.db.execute_query("SELECT AVG(word_count) as a FROM seo_stats")[0]['a'] or 0
            
            # Quality (150-200 words)
            quality_count = self.db.execute_query("SELECT COUNT(*) as c FROM seo_stats WHERE word_count BETWEEN 150 AND 200")[0]['c']
            
            # Group by category
            cats = self.db.execute_query("SELECT category, COUNT(*) as c, AVG(time_seconds) as t FROM seo_stats GROUP BY category")
            by_category = {r['category']: {'count': r['c'], 'avg_time': r['t']} for r in cats}
            
            # Group by language
            langs = self.db.execute_query("SELECT language, COUNT(*) as c FROM seo_stats GROUP BY language")
            by_language = {r['language']: {'count': r['c']} for r in langs}
            
            return {
                'total_generated': total,
                'avg_time': round(avg_time, 2),
                'cache_hit_rate': (hits / total) * 100,
                'avg_word_count': round(avg_words, 1),
                'quality_rate': (quality_count / total) * 100,
                'by_category': by_category,
                'by_language': by_language
            }
        except Exception as e:
            logger.error(f"❌ Erreur lecture stats: {e}")
            return {}
    
    def get_recent(self, limit: int = 10) -> List[Dict]:
        """
        Retourne les N dernières générations
        """
        try:
            rows = self.db.execute_query(
                "SELECT * FROM seo_stats ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"❌ Erreur lecture historique stats: {e}")
            return []
    
    def reset(self):
        """Réinitialise les statistiques"""
        try:
            self.db.execute_update("DELETE FROM seo_stats")
            logger.info("🗑️ Statistiques réinitialisées")
        except Exception as e:
            logger.error(f"❌ Erreur reset stats: {e}")
