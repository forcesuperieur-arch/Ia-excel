"""
Module de gestion des templates Excel
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
import shutil


class TemplateManager:
    """Gère les templates Excel sauvegardés"""
    
    def __init__(self, templates_dir: str = "templates"):
        """
        Initialise le gestionnaire de templates
        
        Args:
            templates_dir: Dossier de stockage des templates
        """
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        self.config_file = self.templates_dir / "config.json"
        self._load_config()
    
    def _load_config(self):
        """Charge la configuration des templates"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "default_template": None,
                "templates": {}
            }
            self._save_config()
    
    def _save_config(self):
        """Sauvegarde la configuration"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def add_template(
        self,
        file_path: str,
        name: Optional[str] = None,
        description: str = "",
        set_as_default: bool = False
    ) -> str:
        """
        Ajoute un nouveau template
        
        Args:
            file_path: Chemin du fichier template
            name: Nom du template (nom du fichier si None)
            description: Description du template
            set_as_default: Définir comme template par défaut
            
        Returns:
            ID du template créé
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
        
        # Enregistre dans la config
        self.config["templates"][template_id] = {
            "name": template_name,
            "description": description,
            "filename": dest.name,
            "original_name": source.name
        }
        
        if set_as_default or not self.config["default_template"]:
            self.config["default_template"] = template_id
        
        self._save_config()
        print(f"✓ Template '{template_name}' ajouté avec l'ID: {template_id}")
        
        return template_id
    
    def _generate_unique_id(self, base_name: str) -> str:
        """Génère un ID unique pour le template"""
        base_id = base_name.lower().replace(" ", "_")
        template_id = base_id
        counter = 1
        
        while template_id in self.config["templates"]:
            template_id = f"{base_id}_{counter}"
            counter += 1
        
        return template_id
    
    def list_templates(self) -> List[Dict]:
        """
        Liste tous les templates disponibles
        
        Returns:
            Liste de dictionnaires avec les infos des templates
        """
        templates = []
        default_id = self.config.get("default_template")
        
        for template_id, info in self.config["templates"].items():
            templates.append({
                "id": template_id,
                "name": info["name"],
                "description": info.get("description", ""),
                "is_default": template_id == default_id,
                "path": str(self.templates_dir / info["filename"])
            })
        
        return templates
    
    def get_template_path(self, template_id: str) -> Optional[str]:
        """
        Récupère le chemin d'un template
        
        Args:
            template_id: ID du template
            
        Returns:
            Chemin du fichier ou None
        """
        if template_id not in self.config["templates"]:
            return None
        
        filename = self.config["templates"][template_id]["filename"]
        path = self.templates_dir / filename
        
        return str(path) if path.exists() else None
    
    def get_default_template(self) -> Optional[Dict]:
        """
        Récupère le template par défaut
        
        Returns:
            Dict avec les infos du template par défaut ou None
        """
        default_id = self.config.get("default_template")
        
        if not default_id or default_id not in self.config["templates"]:
            return None
        
        return {
            "id": default_id,
            "name": self.config["templates"][default_id]["name"],
            "path": self.get_template_path(default_id)
        }
    
    def set_default_template(self, template_id: str) -> bool:
        """
        Définit un template comme défaut
        
        Args:
            template_id: ID du template
            
        Returns:
            True si succès
        """
        if template_id not in self.config["templates"]:
            return False
        
        self.config["default_template"] = template_id
        self._save_config()
        
        print(f"✓ Template '{self.config['templates'][template_id]['name']}' défini par défaut")
        return True
    
    def delete_template(self, template_id: str) -> bool:
        """
        Supprime un template
        
        Args:
            template_id: ID du template à supprimer
            
        Returns:
            True si succès
        """
        if template_id not in self.config["templates"]:
            return False
        
        # Supprime le fichier
        filename = self.config["templates"][template_id]["filename"]
        file_path = self.templates_dir / filename
        
        if file_path.exists():
            file_path.unlink()
        
        # Supprime de la config
        template_name = self.config["templates"][template_id]["name"]
        del self.config["templates"][template_id]
        
        # Si c'était le défaut, on le réinitialise
        if self.config["default_template"] == template_id:
            # Prend le premier template disponible
            remaining = list(self.config["templates"].keys())
            self.config["default_template"] = remaining[0] if remaining else None
        
        self._save_config()
        print(f"✓ Template '{template_name}' supprimé")
        
        return True
    
    def update_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Met à jour les métadonnées d'un template
        
        Args:
            template_id: ID du template
            name: Nouveau nom (optionnel)
            description: Nouvelle description (optionnelle)
            
        Returns:
            True si succès
        """
        if template_id not in self.config["templates"]:
            return False
        
        if name:
            self.config["templates"][template_id]["name"] = name
        
        if description is not None:
            self.config["templates"][template_id]["description"] = description
        
        self._save_config()
        return True
    
    def has_templates(self) -> bool:
        """Vérifie si au moins un template existe"""
        return len(self.config["templates"]) > 0
