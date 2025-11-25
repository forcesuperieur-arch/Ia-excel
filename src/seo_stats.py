"""
Système de statistiques pour les générations SEO
Tracking des performances, qualité, et temps de génération
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class SEOStats:
    """Collecte et analyse des statistiques de génération SEO"""
    
    def __init__(self, stats_file: str = "templates/seo_stats.json"):
        """
        Initialise le système de stats
        
        Args:
            stats_file: Fichier de sauvegarde des statistiques
        """
        self.stats_file = Path(stats_file)
        self.stats_file.parent.mkdir(exist_ok=True)
        self.stats = self._load_stats()
    
    def _load_stats(self) -> Dict:
        """Charge les statistiques depuis le fichier"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                    logger.info(f"📊 Stats chargées: {len(stats.get('generations', []))} générations")
                    return stats
            except Exception as e:
                logger.warning(f"⚠️ Erreur lecture stats: {e}")
                return self._init_stats()
        return self._init_stats()
    
    def _init_stats(self) -> Dict:
        """Initialise la structure des stats"""
        return {
            'generations': [],
            'summary': {
                'total_generated': 0,
                'total_time': 0,
                'avg_time': 0,
                'by_category': {},
                'by_language': {},
                'cache_hits': 0,
                'cache_misses': 0
            },
            'quality': {
                'avg_word_count': 0,
                'avg_char_count': 0,
                'within_target': 0,
                'too_short': 0,
                'too_long': 0
            }
        }
    
    def _save_stats(self):
        """Sauvegarde les statistiques"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
            logger.debug(f"💾 Stats sauvegardées")
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde stats: {e}")
    
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
        
        Args:
            category: Catégorie du produit
            language: Langue de génération
            time_seconds: Temps de génération
            word_count: Nombre de mots
            char_count: Nombre de caractères
            from_cache: Si depuis le cache
        """
        # Ajouter l'entrée
        self.stats['generations'].append({
            'timestamp': datetime.now().isoformat(),
            'category': category,
            'language': language,
            'time': time_seconds,
            'word_count': word_count,
            'char_count': char_count,
            'from_cache': from_cache
        })
        
        # Mettre à jour le résumé
        summary = self.stats['summary']
        summary['total_generated'] += 1
        summary['total_time'] += time_seconds
        summary['avg_time'] = summary['total_time'] / summary['total_generated']
        
        # Par catégorie
        if category not in summary['by_category']:
            summary['by_category'][category] = {'count': 0, 'total_time': 0}
        summary['by_category'][category]['count'] += 1
        summary['by_category'][category]['total_time'] += time_seconds
        summary['by_category'][category]['avg_time'] = (
            summary['by_category'][category]['total_time'] / 
            summary['by_category'][category]['count']
        )
        
        # Par langue
        if language not in summary['by_language']:
            summary['by_language'][language] = {'count': 0}
        summary['by_language'][language]['count'] += 1
        
        # Cache
        if from_cache:
            summary['cache_hits'] += 1
        else:
            summary['cache_misses'] += 1
        
        # Qualité
        quality = self.stats['quality']
        total = summary['total_generated']
        
        # Recalculer moyennes
        quality['avg_word_count'] = (
            (quality['avg_word_count'] * (total - 1) + word_count) / total
        )
        quality['avg_char_count'] = (
            (quality['avg_char_count'] * (total - 1) + char_count) / total
        )
        
        # Classification longueur
        if 150 <= word_count <= 200:
            quality['within_target'] += 1
        elif word_count < 150:
            quality['too_short'] += 1
        else:
            quality['too_long'] += 1
        
        self._save_stats()
    
    def get_summary(self) -> Dict:
        """Retourne un résumé des statistiques"""
        return {
            'total_generated': self.stats['summary']['total_generated'],
            'avg_time': round(self.stats['summary']['avg_time'], 2),
            'cache_hit_rate': (
                self.stats['summary']['cache_hits'] / 
                max(1, self.stats['summary']['total_generated'])
            ) * 100,
            'avg_word_count': round(self.stats['quality']['avg_word_count'], 1),
            'quality_rate': (
                self.stats['quality']['within_target'] / 
                max(1, self.stats['summary']['total_generated'])
            ) * 100,
            'by_category': self.stats['summary']['by_category'],
            'by_language': self.stats['summary']['by_language']
        }
    
    def get_recent(self, limit: int = 10) -> List[Dict]:
        """
        Retourne les N dernières générations
        
        Args:
            limit: Nombre de résultats
            
        Returns:
            Liste des dernières générations
        """
        return self.stats['generations'][-limit:]
    
    def reset(self):
        """Réinitialise les statistiques"""
        self.stats = self._init_stats()
        self._save_stats()
        logger.info("🗑️ Statistiques réinitialisées")
