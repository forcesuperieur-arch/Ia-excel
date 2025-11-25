"""
Système d'apprentissage pour améliorer le matching de colonnes
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class MatchingLearning:
    """Gère l'apprentissage des corrections manuelles de matching"""
    
    def __init__(self, learning_file: str = "templates/matching_history.json"):
        """
        Initialise le système d'apprentissage
        
        Args:
            learning_file: Fichier JSON pour stocker l'historique
        """
        self.learning_file = Path(learning_file)
        self.learning_file.parent.mkdir(exist_ok=True)
        self.history = self._load_history()
    
    def _load_history(self) -> Dict:
        """Charge l'historique d'apprentissage"""
        if self.learning_file.exists():
            with open(self.learning_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"corrections": [], "patterns": {}}
    
    def _save_history(self):
        """Sauvegarde l'historique"""
        with open(self.learning_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
    
    def add_correction(
        self,
        source_column: str,
        target_column: str,
        template_name: Optional[str] = None,
        confidence_before: float = 0.0
    ):
        """
        Enregistre une correction manuelle
        
        Args:
            source_column: Nom de la colonne source (catalogue)
            target_column: Nom de la colonne cible (template)
            template_name: Nom du template utilisé
            confidence_before: Confiance IA avant correction
        """
        correction = {
            "timestamp": datetime.now().isoformat(),
            "source": source_column.lower().strip(),
            "target": target_column.lower().strip(),
            "template": template_name,
            "confidence_before": confidence_before
        }
        
        self.history["corrections"].append(correction)
        
        # Met à jour les patterns
        key = self._normalize(source_column)
        if key not in self.history["patterns"]:
            self.history["patterns"][key] = []
        
        # Ajoute le mapping s'il n'existe pas déjà
        if target_column not in self.history["patterns"][key]:
            self.history["patterns"][key].append(target_column)
        
        self._save_history()
        print(f"✓ Correction enregistrée: {source_column} → {target_column}")
    
    def get_suggestion(self, source_column: str) -> Optional[str]:
        """
        Récupère une suggestion basée sur l'historique
        
        Args:
            source_column: Nom de la colonne source
            
        Returns:
            Suggestion de colonne cible ou None
        """
        key = self._normalize(source_column)
        
        if key in self.history["patterns"]:
            # Retourne la suggestion la plus fréquente
            suggestions = self.history["patterns"][key]
            return suggestions[0] if suggestions else None
        
        return None
    
    def _normalize(self, column_name: str) -> str:
        """Normalise un nom de colonne pour la comparaison"""
        return column_name.lower().strip().replace("_", " ").replace("-", " ")
    
    def get_learning_context(self, max_examples: int = 20) -> str:
        """
        Génère un contexte d'apprentissage pour le prompt IA
        
        Args:
            max_examples: Nombre maximum d'exemples à inclure
            
        Returns:
            Texte formaté avec les exemples d'apprentissage
        """
        if not self.history["corrections"]:
            return ""
        
        # Prend les corrections les plus récentes
        recent = self.history["corrections"][-max_examples:]
        
        context = "\n**Exemples d'apprentissage (corrections validées) :**\n"
        for corr in recent:
            context += f"- '{corr['source']}' → '{corr['target']}'\n"
        
        return context
    
    def get_statistics(self) -> Dict:
        """Retourne des statistiques sur l'apprentissage"""
        total_corrections = len(self.history["corrections"])
        unique_patterns = len(self.history["patterns"])
        
        # Templates les plus utilisés
        templates = {}
        for corr in self.history["corrections"]:
            tmpl = corr.get("template", "Unknown")
            templates[tmpl] = templates.get(tmpl, 0) + 1
        
        return {
            "total_corrections": total_corrections,
            "unique_patterns": unique_patterns,
            "templates": templates,
            "last_correction": self.history["corrections"][-1] if self.history["corrections"] else None
        }
    
    def clear_history(self):
        """Efface tout l'historique d'apprentissage"""
        self.history = {"corrections": [], "patterns": {}}
        self._save_history()
        print("✓ Historique d'apprentissage effacé")
