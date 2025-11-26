"""
Gestionnaire de templates SEO personnalisables
Permet de créer, modifier et gérer des templates par catégorie
"""
import json
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class TemplateSEOManager:
    """Gestion des templates SEO personnalisés"""
    
    DEFAULT_TEMPLATES = {
        "casque": {
            "name": "Casque",
            "structure": """Rédige une description SEO professionnelle pour ce casque moto en {word_count} mots:

{product_info}

Structure:
1. Introduction percutante (1-2 lignes)
2. Sécurité et homologations (2-3 lignes)
3. Caractéristiques techniques (2-3 lignes)
4. Confort et utilisation (1-2 lignes)
5. Conclusion et appel à l'action (1 ligne)

Mots-clés: casque moto, protection, sécurité, homologué, confort
Ton: Professionnel, rassurant, technique
Public: Motards soucieux de sécurité""",
            "word_count": "150-200",
            "keywords": ["casque moto", "protection", "sécurité", "homologué", "confort"],
            "tone": "Professionnel, rassurant, technique"
        },
        "blouson": {
            "name": "Blouson/Veste",
            "structure": """Rédige une description SEO engageante pour ce blouson moto en {word_count} mots:

{product_info}

Structure:
1. Accroche stylée (1-2 lignes)
2. Protections et sécurité (2-3 lignes)
3. Matériaux et finitions (2-3 lignes)
4. Confort et praticité (1-2 lignes)
5. Conclusion et lifestyle (1 ligne)

Mots-clés: blouson moto, protection, style, confort, résistant
Ton: Dynamique, stylé, sécuritaire
Public: Motards urbains et sportifs""",
            "word_count": "150-200",
            "keywords": ["blouson moto", "protection", "style", "confort", "résistant"],
            "tone": "Dynamique, stylé, sécuritaire"
        },
        "gants": {
            "name": "Gants",
            "structure": """Rédige une description SEO précise pour ces gants moto en {word_count} mots:

{product_info}

Structure:
1. Présentation du modèle (1-2 lignes)
2. Protections et sécurité (2-3 lignes)
3. Matériaux et grip (2-3 lignes)
4. Confort et sensations (1-2 lignes)
5. Conclusion pratique (1 ligne)

Mots-clés: gants moto, protection mains, grip, confort, sécurité
Ton: Technique, précis, pratique
Public: Motards exigeants sur le toucher""",
            "word_count": "150-200",
            "keywords": ["gants moto", "protection mains", "grip", "confort", "sécurité"],
            "tone": "Technique, précis, pratique"
        },
        "default": {
            "name": "Accessoire/Autre",
            "structure": """Décris ce produit moto de manière technique et factuelle en {word_count} mots:

{product_info}

Rédige une description concise incluant:
- Type de produit et utilité principale
- Caractéristiques techniques clés
- Matériaux ou construction
- Compatibilité ou usage recommandé

PAS DE PRIX, PAS DE PROMOTION, UNIQUEMENT LES FAITS TECHNIQUES.""",
            "word_count": "80-120",
            "keywords": ["équipement moto", "accessoire", "qualité", "compatible"],
            "tone": "Technique, factuel, direct"
        }
    }
    
    def __init__(self, custom_file: str = "templates/seo_custom.json"):
        """
        Initialise le gestionnaire
        
        Args:
            custom_file: Fichier des templates personnalisés
        """
        self.custom_file = Path(custom_file)
        self.custom_file.parent.mkdir(exist_ok=True)
        self.custom_templates = self._load_custom()
    
    def _load_custom(self) -> Dict:
        """Charge les templates personnalisés"""
        if self.custom_file.exists():
            try:
                with open(self.custom_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
                    logger.info(f"📝 Templates personnalisés chargés: {len(templates)}")
                    return templates
            except Exception as e:
                logger.warning(f"⚠️ Erreur lecture templates custom: {e}")
                return {}
        return {}
    
    def _save_custom(self):
        """Sauvegarde les templates personnalisés"""
        try:
            with open(self.custom_file, 'w', encoding='utf-8') as f:
                json.dump(self.custom_templates, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 Templates sauvegardés: {len(self.custom_templates)}")
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde templates: {e}")
    
    def get_template(self, category: str) -> Dict:
        """
        Récupère un template (custom > default)
        
        Args:
            category: Catégorie du produit
            
        Returns:
            Dict avec structure, word_count, keywords, tone
        """
        # Priorité aux templates personnalisés
        if category in self.custom_templates:
            return self.custom_templates[category]
        
        # Sinon template par défaut
        return self.DEFAULT_TEMPLATES.get(category, self.DEFAULT_TEMPLATES["default"])
    
    def list_templates(self, include_default: bool = True) -> Dict:
        """
        Liste tous les templates disponibles
        
        Args:
            include_default: Inclure les templates par défaut
            
        Returns:
            Dict {category: {name, is_custom}}
        """
        templates = {}
        
        # Templates par défaut
        if include_default:
            for cat, tmpl in self.DEFAULT_TEMPLATES.items():
                templates[cat] = {
                    'name': tmpl['name'],
                    'is_custom': False,
                    'category': cat
                }
        
        # Templates personnalisés
        for cat, tmpl in self.custom_templates.items():
            templates[cat] = {
                'name': tmpl.get('name', cat),
                'is_custom': True,
                'category': cat
            }
        
        return templates
    
    def create_template(
        self,
        category: str,
        name: str,
        structure: str,
        word_count: str = "150-200",
        keywords: List[str] = None,
        tone: str = "Professionnel"
    ) -> bool:
        """
        Crée un nouveau template personnalisé
        
        Args:
            category: ID de la catégorie
            name: Nom du template
            structure: Structure du prompt
            word_count: Nombre de mots cible
            keywords: Liste de mots-clés
            tone: Ton de la description
            
        Returns:
            True si succès
        """
        try:
            self.custom_templates[category] = {
                'name': name,
                'structure': structure,
                'word_count': word_count,
                'keywords': keywords or [],
                'tone': tone
            }
            
            self._save_custom()
            logger.info(f"✅ Template '{name}' créé pour catégorie '{category}'")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur création template: {e}")
            return False
    
    def update_template(
        self,
        category: str,
        updates: Dict
    ) -> bool:
        """
        Met à jour un template existant
        
        Args:
            category: Catégorie du template
            updates: Dict avec les champs à mettre à jour
            
        Returns:
            True si succès
        """
        try:
            if category not in self.custom_templates:
                # Créer à partir du défaut si n'existe pas
                self.custom_templates[category] = self.DEFAULT_TEMPLATES.get(
                    category,
                    self.DEFAULT_TEMPLATES["default"]
                ).copy()
            
            # Appliquer les modifications
            self.custom_templates[category].update(updates)
            
            self._save_custom()
            logger.info(f"✅ Template '{category}' mis à jour")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur modification template: {e}")
            return False
    
    def delete_template(self, category: str) -> bool:
        """
        Supprime un template personnalisé
        
        Args:
            category: Catégorie à supprimer
            
        Returns:
            True si supprimé
        """
        if category in self.custom_templates:
            del self.custom_templates[category]
            self._save_custom()
            logger.info(f"🗑️ Template '{category}' supprimé")
            return True
        return False
    
    def reset_to_default(self, category: str) -> bool:
        """
        Réinitialise un template aux valeurs par défaut
        
        Args:
            category: Catégorie à réinitialiser
            
        Returns:
            True si réinitialisé
        """
        if category in self.custom_templates:
            del self.custom_templates[category]
            self._save_custom()
            logger.info(f"🔄 Template '{category}' réinitialisé")
            return True
        return False
