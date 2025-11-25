"""
Système d'apprentissage forcé pour améliorer le matching IA
Génère et enregistre automatiquement des patterns de matching multi-langues
"""
import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime


class ForcedLearning:
    """Entraîne le système avec des exemples pré-définis multi-langues"""
    
    # Base de connaissances multi-langues pour apprentissage
    TRAINING_PATTERNS = {
        # Français → Template
        "français": [
            ("Référence", "Référence"),
            ("Réf", "Référence"),
            ("Code produit", "Référence"),
            ("Code article", "Référence"),
            ("EAN", "Code barre"),
            ("EAN13", "Code barre"),
            ("Code barre", "Code barre"),
            ("UPC", "Code barre"),
            ("Libellé", "Libellé"),
            ("Nom", "Libellé"),
            ("Titre", "Libellé"),
            ("Désignation", "Libellé"),
            ("Description", "Descriptif"),
            ("Descriptif", "Descriptif"),
            ("Desc", "Descriptif"),
            ("Prix achat", "Prix achats nets Motoblouz"),
            ("Prix achat HT", "Prix achats nets Motoblouz"),
            ("Prix fournisseur", "Prix achats nets Motoblouz"),
            ("Prix public HT", "Prix public HT"),
            ("Prix HT", "Prix public HT"),
            ("Prix TTC", "Prix TTC"),
            ("Prix public TTC", "Prix TTC"),
            ("Catégorie", "Catégorie"),
            ("Cat", "Catégorie"),
            ("Rubrique", "Catégorie"),
            ("Sous-catégorie", "Sous-catégorie"),
            ("Sous-cat", "Sous-catégorie"),
            ("Marque", "Marque"),
            ("Fabricant", "Marque"),
            ("Couleur", "Couleur"),
            ("Coloris", "Couleur"),
            ("Taille", "Taille"),
            ("Dimension", "Taille"),
            ("Poids", "Poids"),
            ("Stock", "Stock"),
            ("Disponibilité", "Stock"),
            ("Dispo", "Stock"),
            ("Image", "Image 1"),
            ("Photo", "Image 1"),
            ("Img", "Image 1"),
        ],
        
        # Italien → Template
        "italien": [
            ("Codice", "Référence"),
            ("Codice articolo", "Référence"),
            ("Codice prodotto", "Référence"),
            ("Item", "Référence"),
            ("EAN13", "Code barre"),
            ("Codice a barre", "Code barre"),
            ("Denominazione", "Libellé"),
            ("Nome", "Libellé"),
            ("Titolo", "Libellé"),
            ("Descrizione", "Descriptif"),
            ("Descrizione completa", "Descriptif"),
            ("Desc", "Descriptif"),
            ("Prezzo acquisto", "Prix achats nets Motoblouz"),
            ("Prezzo di acquisto", "Prix achats nets Motoblouz"),
            ("Prezzo pubblico", "Prix TTC"),
            ("Prezzo pubblico IVA inclusa", "Prix TTC"),
            ("Prezzo lordo", "Prix TTC"),
            ("Prezzo netto", "Prix public HT"),
            ("Prezzo", "Prix unitaire"),
            ("Prezzo Unitario", "Prix unitaire"),
            ("Prezzo HT", "Prix public HT"),
            ("Prezzo IVA Esclusa", "Prix public HT"),
            ("Prezzo TTC", "Prix TTC"),
            ("Prezzo IVA Inclusa", "Prix TTC"),
            ("HT Public", "Prix public HT"),
            ("TTC Public", "Prix TTC"),
            ("Prix achat HT", "Prix achats nets Motoblouz"),
            ("Prix achat\nHT", "Prix achats nets Motoblouz"),
            ("Prix Web TTC Minimum", "Prix TTC"),
            ("Prix Web TTC\nMinimum", "Prix TTC"),
            ("Codice/Item", "Référence"),
            ("Categoria", "Catégorie"),
            ("Categoria principale", "Catégorie"),
            ("Sottocategoria", "Sous-catégorie"),
            ("Marca", "Marque"),
            ("Marchio", "Marque"),
            ("Colore", "Couleur"),
            ("Taglia", "Taille"),
            ("Dimensione", "Taille"),
            ("Peso", "Poids"),
            ("Disponibilità", "Stock"),
            ("Magazzino", "Stock"),
            ("Immagine", "Image 1"),
            ("Foto", "Image 1"),
        ],
        
        # Espagnol → Template
        "espagnol": [
            ("Codigo", "Référence"),
            ("Codigo producto", "Référence"),
            ("Codigo articulo", "Référence"),
            ("Referencia", "Référence"),
            ("Codigo de barras", "Code barre"),
            ("EAN", "Code barre"),
            ("Nombre", "Libellé"),
            ("Titulo", "Libellé"),
            ("Denominacion", "Libellé"),
            ("Descripcion", "Descriptif"),
            ("Descripcion completa", "Descriptif"),
            ("Precio compra", "Prix achats nets Motoblouz"),
            ("Precio de compra", "Prix achats nets Motoblouz"),
            ("Precio publico", "Prix TTC"),
            ("Precio con IVA", "Prix TTC"),
            ("Precio sin IVA", "Prix public HT"),
            ("Precio neto", "Prix public HT"),
            ("Categoria", "Catégorie"),
            ("Subcategoria", "Sous-catégorie"),
            ("Fabricante", "Marque"),
            ("Marca", "Marque"),
            ("Color", "Couleur"),
            ("Tamano", "Taille"),
            ("Talla", "Taille"),
            ("Peso", "Poids"),
            ("Stock", "Stock"),
            ("Disponibilidad", "Stock"),
            ("En stock", "Stock"),
            ("Imagen", "Image 1"),
            ("Foto", "Image 1"),
        ],
        
        # Anglais → Template
        "anglais": [
            ("Reference", "Référence"),
            ("Ref", "Référence"),
            ("Product code", "Référence"),
            ("Item code", "Référence"),
            ("SKU", "Référence"),
            ("Barcode", "Code barre"),
            ("EAN", "Code barre"),
            ("UPC", "Code barre"),
            ("Label", "Libellé"),
            ("Name", "Libellé"),
            ("Title", "Libellé"),
            ("Product name", "Libellé"),
            ("Description", "Descriptif"),
            ("Full description", "Descriptif"),
            ("Purchase price", "Prix achats nets Motoblouz"),
            ("Buying price", "Prix achats nets Motoblouz"),
            ("Cost price", "Prix achats nets Motoblouz"),
            ("Public price", "Prix TTC"),
            ("Retail price", "Prix TTC"),
            ("Price incl VAT", "Prix TTC"),
            ("Price excl VAT", "Prix public HT"),
            ("Net price", "Prix public HT"),
            ("Category", "Catégorie"),
            ("Subcategory", "Sous-catégorie"),
            ("Brand", "Marque"),
            ("Manufacturer", "Marque"),
            ("Color", "Couleur"),
            ("Colour", "Couleur"),
            ("Size", "Taille"),
            ("Weight", "Poids"),
            ("Stock", "Stock"),
            ("Availability", "Stock"),
            ("Available", "Stock"),
            ("Image", "Image 1"),
            ("Picture", "Image 1"),
            ("Photo", "Image 1"),
        ],
        
        # Allemand → Template
        "allemand": [
            ("Artikel", "Référence"),
            ("Artikel-Nr", "Référence"),
            ("Artikelnummer", "Référence"),
            ("Produkt-Code", "Référence"),
            ("Strichcode", "Code barre"),
            ("Barcode", "Code barre"),
            ("EAN", "Code barre"),
            ("Produktname", "Libellé"),
            ("Bezeichnung", "Libellé"),
            ("Titel", "Libellé"),
            ("Beschreibung", "Descriptif"),
            ("Vollständige Beschreibung", "Descriptif"),
            ("Einkaufspreis", "Prix achats nets Motoblouz"),
            ("Bezugspreis", "Prix achats nets Motoblouz"),
            ("Verkaufspreis", "Prix TTC"),
            ("Bruttopreis", "Prix TTC"),
            ("Preis inkl MwSt", "Prix TTC"),
            ("Nettopreis", "Prix public HT"),
            ("Preis ohne MwSt", "Prix public HT"),
            ("Kategorie", "Catégorie"),
            ("Unterkategorie", "Sous-catégorie"),
            ("Hersteller", "Marque"),
            ("Marke", "Marque"),
            ("Farbe", "Couleur"),
            ("Grosse", "Taille"),
            ("Größe", "Taille"),
            ("Gewicht", "Poids"),
            ("Lagerbestand", "Stock"),
            ("Verfügbarkeit", "Stock"),
            ("Bild", "Image 1"),
            ("Foto", "Image 1"),
        ],
        
        # Variations de ponctuation et casse
        "variations": [
            ("prix-achat-ht", "Prix achats nets Motoblouz"),
            ("prix_achat_ht", "Prix achats nets Motoblouz"),
            ("PRIX.ACHAT.HT", "Prix achats nets Motoblouz"),
            ("prixachatht", "Prix achats nets Motoblouz"),
            ("code-barre", "Code barre"),
            ("code_barre", "Code barre"),
            ("CODEBARRE", "Code barre"),
            ("prix-ttc", "Prix TTC"),
            ("prix_ttc", "Prix TTC"),
            ("PRIXTTC", "Prix TTC"),
            ("prix-public-ht", "Prix public HT"),
            ("prix_public_ht", "Prix public HT"),
            ("PRIXPUBLIC", "Prix public HT"),
        ],
        
        # Abréviations courantes
        "abréviations": [
            ("Ref", "Référence"),
            ("Réf", "Référence"),
            ("Cat", "Catégorie"),
            ("Desc", "Descriptif"),
            ("Img", "Image 1"),
            ("Dispo", "Stock"),
            ("HT", "Prix public HT"),
            ("TTC", "Prix TTC"),
            ("Qté", "Stock"),
            ("Qty", "Stock"),
        ]
    }
    
    def __init__(self, learning_file: str = "templates/matching_history.json"):
        """
        Initialise l'apprentissage forcé
        
        Args:
            learning_file: Fichier JSON pour l'historique
        """
        self.learning_file = Path(learning_file)
        self.learning_file.parent.mkdir(exist_ok=True)
    
    def load_existing_history(self) -> Dict:
        """Charge l'historique existant"""
        if self.learning_file.exists():
            with open(self.learning_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"corrections": [], "patterns": {}}
    
    def save_history(self, history: Dict):
        """Sauvegarde l'historique"""
        with open(self.learning_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    
    def normalize_key(self, text: str) -> str:
        """Normalise une clé pour le stockage"""
        return text.lower().strip().replace("_", " ").replace("-", " ")
    
    def train_all_patterns(self, template_name: str = "Auto-learning") -> Dict:
        """
        Entraîne le système avec tous les patterns
        
        Args:
            template_name: Nom du template pour les corrections
            
        Returns:
            Statistiques de l'entraînement
        """
        print("\n" + "="*70)
        print("🎓 APPRENTISSAGE FORCÉ - ENTRAÎNEMENT MULTI-LANGUES")
        print("="*70)
        
        history = self.load_existing_history()
        initial_count = len(history["corrections"])
        
        stats = {
            "total_added": 0,
            "by_language": {},
            "duplicates_skipped": 0
        }
        
        # Entraîner chaque langue
        for language, patterns in self.TRAINING_PATTERNS.items():
            print(f"\n📚 Entraînement: {language.capitalize()}")
            print("-" * 70)
            
            added_count = 0
            
            for source, target in patterns:
                # Vérifier si déjà existant
                source_key = self.normalize_key(source)
                
                # Vérifier dans les corrections existantes
                already_exists = False
                for corr in history["corrections"]:
                    if (self.normalize_key(corr["source"]) == source_key and 
                        self.normalize_key(corr["target"]) == self.normalize_key(target)):
                        already_exists = True
                        stats["duplicates_skipped"] += 1
                        break
                
                if not already_exists:
                    # Ajouter correction
                    correction = {
                        "timestamp": datetime.now().isoformat(),
                        "source": source.lower().strip(),
                        "target": target.lower().strip(),
                        "template": template_name,
                        "confidence_before": 0.0,
                        "training": True,  # Marqueur pour différencier
                        "language": language
                    }
                    history["corrections"].append(correction)
                    
                    # Mettre à jour patterns
                    if source_key not in history["patterns"]:
                        history["patterns"][source_key] = []
                    
                    target_lower = target.lower().strip()
                    if target_lower not in history["patterns"][source_key]:
                        history["patterns"][source_key].append(target_lower)
                    
                    added_count += 1
                    stats["total_added"] += 1
                    print(f"  ✅ {source:30} → {target}")
            
            stats["by_language"][language] = added_count
            print(f"\n  ✓ {added_count} patterns ajoutés pour {language}")
        
        # Sauvegarder
        self.save_history(history)
        
        # Afficher résumé
        print("\n" + "="*70)
        print("📊 RÉSUMÉ DE L'ENTRAÎNEMENT")
        print("="*70)
        print(f"\nCorrections avant: {initial_count}")
        print(f"Corrections après: {len(history['corrections'])}")
        print(f"Nouvelles corrections: {stats['total_added']}")
        print(f"Doublons ignorés: {stats['duplicates_skipped']}")
        print(f"\nPatterns uniques: {len(history['patterns'])}")
        
        print("\n📈 Répartition par langue:")
        for lang, count in stats["by_language"].items():
            print(f"  • {lang.capitalize():15} : {count:3} patterns")
        
        print("\n✅ Apprentissage forcé terminé!")
        print("="*70)
        
        return stats
    
    def train_specific_language(self, language: str, template_name: str = "Auto-learning") -> int:
        """
        Entraîne uniquement une langue spécifique
        
        Args:
            language: Langue à entraîner
            template_name: Nom du template
            
        Returns:
            Nombre de patterns ajoutés
        """
        if language not in self.TRAINING_PATTERNS:
            print(f"❌ Langue '{language}' non supportée")
            print(f"Langues disponibles: {list(self.TRAINING_PATTERNS.keys())}")
            return 0
        
        print(f"\n🎓 Entraînement: {language.capitalize()}")
        
        history = self.load_existing_history()
        patterns = self.TRAINING_PATTERNS[language]
        added = 0
        
        for source, target in patterns:
            source_key = self.normalize_key(source)
            
            # Vérifier existence
            exists = any(
                self.normalize_key(c["source"]) == source_key and
                self.normalize_key(c["target"]) == self.normalize_key(target)
                for c in history["corrections"]
            )
            
            if not exists:
                correction = {
                    "timestamp": datetime.now().isoformat(),
                    "source": source.lower().strip(),
                    "target": target.lower().strip(),
                    "template": template_name,
                    "confidence_before": 0.0,
                    "training": True,
                    "language": language
                }
                history["corrections"].append(correction)
                
                if source_key not in history["patterns"]:
                    history["patterns"][source_key] = []
                
                target_lower = target.lower().strip()
                if target_lower not in history["patterns"][source_key]:
                    history["patterns"][source_key].append(target_lower)
                
                added += 1
                print(f"  ✅ {source} → {target}")
        
        self.save_history(history)
        print(f"\n✓ {added} patterns ajoutés")
        
        return added
    
    def get_training_stats(self) -> Dict:
        """Obtient les statistiques de l'entraînement"""
        history = self.load_existing_history()
        
        total = len(history["corrections"])
        training_corrections = [c for c in history["corrections"] if c.get("training", False)]
        manual_corrections = [c for c in history["corrections"] if not c.get("training", False)]
        
        # Statistiques par langue
        by_language = {}
        for corr in training_corrections:
            lang = corr.get("language", "unknown")
            by_language[lang] = by_language.get(lang, 0) + 1
        
        return {
            "total_corrections": total,
            "training_corrections": len(training_corrections),
            "manual_corrections": len(manual_corrections),
            "unique_patterns": len(history["patterns"]),
            "by_language": by_language
        }
    
    def clear_training_data(self):
        """Efface uniquement les données d'entraînement, garde les corrections manuelles"""
        history = self.load_existing_history()
        
        # Garder uniquement les corrections manuelles
        manual_corrections = [c for c in history["corrections"] if not c.get("training", False)]
        
        print(f"❌ Suppression de {len(history['corrections']) - len(manual_corrections)} corrections d'entraînement")
        print(f"✓ Conservation de {len(manual_corrections)} corrections manuelles")
        
        # Reconstruire patterns uniquement avec corrections manuelles
        new_patterns = {}
        for corr in manual_corrections:
            source_key = self.normalize_key(corr["source"])
            if source_key not in new_patterns:
                new_patterns[source_key] = []
            target_lower = corr["target"].lower().strip()
            if target_lower not in new_patterns[source_key]:
                new_patterns[source_key].append(target_lower)
        
        new_history = {
            "corrections": manual_corrections,
            "patterns": new_patterns
        }
        
        self.save_history(new_history)
        print("✅ Nettoyage terminé")


def main():
    """Fonction principale pour exécuter l'entraînement"""
    import sys
    
    trainer = ForcedLearning()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "train":
            # Entraîner toutes les langues
            trainer.train_all_patterns()
        
        elif command == "stats":
            # Afficher statistiques
            stats = trainer.get_training_stats()
            print("\n📊 STATISTIQUES D'APPRENTISSAGE")
            print("="*60)
            print(f"Total corrections: {stats['total_corrections']}")
            print(f"  - Entraînement: {stats['training_corrections']}")
            print(f"  - Manuelles: {stats['manual_corrections']}")
            print(f"Patterns uniques: {stats['unique_patterns']}")
            print(f"\nPar langue:")
            for lang, count in stats['by_language'].items():
                print(f"  • {lang}: {count}")
        
        elif command == "clear":
            # Effacer données d'entraînement
            trainer.clear_training_data()
        
        elif command.startswith("train-"):
            # Entraîner langue spécifique
            language = command.split("-")[1]
            trainer.train_specific_language(language)
        
        else:
            print("Commandes disponibles:")
            print("  train         : Entraîner toutes les langues")
            print("  stats         : Afficher statistiques")
            print("  clear         : Effacer données d'entraînement")
            print("  train-<lang>  : Entraîner langue spécifique")
    else:
        # Par défaut: entraîner tout
        trainer.train_all_patterns()


if __name__ == "__main__":
    main()
