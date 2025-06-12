# HelloWork Job Scraper Plus

Ce script permet de scraper les offres d'emploi du site HelloWork et de générer automatiquement des lettres de motivation personnalisées.

## Fonctionnalités

- Recherche et extraction d'offres d'emploi depuis HelloWork
- Extraction de données complètes: titre, entreprise, localisation, description, lien
- Enregistrement des offres dans Google Sheets
- Génération automatique de lettres de motivation personnalisées
- Possibilité de configurer la recherche (poste, localisation, nombre de pages)
- Interface interactive facile à utiliser

## Prérequis

- Python 3.7+
- Les packages Python listés dans `requirements.txt`
- Un compte Google et un projet Google Cloud Platform avec l'API Google Sheets activée (pour la fonctionnalité Google Sheets)

## Installation

1. Clonez ce dépôt ou téléchargez les fichiers

2. Installez les dépendances :

```
pip install -r requirements.txt
```

3. Pour l'intégration avec Google Sheets :
   a. Allez sur [Google Cloud Console](https://console.cloud.google.com/)
   b. Créez un nouveau projet ou sélectionnez un projet existant
   c. Activez l'API Google Drive et l'API Google Sheets
   d. Créez un compte de service et téléchargez le fichier de clé JSON
   e. Renommez le fichier téléchargé en `credentials.json` et placez-le à la racine du projet

4. Créez les fichiers nécessaires pour la génération des lettres de motivation :
   a. `cv.txt` : Votre CV au format texte
   b. `parcours.txt` : Votre parcours professionnel et motivations
   c. `infos_perso.json` : Vos informations personnelles (nom, coordonnées, texte de motivation, signature)

## Utilisation simplifiée (Recommandée)

### Avec les scripts de lancement

Nous avons créé des scripts qui simplifient l'utilisation du scraper :

#### Windows

Double-cliquez simplement sur `lancer_scraper.bat` et suivez les instructions.

#### En ligne de commande (toutes plateformes)

```bash
python lancer_scraper.py
```

#### Linux/macOS

```bash
chmod +x lancer_scraper.sh
./lancer_scraper.sh
```

Le lanceur offre un menu intuitif avec les options suivantes :

1. Lancer le scraper en mode interactif
2. Vérifier l'environnement et les dépendances
3. Afficher l'aide
4. Quitter

## Utilisation en ligne de commande

Si vous préférez utiliser directement les options en ligne de commande :

### Mode interactif (Recommandé)

```bash
python hellowork_scraper_interactive.py --interactive
```

### Recherche d'offres d'emploi avec options spécifiques

```bash
python hellowork_scraper_interactive.py --job "data engineer" --location "paris" --pages 2
```

### Recherche d'offres avec génération de lettres de motivation

```bash
python hellowork_scraper_interactive.py --job "data engineer" --location "paris" --pages 2 --generate-letters
```

### Recherche sans sauvegarde dans Google Sheets

```bash
python hellowork_scraper_interactive.py --job "data engineer" --location "paris" --pages 1 --skip-sheets
```

### Options disponibles

- `--interactive` : Lancer en mode interactif avec interface guidée
- `--job` : Titre du poste à rechercher
- `--location` : Localisation de la recherche (optionnel)
- `--contrat` : Type de contrat (alternance, cdi, cdd, stage, etc.)
- `--pages` : Nombre de pages à scraper (par défaut: 1)
- `--generate-letters` : Générer des lettres de motivation (optionnel)
- `--sheet-name` : Nom de la feuille Google Sheets (par défaut: "Offres HelloWork")

## Structure des fichiers

- `hellowork_scraper_interactive.py` : Script principal avec interface interactive
- `lancer_scraper.py` : Script Python de lancement avec menu
- `lancer_scraper.bat` : Script de lancement Windows
- `lancer_scraper.sh` : Script de lancement Linux/macOS
- `cv.txt` : Fichier contenant votre CV
- `parcours.txt` : Fichier contenant votre parcours professionnel
- `infos_perso.json` : Vos informations personnelles pour la personnalisation des lettres
- `credentials.json` : Identifiants Google API pour Google Sheets
- `proxies.txt` : Liste de proxies (optionnel)
- `lettres/` : Dossier contenant les lettres de motivation générées

## Personnalisation des lettres de motivation

Le script utilise les informations contenues dans le fichier `infos_perso.json` pour personnaliser les lettres de motivation. Ce fichier doit contenir les champs suivants :

```json
{
  "nom": "Votre Nom",
  "coordonnees": "email@example.com | 06 XX XX XX XX | Ville, Pays",
  "texte_motivation": "Votre texte de motivation personnalisé...",
  "signature": "Cordialement,\nVotre Nom"
}
```

Le texte de motivation sera automatiquement adapté à chaque entreprise en remplaçant "EDF" par le nom de l'entreprise cible.

## Résultat

### Google Sheets

Le script créera une feuille de calcul Google Sheets avec les colonnes suivantes :

- Date (date d'ajout de l'offre)
- Titre (intitulé du poste)
- Entreprise (nom de l'entreprise)
- Localisation (lieu de travail)
- Description (extrait de la description)
- Lien (URL de l'offre d'emploi)

### Lettres de motivation

Les lettres de motivation générées seront enregistrées au format texte dans le dossier `lettres/` avec un nom de fichier incluant la date, l'entreprise et le titre du poste.

## Remarques

- Pour éviter d'être bloqué par le site, le script inclut un délai entre chaque requête.
- Vous pouvez utiliser des proxies en les ajoutant au fichier `proxies.txt` (un proxy par ligne).
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
  - Votre adresse IP soit temporairement bloquée pour cause de trop nombreuses requêtes
  - Utilisez l'option des proxies pour contourner les limitations d'accès
