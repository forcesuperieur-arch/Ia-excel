#!/bin/bash
# Script de déploiement Cloud Run pour IA Excel Pro

set -e

PROJECT_ID="potent-galaxy-479319-r7"
SERVICE_NAME="ia-excel"
REGION="europe-west1"

echo "🚀 Déploiement IA Excel Pro sur Cloud Run"
echo "════════════════════════════════════════════"
echo "Projet: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Région: $REGION"
echo ""

# 1. Vérifier authentification
echo "1️⃣ Vérification authentification..."
if ! gcloud auth list | grep -q ACTIVE; then
    echo "❌ Pas authentifié. Lance: gcloud auth login"
    exit 1
fi
echo "✓ Authentifié"

# 2. Vérifier projet
echo ""
echo "2️⃣ Configuration du projet..."
gcloud config set project $PROJECT_ID
echo "✓ Projet configuré"

# 3. Activer APIs
echo ""
echo "3️⃣ Activation des APIs..."
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com --quiet
echo "✓ APIs activées"

# 4. Déployer
echo ""
echo "4️⃣ Déploiement sur Cloud Run..."
echo "   (Cela peut prendre 2-5 minutes...)"
echo ""

gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --allow-unauthenticated \
  --set-env-vars "STREAMLIT_SERVER_HEADLESS=true"

# 5. Récupérer l'URL
echo ""
echo "5️⃣ Récupération de l'URL..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)' 2>/dev/null || echo "")

if [ -z "$SERVICE_URL" ]; then
    echo "⚠️ Impossible de récupérer l'URL"
else
    echo "✓ URL du service: $SERVICE_URL"
fi

# 6. Résumé
echo ""
echo "════════════════════════════════════════════"
echo "✅ DÉPLOIEMENT RÉUSSI!"
echo "════════════════════════════════════════════"
echo ""
echo "📊 Ressources:"
echo "  • Mémoire: 2GB"
echo "  • CPU: 2 vCPU"
echo "  • Timeout: 1h"
echo "  • Auto-scaling: activé"
echo ""
echo "🔗 Accès:"
if [ ! -z "$SERVICE_URL" ]; then
    echo "  → $SERVICE_URL"
fi
echo ""
echo "⚙️ Prochaines étapes:"
echo "  1. Configurer les secrets (clés API, DB):"
echo "     gcloud run services update $SERVICE_NAME \\"
echo "       --set-env-vars OPENAI_API_KEY=sk-...,SERPER_API_KEY=... \\"
echo "       --region $REGION"
echo ""
echo "  2. Consulter les logs:"
echo "     gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" --limit 50"
echo ""
echo "  3. Modifier la config:"
echo "     gcloud run services update $SERVICE_NAME --region $REGION [options]"
echo ""
