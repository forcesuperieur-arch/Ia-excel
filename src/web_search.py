"""
Module de recherche web pour enrichir les descriptions produits via Serper.dev API
"""
import logging
import requests
import os
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


def _get_secret(key: str, default: str = "") -> str:
    """Récupère un secret depuis st.secrets ou os.environ"""
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except:
        pass
    return os.getenv(key, default)


class WebSearchEnricher:
    """Enrichit les données produit avec des infos trouvées sur Google via Serper.dev API"""
    
    def __init__(self, serper_api_key: Optional[str] = None, timeout: int = 10):
        self.timeout = timeout
        self.serper_api_key = serper_api_key or _get_secret('SERPER_API_KEY')
        
        if not self.serper_api_key:
            logger.warning("⚠️ SERPER_API_KEY non définie. Recherche web désactivée.")
            logger.warning("💡 Obtenez une clé gratuite sur https://serper.dev (2500 recherches/mois)")
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_product_info(self, product_data: Dict) -> Dict:
        """
        Recherche des infos sur le produit via Serper.dev (Google Search API)
        Format: MARQUE (du catalogue) + RÉFÉRENCE (fournisseur)
        Exemple: ARROW 11005MI
        
        Args:
            product_data: Dict avec Référence (fournisseur), Marque (catalogue), Libellé, etc.
            
        Returns:
            Dict avec infos enrichies trouvées
        """
        enriched_info = {
            'found': False,
            'search_results': [],
            'context': ''
        }
        
        if not self.serper_api_key:
            logger.warning("Recherche web désactivée (pas de clé API)")
            return enriched_info
        
        # Extraire les infos clés
        ref_fournisseur = product_data.get('Référence', '').strip()
        marque_catalogue = product_data.get('Marque', '').strip()
        libelle = product_data.get('Libellé', '').strip()
        categorie = product_data.get('Catégorie', '').strip()
        
        if not marque_catalogue or not ref_fournisseur:
            logger.warning("Marque ou référence fournisseur manquante")
            return enriched_info
        
        # Stratégie de recherche progressive
        search_queries = []
        
        # 1. Recherche précise: MARQUE RÉFÉRENCE
        search_queries.append(f"{marque_catalogue} {ref_fournisseur} motorcycle")
        
        # 2. Avec libellé si disponible
        if libelle:
            search_queries.append(f"{marque_catalogue} {libelle} {ref_fournisseur}")
        
        # 3. Recherche générique si pas de résultats
        if categorie:
            search_queries.append(f"{marque_catalogue} {categorie} motorcycle parts")
        
        # Essayer chaque requête jusqu'à trouver des résultats
        all_results = []
        for query in search_queries:
            logger.info(f"🔍 Recherche Serper: {query}")
            results = self._serper_search(query)
            
            if results:
                all_results.extend(results)
                break  # On a trouvé des résultats, stop
        
        if all_results:
            enriched_info['found'] = True
            enriched_info['search_results'] = all_results
            enriched_info['context'] = self._format_context(all_results)
            logger.info(f"✅ {len(all_results)} résultats trouvés")
        else:
            logger.info("❌ Aucun résultat trouvé")
        
        return enriched_info
    
    def _serper_search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Recherche via Serper.dev API (Google Search)"""
        try:
            url = "https://google.serper.dev/search"
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            payload = {
                'q': query,
                'num': max_results,
                'gl': 'fr',  # Géolocalisation France
                'hl': 'fr'   # Langue française
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            results = []
            
            # Knowledge Graph (informations structurées)
            if data.get('knowledgeGraph'):
                kg = data['knowledgeGraph']
                results.append({
                    'title': kg.get('title', ''),
                    'snippet': kg.get('description', ''),
                    'source': kg.get('website', ''),
                    'type': 'knowledge_graph',
                    'attributes': kg.get('attributes', {})
                })
            
            # Résultats organiques
            for item in data.get('organic', [])[:max_results]:
                results.append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'source': item.get('link', ''),
                    'type': 'organic'
                })
            
            # People Also Ask
            for item in data.get('peopleAlsoAsk', [])[:2]:
                results.append({
                    'title': item.get('question', ''),
                    'snippet': item.get('answer', ''),
                    'source': item.get('link', ''),
                    'type': 'faq'
                })
            
            logger.info(f"✅ Serper API: {len(results)} résultats")
            return results
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error("❌ Clé API Serper invalide ou expirée")
            elif e.response.status_code == 429:
                logger.error("❌ Limite de requêtes Serper atteinte")
            else:
                logger.error(f"❌ Erreur HTTP Serper: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Erreur Serper API: {e}")
            return []
    
    def _format_context(self, results: List[Dict]) -> str:
        """Formate les résultats en contexte textuel pour l'IA"""
        context_parts = []
        
        for i, result in enumerate(results[:5], 1):
            result_type = result.get('type', 'unknown')
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            
            if result_type == 'knowledge_graph':
                context_parts.append(f"📚 INFORMATIONS OFFICIELLES:\n{title}\n{snippet}")
                
                # Ajouter les attributs si disponibles
                attributes = result.get('attributes', {})
                if attributes:
                    attrs_text = '\n'.join([f"- {k}: {v}" for k, v in attributes.items()])
                    context_parts.append(attrs_text)
                    
            elif result_type == 'faq':
                context_parts.append(f"❓ FAQ: {title}\n{snippet}")
            else:
                context_parts.append(f"{i}. {title}\n{snippet}")
        
        return '\n\n'.join(context_parts)
    
    def format_enriched_info(self, enriched_info: Dict) -> str:
        """Formate les infos enrichies pour intégration dans le prompt de génération"""
        if not enriched_info.get('found'):
            return ""
        
        context = enriched_info.get('context', '')
        if context:
            return f"\n\n🌐 INFORMATIONS WEB TROUVÉES:\n{context}\n"
        
        return ""


# Test rapide
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Note: Définir SERPER_API_KEY dans l'environnement
    searcher = WebSearchEnricher()
    
    test_product = {
        'Référence': '11005MI',
        'Marque': 'ARROW',
        'Libellé': 'CARBON HEAT SHIELD',
        'Catégorie': 'Pare-chaleur'
    }
    
    print("\n" + "="*80)
    print("TEST: ARROW 11005MI")
    print("="*80)
    
    result = searcher.search_product_info(test_product)
    
    if result.get('found'):
        print(f"\n✅ TROUVÉ! {len(result.get('search_results', []))} résultats")
        print("\n" + result.get('context', ''))
    else:
        print("\n❌ Aucun résultat (vérifiez SERPER_API_KEY)")
