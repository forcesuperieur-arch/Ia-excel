"""
Configuration centralisée du logging pour l'application Ia-Excel
Support: fichier local, PostgreSQL, console avec rotation
"""
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
import json

class LoggerConfig:
    """Gestionnaire centralisé des logs avec support multi-backends"""
    
    _instance = None
    LOG_DIR = Path("logs")
    LOG_FILE = LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerConfig, cls).__new__(cls)
            cls._instance._setup_logging()
        return cls._instance
    
    def _setup_logging(self):
        """Configure le logging avec rotation et formatage professionnel"""
        self.LOG_DIR.mkdir(exist_ok=True)
        
        # Supprimer les logs DEBUG inutiles de libraries tierces
        logging.getLogger("watchdog").setLevel(logging.WARNING)
        logging.getLogger("streamlit").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        
        # Format détaillé pour les fichiers
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Format simple pour la console
        console_formatter = logging.Formatter(
            '%(levelname)s - %(name)s - %(message)s'
        )
        
        # Handler fichier avec rotation (max 10MB par fichier, 7 fichiers)
        file_handler = logging.handlers.RotatingFileHandler(
            self.LOG_FILE,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=7
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.INFO)  # INFO seulement (pas DEBUG)
        
        # Handler console (seulement INFO et plus)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        
        # Logger root
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)  # INFO seulement
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Log de démarrage
        root_logger.info("=" * 80)
        root_logger.info(f"🚀 Application démarrée - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        root_logger.info(f"📁 Logs: {self.LOG_FILE}")
        root_logger.info("=" * 80)
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """Obtient un logger nommé"""
        return logging.getLogger(name)
    
    @staticmethod
    def log_user_action(user_id: str, action: str, details: dict = None):
        """Log une action utilisateur avec contexte"""
        logger = logging.getLogger("USER_ACTIONS")
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'action': action,
            'details': details or {}
        }
        logger.info(json.dumps(log_entry, ensure_ascii=False))
    
    @staticmethod
    def log_performance(function_name: str, duration_seconds: float, success: bool, details: dict = None):
        """Log les métriques de performance"""
        logger = logging.getLogger("PERFORMANCE")
        status = "✅ SUCCESS" if success else "❌ FAILED"
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'function': function_name,
            'duration_seconds': duration_seconds,
            'status': status,
            'details': details or {}
        }
        logger.info(json.dumps(log_entry, ensure_ascii=False))
    
    @staticmethod
    def log_cache_hit(cache_key: str, source: str = "unknown"):
        """Log un hit de cache"""
        logger = logging.getLogger("CACHE")
        logger.debug(f"✅ CACHE HIT: {cache_key} (source: {source})")
    
    @staticmethod
    def log_cache_miss(cache_key: str):
        """Log un miss de cache"""
        logger = logging.getLogger("CACHE")
        logger.debug(f"❌ CACHE MISS: {cache_key}")
    
    @staticmethod
    def log_database_query(query: str, duration_ms: float, rows_affected: int = 0):
        """Log les requêtes base de données"""
        logger = logging.getLogger("DATABASE")
        logger.debug(f"📊 Query ({duration_ms:.2f}ms, {rows_affected} rows): {query[:100]}...")
    
    @staticmethod
    def log_api_call(provider: str, model: str, tokens_in: int, tokens_out: int, duration_seconds: float):
        """Log les appels API IA"""
        logger = logging.getLogger("API_CALLS")
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'provider': provider,
            'model': model,
            'tokens_in': tokens_in,
            'tokens_out': tokens_out,
            'duration_seconds': duration_seconds
        }
        logger.info(json.dumps(log_entry, ensure_ascii=False))
    
    @staticmethod
    def log_error(error_type: str, message: str, traceback_str: str = None, context: dict = None):
        """Log une erreur avec contexte complet"""
        logger = logging.getLogger("ERRORS")
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'message': message,
            'context': context or {},
            'traceback': traceback_str
        }
        logger.error(json.dumps(error_entry, ensure_ascii=False))
    
    @staticmethod
    def get_logs_summary(limit: int = 100) -> list:
        """Récupère les derniers logs (pour UI Streamlit)"""
        try:
            with open(LoggerConfig.LOG_FILE, 'r') as f:
                lines = f.readlines()
                return lines[-limit:]
        except:
            return []


# Instance globale
logger_config = LoggerConfig()
