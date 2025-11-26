#!/bin/bash
# Script de déploiement sur Google Cloud Run

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 IA Excel Pro - Déploiement Cloud Run${NC}"
echo ""

# 1. Vérifier les prérequis
echo -e "${BLUE}1️⃣ Vérification des prérequis...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI non trouvé. Installer: https://cloud.google.com/sdk/docs/install${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker non trouvé. Installer: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

echo -e "${GREEN}✓ gcloud et Docker présents${NC}"

# 2. Authentifier
echo ""
echo -e "${BLUE}2️⃣ Configuration Google Cloud...${NC}"

PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Aucun projet Google Cloud configuré${NC}"
    echo "Exécute: gcloud init"
    exit 1
fi

echo -e "${GREEN}✓ Projet: $PROJECT_ID${NC}"

# 3. Vérifier les APIs
echo ""
echo -e "${BLUE}3️⃣ Activation des APIs...${NC}"

gcloud services enable cloudbuild.googleapis.com run.googleapis.com 2>/dev/null || true
echo -e "${GREEN}✓ APIs activées${NC}"

# 4. Build et push
echo ""
echo -e "${BLUE}4️⃣ Build de l'image Docker...${NC}"

IMAGE_TAG="gcr.io/$PROJECT_ID/ia-excel:latest"
docker build -t "$IMAGE_TAG" .

echo ""
echo -e "${BLUE}5️⃣ Push vers Container Registry...${NC}"
docker push "$IMAGE_TAG"

echo -e "${GREEN}✓ Image pushée: $IMAGE_TAG${NC}"

# 5. Déployer
echo ""
echo -e "${BLUE}6️⃣ Déploiement sur Cloud Run...${NC}"

gcloud run deploy ia-excel \
  --image "$IMAGE_TAG" \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 3600 \
  --set-env-vars "STREAMLIT_SERVER_HEADLESS=true" \
  --quiet

# 6. Obtenir l'URL
echo ""
echo -e "${BLUE}7️⃣ Récupération de l'URL...${NC}"

SERVICE_URL=$(gcloud run services describe ia-excel \
  --platform managed \
  --region europe-west1 \
  --format 'value(status.url)' 2>/dev/null || echo "")

if [ -z "$SERVICE_URL" ]; then
    echo -e "${RED}⚠️ Impossible de récupérer l'URL${NC}"
else
    echo -e "${GREEN}✓ URL: $SERVICE_URL${NC}"
fi

# 7. Résumé
echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Déploiement réussi!${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo "📊 Commandes utiles:"
echo "  • Voir les logs: gcloud logging read \"resource.type=cloud_run_revision\" --limit 50"
echo "  • Détails service: gcloud run services describe ia-excel --region europe-west1"
echo "  • Supprimer: gcloud run services delete ia-excel --region europe-west1"
echo ""
