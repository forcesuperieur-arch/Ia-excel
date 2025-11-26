import os
import logging

import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gestionnaire de base de données PostgreSQL (Supabase) centralisé"""
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._init_connection_params()
            cls._instance._init_db()
        return cls._instance

    def _init_connection_params(self):
        """Initialise les paramètres de connexion depuis les secrets ou l'environnement"""
        self.dsn = None
        self.is_pgbouncer = False
        
        # 1. Essayer st.secrets (Streamlit Cloud)
        try:
            if "postgres" in st.secrets:
                self.dsn = st.secrets["postgres"]["url"]
            elif "SUPABASE_DB_URL" in st.secrets:
                self.dsn = st.secrets["SUPABASE_DB_URL"]
        except FileNotFoundError:
            pass
            
        # 2. Essayer les variables d'environnement
        if not self.dsn:
            self.dsn = os.getenv("POSTGRES_URL") or os.getenv("SUPABASE_DB_URL")
        
        # 3. Nettoyer l'URL si elle contient ?pgbouncer=true (non supporté par psycopg2)
        if self.dsn and "pgbouncer" in self.dsn:
            self.is_pgbouncer = True
            # Retirer le paramètre pgbouncer de l'URL
            if "?pgbouncer=true" in self.dsn:
                self.dsn = self.dsn.replace("?pgbouncer=true", "")
            elif "&pgbouncer=true" in self.dsn:
                self.dsn = self.dsn.replace("&pgbouncer=true", "")
            logger.info("🔄 Mode PgBouncer détecté")
            
        if not self.dsn:
            logger.warning("⚠️ Aucune configuration de base de données trouvée (Secrets/Env). L'application risque de ne pas fonctionner.")

    def get_connection(self):
        """Retourne une connexion à la base de données"""
        if not self.dsn:
            raise ValueError("Configuration de base de données manquante")
        
        try:
            # Connexion simple - PgBouncer gère le pooling côté serveur
            conn = psycopg2.connect(self.dsn)
            return conn
        except Exception as e:
            logger.error(f"❌ Erreur de connexion DB: {e}")
            raise e

    def _init_db(self):
        """Initialise le schéma de la base de données"""
        if not self.dsn:
            return

        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 1. Cache SEO
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_seo (
                    hash TEXT PRIMARY KEY,
                    reference TEXT,
                    description TEXT,
                    seo_title TEXT,
                    meta_description TEXT,
                    language TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 2. SEO Stats
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS seo_stats (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP WITH TIME ZONE,
                    category TEXT,
                    language TEXT,
                    time_seconds REAL,
                    word_count INTEGER,
                    char_count INTEGER,
                    from_cache BOOLEAN
                )
            """)
            
            # 3. Learning Corrections (Historique)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_corrections (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP WITH TIME ZONE,
                    source_column TEXT,
                    target_column TEXT,
                    template_name TEXT,
                    confidence_before REAL
                )
            """)
            
            # 4. Learning Patterns (Patterns uniques)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_patterns (
                    source_key TEXT,
                    target_column TEXT,
                    frequency INTEGER DEFAULT 1,
                    last_used TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (source_key, target_column)
                )
            """)
            
            # 5. Templates Config
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    filename TEXT,
                    original_name TEXT,
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 6. App Settings (Branding, Config globale)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("✅ Base de données initialisée (PostgreSQL/Supabase)")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation DB: {e}")

    def _translate_query(self, query: str) -> str:
        """Convertit la syntaxe SQLite (?) vers PostgreSQL (%s)"""
        return query.replace('?', '%s')

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Exécute une requête de lecture"""
        conn = self.get_connection()
        try:
            # Utiliser RealDictCursor pour avoir des résultats comme des dictionnaires
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Traduction de la requête
            pg_query = self._translate_query(query)
            
            cursor.execute(pg_query, params)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Erreur requête lecture: {e}")
            # En cas d'erreur (table vide ou autre), retourner liste vide
            return []
        finally:
            conn.close()

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Exécute une requête d'écriture (INSERT, UPDATE, DELETE)"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Traduction de la requête
            pg_query = self._translate_query(query)
            
            cursor.execute(pg_query, params)
            conn.commit()
            
            # Retourner l'ID inséré si disponible (nécessite RETURNING id dans la requête PG)
            # ou le nombre de lignes affectées
            return cursor.rowcount
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Erreur requête écriture: {e}")
            raise e
        finally:
            conn.close()
