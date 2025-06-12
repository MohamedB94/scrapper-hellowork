#!/bin/bash

echo "---------------------------------------------"
echo "    LANCEMENT DU SCRAPER HELLOWORK"
echo "---------------------------------------------"
echo

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "[ERREUR] Python n'est pas installé."
    echo "Veuillez installer Python avec votre gestionnaire de paquets."
    echo "Par exemple : sudo apt install python3 python3-pip (Ubuntu/Debian)"
    echo "ou : brew install python (macOS avec Homebrew)"
    echo
    read -p "Appuyez sur Entrée pour quitter..."
    exit 1
fi

# Lancer le script Python
echo "Lancement du scraper HelloWork..."
echo
python3 lancer_scraper.py

# En cas d'erreur
if [ $? -ne 0 ]; then
    echo
    echo "[ERREUR] Une erreur s'est produite lors de l'exécution du script."
    read -p "Appuyez sur Entrée pour quitter..."
fi

exit 0
