"""
Module de gestion des templates Excel (SQLite)
"""
from pathlib import Path
from typing import List, Dict, Optional
import shutil
from .database import DatabaseManager


class TemplateManager:
    """Gère les templates Excel sauvegardés via SQLite"""
    
    def __init__(self, templates_dir: str = "templates"):
        """
        Initialise le gestionnaire de templates
        
        Args:
            templates_dir: Dossier de stockage des fichiers templates
        """
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        self.db = DatabaseManager()
    
    def add_template(
        self,
        file_path: str,
        name: Optional[str] = None,
        description: str = "",
        set_as_default: bool = False
    ) -> str:
        """
        Ajoute un nouveau template
        """
        source = Path(file_path)
        
        if not source.exists():
            raise FileNotFoundError(f"Fichier introuvable: {file_path}")
        
        # Génère un nom unique
        template_name = name or source.stem
        template_id = self._generate_unique_id(template_name)
        
        # Copie le fichier
        dest = self.templates_dir / f"{template_id}.xlsx"
        shutil.copy2(source, dest)
        
        # Enregistre dans la DB
        try:
            # Si c'est le premier ou demandé par défaut, on reset les autres
            if set_as_default or not self.has_templates():
                self.db.execute_update("UPDATE templates SET is_default = FALSE")
                is_default = True
            else:
                is_default = False
            
            self.db.execute_update(
                """
                INSERT INTO templates (id, name, description, filename, original_name, is_default)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (template_id, template_name, description, dest.name, source.name, is_default)
            )
            
            print(f"✓ Template '{template_name}' ajouté avec l'ID: {template_id}")
            return template_id
            
        except Exception as e:
            # Nettoyage en cas d'erreur
            if dest.exists():
                dest.unlink()
            raise e
    
    def _generate_unique_id(self, base_name: str) -> str:
        """Génère un ID unique pour le template"""
        base_id = base_name.lower().replace(" ", "_")
        template_id = base_id
        counter = 1
        
        while True:
            rows = self.db.execute_query("SELECT 1 FROM templates WHERE id = ?", (template_id,))
            if not rows:
                break
            template_id = f"{base_id}_{counter}"
            counter += 1
        
        return template_id
    
    def list_templates(self) -> List[Dict]:
        """
        Liste tous les templates disponibles
        """
        try:
            rows = self.db.execute_query("SELECT * FROM templates ORDER BY name")
            return [
                {
                    "id": row['id'],
                    "name": row['name'],
                    "description": row['description'],
                    "is_default": bool(row['is_default']),
                    "path": str(self.templates_dir / row['filename'])
                }
                for row in rows
            ]
        except Exception as e:
            print(f"❌ Erreur liste templates: {e}")
            return []
    
    def get_template_path(self, template_id: str) -> Optional[str]:
        """
        Récupère le chemin d'un template
        """
        try:
            rows = self.db.execute_query("SELECT filename FROM templates WHERE id = ?", (template_id,))
            if not rows:
                return None
            
            path = self.templates_dir / rows[0]['filename']
            return str(path) if path.exists() else None
        except Exception as e:
            print(f"❌ Erreur chemin template: {e}")
            return None
    
    def get_default_template(self) -> Optional[Dict]:
        """
        Récupère le template par défaut
        """
        try:
            rows = self.db.execute_query("SELECT * FROM templates WHERE is_default = TRUE LIMIT 1")
            if not rows:
                return None
            
            row = rows[0]
            return {
                "id": row['id'],
                "name": row['name'],
                "path": str(self.templates_dir / row['filename'])
            }
        except Exception as e:
            print(f"❌ Erreur default template: {e}")
            return None
    
    def set_default_template(self, template_id: str) -> bool:
        """
        Définit un template comme défaut
        """
        try:
            # Vérifie existence
            rows = self.db.execute_query("SELECT name FROM templates WHERE id = ?", (template_id,))
            if not rows:
                return False
            
            # Transaction implicite via execute_update successifs
            self.db.execute_update("UPDATE templates SET is_default = FALSE")
            self.db.execute_update("UPDATE templates SET is_default = TRUE WHERE id = ?", (template_id,))
            
            print(f"✓ Template '{rows[0]['name']}' défini par défaut")
            return True
        except Exception as e:
            print(f"❌ Erreur set default: {e}")
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """
        Supprime un template
        """
        try:
            # Récupère info fichier
            rows = self.db.execute_query("SELECT filename, name, is_default FROM templates WHERE id = ?", (template_id,))
            if not rows:
                return False
            
            row = rows[0]
            file_path = self.templates_dir / row['filename']
            
            # Supprime fichier
            if file_path.exists():
                file_path.unlink()
            
            # Supprime DB
            self.db.execute_update("DELETE FROM templates WHERE id = ?", (template_id,))
            
            # Si c'était le défaut, on en met un autre
            if row['is_default']:
                remaining = self.db.execute_query("SELECT id FROM templates LIMIT 1")
                if remaining:
                    self.db.execute_update("UPDATE templates SET is_default = TRUE WHERE id = ?", (remaining[0]['id'],))
            
            print(f"✓ Template '{row['name']}' supprimé")
            return True
            
        except Exception as e:
            print(f"❌ Erreur suppression template: {e}")
            return False
    
    def update_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Met à jour les métadonnées d'un template
        """
        try:
            updates = []
            params = []
            
            if name:
                updates.append("name = ?")
                params.append(name)
            
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            
            if not updates:
                return False
            
            params.append(template_id)
            query = f"UPDATE templates SET {', '.join(updates)} WHERE id = ?"
            
            count = self.db.execute_update(query, tuple(params))
            return count > 0
            
        except Exception as e:
            print(f"❌ Erreur update template: {e}")
            return False
    
    def has_templates(self) -> bool:
        """Vérifie si au moins un template existe"""
        try:
            count = self.db.execute_query("SELECT COUNT(*) as c FROM templates")[0]['c']
            return count > 0
        except:
            return False
