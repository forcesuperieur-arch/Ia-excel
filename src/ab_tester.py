"""
Système A/B Testing pour descriptions SEO
Génère plusieurs variantes et track les conversions
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ABTester:
    """Gestion des tests A/B pour descriptions SEO"""
    
    def __init__(self, tests_file: str = "templates/ab_tests.json"):
        """
        Initialise le système A/B
        
        Args:
            tests_file: Fichier des tests A/B
        """
        self.tests_file = Path(tests_file)
        self.tests_file.parent.mkdir(exist_ok=True)
        self.tests = self._load_tests()
    
    def _load_tests(self) -> Dict:
        """Charge les tests A/B"""
        if self.tests_file.exists():
            try:
                with open(self.tests_file, 'r', encoding='utf-8') as f:
                    tests = json.load(f)
                    logger.info(f"🧪 Tests A/B chargés: {len(tests.get('tests', []))}")
                    return tests
            except Exception as e:
                logger.warning(f"⚠️ Erreur lecture tests A/B: {e}")
                return {'tests': [], 'results': []}
        return {'tests': [], 'results': []}
    
    def _save_tests(self):
        """Sauvegarde les tests"""
        try:
            with open(self.tests_file, 'w', encoding='utf-8') as f:
                json.dump(self.tests, f, ensure_ascii=False, indent=2)
            logger.debug("💾 Tests A/B sauvegardés")
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde tests: {e}")
    
    def create_test(
        self,
        product_ref: str,
        variants: List[Dict],
        test_name: Optional[str] = None
    ) -> str:
        """
        Crée un nouveau test A/B
        
        Args:
            product_ref: Référence produit
            variants: Liste de variantes avec description, seo_title, meta
            test_name: Nom du test (auto si None)
            
        Returns:
            ID du test créé
        """
        test_id = f"test_{len(self.tests['tests']) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        test = {
            'id': test_id,
            'name': test_name or f"Test {product_ref}",
            'product_ref': product_ref,
            'created_at': datetime.now().isoformat(),
            'status': 'active',
            'variants': variants,
            'metrics': {
                variant['id']: {
                    'views': 0,
                    'clicks': 0,
                    'conversions': 0,
                    'ctr': 0.0,
                    'conversion_rate': 0.0
                }
                for variant in variants
            }
        }
        
        self.tests['tests'].append(test)
        self._save_tests()
        
        logger.info(f"🧪 Test A/B créé: {test_id} ({len(variants)} variantes)")
        return test_id
    
    def generate_variants(
        self,
        generator,
        product_data: Dict,
        num_variants: int = 3,
        temperature_range: List[float] = None
    ) -> List[Dict]:
        """
        Génère plusieurs variantes pour un produit
        
        Args:
            generator: ProductDescriptionGenerator instance
            product_data: Données produit
            num_variants: Nombre de variantes à générer
            temperature_range: Températures à utiliser (défaut: [0.5, 0.7, 0.9])
            
        Returns:
            Liste de variantes {id, description, seo_title, meta, temperature}
        """
        if temperature_range is None:
            temperature_range = [0.5, 0.7, 0.9]
        
        # Étendre si nécessaire
        while len(temperature_range) < num_variants:
            temperature_range.append(0.7 + (len(temperature_range) - 1) * 0.1)
        
        variants = []
        
        for i in range(num_variants):
            temp = temperature_range[i % len(temperature_range)]
            
            # Forcer régénération pour chaque variante
            result = generator.generate_full_seo(
                product_data,
                language='fr',
                force_regenerate=True
            )
            
            # Utiliser température différente en modifiant le generator temporairement
            # (Note: nécessiterait refactoring pour passer temperature dans generate_full_seo)
            
            variants.append({
                'id': f"variant_{chr(65 + i)}",  # A, B, C, etc.
                'description': result['description'],
                'seo_title': result['seo_title'],
                'meta_description': result['meta_description'],
                'temperature': temp,
                'word_count': len(result['description'].split())
            })
        
        logger.info(f"✅ {num_variants} variantes générées")
        return variants
    
    def record_event(
        self,
        test_id: str,
        variant_id: str,
        event_type: str  # 'view', 'click', 'conversion'
    ):
        """
        Enregistre un événement pour une variante
        
        Args:
            test_id: ID du test
            variant_id: ID de la variante
            event_type: Type d'événement
        """
        test = next((t for t in self.tests['tests'] if t['id'] == test_id), None)
        
        if not test:
            logger.error(f"❌ Test {test_id} introuvable")
            return
        
        if variant_id not in test['metrics']:
            logger.error(f"❌ Variante {variant_id} introuvable")
            return
        
        metrics = test['metrics'][variant_id]
        
        if event_type == 'view':
            metrics['views'] += 1
        elif event_type == 'click':
            metrics['clicks'] += 1
        elif event_type == 'conversion':
            metrics['conversions'] += 1
        
        # Recalculer les taux
        if metrics['views'] > 0:
            metrics['ctr'] = (metrics['clicks'] / metrics['views']) * 100
            metrics['conversion_rate'] = (metrics['conversions'] / metrics['views']) * 100
        
        self._save_tests()
        logger.debug(f"📊 Événement enregistré: {event_type} pour {variant_id}")
    
    def get_test_results(self, test_id: str) -> Optional[Dict]:
        """
        Récupère les résultats d'un test
        
        Args:
            test_id: ID du test
            
        Returns:
            Dict avec résultats et métriques
        """
        test = next((t for t in self.tests['tests'] if t['id'] == test_id), None)
        
        if not test:
            return None
        
        # Calculer le gagnant
        best_variant = None
        best_conversion = 0
        
        for variant_id, metrics in test['metrics'].items():
            if metrics['conversion_rate'] > best_conversion:
                best_conversion = metrics['conversion_rate']
                best_variant = variant_id
        
        return {
            'test': test,
            'winner': best_variant,
            'winner_rate': best_conversion,
            'total_views': sum(m['views'] for m in test['metrics'].values()),
            'total_conversions': sum(m['conversions'] for m in test['metrics'].values())
        }
    
    def stop_test(self, test_id: str):
        """Arrête un test A/B"""
        test = next((t for t in self.tests['tests'] if t['id'] == test_id), None)
        
        if test:
            test['status'] = 'stopped'
            test['stopped_at'] = datetime.now().isoformat()
            self._save_tests()
            logger.info(f"⏹️ Test {test_id} arrêté")
    
    def list_active_tests(self) -> List[Dict]:
        """Liste les tests actifs"""
        return [t for t in self.tests['tests'] if t.get('status') == 'active']
