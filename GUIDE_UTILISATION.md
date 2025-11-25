# 🚀 Guide d'Utilisation Rapide - IA Excel Matcher

## 📖 Table des matières
1. [Démarrage rapide](#démarrage-rapide)
2. [Workflow standard](#workflow-standard)
3. [Fonctionnalités avancées](#fonctionnalités-avancées)
4. [Résolution de problèmes](#résolution-de-problèmes)

---

## 🏁 Démarrage rapide

### Installation

```bash
# 1. Cloner le projet
git clone <votre-repo>
cd Ia-excel

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer la clé API (optionnel mais recommandé)
echo "OPENAI_API_KEY=votre-clé-ici" > .env

# 4. Lancer l'application
streamlit run app.py
```

L'application s'ouvre automatiquement dans votre navigateur à l'adresse : **http://localhost:8501**

---

## 📋 Workflow standard

### Étape 1 : Préparer votre template

1. Cliquez sur **"📤 Télécharger un template"**
2. Uploadez votre fichier Excel de référence (avec les colonnes souhaitées)
3. Donnez-lui un nom descriptif (ex: "Template Fournisseur XYZ")
4. ✅ Le template est maintenant sauvegardé et réutilisable

### Étape 2 : Importer un catalogue

1. Cliquez sur **"📁 Importer un catalogue Excel"**
2. Uploadez le fichier Excel du fournisseur
3. L'application détecte automatiquement :
   - La ligne d'en-têtes
   - Les colonnes disponibles
   - Le nombre de produits

### Étape 3 : Analyser et matcher

1. Cliquez sur **"🔍 Analyser et Matcher"**
2. Le système analyse automatiquement les colonnes :
   - 🤖 **Avec IA :** Utilise GPT-4o pour matcher intelligemment
   - 📚 **Sans IA :** Utilise l'historique d'apprentissage (23 patterns)
3. Les matchings proposés s'affichent avec un indicateur de confiance

### Étape 4 : Valider et corriger

Pour chaque colonne :
- ✅ **Vert** : Matching validé automatiquement
- ⚠️ **Orange** : À vérifier
- ❌ **Rouge** : Non mappé

**Correction manuelle :**
1. Utilisez les dropdowns pour changer un matching incorrect
2. Chaque correction est automatiquement apprise pour les prochains imports
3. Cliquez sur **"✅ Valider les mappings"**

### Étape 5 : Prévisualiser

Avant de générer :
- 👁️ Visualisez les premières lignes de données
- Vérifiez que les données apparaissent dans les bonnes colonnes
- Utilisez les filtres pour isoler certaines colonnes

### Étape 6 : Générer et télécharger

1. Cliquez sur **"⚡ Générer le fichier Excel"**
2. Le fichier est généré avec :
   - ✅ Vos données injectées
   - ✅ Le format du template préservé
   - ✅ Toutes les formules et styles conservés
3. Cliquez sur **"💾 Télécharger"** pour récupérer votre fichier

---

## 🔥 Fonctionnalités avancées

### Mode Batch

Pour traiter plusieurs fichiers d'un coup :

1. Activez **"📦 Mode Batch"** dans la sidebar
2. Uploadez plusieurs fichiers Excel
3. Les fichiers sont traités séquentiellement
4. Téléchargez tous les résultats en ZIP

### Filtres de recherche

Pour traiter uniquement certaines colonnes :

1. Activez **"🔍 Activer les filtres"**
2. Entrez des mots-clés (ex: "prix", "référence")
3. Seules les colonnes correspondantes sont traitées

### Statistiques d'apprentissage

Dans la **sidebar** :
- 📊 Nombre total de corrections
- 🎯 Patterns uniques appris
- 📈 Taux de succès du matching
- 🕒 Dernière correction enregistrée

### Gestion des templates

#### Créer un nouveau template
```python
# Via l'interface
1. Section "Gestion des templates"
2. Upload fichier Excel
3. Nommer le template
4. Sauvegarder
```

#### Définir un template par défaut
```python
# Via l'interface
1. Liste des templates
2. Cocher "Définir par défaut"
3. Ce template sera pré-sélectionné
```

#### Supprimer un template
```python
# Via l'interface
1. Liste des templates
2. Bouton "🗑️ Supprimer"
3. Confirmation requise
```

---

## 🛠️ Résolution de problèmes

### ❌ "OpenAI API Error"

**Cause :** Clé API manquante ou invalide

**Solution :**
```bash
# Option 1 : Fichier .env
echo "OPENAI_API_KEY=sk-..." > .env

# Option 2 : Variable d'environnement
export OPENAI_API_KEY=sk-...
```

**Alternative :** L'application fonctionne sans API grâce à l'historique d'apprentissage !

---

### ❌ "Erreur de détection d'en-tête"

**Cause :** Structure Excel non standard

**Solution :**
1. Ouvrez votre fichier Excel
2. Assurez-vous que la première ligne contient les noms des colonnes
3. Supprimez les lignes vides au début
4. Réessayez l'import

---

### ❌ "Colonnes non mappées"

**Cause :** Noms de colonnes inconnus

**Solution :**
1. Utilisez la correction manuelle (dropdowns)
2. Chaque correction est apprise automatiquement
3. Au prochain import similaire, le matching sera automatique

---

### ❌ "Fichier généré vide"

**Cause :** Aucun mapping validé

**Solution :**
1. Vérifiez l'étape "Valider les mappings"
2. Au moins une colonne doit être mappée
3. Cliquez sur "✅ Valider" avant de générer

---

### ⚠️ "Warning: Marqueur {{DATA}} non trouvé"

**Impact :** Aucun (warning informatif)

**Explication :** Le système injecte directement en début de tableau, fonctionne normalement.

---

## 💡 Astuces et bonnes pratiques

### 🎯 Optimiser le matching

1. **Utilisez l'IA pour les nouveaux fournisseurs**
   - Première import : Matching IA + corrections manuelles
   - Imports suivants : Matching automatique grâce à l'apprentissage

2. **Nommez vos colonnes de façon cohérente**
   - "Prix TTC" plutôt que "PrixTTC" ou "PRIX_TTC"
   - Aide l'IA à mieux comprendre

3. **Créez un template par fournisseur**
   - Template "Fournisseur A"
   - Template "Fournisseur B"
   - Évite les confusions

### 📊 Exploiter l'apprentissage

- Après 10-15 corrections, le système devient très précis
- Consultez les statistiques pour voir vos patterns
- Exportez `matching_history.json` pour backup

### ⚡ Performance

Pour les gros fichiers (> 5000 lignes) :
1. Testez d'abord avec un échantillon (100 lignes)
2. Validez le mapping
3. Appliquez sur le fichier complet

### 🔒 Sécurité

- ✅ Ne commitez JAMAIS `.env` dans Git
- ✅ `.gitignore` est déjà configuré
- ✅ Clé API stockée de façon sécurisée

---

## 📞 Support

### Logs de debug

Pour diagnostiquer un problème :

```bash
# Vérifier les logs
tail -f debug.log

# Tester un module individuellement
python -c "from src.catalog_parser import CatalogParser; print('OK')"
```

### Réinitialiser l'apprentissage

Si nécessaire :

```python
# Via Python
from src.matching_learning import MatchingLearning
learner = MatchingLearning()
learner.clear_history()
```

### Contacts

- 📧 Issues GitHub : [Créer une issue](https://github.com/votre-repo/issues)
- 📚 Documentation complète : `README.md`
- 🧪 Rapport de tests : `RAPPORT_TEST.md`

---

## 🎓 Exemples d'utilisation

### Cas d'usage 1 : Nouveau fournisseur

```
1. Import catalogue fournisseur
2. Matching IA (90% de réussite)
3. Corrections manuelles (5 colonnes)
4. Génération fichier ✅
5. Prochain import : 100% automatique !
```

### Cas d'usage 2 : Fournisseur connu

```
1. Import catalogue
2. Matching automatique (historique)
3. Génération directe ✅
4. Temps total : < 30 secondes
```

### Cas d'usage 3 : Batch de 10 fichiers

```
1. Mode Batch activé
2. Upload 10 catalogues
3. Matching automatique pour tous
4. Téléchargement ZIP ✅
5. Temps total : < 2 minutes
```

---

**Version:** 1.0  
**Dernière mise à jour:** 24 novembre 2025  
**Auteur:** ForceSuperieur
