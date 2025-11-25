"""
Client Ollama pour génération de contenu avec IA locale
"""
import json
import requests
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client pour interagir avec Ollama en local"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:3b"):
        """
        Initialise le client Ollama
        
        Args:
            base_url: URL de l'API Ollama
            model: Nom du modèle à utiliser (qwen2.5:3b, qwen2.5:7b, qwen2.5:13b, etc.)
        """
        self.base_url = base_url
        self.model = model
        self.available = self._check_availability()
        self.available_models = self._list_models()
        
    def _list_models(self) -> List[str]:
        """Liste les modèles Ollama disponibles"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [m['name'] for m in models]
        except:
            pass
        return []
    
    def get_available_models(self) -> List[Dict]:
        """
        Retourne les modèles disponibles avec infos
        
        Returns:
            Liste de dicts avec name, size, description
        """
        model_info = {
            'qwen2.5:3b': {'size': '1.9GB', 'speed': 'Rapide', 'quality': 'Bonne'},
            'qwen2.5:7b': {'size': '4.7GB', 'speed': 'Moyen', 'quality': 'Très bonne'},
            'qwen2.5:13b': {'size': '7.7GB', 'speed': 'Lent', 'quality': 'Excellente'},
            'llama3.2:3b': {'size': '2.0GB', 'speed': 'Rapide', 'quality': 'Bonne'},
            'mistral:7b': {'size': '4.1GB', 'speed': 'Moyen', 'quality': 'Très bonne'}
        }
        
        available = []
        for model_name in self.available_models:
            info = model_info.get(model_name, {'size': 'N/A', 'speed': 'N/A', 'quality': 'N/A'})
            available.append({
                'name': model_name,
                'size': info['size'],
                'speed': info['speed'],
                'quality': info['quality'],
                'is_current': model_name == self.model
            })
        
        return available
    
    def switch_model(self, model_name: str) -> bool:
        """
        Change le modèle Ollama utilisé
        
        Args:
            model_name: Nom du nouveau modèle
            
        Returns:
            True si changement réussi
        """
        if model_name in self.available_models:
            self.model = model_name
            logger.info(f"🔄 Modèle changé: {model_name}")
            return True
        else:
            logger.error(f"❌ Modèle {model_name} non disponible. Disponibles: {', '.join(self.available_models)}")
            return False
        
    def _check_availability(self) -> bool:
        """Vérifie si Ollama est disponible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                if self.model in model_names:
                    logger.info(f"✅ Ollama disponible avec modèle {self.model}")
                    return True
                else:
                    logger.warning(f"⚠️  Modèle {self.model} non trouvé. Disponibles: {', '.join(model_names)}")
                    # Utilise le premier modèle disponible
                    if model_names:
                        self.model = model_names[0]
                        logger.info(f"🔄 Utilisation de {self.model} à la place")
                        return True
                    logger.error("❌ Aucun modèle Ollama disponible. Lancez: ollama pull qwen2.5:3b")
                    return False
        except requests.exceptions.ConnectionError:
            logger.error("❌ Ollama non démarré. Lancez: ollama serve")
            return False
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout connexion Ollama (>2s)")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur vérification Ollama: {type(e).__name__} - {str(e)}")
            return False
    
    def is_available(self) -> bool:
        """Vérifie si Ollama est prêt à l'emploi"""
        return self.available
    
    def unload_model(self) -> bool:
        """
        Décharge le modèle de la mémoire pour libérer la RAM
        
        Returns:
            True si succès
        """
        try:
            # Envoie une requête avec keep_alive=0 pour décharger
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": "",
                    "keep_alive": 0  # Décharge immédiatement
                },
                timeout=5
            )
            logger.info(f"🧹 Modèle {self.model} déchargé de la RAM")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Impossible de décharger le modèle: {e}")
            return False
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        stream: bool = False
    ) -> Optional[str]:
        """
        Génère du texte avec Ollama
        
        Args:
            prompt: Prompt utilisateur
            system: Instruction système (optionnel)
            temperature: Créativité (0-1)
            max_tokens: Longueur maximale
            stream: Mode streaming
            
        Returns:
            Texte généré ou None si erreur
        """
        if not self.available:
            logger.error("Ollama n'est pas disponible")
            return None
        
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "num_ctx": 2048  # Réduire contexte pour économiser RAM (défaut=4096)
                }
            }
            
            if system:
                payload["system"] = system
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=300  # Augmenté à 5 minutes pour descriptions longues
            )
            
            if response.status_code == 200:
                if stream:
                    # Mode streaming - concatène les réponses
                    full_response = ""
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line)
                            full_response += data.get('response', '')
                    return full_response
                else:
                    # Mode normal
                    data = response.json()
                    return data.get('response', '')
            else:
                logger.error(f"❌ Erreur Ollama HTTP {response.status_code}: {response.text[:200]}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout génération (>300s). Prompt trop long ou modèle surchargé.")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Connexion Ollama perdue. Vérifiez: ollama serve")
            self.available = False  # Marquer comme indisponible
            return None
        except json.JSONDecodeError as e:
            logger.error(f"❌ Réponse Ollama invalide (JSON): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur génération: {type(e).__name__} - {str(e)}")
            return None
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> Optional[str]:
        """
        Mode chat avec contexte
        
        Args:
            messages: Liste de messages [{"role": "user", "content": "..."}]
            temperature: Créativité
            max_tokens: Longueur max
            
        Returns:
            Réponse du modèle
        """
        if not self.available:
            return None
        
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=300  # Augmenté à 5 minutes
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('message', {}).get('content', '')
            else:
                logger.error(f"❌ Erreur chat Ollama HTTP {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout chat (>300s)")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Connexion Ollama perdue pendant chat")
            self.available = False
            return None
        except Exception as e:
            logger.error(f"❌ Erreur chat: {type(e).__name__} - {str(e)}")
            return None
    
    def match_column(
        self,
        catalog_column: str,
        template_columns: List[str],
        context: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Matche une colonne catalogue avec le template
        
        Args:
            catalog_column: Nom de la colonne catalogue
            template_columns: Liste des colonnes template
            context: Contexte additionnel (langue, exemples...)
            
        Returns:
            Nom de la colonne template matchée
        """
        if not self.available:
            return None
        
        # Construit le prompt
        system_prompt = """Tu es un expert en mapping de colonnes de catalogues Excel multilingues.
Ta tâche est de trouver la meilleure correspondance entre une colonne source et une liste de colonnes cibles.
Réponds UNIQUEMENT avec le nom exact de la colonne cible, sans explication."""
        
        template_list = "\n".join([f"- {col}" for col in template_columns])
        
        user_prompt = f"""Colonne source: "{catalog_column}"

Colonnes cibles disponibles:
{template_list}

Quelle colonne cible correspond le mieux à la colonne source?
Réponds uniquement avec le nom exact de la colonne."""
        
        # Ajoute le contexte si disponible
        if context:
            if 'language' in context:
                user_prompt = f"Langue: {context['language']}\n\n" + user_prompt
            if 'examples' in context:
                user_prompt += f"\n\nExemples de valeurs: {context['examples']}"
        
        response = self.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.3,  # Plus déterministe pour matching
            max_tokens=50
        )
        
        if response:
            # Nettoie la réponse
            cleaned = response.strip().strip('"').strip("'")
            
            # Vérifie que la réponse est dans les colonnes cibles
            for col in template_columns:
                if col.lower() == cleaned.lower():
                    return col
            
            # Recherche partielle
            for col in template_columns:
                if cleaned.lower() in col.lower() or col.lower() in cleaned.lower():
                    return col
        
        return None
    
    def get_model_info(self) -> Optional[Dict]:
        """Récupère les infos du modèle actuel"""
        if not self.available:
            return None
        
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": self.model},
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            
        except Exception as e:
            logger.error(f"Erreur info modèle: {e}")
        
        return None


def test_ollama():
    """Teste la connexion Ollama"""
    print("\n" + "="*80)
    print("🧪 TEST CLIENT OLLAMA")
    print("="*80)
    
    client = OllamaClient()
    
    if not client.is_available():
        print("\n❌ Ollama n'est pas disponible")
        print("\n💡 Pour installer Ollama:")
        print("   1. curl -fsSL https://ollama.com/install.sh | sh")
        print("   2. ollama pull qwen2.5:3b")
        print("   3. ollama serve")
        return False
    
    print(f"\n✅ Ollama disponible avec modèle: {client.model}")
    
    # Test simple
    print("\n🔹 Test génération simple...")
    response = client.generate("Quelle est la capitale de la France?", temperature=0.1, max_tokens=50)
    
    if response:
        print(f"✅ Réponse: {response[:100]}")
    else:
        print("❌ Pas de réponse")
        return False
    
    # Test matching
    print("\n🔹 Test matching de colonnes...")
    match = client.match_column(
        catalog_column="Codice Item",
        template_columns=["Référence", "Désignation", "Prix unitaire", "Quantité"]
    )
    
    if match:
        print(f"✅ Match trouvé: 'Codice Item' → '{match}'")
    else:
        print("⚠️  Pas de match trouvé")
    
    # Infos modèle
    print("\n🔹 Informations modèle...")
    info = client.get_model_info()
    if info:
        print(f"✅ Modèle: {info.get('modelfile', 'N/A')[:100]}")
    
    print("\n" + "="*80)
    print("✅ TESTS OLLAMA RÉUSSIS")
    print("="*80)
    return True


if __name__ == "__main__":
    test_ollama()
