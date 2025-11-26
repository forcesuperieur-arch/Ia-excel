"""
Système d'apprentissage pour améliorer le matching de colonnes (SQLite)
"""
from datetime import datetime
from typing import Dict, Optional
from .database import DatabaseManager


class MatchingLearning:
    """Gère l'apprentissage des corrections manuelles de matching via SQLite"""
    
    def __init__(self):
        """Initialise le système d'apprentissage avec la base de données"""
        self.db = DatabaseManager()
    
    def add_correction(
        self,
        source_column: str,
        target_column: str,
        template_name: Optional[str] = None,
        confidence_before: float = 0.0
    ):
        """
        Enregistre une correction manuelle
        """
        try:
            # 1. Enregistrer l'historique
            self.db.execute_update(
                """
                INSERT INTO learning_corrections 
                (timestamp, source_column, target_column, template_name, confidence_before)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(),
                    source_column.lower().strip(),
                    target_column.lower().strip(),
                    template_name,
                    confidence_before
                )
            )
            
            # 2. Mettre à jour le pattern (Upsert simplifié)
            key = self._normalize(source_column)
            
            # Vérifier si existe déjà
            existing = self.db.execute_query(
                "SELECT frequency FROM learning_patterns WHERE source_key = ? AND target_column = ?",
                (key, target_column)
            )
            
            if existing:
                # Update frequency
                self.db.execute_update(
                    "UPDATE learning_patterns SET frequency = frequency + 1, last_used = ? WHERE source_key = ? AND target_column = ?",
                    (datetime.now(), key, target_column)
                )
            else:
                # Insert new
                self.db.execute_update(
                    "INSERT INTO learning_patterns (source_key, target_column, frequency, last_used) VALUES (?, ?, 1, ?)",
                    (key, target_column, datetime.now())
                )
            
            print(f"✓ Correction enregistrée: {source_column} → {target_column}")
            
        except Exception as e:
            print(f"❌ Erreur enregistrement correction: {e}")
    
    def get_suggestion(self, source_column: str) -> Optional[str]:
        """
        Récupère une suggestion basée sur l'historique
        """
        key = self._normalize(source_column)
        
        try:
            # Retourne la suggestion la plus fréquente
            rows = self.db.execute_query(
                "SELECT target_column FROM learning_patterns WHERE source_key = ? ORDER BY frequency DESC LIMIT 1",
                (key,)
            )
            return rows[0]['target_column'] if rows else None
        except Exception as e:
            print(f"❌ Erreur lecture suggestion: {e}")
            return None
    
    def _normalize(self, column_name: str) -> str:
        """Normalise un nom de colonne pour la comparaison"""
        return column_name.lower().strip().replace("_", " ").replace("-", " ")
    
    def get_learning_context(self, max_examples: int = 20) -> str:
        """
        Génère un contexte d'apprentissage pour le prompt IA
        """
        try:
            rows = self.db.execute_query(
                "SELECT source_column, target_column FROM learning_corrections ORDER BY timestamp DESC LIMIT ?",
                (max_examples,)
            )
            
            if not rows:
                return ""
            
            context = "\n**Exemples d'apprentissage (corrections validées) :**\n"
            for row in rows:
                context += f"- '{row['source_column']}' → '{row['target_column']}'\n"
            
            return context
        except Exception as e:
            print(f"❌ Erreur lecture contexte: {e}")
            return ""
    
    def get_statistics(self) -> Dict:
        """Retourne des statistiques sur l'apprentissage"""
        try:
            total_corrections = self.db.execute_query("SELECT COUNT(*) as c FROM learning_corrections")[0]['c']
            unique_patterns = self.db.execute_query("SELECT COUNT(*) as c FROM learning_patterns")[0]['c']
            
            # Templates les plus utilisés
            tmpl_rows = self.db.execute_query("SELECT template_name, COUNT(*) as c FROM learning_corrections GROUP BY template_name")
            templates = {r['template_name'] or "Unknown": r['c'] for r in tmpl_rows}
            
            # Dernière correction
            last_rows = self.db.execute_query("SELECT * FROM learning_corrections ORDER BY timestamp DESC LIMIT 1")
            last_correction = dict(last_rows[0]) if last_rows else None
            
            return {
                "total_corrections": total_corrections,
                "unique_patterns": unique_patterns,
                "templates": templates,
                "last_correction": last_correction
            }
        except Exception as e:
            print(f"❌ Erreur stats apprentissage: {e}")
            return {"total_corrections": 0, "unique_patterns": 0}
    
    def clear_history(self):
        """Efface tout l'historique d'apprentissage"""
        try:
            self.db.execute_update("DELETE FROM learning_corrections")
            self.db.execute_update("DELETE FROM learning_patterns")
            print("✓ Historique d'apprentissage effacé")
        except Exception as e:
            print(f"❌ Erreur effacement historique: {e}")
