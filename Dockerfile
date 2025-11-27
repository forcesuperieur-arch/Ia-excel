# Utiliser une image Python légère
FROM python:3.12-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système (minimales pour PyTorch, psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements Cloud Run
COPY requirements-gcloud.txt .

# Installer les dépendances Python avec cache
RUN pip install --no-cache-dir -r requirements-gcloud.txt

# Copier le reste de l'application
COPY . .

# Créer un secrets.toml vide pour éviter les avertissements Streamlit sur Cloud Run
RUN mkdir -p /root/.streamlit && \
    echo "# Cloud Run: Secrets depuis variables d'environnement\nDUMMY = \"true\"" > /root/.streamlit/secrets.toml && \
    chmod 600 /root/.streamlit/secrets.toml

# Configuration Streamlit pour Cloud Run
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_CLIENT_TOOLBAR_MODE=minimal
ENV STREAMLIT_LOGGER_LEVEL=info

# Exposition du port
EXPOSE 8080

# Démarrer Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
