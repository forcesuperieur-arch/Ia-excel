"""
Client OpenAI pour génération de contenu avec GPT
"""
import os
import json
from typing import Optional, Dict, List
import logging
from openai import OpenAI
from dotenv import load_dotenv

# Charger variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client pour interagir avec l'API OpenAI ou OpenRouter"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini", base_url: Optional[str] = None):
        """
        Initialise le client OpenAI/OpenRouter
        
        Args:
            api_key: Clé API OpenAI/OpenRouter (ou depuis OPENAI_API_KEY env)
            model: Modèle à utiliser (gpt-4o-mini, gpt-4o, etc.)
            base_url: URL de base (None=OpenAI, "https://openrouter.ai/api/v1"=OpenRouter)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        # Détecter OpenRouter automatiquement si clé commence par sk-or-
        if self.api_key and self.api_key.startswith("sk-or-"):
            self.base_url = base_url or "https://openrouter.ai/api/v1"
            self.is_openrouter = True
            # Utiliser le modèle de l'env ou le défaut OpenRouter
            self.model = os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")
            logger.info("🔄 Détection OpenRouter")
        else:
            self.base_url = base_url
            self.is_openrouter = False
            self.model = os.getenv("OPENAI_MODEL", model)
        
        if not self.api_key:
            logger.error("❌ OPENAI_API_KEY non définie")
            self.available = False
            self.client = None
        else:
            try:
                # Initialiser avec base_url pour OpenRouter
                client_kwargs = {
                    "api_key": self.api_key,
                    "max_retries": 2,
                    "timeout": 60.0
                }
                
                if self.base_url:
                    client_kwargs["base_url"] = self.base_url
                
                self.client = OpenAI(**client_kwargs)
                self.available = self._check_availability()
                
                if self.available:
                    provider = "OpenRouter" if self.is_openrouter else "OpenAI"
                    logger.info(f"✅ {provider} disponible avec modèle {self.model}")
            except Exception as e:
                logger.error(f"❌ Erreur initialisation: {e}")
                self.available = False
                self.client = None
    
    def _check_availability(self) -> bool:
        """Vérifie si l'API OpenAI est accessible"""
        if not self.client:
            return False
        
        try:
            # Test simple avec une requête minimale
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"❌ Test API OpenAI échoué: {e}")
            return False
    
    def is_available(self) -> bool:
        """Vérifie si OpenAI est prêt à l'emploi"""
        return self.available and self.client is not None
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> Optional[str]:
        """
        Génère du texte avec OpenAI
        
        Args:
            prompt: Prompt utilisateur
            system: Instruction système (optionnel)
            temperature: Créativité (0-1)
            max_tokens: Longueur maximale
            
        Returns:
            Texte généré ou None si erreur
        """
        if not self.is_available():
            logger.error("OpenAI n'est pas disponible")
            return None
        
        try:
            messages = []
            
            if system:
                messages.append({"role": "system", "content": system})
            
            messages.append({"role": "user", "content": prompt})
            
            # Paramètres de requête
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # OpenRouter nécessite des headers spécifiques
            if self.is_openrouter:
                # Pas de extra_headers dans create(), déjà dans le client
                pass
            
            response = self.client.chat.completions.create(**request_params)
            
            content = response.choices[0].message.content
            
            if content:
                logger.info(f"✅ Génération réussie ({len(content)} caractères)")
                return content.strip()
            else:
                logger.error("❌ Réponse vide de l'API")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur génération OpenAI: {e}")
            return None
    
    def generate_with_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Optional[Dict]:
        """
        Génère du contenu structuré en JSON
        
        Args:
            prompt: Prompt utilisateur
            system: Instruction système
            temperature: Créativité
            max_tokens: Longueur maximale
            
        Returns:
            Dict parsé ou None si erreur
        """
        if not self.is_available():
            return None
        
        try:
            messages = []
            
            if system:
                messages.append({"role": "system", "content": system})
            
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            
            if content:
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON invalide: {e}")
                    return None
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur génération JSON: {e}")
            return None
    
    def get_available_models(self) -> List[str]:
        """Retourne les modèles disponibles"""
        if self.is_openrouter:
            # Modèles OpenRouter populaires
            return [
                "openai/gpt-4o",
                "openai/gpt-4o-mini",
                "openai/gpt-3.5-turbo",
                "anthropic/claude-3.5-sonnet",
                "google/gemini-pro-1.5",
                "meta-llama/llama-3.1-70b-instruct"
            ]
        else:
            return [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-3.5-turbo"
            ]
    
    def switch_model(self, model_name: str) -> bool:
        """
        Change le modèle OpenAI utilisé
        
        Args:
            model_name: Nom du nouveau modèle
            
        Returns:
            True si changement réussi
        """
        available = self.get_available_models()
        if model_name in available:
            self.model = model_name
            logger.info(f"🔄 Modèle changé: {model_name}")
            return True
        else:
            logger.error(f"❌ Modèle {model_name} non disponible")
            return False


# Exemple d'utilisation
if __name__ == "__main__":
    client = OpenAIClient()
    
    if client.is_available():
        result = client.generate(
            "Écris une description courte pour un casque moto BMW",
            system="Tu es un rédacteur technique spécialisé en équipement moto."
        )
        print(f"Résultat: {result}")
