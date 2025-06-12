# HelloWork Job Scraper Plus - Enhanced Edition

Ce script permet de scraper les offres d'emploi du site HelloWork, de les sauvegarder dans Google Sheets ou CSV, et de générer automatiquement des lettres de motivation personnalisées.

## Nouvelles fonctionnalités

- **Interface en ligne de commande améliorée** avec indicateurs de progression
- **Extraction intelligente des compétences** pour personnaliser les lettres de motivation
- **Support de proxy** pour éviter les limitations de requêtes
- **Gestion avancée des erreurs** avec journalisation détaillée
- **Export flexible** vers Google Sheets ou fichier CSV
- **Système anti-blocage** avec rotation d'User-Agents et délais intelligents

## Fonctionnalités existantes

- Recherche et extraction d'offres d'emploi depuis HelloWork
- Extraction de données complètes: titre, entreprise, localisation, description, lien
- Enregistrement des offres dans Google Sheets
- Génération automatique de lettres de motivation personnalisées
- Possibilité de configurer la recherche (poste, localisation, nombre de pages)

## Prérequis

- Python 3.7+
- Les packages Python listés dans `requirements.txt`
- Un compte Google et un projet Google Cloud Platform avec l'API Google Sheets activée (optionnel, pour la fonctionnalité Google Sheets)

## Installation

1. Clonez ce dépôt ou téléchargez les fichiers

2. Installez les dépendances :

```
pip install -r requirements.txt
```

3. Pour l'intégration avec Google Sheets :

   - Allez sur [Google Cloud Console](https://console.cloud.google.com/)
   - Créez un nouveau projet ou sélectionnez un projet existant
   - Activez l'API Google Drive et l'API Google Sheets
   - Créez un compte de service et téléchargez le fichier de clé JSON
   - Renommez le fichier téléchargé en `credentials.json` et placez-le à la racine du projet

4. Pour utiliser les proxies (optionnel) :

   - Créez un fichier `proxies.txt` à la racine du projet
   - Ajoutez un proxy par ligne au format `ip:port`

5. Créez les fichiers nécessaires pour la génération des lettres de motivation :
   - `cv.txt` : Votre CV au format texte
   - `parcours.txt` : Votre parcours professionnel et motivations

## Utilisation

### Recherche d'offres d'emploi (basique)

```bash
python hellowork_scraper_enhanced.py --job "data engineer" --location "paris" --pages 2 --save-csv
```

### Recherche avec Google Sheets et génération de lettres de motivation

```bash
python hellowork_scraper_enhanced.py --job "data engineer" --location "paris" --pages 2 --save-sheets --generate-letters
```

### Utilisation avec proxy et débogage

```bash
python hellowork_scraper_enhanced.py --job "data engineer" --location "paris" --pages 2 --use-proxy --debug
```

### Options disponibles

- `--job` : Titre du poste à rechercher (obligatoire)
- `--location` : Localisation de la recherche (optionnel)
- `--pages` : Nombre de pages à scraper (par défaut: 1)
- `--generate-letters` : Générer des lettres de motivation (optionnel)
- `--save-sheets` : Sauvegarder dans Google Sheets (optionnel)
- `--save-csv` : Sauvegarder dans un fichier CSV (optionnel)
- `--csv-file` : Nom du fichier CSV de sortie (par défaut: 'offres_emploi.csv')
- `--debug` : Activer le mode de débogage (optionnel)
- `--use-proxy` : Utiliser des proxies pour les requêtes (optionnel)
- `--proxy-file` : Fichier contenant la liste des proxies (par défaut: 'proxies.txt')
- `--rate-limit` : Délai minimum entre les requêtes en secondes (par défaut: 2.0)

## Structure des fichiers

- `hellowork_scraper_enhanced.py` : Script principal amélioré
- `cv.txt` : Fichier contenant votre CV
- `parcours.txt` : Fichier contenant votre parcours professionnel
- `credentials.json` : Identifiants Google API pour Google Sheets
- `proxies.txt` : Liste des proxies (optionnel)
- `lettres/` : Dossier contenant les lettres de motivation générées
- `debug/` : Dossier contenant les pages HTML sauvegardées en mode debug

## Résultat

### Google Sheets

Le script créera une feuille de calcul Google Sheets nommée "Offres HelloWork" avec les colonnes suivantes :

- Date (date d'ajout de l'offre)
- Titre (intitulé du poste)
- Entreprise (nom de l'entreprise)
- Localisation (lieu de travail)
- Description (extrait de la description)
- Lien (URL de l'offre d'emploi)

### Fichier CSV

Le script peut générer un fichier CSV avec les mêmes informations que Google Sheets.

### Lettres de motivation

Les lettres de motivation générées seront enregistrées au format texte dans le dossier `lettres/` avec un nom de fichier incluant la date, l'entreprise et le titre du poste.

## Fonctionnement de la génération des lettres de motivation

La nouvelle version utilise une approche plus intelligente pour générer des lettres personnalisées :

1. **Extraction de compétences** : Le script analyse votre CV pour identifier vos compétences clés
2. **Analyse de l'offre** : Il extrait les compétences requises de la description du poste
3. **Correspondance** : Il identifie les correspondances entre votre profil et les exigences du poste
4. **Personnalisation** : Il génère une lettre mettant en avant vos compétences pertinentes pour le poste
5. **Contextualisation** : Il intègre des éléments de la mission du poste dans votre motivation

## Améliorations techniques

- **Programmation orientée objet** : Code restructuré en classe pour une meilleure maintenabilité
- **Gestion des erreurs** : Système complet de logging et traitement des exceptions
- **Anti-blocage** : Rotation d'User-Agents et délais variables entre requêtes
- **Support proxy** : Possibilité d'utiliser des proxies pour distribuer les requêtes
- **Performances** : Optimisation des requêtes et du traitement des données

## Remarques

- Pour éviter d'être bloqué par le site, le script inclut un délai entre chaque requête.
- Si la feuille Google Sheets n'existe pas, elle sera automatiquement créée.
- Pour des raisons légales, veuillez utiliser ce script uniquement à des fins personnelles et respectez les conditions d'utilisation du site HelloWork.

## Dépannage

- Si vous obtenez des erreurs d'authentification avec Google Sheets, vérifiez que :

  - Le fichier `credentials.json` est correctement configuré
  - Les API nécessaires sont activées dans votre projet Google Cloud
  - Le compte de service a les autorisations suffisantes
  - La feuille de calcul est partagée avec l'email du compte de service

- Si vous ne trouvez pas de résultats, il est possible que :

  - La structure du site HelloWork ait changé (les sélecteurs CSS pourraient devoir être mis à jour)
  - Votre adresse IP soit temporairement bloquée (essayez d'utiliser l'option `--use-proxy`)
  - Le délai entre les requêtes soit trop court (augmentez avec `--rate-limit`)

- Les erreurs sont enregistrées dans le fichier `hellowork_scraper.log` pour faciliter le débogage
