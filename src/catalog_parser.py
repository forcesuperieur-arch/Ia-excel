"""
Module pour parser et extraire les données des catalogues Excel fournisseurs
"""
import pandas as pd
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class CatalogParser:
    """Parse les catalogues Excel de fournisseurs avec structures variables"""
    
    def __init__(self, file_path: str):
        """
        Initialise le parser avec un fichier Excel
        
        Args:
            file_path: Chemin vers le fichier Excel du catalogue
        """
        self.file_path = Path(file_path)
        self.df: Optional[pd.DataFrame] = None
        self.headers: List[str] = []
        
    def load(self, sheet_name: Optional[str] = None, header_row: int = 0) -> bool:
        """
        Charge le fichier Excel
        
        Args:
            sheet_name: Nom de la feuille (première par défaut)
            header_row: Numéro de ligne des en-têtes (0 par défaut)
            
        Returns:
            True si chargement réussi
        """
        try:
            self.df = pd.read_excel(
                self.file_path,
                sheet_name=sheet_name or 0,
                header=header_row
            )
            self.headers = self.df.columns.tolist()
            
            # Nettoie les noms de colonnes
            self.df.columns = [str(col).strip() for col in self.df.columns]
            self.headers = self.df.columns.tolist()
            
            print(f"✓ Catalogue chargé: {len(self.df)} lignes, {len(self.headers)} colonnes")
            return True
            
        except Exception as e:
            print(f"✗ Erreur lors du chargement du catalogue: {e}")
            return False
    
    def get_headers(self) -> List[str]:
        """Retourne la liste des en-têtes de colonnes"""
        return self.headers
    
    def detect_header_row(self, max_rows: int = 10) -> int:
        """
        Détecte automatiquement la ligne d'en-têtes
        (utile pour les catalogues avec des en-têtes sur plusieurs lignes)
        
        Args:
            max_rows: Nombre maximum de lignes à analyser
            
        Returns:
            Numéro de ligne probable des en-têtes
        """
        try:
            # Charge sans en-tête pour analyser
            df_temp = pd.read_excel(self.file_path, header=None, nrows=max_rows)
            
            # Cherche la ligne avec le plus de cellules non vides et textuelles
            best_row = 0
            best_score = 0
            
            for i in range(min(max_rows, len(df_temp))):
                row = df_temp.iloc[i]
                # Score = nombre de cellules textuelles non vides
                score = sum(
                    1 for cell in row 
                    if pd.notna(cell) and isinstance(cell, str) and len(str(cell)) > 1
                )
                
                if score > best_score:
                    best_score = score
                    best_row = i
            
            print(f"Ligne d'en-têtes détectée: {best_row}")
            return best_row
            
        except Exception as e:
            print(f"Erreur détection en-têtes: {e}")
            return 0
    
    def extract_data(self, column_mapping: Dict[str, str]) -> pd.DataFrame:
        """
        Extrait les données selon le mapping de colonnes
        
        Args:
            column_mapping: Dict mappant colonne_cible -> colonne_source
            
        Returns:
            DataFrame avec les colonnes renommées
        """
        if self.df is None:
            raise ValueError("Aucun catalogue chargé. Utilisez load() d'abord.")
        
        # Inverse le mapping pour pandas rename
        rename_map = {v: k for k, v in column_mapping.items() if v is not None}
        
        # Sélectionne et renomme les colonnes
        available_cols = [col for col in rename_map.keys() if col in self.df.columns]
        
        extracted_df = self.df[available_cols].copy()
        extracted_df = extracted_df.rename(columns=rename_map)
        
        # Ajoute les colonnes manquantes avec None
        for target_col in column_mapping.keys():
            if target_col not in extracted_df.columns:
                extracted_df[target_col] = None
        
        print(f"✓ Données extraites: {len(extracted_df)} lignes, {len(extracted_df.columns)} colonnes")
        return extracted_df
    
    def get_sample_data(self, n_rows: int = 5) -> pd.DataFrame:
        """Retourne un échantillon des données pour preview"""
        if self.df is None:
            raise ValueError("Aucun catalogue chargé")
        return self.df.head(n_rows)
    
    def list_sheets(self) -> List[str]:
        """Liste toutes les feuilles du fichier Excel"""
        try:
            xl_file = pd.ExcelFile(self.file_path)
            return xl_file.sheet_names
        except Exception as e:
            print(f"Erreur lecture des feuilles: {e}")
            return []
