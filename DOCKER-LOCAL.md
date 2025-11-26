# Test Local avec Docker

## 🐳 Build et Run

### 1. Construire l'image
```bash
docker build -t ia-excel:local .
```

### 2. Créer un fichier .env local
```bash
cat > .env.docker << 'EOF'
OPENAI_API_KEY=sk-...
SERPER_API_KEY=...
DB_HOST=aws-0-eu-west-1.pooler.supabase.com
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres.yourprojectid
DB_PASSWORD=your-password
EOF
```

### 3. Lancer le container
```bash
docker run -it --rm \
  -p 8080:8080 \
  --env-file .env.docker \
  -v $(pwd)/catalogues:/app/catalogues \
  -v $(pwd)/templates:/app/templates \
  ia-excel:local
```

### 4. Accéder à l'app
```
http://localhost:8080
```

## 📊 Monitoring

### Voir les logs du container
```bash
docker logs -f <container_id>
```

### Stats du container
```bash
docker stats <container_id>
```

## 🧹 Nettoyage

```bash
# Arrêter le container
docker stop <container_id>

# Supprimer l'image
docker rmi ia-excel:local

# Nettoyer les ressources non utilisées
docker system prune
```

## 📝 Comparaison Streamlit Cloud vs Docker

| Aspect | Streamlit Cloud | Docker Local | Cloud Run |
|--------|-----------------|--------------|-----------|
| Setup | 1 min (git push) | 5 min | 10 min |
| Mémoire | 512MB | Configurable | 1-4GB |
| Timeout | 1h | Illimité | 1h |
| Coût | Gratuit | Local | $0.30-0.50/mois |
| Cold start | 30-60s | Rapide | 5-10s |

## ⚠️ Notes

- Les volumes Docker (`-v`) permettent de conserver les fichiers entre les redémarrages
- Streamlit Cloud rechargé à chaque sauvegarde (hot reload) - à désactiver pour la prod avec `runOnSave=false`
- Sur Docker, tu dois relancer le container pour voir les changements
