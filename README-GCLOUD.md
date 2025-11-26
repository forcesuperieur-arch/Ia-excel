# Guide de Déploiement sur Google Cloud Run

## 📋 Prérequis

- Compte Google Cloud
- `gcloud` CLI installé et configuré
- Projet Google Cloud créé
- Accès à Cloud Run, Cloud Build, et Container Registry

## 🚀 Déploiement Manuel (Rapide)

### 1. Authentifier avec Google Cloud
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 2. Construire et déployer
```bash
gcloud run deploy ia-excel \
  --source . \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 3600
```

### 3. Configurer les secrets (si nécessaire)
```bash
gcloud run services update ia-excel \
  --set-env-vars "OPENAI_API_KEY=YOUR_KEY,SERPER_API_KEY=YOUR_KEY" \
  --region europe-west1
```

## 🔄 Déploiement Automatique (CI/CD)

### 1. Configurer Cloud Build
```bash
# Activer l'API Cloud Build
gcloud services enable cloudbuild.googleapis.com

# Donner les permissions au service account Cloud Build
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member=serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com \
  --role=roles/run.admin
```

### 2. Connecter le repo GitHub
```bash
gcloud builds connect --repository-name Ia-excel --repository-owner forcesuperieur-arch
```

### 3. Créer la trigger
```bash
gcloud builds triggers create github \
  --name ia-excel-trigger \
  --repo-name Ia-excel \
  --repo-owner forcesuperieur-arch \
  --branch-pattern "^main$" \
  --build-config cloudbuild.yaml
```

## 📊 Coûts estimés

- **Cloud Run**: ~$0.20/mois (1GB RAM, <100K requêtes/mois)
- **Container Registry**: ~$0.10/mois (stockage image)
- **Total estimé**: ~$0.30-0.50/mois

vs Streamlit Cloud: **Gratuit** (mais limité)

## ⚙️ Configuration Streamlit Cloud

Si tu veux rester sur Streamlit Cloud, ajoute dans `.streamlit/secrets.toml`:
```toml
[general]
OPENAI_API_KEY = "sk-..."
SERPER_API_KEY = "..."

[database]
DB_HOST = "your-supabase-host"
DB_PORT = "5432"
DB_NAME = "postgres"
DB_USER = "postgres.yourprojectid"
DB_PASSWORD = "your-password"
```

## 🔍 Debugging

### Voir les logs Cloud Run
```bash
gcloud run services describe ia-excel --region europe-west1
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ia-excel" --limit 50
```

### Test local avec Docker
```bash
docker build -t ia-excel:test .
docker run -p 8080:8080 \
  -e OPENAI_API_KEY="sk-..." \
  -e DB_HOST="..." \
  ia-excel:test
```

## 📝 Notes

- Cloud Run timeouts max: 3600s (1 heure)
- Mémoire recommandée: 1GB pour le matching complet
- CPU: 1 vCPU suffisant (peut être augmenté)
- Les instances démarrent en ~5-10s (vs 30-60s Streamlit Cloud)

## ❓ Troubleshooting

**Image trop grosse?**
- Utiliser Python 3.12-slim au lieu de 3.12-full
- Réduire sentence-transformers en n'incluant que le modèle utilisé

**OOM (Out of Memory)?**
- Augmenter `--memory` à 2Gi
- Vérifier les limites du chunking dans ai_matcher.py

**Timeout?**
- Augmenter `--timeout` jusqu'à 3600 (1h max)
- Vérifier les logs pour voir où ça s'arrête
