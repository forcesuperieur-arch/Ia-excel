"""
Module de normalisation intelligente des noms de colonnes
Gère les différences de langues, ponctuations et formats
"""
import re
import unicodedata
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher


class ColumnNormalizer:
    """Normalise les noms de colonnes pour faciliter le matching multi-langues"""
    
    # Dictionnaire de traduction multi-langues pour termes courants
    TRANSLATIONS = {
        # Identifiants / Références
        'reference': ['référence', 'ref', 'codigo', 'codice', 'code', 'item', 'sku', 'artikel', 'articolo', 'artigo', 'product_id', 'productid', 'artikel nr', 'art', 'art nr'],
        'barcode': ['code barre', 'ean', 'ean13', 'upc', 'gtin', 'barcode', 'codice a barre', 'codigo de barras', 'codebar'],
        'id': ['identifiant', 'identifier', 'identificador', 'identificatore', 'uid', 'uuid', 'id'],
        
        # Descriptions
        'label': ['libellé', 'libelle', 'nom', 'name', 'nome', 'nombre', 'bezeichnung', 'denominazione', 'title', 'titre', 'benaming'],
        'description': ['descriptif', 'descrizione', 'descripcion', 'beschreibung', 'descricao', 'desc', 'description', 'omschrijving'],
        
        # Prix
        'price': ['prix', 'prezzo', 'precio', 'preis', 'preco', 'cost', 'cout', 'costo', 'coste', 'custo', 'price', 'pris', 'hinta'],
        'price_ht': ['prix ht', 'prix public ht', 'ht public', 'price excl vat', 'prezzo netto', 'precio sin iva', 'preis netto', 'net price', 'excl vat', 'hors taxe', 'sans tva'],
        'price_ttc': ['prix ttc', 'prix public ttc', 'ttc public', 'price incl vat', 'prezzo lordo', 'precio con iva', 'preis brutto', 'gross price', 'incl vat', 'toutes taxes', 'avec tva', 'pubblico'],
        'purchase_price': ['prix achat', 'prix dachat', 'prix d achat', 'purchase price', 'buying price', 'prezzo acquisto', 'precio compra', 'einkaufspreis', 'prix fournisseur', 'acquisto'],
        'web_price': ['prix web', 'prix internet', 'web price', 'online price', 'prezzo web', 'precio web', 'prix en ligne', 'minimumprezzo web'],
        
        # Catégories / Classifications
        'category': ['catégorie', 'categorie', 'categoria', 'kategorie', 'rubrique', 'famille', 'family'],
        'subcategory': ['sous-catégorie', 'sous categorie', 'subcategoria', 'unterkategorie', 'sous-famille'],
        'brand': ['marque', 'marca', 'marke', 'brand', 'fabricant', 'manufacturer', 'fabbricante'],
        'model': ['modèle', 'modele', 'modello', 'modelo', 'modell'],
        
        # Caractéristiques produit
        'color': ['couleur', 'colore', 'color', 'farbe', 'cor', 'kleur', 'vari'],
        'size': ['taille', 'dimension', 'taglia', 'tamano', 'grosse', 'tamanho', 'maat', 'size'],
        'weight': ['poids', 'peso', 'gewicht', 'weight', 'gewicht'],
        'material': ['matière', 'matiere', 'matériau', 'materiau', 'material', 'materiale', 'stoff', 'materiaal'],
        
        # Stock / Quantité
        'stock': ['stock', 'inventaire', 'inventory', 'disponibilité', 'disponibilite', 'disponibile', 'disponible', 'verfugbar'],
        'quantity': ['quantité', 'quantite', 'quantita', 'cantidad', 'menge', 'quantidade', 'qty', 'qte'],
        
        # Images / Médias
        'image': ['image', 'immagine', 'imagen', 'bild', 'photo', 'foto', 'picture', 'pic', 'img', 'afbeelding'],
        'image_url': ['url image', 'lien image', 'image url', 'image link', 'link immagine', 'foto link'],
        
        # Dimensions / Poids
        'length': ['longueur', 'lunghezza', 'longitud', 'lange', 'comprimento'],
        'width': ['largeur', 'larghezza', 'anchura', 'breite', 'largura'],
        'height': ['hauteur', 'altezza', 'altura', 'hohe'],
        
        # Informations supplémentaires
        'supplier': ['fournisseur', 'fornitore', 'proveedor', 'lieferant', 'fornecedor', 'vendor'],
        'availability': ['disponibilité', 'disponibilite', 'disponibilita', 'disponibilidad', 'verfugbarkeit'],
        'delivery': ['livraison', 'délai', 'delai', 'consegna', 'entrega', 'lieferung', 'delivery time'],
    }
    
    # Mots à ignorer (articles, prépositions, etc.)
    STOPWORDS = {
        'de', 'du', 'des', 'le', 'la', 'les', 'un', 'une', 'di', 'del', 'della', 'il', 'lo', 'la',
        'el', 'los', 'las', 'der', 'die', 'das', 'the', 'a', 'an', 'of', 'for', 'in', 'on', 'at',
        'public', 'minimum', 'maximum', 'net', 'gross', 'total', 'base'
    }
    
    def __init__(self):
        """Initialise le normaliseur avec les dictionnaires inversés"""
        # Crée un dictionnaire inversé pour recherche rapide
        self.inverse_translations = {}
        for key, variations in self.TRANSLATIONS.items():
            for variation in variations:
                normalized = self._normalize(variation)
                if normalized not in self.inverse_translations:
                    self.inverse_translations[normalized] = []
                if key not in self.inverse_translations[normalized]:
                    self.inverse_translations[normalized].append(key)
    
    def _normalize(self, text: str) -> str:
        """
        Normalise un texte en retirant accents, ponctuation et en convertissant en minuscules
        
        Args:
            text: Texte à normaliser
            
        Returns:
            Texte normalisé
        """
        if not text:
            return ""
        
        # Convertir en minuscules
        text = text.lower().strip()
        
        # Retirer les accents
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
        
        # Remplacer la ponctuation par des espaces
        text = re.sub(r'[/_\-\.]', ' ', text)
        text = re.sub(r'[^\w\s]', '', text)
        
        # Normaliser les espaces multiples
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extrait les mots-clés pertinents d'un texte normalisé
        
        Args:
            text: Texte normalisé
            
        Returns:
            Liste de mots-clés sans stopwords
        """
        words = text.split()
        return [w for w in words if w not in self.STOPWORDS and len(w) > 1]
    
    def get_semantic_key(self, column_name: str) -> str:
        """
        Génère une clé sémantique pour une colonne
        
        Args:
            column_name: Nom de la colonne
            
        Returns:
            Clé sémantique standardisée
        """
        normalized = self._normalize(column_name)
        keywords = self._extract_keywords(normalized)
        
        # Chercher des correspondances dans le dictionnaire
        semantic_parts = []
        for keyword in keywords:
            if keyword in self.inverse_translations:
                semantic_parts.extend(self.inverse_translations[keyword])
            else:
                semantic_parts.append(keyword)
        
        return '_'.join(sorted(set(semantic_parts)))
    
    def similarity_score(self, col1: str, col2: str) -> float:
        """
        Calcule un score de similarité entre deux noms de colonnes
        
        Args:
            col1: Premier nom de colonne
            col2: Deuxième nom de colonne
            
        Returns:
            Score entre 0 et 1 (1 = identiques)
        """
        # Normalisation
        norm1 = self._normalize(col1)
        norm2 = self._normalize(col2)
        
        # Similarité directe
        direct_similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Similarité sémantique
        key1 = self.get_semantic_key(col1)
        key2 = self.get_semantic_key(col2)
        semantic_similarity = SequenceMatcher(None, key1, key2).ratio()
        
        # Similarité par mots-clés
        words1 = set(self._extract_keywords(norm1))
        words2 = set(self._extract_keywords(norm2))
        
        if words1 and words2:
            keyword_similarity = len(words1.intersection(words2)) / len(words1.union(words2))
        else:
            keyword_similarity = 0.0
        
        # Score pondéré
        return (
            0.3 * direct_similarity +
            0.4 * semantic_similarity +
            0.3 * keyword_similarity
        )
    
    def find_best_match(
        self, 
        source_column: str, 
        target_columns: List[str],
        min_score: float = 0.5
    ) -> Optional[Tuple[str, float]]:
        """
        Trouve la meilleure correspondance pour une colonne source
        
        Args:
            source_column: Nom de la colonne source
            target_columns: Liste des colonnes cibles possibles
            min_score: Score minimum requis
            
        Returns:
            Tuple (colonne_cible, score) ou None
        """
        best_match = None
        best_score = min_score
        
        for target in target_columns:
            score = self.similarity_score(source_column, target)
            if score > best_score:
                best_score = score
                best_match = target
        
        return (best_match, best_score) if best_match else None
    
    def create_mapping(
        self,
        source_columns: List[str],
        target_columns: List[str],
        min_score: float = 0.6
    ) -> Dict[str, Optional[str]]:
        """
        Crée un mapping complet entre colonnes sources et cibles
        
        Args:
            source_columns: Colonnes du catalogue fournisseur
            target_columns: Colonnes du template
            min_score: Score minimum pour valider un match
            
        Returns:
            Dict {colonne_source: colonne_cible ou None}
        """
        mapping = {}
        used_targets = set()
        
        # Première passe: matches exacts ou très proches
        for source in source_columns:
            match = self.find_best_match(source, target_columns, min_score=0.85)
            if match and match[0] not in used_targets:
                mapping[source] = match[0]
                used_targets.add(match[0])
        
        # Deuxième passe: matches avec score plus bas
        for source in source_columns:
            if source not in mapping:
                remaining_targets = [t for t in target_columns if t not in used_targets]
                match = self.find_best_match(source, remaining_targets, min_score=min_score)
                if match:
                    mapping[source] = match[0]
                    used_targets.add(match[0])
                else:
                    mapping[source] = None
        
        return mapping
    
    def explain_match(self, source: str, target: str) -> str:
        """
        Explique pourquoi deux colonnes ont été matchées
        
        Args:
            source: Colonne source
            target: Colonne cible
            
        Returns:
            Explication textuelle
        """
        score = self.similarity_score(source, target)
        norm_source = self._normalize(source)
        norm_target = self._normalize(target)
        
        key_source = self.get_semantic_key(source)
        key_target = self.get_semantic_key(target)
        
        words_source = set(self._extract_keywords(norm_source))
        words_target = set(self._extract_keywords(norm_target))
        common_words = words_source.intersection(words_target)
        
        explanation = f"Score: {score:.2%}\n"
        
        if common_words:
            explanation += f"Mots communs: {', '.join(common_words)}\n"
        
        if key_source == key_target:
            explanation += "Équivalence sémantique détectée\n"
        
        return explanation
