#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de lancement pour le scraper HelloWork
Ce script simplifie le lancement du scraper HelloWork en vérifiant l'environnement
et en exécutant le script interactif avec les bonnes options.
"""

import os
import sys
import subprocess
import time
import pkg_resources

# Couleurs pour terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def afficher_message(message, type_message="info"):
    """Affiche un message formaté dans le terminal"""
    if type_message == "info":
        print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {message}")
    elif type_message == "success":
        print(f"{Colors.GREEN}[SUCCÈS]{Colors.ENDC} {message}")
    elif type_message == "warning":
        print(f"{Colors.WARNING}[ATTENTION]{Colors.ENDC} {message}")
    elif type_message == "error":
        print(f"{Colors.FAIL}[ERREUR]{Colors.ENDC} {message}")
    elif type_message == "header":
        print(f"\n{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}\n")

def verifier_dependances():
    """Vérifie que toutes les dépendances requises sont installées"""
    required_packages = [
        "requests", "beautifulsoup4", "gspread", "google-auth", 
        "oauth2client", "pandas", "tqdm", "argparse", "colorama", "python-dotenv"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            pkg_resources.get_distribution(package)
        except pkg_resources.DistributionNotFound:
            missing_packages.append(package)
    
    return missing_packages

def installer_dependances(packages):
    """Installe les dépendances manquantes"""
    afficher_message(f"Installation des dépendances manquantes: {', '.join(packages)}", "info")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        afficher_message("Installation des dépendances terminée avec succès", "success")
        return True
    except subprocess.CalledProcessError:
        afficher_message("Erreur lors de l'installation des dépendances", "error")
        return False

def verifier_fichiers_essentiels():
    """Vérifie que tous les fichiers essentiels sont présents"""
    fichiers_essentiels = [
        "hellowork_scraper_interactive.py",
        "cv.txt",
        "parcours.txt",
        "infos_perso.json"
    ]
    
    # Au moins un des fichiers d'authentification Google doit être présent
    fichiers_auth = ["credentials.json", ".env"]
    auth_present = False
    
    for fichier in fichiers_auth:
        if os.path.exists(fichier):
            auth_present = True
            break
    
    if not auth_present:
        fichiers_essentiels.append("credentials.json ou .env")
    
    fichiers_manquants = []
    for fichier in fichiers_essentiels:
        if "ou" in fichier:
            # Cas spécial pour les alternatives
            continue
        elif not os.path.exists(fichier):
            fichiers_manquants.append(fichier)
    
    return fichiers_manquants

def lancer_scraper(mode="interactive"):
    """Lance le scraper HelloWork"""
    script_path = "hellowork_scraper_interactive.py"
    
    afficher_message("Lancement du scraper HelloWork...", "info")
    
    if mode == "interactive":
        commande = [sys.executable, script_path, "--interactive"]
    else:
        # Ajoutez ici d'autres modes si nécessaire
        commande = [sys.executable, script_path, "--interactive"]
    
    try:
        subprocess.call(commande)
        return True
    except Exception as e:
        afficher_message(f"Erreur lors de l'exécution du scraper: {str(e)}", "error")
        return False

def afficher_menu():
    """Affiche le menu principal"""
    afficher_message("SCRAPER HELLOWORK - MENU PRINCIPAL", "header")
    print(f"{Colors.BOLD}1.{Colors.ENDC} Lancer le scraper en mode interactif")
    print(f"{Colors.BOLD}2.{Colors.ENDC} Vérifier l'environnement et les dépendances")
    print(f"{Colors.BOLD}3.{Colors.ENDC} Afficher l'aide")
    print(f"{Colors.BOLD}4.{Colors.ENDC} Quitter")
    
    choix = input("\nVotre choix (1-4): ")
    return choix

def afficher_aide():
    """Affiche l'aide du script"""
    afficher_message("AIDE DU SCRAPER HELLOWORK", "header")
    print("Ce script vous permet de scraper les offres d'emploi sur HelloWork et de générer")
    print("des lettres de motivation personnalisées pour chaque offre.")
    print("\nOptions disponibles :")
    print("1. Mode interactif : Vous guide à travers les étapes pour rechercher et traiter les offres d'emploi")
    print("2. Vérification de l'environnement : S'assure que toutes les dépendances sont installées")
    print("\nPour fonctionner correctement, le script nécessite les fichiers suivants :")
    print("- hellowork_scraper_interactive.py : Le script principal")
    print("- cv.txt : Votre CV au format texte")
    print("- parcours.txt : Description de votre parcours professionnel")
    print("- infos_perso.json : Vos informations personnelles pour les lettres de motivation")
    print("- .env ou credentials.json : Vos identifiants Google API (pour l'accès à Google Sheets)")
    input("\nAppuyez sur Entrée pour revenir au menu principal...")

def main():
    """Fonction principale"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
    while True:
        choix = afficher_menu()
        
        if choix == "1":
            # Vérifier les dépendances avant de lancer
            missing_packages = verifier_dependances()
            if missing_packages:
                if not installer_dependances(missing_packages):
                    afficher_message("Impossible de continuer sans les dépendances requises", "error")
                    time.sleep(2)
                    continue
            
            # Vérifier les fichiers essentiels
            fichiers_manquants = verifier_fichiers_essentiels()
            if fichiers_manquants:
                afficher_message(f"Fichiers manquants: {', '.join(fichiers_manquants)}", "error")
                afficher_message("Veuillez créer ou restaurer ces fichiers avant de continuer", "warning")
                time.sleep(3)
                continue
            
            # Lancer le scraper
            lancer_scraper()
            input("\nAppuyez sur Entrée pour revenir au menu principal...")
            
        elif choix == "2":
            # Vérifier l'environnement
            afficher_message("Vérification de l'environnement...", "info")
            
            # Vérifier Python
            python_version = sys.version.split()[0]
            afficher_message(f"Version de Python: {python_version}", "info")
            
            # Vérifier les dépendances
            missing_packages = verifier_dependances()
            if missing_packages:
                afficher_message(f"Dépendances manquantes: {', '.join(missing_packages)}", "warning")
                choix_install = input("Voulez-vous installer les dépendances manquantes ? (o/n): ")
                if choix_install.lower() == 'o':
                    installer_dependances(missing_packages)
            else:
                afficher_message("Toutes les dépendances sont installées", "success")
            
            # Vérifier les fichiers essentiels
            fichiers_manquants = verifier_fichiers_essentiels()
            if fichiers_manquants:
                afficher_message(f"Fichiers manquants: {', '.join(fichiers_manquants)}", "warning")
            else:
                afficher_message("Tous les fichiers essentiels sont présents", "success")
            
            input("\nAppuyez sur Entrée pour revenir au menu principal...")
            
        elif choix == "3":
            # Afficher l'aide
            afficher_aide()
            
        elif choix == "4":
            # Quitter
            afficher_message("Merci d'avoir utilisé le scraper HelloWork !", "success")
            sys.exit(0)
            
        else:
            afficher_message("Choix invalide. Veuillez choisir une option entre 1 et 4.", "warning")
            time.sleep(1)
        
        os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        afficher_message("Programme interrompu par l'utilisateur", "warning")
        sys.exit(0)
