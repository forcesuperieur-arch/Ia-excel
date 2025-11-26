import os
from typing import Optional
from .openai_client import OpenAIClient
from .ollama_client import OllamaClient


def _get_secret(key: str, default: str = "") -> str:
    """Récupère un secret depuis st.secrets ou os.environ"""
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except:
        pass
    return os.getenv(key, default)


class AIClientFactory:
    """Factory pour instancier les clients IA de manière centralisée"""
    _openai_instance = None
    _ollama_instance = None

    @classmethod
    def get_client(cls, provider: str = "openai", api_key: Optional[str] = None):
        """
        Retourne une instance du client IA demandé.
        Utilise le pattern Singleton pour éviter de recréer les clients.
        """
        if provider.lower() == "openai":
            # Si la clé change, on recrée l'instance
            current_key = api_key or _get_secret("OPENAI_API_KEY")
            
            if cls._openai_instance is None:
                cls._openai_instance = OpenAIClient(api_key=current_key)
            elif current_key and cls._openai_instance.api_key != current_key:
                # Mise à jour de la clé si elle a changé
                cls._openai_instance = OpenAIClient(api_key=current_key)
                
            return cls._openai_instance
            
        elif provider.lower() == "ollama":
            if cls._ollama_instance is None:
                cls._ollama_instance = OllamaClient()
            return cls._ollama_instance
            
        return None

    @classmethod
    def reset(cls):
        """Réinitialise les instances (utile pour les tests ou changement de config)"""
        cls._openai_instance = None
        cls._ollama_instance = None
