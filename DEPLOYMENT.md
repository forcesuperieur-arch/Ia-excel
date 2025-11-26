# Guide de Déploiement sur Streamlit Cloud

Ce guide vous accompagne étape par étape pour déployer votre application **IA Excel Pro** sur Streamlit Cloud avec une base de données **Supabase**.

## Prérequis

*   Un compte [GitHub](https://github.com/)
*   Un compte [Streamlit Cloud](https://streamlit.io/cloud)
*   Un compte [Supabase](https://supabase.com/)

## Étape 1 : Préparation de la Base de Données (Supabase)

1.  Connectez-vous à [Supabase](https://supabase.com/) et créez un nouveau projet.
2.  Une fois le projet prêt, allez dans l'onglet **SQL Editor** (icône terminal dans la barre latérale gauche).
3.  Cliquez sur **New query**.
4.  Copiez le contenu du fichier `supabase_schema.sql` (situé à la racine de ce projet) et collez-le dans l'éditeur.
5.  Cliquez sur **Run** pour créer les tables nécessaires.
6.  Allez dans **Project Settings** (roue dentée) > **Database**.
7.  Dans la section **Connection string**, sélectionnez l'onglet **URI**.
8.  Copiez la chaîne de connexion. Elle ressemble à :
    `postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
    *(Notez bien le mot de passe que vous avez défini lors de la création du projet, vous devrez remplacer `[YOUR-PASSWORD]` par celui-ci).*

## Étape 2 : Mise en ligne du Code (GitHub)

1.  Assurez-vous que tous vos fichiers sont sauvegardés.
2.  Poussez votre code sur un dépôt GitHub (public ou privé).
    ```bash
    git add .
    git commit -m "Préparation déploiement Supabase"
    git push
    ```

## Étape 3 : Déploiement sur Streamlit Cloud

1.  Connectez-vous à [Streamlit Cloud](https://share.streamlit.io/).
2.  Cliquez sur **New app**.
3.  Sélectionnez votre dépôt GitHub, la branche (`main`) et le fichier principal (`app.py`).
4.  Cliquez sur **Advanced settings**.
5.  Dans la section **Secrets**, copiez-collez le contenu ci-dessous en remplaçant les valeurs par les vôtres :

    ```toml
    [postgres]
    url = "postgresql://postgres:VOTRE_MOT_DE_PASSE@db.VOTRE_PROJET.supabase.co:5432/postgres"

    [api_keys]
    # Ajoutez vos clés API ici si vous voulez qu'elles soient pré-configurées
    # Sinon, vous pourrez les entrer dans l'interface de l'application
    openai = "sk-..."
    openrouter = "sk-or-..."
    ```

6.  Cliquez sur **Save** puis sur **Deploy**.

## Étape 4 : Vérification

Une fois l'application déployée :
1.  L'application devrait démarrer sans erreur.
2.  Les fonctionnalités nécessitant la base de données (Historique, Templates, Cache SEO) utiliseront maintenant votre base Supabase.
3.  Les données seront persistantes même si l'application redémarre.

## Dépannage

*   **Erreur de connexion DB** : Vérifiez que l'URL dans les secrets est correcte et que le mot de passe ne contient pas de caractères spéciaux non échappés (si c'est le cas, encodez-les en URL encoding).
*   **Dépendances manquantes** : Le fichier `requirements.txt` et `packages.txt` sont là pour assurer que Streamlit installe tout le nécessaire. Si une erreur survient, vérifiez les logs dans la console Streamlit Cloud.
