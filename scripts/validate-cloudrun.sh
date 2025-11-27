#!/bin/bash
# Script de validation pour Cloud Run
# Vérifie tous les éléments critiques avant déploiement

echo "🔍 VALIDATION CLOUD RUN - IA EXCEL"
echo "===================================="
echo ""

fail_count=0
pass_count=0

# 1. DÉPENDANCES
echo "1️⃣ DÉPENDANCES"
echo "==============="
[ -f requirements-gcloud.txt ] && echo "✓ requirements-gcloud.txt" && ((pass_count++)) || echo "✗ requirements-gcloud.txt" && ((fail_count++))
[ -f requirements.txt ] && echo "✓ requirements.txt" && ((pass_count++)) || echo "✗ requirements.txt" && ((fail_count++))
grep -q '==' requirements-gcloud.txt && echo "✓ Versions spécifiées" && ((pass_count++)) || echo "✗ Versions spécifiées" && ((fail_count++))
echo ""

# 2. FICHIERS CRITIQUES
echo "2️⃣ FICHIERS CRITIQUES"
echo "======================"
[ -f app.py ] && echo "✓ app.py" && ((pass_count++)) || echo "✗ app.py" && ((fail_count++))
[ -f src/__init__.py ] && echo "✓ src/__init__.py" && ((pass_count++)) || echo "✗ src/__init__.py" && ((fail_count++))
[ -f Dockerfile ] && echo "✓ Dockerfile" && ((pass_count++)) || echo "✗ Dockerfile" && ((fail_count++))
[ -f .dockerignore ] && echo "✓ .dockerignore" && ((pass_count++)) || echo "✗ .dockerignore" && ((fail_count++))
[ -f .streamlit/config.toml ] && echo "✓ .streamlit/config.toml" && ((pass_count++)) || echo "✗ .streamlit/config.toml" && ((fail_count++))
[ -f .streamlit/secrets.toml ] && echo "✓ .streamlit/secrets.toml" && ((pass_count++)) || echo "✗ .streamlit/secrets.toml" && ((fail_count++))
[ -f cloudbuild.yaml ] && echo "✓ cloudbuild.yaml" && ((pass_count++)) || echo "✗ cloudbuild.yaml" && ((fail_count++))
echo ""

# 3. SYNTAXE PYTHON
echo "3️⃣ SYNTAXE PYTHON"
echo "=================="
python3 -m py_compile app.py 2>/dev/null && echo "✓ app.py syntaxe" && ((pass_count++)) || echo "✗ app.py syntaxe" && ((fail_count++))
python3 -m py_compile src/ui_components.py 2>/dev/null && echo "✓ ui_components.py" && ((pass_count++)) || echo "✗ ui_components.py" && ((fail_count++))
python3 -m py_compile src/ai_matcher.py 2>/dev/null && echo "✓ ai_matcher.py" && ((pass_count++)) || echo "✗ ai_matcher.py" && ((fail_count++))
python3 -m py_compile src/ai_client_factory.py 2>/dev/null && echo "✓ ai_client_factory.py" && ((pass_count++)) || echo "✗ ai_client_factory.py" && ((fail_count++))
echo ""

# 4. CONFIGURATION
echo "4️⃣ CONFIGURATION"
echo "================"
grep -q 'requirements-gcloud.txt' Dockerfile && echo "✓ Dockerfile use gcloud requirements" && ((pass_count++)) || echo "✗ Dockerfile should use gcloud requirements" && ((fail_count++))
grep -q '8080' Dockerfile && echo "✓ Dockerfile port 8080" && ((pass_count++)) || echo "✗ Dockerfile port 8080" && ((fail_count++))
grep -q 'STREAMLIT_SERVER_HEADLESS=true' Dockerfile && echo "✓ HEADLESS mode" && ((pass_count++)) || echo "✗ HEADLESS mode" && ((fail_count++))
grep -q 'showErrorDetails = false' .streamlit/config.toml && echo "✓ Streamlit errors disabled" && ((pass_count++)) || echo "✗ Streamlit errors disabled" && ((fail_count++))
echo ""

# 5. SECRETS
echo "5️⃣ SECRETS & ENV VARS"
echo "====================="
grep -q 'if key in os.environ:' src/ui_components.py && echo "✓ ui_components _get_secret correct" && ((pass_count++)) || echo "✗ ui_components _get_secret" && ((fail_count++))
grep -q 'if key in os.environ:' src/openai_client.py && echo "✓ openai_client _get_secret correct" && ((pass_count++)) || echo "✗ openai_client _get_secret" && ((fail_count++))
grep -q 'if key in os.environ:' src/web_search.py && echo "✓ web_search _get_secret correct" && ((pass_count++)) || echo "✗ web_search _get_secret" && ((fail_count++))
grep -q 'if key in os.environ:' src/ai_client_factory.py && echo "✓ ai_client_factory _get_secret correct" && ((pass_count++)) || echo "✗ ai_client_factory _get_secret" && ((fail_count++))
echo ""

# RÉSUMÉ
echo "📊 RÉSUMÉ"
echo "========="
total=$((pass_count + fail_count))
echo "Réussis: $pass_count/$total"
echo "Échoués: $fail_count/$total"
echo ""

if [ $fail_count -eq 0 ]; then
    echo "✓ PRÊT POUR CLOUD RUN !"
    exit 0
else
    echo "✗ PROBLÈMES DÉTECTÉS"
    exit 1
fi
