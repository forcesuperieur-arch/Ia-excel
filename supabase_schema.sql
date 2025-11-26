-- Schéma de base de données pour l'application IA Excel (Supabase / PostgreSQL)

-- 1. Cache SEO
CREATE TABLE IF NOT EXISTS cache_seo (
    hash TEXT PRIMARY KEY,
    reference TEXT,
    description TEXT,
    seo_title TEXT,
    meta_description TEXT,
    language TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. SEO Stats
CREATE TABLE IF NOT EXISTS seo_stats (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE,
    category TEXT,
    language TEXT,
    time_seconds REAL,
    word_count INTEGER,
    char_count INTEGER,
    from_cache BOOLEAN
);

-- 3. Learning Corrections (Historique)
CREATE TABLE IF NOT EXISTS learning_corrections (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE,
    source_column TEXT,
    target_column TEXT,
    template_name TEXT,
    confidence_before REAL
);

-- 4. Learning Patterns (Patterns uniques)
CREATE TABLE IF NOT EXISTS learning_patterns (
    source_key TEXT,
    target_column TEXT,
    frequency INTEGER DEFAULT 1,
    last_used TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source_key, target_column)
);

-- 5. Templates Config
CREATE TABLE IF NOT EXISTS templates (
    id TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,
    filename TEXT,
    original_name TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. App Settings (Branding, Config globale)
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
