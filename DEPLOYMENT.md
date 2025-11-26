# 🚀 DÉPLOIEMENT CLOUD RUN - INSTRUCTIONS

## Status: ✅ PRÊT À DÉPLOYER

Le projet Cloud Run est entièrement préparé. Tu dois exécuter le déploiement **depuis ta machine locale** avec tes identifiants Google Cloud.

## 📋 Prérequis

1. **Google Cloud CLI** installé: https://cloud.google.com/sdk/docs/install
2. **Compte Google Cloud** authentifié
3. **Projet**: `potent-galaxy-479319-r7` (déjà configuré)

## 🚀 Déployer en 3 commandes

```bash
# 1. Clone le repo
git clone https://github.com/forcesuperieur-arch/Ia-excel.git
cd Ia-excel

# 2. Authentifier Google Cloud
gcloud auth login

# 3. Lancer le déploiement
bash deploy-cloud-run.sh
```

**C'est tout!** ✨ Le script va:
- Activer les APIs nécessaires
- Construire l'image Docker
- Déployer le service
- Afficher l'URL d'accès

## 📊 Ressources Déployées

- **Mémoire**: 2GB (vs 512MB Streamlit Cloud)
- **CPU**: 2 vCPU (permet le batch encoding)
- **Timeout**: 1h max
- **Auto-scaling**: Activé (scale de 0 à N instances)
- **Région**: Europe West 1 (Belgique)
- **Coût**: ~$0.60-1.00/mois

## ⚙️ Après Déploiement: Configurer les Secrets

```bash
gcloud run services update ia-excel \
  --set-env-vars \
    "OPENAI_API_KEY=sk-...,SERPER_API_KEY=...,DB_HOST=...,DB_USER=...,DB_PASSWORD=..." \
  --region europe-west1
```

## 🔍 Commandes Utiles

```bash
# Voir l'URL du service
gcloud run services describe ia-excel --region europe-west1 --format 'value(status.url)'

# Voir les logs en temps réel
gcloud logging read "resource.labels.service_name=ia-excel" --limit 50 --follow

# Redéployer (mise à jour)
gcloud run deploy ia-excel --source . --region europe-west1 --allow-unauthenticated

# Augmenter la mémoire si OOM
gcloud run services update ia-excel --memory 4Gi --region europe-west1
```

## 📁 Fichiers Déploiement

```
Dockerfile              ← Image Docker Python 3.12-slim
.dockerignore          ← Exclusions pour build léger
deploy-cloud-run.sh    ← Script déploiement (appelle gcloud)
cloudbuild.yaml        ← CI/CD optionnel (GitHub → auto-deploy)
requirements.txt       ← Dépendances Python
```

## ❓ Troubleshooting

### "You do not currently have an active account"
```bash
gcloud auth login
# Puis accepter les permissions
```

### "Permission denied" sur Cloud Run
```bash
gcloud projects add-iam-policy-binding potent-galaxy-479319-r7 \
  --member=user:TON_EMAIL@gmail.com \
  --role=roles/run.admin
```

### Out of Memory (OOM)?
L'app utilise du **matching prioritaire** - elle traite d'abord les colonnes critiques (ref, desc, prix) puis les optionnelles. Si OOM:
```bash
gcloud run services update ia-excel --memory 4Gi --region europe-west1
```

### Logs d'erreur?
```bash
gcloud logging read "resource.labels.service_name=ia-excel" --limit 100 --format json
```

## 📞 Support

- Cloud Run Docs: https://cloud.google.com/run/docs
- Console Google Cloud: https://console.cloud.google.com/
- Monitoring: https://console.cloud.google.com/run

**Prêt à déployer? Lance `bash deploy-cloud-run.sh`!** 🚀
