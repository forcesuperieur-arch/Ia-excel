# 🚀 Migration Google Cloud Run - STATUS

## ✅ Fichiers Préparés (Prêts à déployer)

```
Dockerfile                  ← Image Docker optimisée pour Cloud Run
.dockerignore              ← Fichiers à exclure du build
requirements-gcloud.txt    ← Dépendances pinées (versions exactes)
cloudbuild.yaml            ← CI/CD automatique (GitHub → Cloud Run)
.streamlit/config.toml     ← Config Streamlit produit
deploy-gcloud.sh           ← Script helper de déploiement
README-GCLOUD.md           ← Guide complet de déploiement
DOCKER-LOCAL.md            ← Guide test local Docker
```

## 🎯 État Actuel

**Streamlit Cloud**: En test avec optimisations matching
**Cloud Run**: ✅ Prêt à l'emploi (attente pour upload)

## 📊 Comparaison

| | Streamlit Cloud | Cloud Run |
|---|---|---|
| **Coût** | Gratuit | ~$0.30-0.50/mois |
| **Mémoire** | 512MB (limité) | 1GB configurable |
| **Timeout** | 1h | 1h (configurable) |
| **Démarrage** | 30-60s | 5-10s |
| **CI/CD** | Automatique | Automatique ✓ |
| **Scaling** | Non | Auto-scale ✓ |
| **Uptime** | 99.7% | 99.95% ✓ |

## 🚀 Déploiement Rapide (Quand tu es prêt)

### Option 1: Script automatique
```bash
./deploy-gcloud.sh
```

### Option 2: Manuel
```bash
gcloud run deploy ia-excel \
  --source . \
  --platform managed \
  --region europe-west1 \
  --memory 1Gi
```

## ⏳ Prochaines étapes

1. **Attendre résultats Streamlit Cloud** - Si matching <30s → OK, rester sur Streamlit
2. **Si Streamlit freeze** → Déployer sur Cloud Run avec les fichiers préparés
3. **Paramétrer les secrets** - OpenAI key, Supabase credentials via gcloud

## 📝 Notes

- ✅ Dockerfile optimisé pour Python 3.12
- ✅ Requirements-gcloud.txt = versions stables
- ✅ CloudBuild.yaml = push to deploy automatique
- ✅ Scripts et docs complètes

**Ne rien faire jusque-là - attendre résultats test!** 🔄
