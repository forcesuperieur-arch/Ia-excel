# IA Excel - Traitement Intelligent de Catalogues + Génération SEO

Outil d'automatisation pour traiter des catalogues Excel fournisseurs avec structures variables, en utilisant l'IA locale (Ollama) ou OpenAI GPT-4o pour identifier automatiquement les colonnes et générer des descriptions produits SEO-optimisées.

## 🎯 Fonctionnalités

### 📋 Traitement de catalogues
- ✅ **Parsing intelligent** : Détection automatique des en-têtes de colonnes
- 🎓 **Matching automatique** : 90% de réussite sans API grâce à l'apprentissage forcé (173 patterns)
- 🌍 **Multi-langue** : Support de 7 langues (FR, IT, ES, EN, DE, PT, NL)
- 🤖 **IA en option** : OpenAI GPT-4o ou Ollama local pour cas complexes
- 📊 **Génération Excel** : Création de fichiers formatés avec tables matricielles
- 📈 **Rapports** : Feuilles de résumé et mapping des colonnes

### 🎨 Génération de descriptions SEO (NOUVEAU)
- ✨ **Descriptions produits** : Textes SEO-optimisés de 150-200 mots
- 🏷️ **Titres SEO** : Optimisés pour Google (60 caractères)
- 📝 **Meta descriptions** : Snippets attractifs (160 caractères)
- 🌐 **Multi-langue** : FR, IT, ES, EN, DE
- 🆓 **Gratuit** : Utilise Ollama (IA locale)
- 🎯 **Motoblouz-ready** : Templates adaptés à l'équipement moto
- ⚡ **Batch** : Traitement de catalogues entiers

## 📁 Structure du projet

```
Ia-excel/
├── src/
│   ├── ai_matcher.py                    # Matching IA hybride (OpenAI/local)
│   ├── catalog_parser.py                # Parser de catalogues Excel
│   ├── column_normalizer.py             # Normalisation multi-langue
│   ├── forced_learning.py               # Apprentissage forcé (173 patterns)
│   ├── matching_learning.py             # Historique d'apprentissage
│   ├── matrix_generator.py              # Générateur Excel formaté
│   ├── template_manager.py              # Gestion templates
│   ├── template_injector.py             # Injection données dans templates
│   ├── ollama_client.py                 # 🆕 Client IA locale Ollama
│   └── product_description_generator.py # 🆕 Générateur descriptions SEO
├── catalogues/                          # 📥 Placez vos catalogues ici
├── output/                              # 📤 Fichiers générés
├── templates/                           # 📋 Templates Excel + config
├── main.py                              # Script principal (CLI)
├── app.py                               # Interface web Streamlit
├── train_ia.py                          # 🎓 Entraînement du système
├── generate_descriptions.py             # 🆕 Génération batch descriptions SEO
├── requirements.txt                     # Dépendances Python
├── README.md                            # Ce fichier
├── APPRENTISSAGE_FORCE.md               # 📖 Doc apprentissage forcé
├── MATCHING_MULTILANGUE.md              # 📖 Doc système multi-langue
├── GENERATION_DESCRIPTIONS.md           # 🆕 📖 Doc génération SEO
└── .env.example                         # Template configuration
```

## 🚀 Installation

### 1. Créer l'environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configuration (optionnelle)

#### Option A : Utiliser le système SANS API (recommandé)

Le système fonctionne à **90% de réussite** sans aucune clé API grâce à l'apprentissage forcé (173 patterns multi-langues).

✅ **Aucune configuration nécessaire - prêt à l'emploi !**

#### Option B : Ajouter OpenAI pour cas complexes

Si vous avez une clé OpenAI, créez un fichier `.env` :

```bash
cp .env.example .env
```

Éditez `.env` :

```env
OPENAI_API_KEY=sk-votre-cle-api-ici
OPENAI_MODEL=gpt-4o
```

> 💡 Obtenez votre clé API sur : https://platform.openai.com/api-keys

#### Option C : Installer Ollama pour IA locale + génération SEO

**Ollama** est une IA locale gratuite pour le matching avancé et la génération de descriptions SEO.

```bash
# 1. Installer Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Télécharger un modèle (recommandé: qwen2.5:3b)
ollama pull qwen2.5:3b

# 3. Démarrer Ollama
ollama serve
```

> 📖 **Guide complet** : Voir [GENERATION_DESCRIPTIONS.md](GENERATION_DESCRIPTIONS.md)

### 4. Tester l'installation

```bash
# Test du système de matching (sans API)
python -c "from src.matching_learning import test_learning; test_learning()"

# Test d'Ollama (si installé)
python -c "from src.ollama_client import test_ollama; test_ollama()"
```

## 📖 Utilisation

### 🎯 Workflow complet

```bash
# ÉTAPE 1 : Traiter un catalogue (matching colonnes)
streamlit run app.py
# → Upload → Mapping automatique (90%) → Export Excel

# ÉTAPE 2 : Générer descriptions SEO (optionnel, nécessite Ollama)
python generate_descriptions.py catalogues/mon_catalogue.xlsx -o catalogue_avec_seo.xlsx
# → Descriptions produits optimisées pour Motoblouz
```

### 📱 Interface Web (recommandée) 🌐

Lancez l'application web avec un design moderne :

```bash
streamlit run app.py
```

L'interface s'ouvrira automatiquement dans votre navigateur avec :
- 📤 Upload drag & drop de fichiers
- ⚙️ Configuration interactive (templates, colonnes cibles)
- 🎯 **Matching automatique** : 90% de réussite sans API
- 📊 Visualisation en temps réel des résultats
- 💾 Téléchargement Excel et CSV
- 📈 Métriques et statistiques de matching
- 🎨 **Option génération SEO** (si Ollama installé)

### 💻 Génération descriptions SEO (CLI)

```bash
# Catalogue complet en français
python generate_descriptions.py catalogues/produits.xlsx -o produits_seo.xlsx

# Catalogue en italien
python generate_descriptions.py catalogues/produits.xlsx -o produits_it.xlsx -l it

# Mode test (5 produits) avec prévisualisation
python generate_descriptions.py catalogues/test.xlsx -o test.xlsx --limit 5 --preview

# Sortie CSV en espagnol
python generate_descriptions.py catalogues/produits.xlsx -o produits_es.csv -l es
```

> 📖 **Guide complet génération SEO** : [GENERATION_DESCRIPTIONS.md](GENERATION_DESCRIPTIONS.md)

### ⚙️ Ligne de commande (matching)

```bash
python main.py catalogues/votre_catalogue.xlsx
```

### Spécifier le fichier de sortie

```bash
python main.py catalogues/fournisseur_A.xlsx output/resultat_A.xlsx
```

### 🎓 Entraîner le système

Le système possède déjà 173 patterns, mais vous pouvez en ajouter :

```bash
python train_ia.py
```

Menu interactif :
1. Entraîner tous les patterns (150 patterns multi-langues)
2. Entraîner une langue spécifique
3. Voir les statistiques
4. Tester le système
5. Effacer les données
6. Sauvegarder un rapport

> 📖 **Guide apprentissage forcé** : [APPRENTISSAGE_FORCE.md](APPRENTISSAGE_FORCE.md)

### Exemple complet

```bash
# 1. Placez votre catalogue dans le dossier catalogues/
cp ~/Downloads/catalogue_fournisseur.xlsx catalogues/

# 2. Lancez le traitement (interface web)
streamlit run app.py

# OU en ligne de commande
python main.py catalogues/catalogue_fournisseur.xlsx

# 3. Générez les descriptions SEO (optionnel)
python generate_descriptions.py output/catalogue_traite.xlsx -o catalogue_final.xlsx

# 4. Récupérez le résultat dans output/
```

## 🎛️ Personnalisation

### Modifier les colonnes cibles

Éditez `main.py`, ligne 12 :

```python
TARGET_COLUMNS = [
    "référence",
    "désignation",
    "prix_unitaire",
    "quantité",
    "unité",
    "famille",
    "fournisseur"
]
```

### Ajuster le seuil de confiance

Dans `main.py`, ligne 66 :

```python
column_mapping = matcher.get_column_mapping_with_confidence(
    column_headers=headers,
    target_columns=target_columns,
    min_confidence=0.6  # Ajustez entre 0.0 et 1.0
)
```

## 📊 Format de sortie

Le fichier Excel généré contient :

1. **Feuille "Résumé"** : Statistiques du traitement
2. **Feuille "Mapping colonnes"** : Correspondances détectées avec scores de confiance
3. **Feuille "Catalogue"** : Données extraites et formatées

## 🔧 Utilisation programmatique

```python
from src.catalog_parser import CatalogParser
from src.ai_matcher import ColumnMatcher
from src.matrix_generator import MatrixGenerator

# Parser le catalogue
parser = CatalogParser("mon_catalogue.xlsx")
parser.load()

# Matcher les colonnes
matcher = ColumnMatcher()
mapping = matcher.identify_columns(
    parser.get_headers(),
    ["référence", "prix", "description"]
)

# Extraire et générer
df = parser.extract_data(mapping)
MatrixGenerator.create_matrix_excel(df, "output.xlsx")
```

## 🛠️ Dépannage

### Matching de colonnes

#### ✅ Le système fonctionne SANS API

Si vous voyez un message d'erreur API, **pas de panique** ! Le système utilise l'apprentissage forcé qui fonctionne parfaitement sans clé OpenAI.

#### Colonnes non détectées

→ Le système a un taux de 90% de réussite automatique  
→ Les 10% restants peuvent être mappés manuellement dans l'interface Streamlit  
→ Pour améliorer : utilisez `python train_ia.py` pour ajouter des patterns

#### Erreur d'API OpenAI (si vous utilisez OpenAI)

```
Error: Incorrect API key provided
```

→ Vérifiez que votre clé est correcte dans `.env`  
→ OU utilisez le système sans API (90% de réussite)

### Génération de descriptions SEO

#### Ollama non disponible

```bash
# Vérifier qu'Ollama tourne
ollama list

# Redémarrer Ollama
ollama serve

# Réinstaller un modèle
ollama pull qwen2.5:3b
```

#### Descriptions trop courtes/longues

Éditez `src/product_description_generator.py` :
```python
max_tokens=400  # Augmentez ou réduisez (ligne 287)
```

#### Génération trop lente

```bash
# Utilisez un modèle plus léger
ollama pull qwen2.5:3b  # Le plus rapide (recommandé)
```

### Fichier Excel corrompu

→ Essayez d'ouvrir et resauvegarder le fichier dans Excel  
→ Vérifiez le paramètre `header_row` si les en-têtes ne sont pas en ligne 1

## 💰 Coûts

### Système de matching (catalogues)

**100% GRATUIT** - Le système fonctionne sans API grâce à :
- 🎓 Apprentissage forcé : 173 patterns pré-entraînés
- 🔤 Normalisation sémantique : 150+ synonymes multi-langues
- ✅ **90% de réussite** sans aucun coût

**OpenAI (optionnel)** - Pour les 10% de cas complexes :
- Petits catalogues (< 20 colonnes) : ~$0.001 - $0.005
- Grands catalogues (> 50 colonnes) : ~$0.01 - $0.02
- Modèle utilisé : GPT-4o (optimisé coût/performance)

### Génération descriptions SEO

**100% GRATUIT avec Ollama** - IA locale :
- ✅ Installation gratuite
- ✅ Aucun coût par description
- ✅ Génération illimitée
- ⚡ Rapide : 3-5s par description (qwen2.5:3b)
- 💾 Ressources : 2GB RAM + 2GB disque

**Estimation catalogues** :
- 100 produits : ~5-10 minutes
- 1000 produits : ~50-90 minutes
- Aucun coût quel que soit le volume

## 📚 Documentation

- 📖 **[APPRENTISSAGE_FORCE.md](APPRENTISSAGE_FORCE.md)** - Système d'apprentissage forcé (173 patterns)
- 📖 **[MATCHING_MULTILANGUE.md](MATCHING_MULTILANGUE.md)** - Normalisation multi-langue (7 langues)
- 📖 **[GENERATION_DESCRIPTIONS.md](GENERATION_DESCRIPTIONS.md)** - Génération descriptions SEO avec Ollama
- 📖 **[RAPPORT_TEST.md](RAPPORT_TEST.md)** - Tests et validations du système
- 📖 **[GUIDE_UTILISATION.md](GUIDE_UTILISATION.md)** - Guide d'utilisation détaillé

## 🎯 Performances

### Matching de colonnes

| Méthode | Taux de réussite | Vitesse | Coût |
|---------|------------------|---------|------|
| Apprentissage forcé | 80-95% | ⚡⚡⚡ Instantané | 🆓 Gratuit |
| Normalisation | 70-85% | ⚡⚡⚡ Instantané | 🆓 Gratuit |
| Système complet | **90%** | ⚡⚡⚡ < 1s | 🆓 Gratuit |
| OpenAI GPT-4o (optionnel) | 95-99% | ⚡⚡ 2-5s | 💰 ~$0.01 |

**Test validé** : Catalogue 10 colonnes multi-langues (IT/FR) → 9/10 matchées (90%)

### Génération descriptions SEO

| Modèle Ollama | Taille | Temps/desc | Qualité | RAM |
|---------------|--------|------------|---------|-----|
| qwen2.5:3b ⭐ | 2GB | 3-5s | Excellente | 8GB |
| llama3.2:3b | 2GB | 5-8s | Très bonne | 8GB |
| mistral:7b | 4GB | 10-15s | Supérieure | 16GB |

**Recommandation** : qwen2.5:3b (meilleur rapport qualité/vitesse/ressources)

## 📝 Licence

MIT - Libre d'utilisation et modification

## 🤝 Contribution

Les contributions sont les bienvenues ! Ouvrez une issue ou un PR.

---

**Développé avec ❤️ par l'équipe IA Excel**  
**Technologies** : Python, OpenAI GPT-4o, Ollama, Streamlit, Pandas, Sentence Transformers
