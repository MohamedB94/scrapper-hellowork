#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HelloWork Job Scraper Plus - Version Interactive
Script pour extraire les offres d'emploi de HelloWork, les enregistrer dans Google Sheets
et générer des lettres de motivation personnalisées, le tout avec une interface conviviale.
"""

import os
import sys
import time
import json
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import argparse
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import textwrap
import colorama
from colorama import Fore, Back, Style

# Initialiser colorama pour les couleurs dans le terminal
colorama.init()

# Configuration
BASE_URL = "https://www.hellowork.com"
SEARCH_URL_PATTERN = "https://www.hellowork.com/fr-fr/emploi/recherche.html?k={job}&l={location}"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
]

def print_header():
    """Affiche un en-tête stylisé pour le programme"""
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.YELLOW}{'HelloWork Job Scraper Plus - Version Interactive':^80}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")

def print_section(title):
    """Affiche un titre de section"""
    print(f"\n{Fore.GREEN}{'=' * 60}")
    print(f"{title:^60}")
    print(f"{'=' * 60}{Style.RESET_ALL}\n")

def print_success(message):
    """Affiche un message de succès"""
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")

def print_error(message):
    """Affiche un message d'erreur"""
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")

def print_warning(message):
    """Affiche un message d'avertissement"""
    print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")

def print_info(message):
    """Affiche un message d'information"""
    print(f"{Fore.BLUE}ℹ {message}{Style.RESET_ALL}")

def print_progress(current, total, description="Progression"):
    """Affiche une barre de progression"""
    bar_length = 50
    filled_length = int(bar_length * current / total)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    percent = int(100 * current / total)
    print(f"\r{Fore.CYAN}{description}: |{bar}| {percent}% ({current}/{total}){Style.RESET_ALL}", end='')
    if current == total:
        print()

def get_random_user_agent():
    """Retourne un User-Agent aléatoire"""
    return random.choice(USER_AGENTS)

def load_proxies(proxy_file="proxies.txt"):
    """
    Charge une liste de proxies depuis un fichier texte.
    Chaque ligne du fichier doit contenir un proxy au format 'ip:port'
    
    Args:
        proxy_file (str): Chemin vers le fichier de proxies
        
    Returns:
        list: Liste des proxies chargés
    """
    proxies = []
    try:
        if os.path.exists(proxy_file):
            with open(proxy_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Ignorer les lignes vides ou commentaires
                    if line and not line.startswith('#') and ':' in line:
                        # Formater correctement le proxy
                        proxies.append(f"http://{line}")
            print_info(f"{len(proxies)} proxies chargés depuis {proxy_file}")
        else:
            print_warning(f"Fichier de proxies {proxy_file} non trouvé")
    except Exception as e:
        print_error(f"Erreur lors du chargement des proxies: {str(e)}")
    return proxies

def get_request_with_proxy(url, headers, proxies=None):
    """
    Effectue une requête HTTP GET avec gestion des proxies et des erreurs
    
    Args:
        url (str): L'URL à requêter
        headers (dict): Les en-têtes HTTP à utiliser
        proxies (list): Liste de proxies disponibles
        
    Returns:
        response: La réponse HTTP ou None en cas d'erreur
    """
    if not proxies:
        # Sans proxy
        try:
            return requests.get(url, headers=headers, timeout=10)
        except Exception as e:
            print_error(f"Erreur lors de la requête: {str(e)}")
            return None
    
    # Avec proxies, essayer chaque proxy jusqu'à ce qu'un fonctionne
    for proxy in proxies:
        try:
            proxy_dict = {"http": proxy, "https": proxy}
            response = requests.get(url, headers=headers, proxies=proxy_dict, timeout=10)
            if response.status_code == 200:
                print_info(f"Requête réussie avec proxy: {proxy}")
                return response
        except Exception as e:
            continue
    
    # Si tous les proxies ont échoué, essayer sans proxy
    try:
        print_warning("Tous les proxies ont échoué, tentative sans proxy...")
        return requests.get(url, headers=headers, timeout=10)
    except Exception as e:
        print_error(f"Erreur lors de la requête sans proxy: {str(e)}")
        return None

def get_user_input(prompt, default=None):
    """
    Récupère une entrée utilisateur avec une valeur par défaut
    
    Args:
        prompt (str): Le message à afficher à l'utilisateur
        default (str): Valeur par défaut si l'utilisateur n'entre rien
        
    Returns:
        str: L'entrée utilisateur ou la valeur par défaut
    """
    if default:
        user_input = input(f"{Fore.YELLOW}{prompt} [{default}]: {Style.RESET_ALL}")
        return user_input if user_input else default
    else:
        return input(f"{Fore.YELLOW}{prompt}: {Style.RESET_ALL}")

def get_yes_no(prompt, default="oui"):
    """
    Demande une confirmation oui/non à l'utilisateur
    
    Args:
        prompt (str): La question à poser
        default (str): Valeur par défaut ('oui' ou 'non')
        
    Returns:
        bool: True pour oui, False pour non
    """
    while True:
        if default.lower() in ['oui', 'o', 'yes', 'y']:
            choice = input(f"{Fore.YELLOW}{prompt} [O/n]: {Style.RESET_ALL}").lower()
            if not choice or choice in ['o', 'oui', 'y', 'yes']:
                return True
            elif choice in ['n', 'non', 'no']:
                return False
        else:
            choice = input(f"{Fore.YELLOW}{prompt} [o/N]: {Style.RESET_ALL}").lower()
            if not choice or choice in ['n', 'non', 'no']:
                return False
            elif choice in ['o', 'oui', 'y', 'yes']:
                return True
        
        print_warning("Veuillez répondre par 'o' ou 'n'.")

def scrape_job_listings(job_title, location="", max_pages=1, contract_type="", proxies=None):
    """
    Scrape les offres d'emploi depuis HelloWork.
    
    Args:
        job_title (str): Le titre du poste recherché
        location (str, optional): La localisation. Par défaut "".
        max_pages (int, optional): Nombre maximum de pages à scraper. Par défaut 1.
        contract_type (str, optional): Type de contrat à filtrer. Par défaut "".
        proxies (list, optional): Liste de proxies à utiliser. Par défaut None.
    
    Returns:
        list: Liste des offres d'emploi
    """
    job_listings = []
    seen_links = set()  # Ensemble pour suivre les liens déjà vus
    
    # Préparer les paramètres de l'URL
    job_param = job_title.replace(" ", "+")
    location_param = location.replace(" ", "+") if location else ""
    
    # Construire l'URL de recherche
    search_url = SEARCH_URL_PATTERN.format(job=job_param, location=location_param)
    
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }
    
    print_info(f"Recherche d'offres pour: {job_title}")
    print_info(f"URL de recherche: {search_url}")
    
    # Charger les proxies depuis un fichier
    proxies = load_proxies("proxies.txt")
    
    for page in range(1, max_pages + 1):
        try:
            # Ajout du paramètre de pagination si nécessaire
            if page > 1:
                page_url = f"{search_url}&page={page}"
            else:
                page_url = search_url
            
            print_info(f"Scraping de la page {page}/{max_pages}...")
            response = get_request_with_proxy(page_url, headers, proxies)
            
            if response is None or response.status_code != 200:
                print_error(f"Erreur lors de la requête: {response.status_code if response else 'Aucune réponse'}")
                break
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Sauvegarder la page pour analyse (en mode debug)
            debug_dir = 'debug'
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
                
            with open(os.path.join(debug_dir, f"debug_page_{page}.html"), "w", encoding="utf-8") as f:
                f.write(response.text)
            
            # 1. Chercher des éléments qui pourraient contenir des offres d'emploi par data-cy="serpCard"
            job_cards = soup.select('div[data-cy="serpCard"]')
            
            # 2. Si aucune offre trouvée, chercher des liens d'offres
            if not job_cards:
                print_warning("Pas d'offres trouvées avec les sélecteurs standards, essai avec les liens...")
                job_links = soup.find_all('a', href=lambda href: href and '/emplois/' in href)
                
                # Filtrer pour ne garder que les liens qui semblent être des offres
                job_links = [link for link in job_links if not any(exclude in link.get('href', '') for exclude in ['recherche', 'page='])]
                
                if job_links:
                    print_info(f"Trouvé {len(job_links)} liens directs vers des offres")
                
                for link in job_links:
                    href = link.get('href')
                    title = link.get_text(strip=True)
                    
                    if not title:
                        title_elem = link.find(['h2', 'h3', 'p'])
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                        else:
                            title = "Titre non disponible"
                      # Construire l'URL complète
                    full_url = href if href.startswith(('http://', 'https://')) else BASE_URL + href
                    
                    # Vérifier si ce lien a déjà été traité
                    if full_url in seen_links:
                        continue
                    seen_links.add(full_url)
                    
                    # Extraire l'entreprise et la localisation de l'attribut title/aria-label
                    company = "Non spécifié"
                    job_location = location or "Non spécifié"
                    
                    aria_label = link.get('aria-label')
                    if aria_label:
                        company_match = re.search(r'chez\s+(\w+)', aria_label)
                        if company_match:
                            company = company_match.group(1)
                        
                        location_match = re.search(r'à\s+([^,]+)', aria_label)
                        if location_match:
                            job_location = location_match.group(1)
                    
                    # Vérifier si c'est potentiellement une alternance basé sur le titre
                    is_alternance = False
                    detected_contract_type = "À déterminer"
                    if 'altern' in title.lower() or 'apprentissage' in title.lower():
                        is_alternance = True
                        detected_contract_type = "Potentiellement alternance/apprentissage"
                    
                    # Vérifier si cela correspond au type de contrat recherché
                    if contract_type and (contract_type.lower() not in title.lower() and contract_type.lower() not in detected_contract_type.lower()):
                        continue  # Ignorer cette offre si elle ne correspond pas au type de contrat recherché
                    
                    job_listings.append({
                        "title": title,
                        "company": company,
                        "location": job_location,
                        "description": f"Type de contrat: {detected_contract_type}",
                        "link": full_url,
                        "contract_type": detected_contract_type,
                        "is_alternance": is_alternance
                    })
            
            # 3. Si des offres ont été trouvées avec les sélecteurs standards
            else:
                print_info(f"Nombre d'offres trouvées sur la page {page}: {len(job_cards)}")
                
                # Afficher une barre de progression
                progress_count = 0
                total_jobs = len(job_cards)
                
                for job in job_cards:
                    progress_count += 1
                    print_progress(progress_count, total_jobs, "Analyse des offres")
                    
                    try:                        # Trouver le lien principal de l'offre
                        link_element = job.select_one('a[href*="/emplois/"]')
                        if not link_element:
                            link_element = job.find('a')
                            if not link_element or not link_element.get('href'):
                                continue
                        
                        link = link_element.get('href')
                        
                        # S'assurer que le lien est absolu
                        if not link.startswith(('http://', 'https://')):
                            link = BASE_URL + link
                            
                        # Vérifier si ce lien a déjà été traité
                        if link in seen_links:
                            continue
                        seen_links.add(link)
                        
                        # Trouver le titre de l'offre
                        title_element = job.select_one('p.tw-typo-l, p.tw-typo-xl, h3 p')
                        
                        if not title_element:
                            title_element = job.find(['h3', 'h2', 'p.tw-typo-l'])
                            if not title_element:
                                continue
                        
                        title = title_element.get_text(strip=True)
                        
                        # Trouver le nom de l'entreprise
                        company_element = job.select_one('p.tw-inline, p.tw-typo-s')
                        company = company_element.get_text(strip=True) if company_element else "Non spécifié"
                        
                        # Trouver la localisation
                        location_element = job.select_one('div[data-cy="localisationCard"]')
                        job_location = location_element.get_text(strip=True) if location_element else location or "Non spécifié"
                        
                        # Trouver des informations supplémentaires comme le type de contrat
                        contract_element = job.select_one('div[data-cy="contractCard"]')
                        detected_contract_type = contract_element.get_text(strip=True) if contract_element else "Non spécifié"
                        
                        # Chercher une description ou extrait
                        description = f"Type de contrat: {detected_contract_type}"
                        
                        # Vérifier si c'est une alternance (peut être dans le titre ou type de contrat)
                        is_alternance = False
                        if 'altern' in detected_contract_type.lower() or 'apprentissage' in detected_contract_type.lower():
                            is_alternance = True
                            description += " (Alternance)"
                        elif 'altern' in title.lower() or 'apprentissage' in title.lower():
                            is_alternance = True
                            description += " (Alternance mentionnée dans le titre)"
                        
                        # Vérifier si cela correspond au type de contrat recherché
                        if contract_type and not (contract_type.lower() in detected_contract_type.lower() or 
                                                ('alternance' in contract_type.lower() and is_alternance)):
                            continue  # Ignorer cette offre si elle ne correspond pas au type de contrat recherché
                        
                        # Ajouter la date de publication si disponible
                        date_element = job.select_one('div.tw-typo-s.tw-text-grey')
                        if date_element:
                            description += f" | Publié: {date_element.get_text(strip=True)}"
                        
                        job_listings.append({
                            "title": title,
                            "company": company,
                            "location": job_location,
                            "description": description,
                            "link": link,
                            "contract_type": detected_contract_type,
                            "is_alternance": is_alternance
                        })
                        
                    except Exception as e:
                        print_error(f"Erreur lors de l'extraction d'une offre: {str(e)}")
            
            # Pause pour éviter de surcharger le serveur
            time.sleep(2)
            
        except Exception as e:
            print_error(f"Erreur lors du scraping de la page {page}: {str(e)}")
    
    print_success(f"Nombre total d'offres trouvées: {len(job_listings)}")
    
    # Si un type de contrat est spécifié, filtrer davantage en vérifiant les détails
    if contract_type and job_listings:
        print_section("Filtrage des offres par type de contrat")
        print_info(f"Recherche approfondie des offres de type '{contract_type}'...")
        
        filtered_listings = []
        progres_count = 0
        
        for job in job_listings:
            progres_count += 1
            print_progress(progres_count, len(job_listings), f"Vérification des offres pour '{contract_type}'")
            
            # Si déjà identifié comme correspondant au type de contrat, l'ajouter directement
            if (contract_type.lower() == 'alternance' and job['is_alternance']) or \
               contract_type.lower() in job['contract_type'].lower():
                filtered_listings.append(job)
            else:
                # Sinon, récupérer les détails pour vérifier le type de contrat
                job_details = fetch_job_details(job['link'])
                if job_details and contract_type.lower() in job_details.lower():
                    job['job_details_text'] = job_details  # Sauvegarder les détails pour éviter de refaire la requête
                    filtered_listings.append(job)
        
        job_listings = filtered_listings
        print_success(f"{len(job_listings)} offres correspondent au type de contrat '{contract_type}'")
    
    return job_listings

def fetch_job_details(url):
    """
    Récupère les détails complets d'une offre d'emploi depuis sa page dédiée.
    
    Args:
        url (str): URL de l'offre d'emploi
        
    Returns:
        str: Contenu complet de la description de l'offre
    """
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    try:
        print_info(f"Récupération des détails de l'offre : {url}")
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print_error(f"Erreur lors de la récupération des détails: {response.status_code}")
            return "Impossible de récupérer les détails de l'offre."
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Tenter de trouver la section de description de l'offre
        description_selectors = [
            "div.job-description", 
            "div.description", 
            "div[data-testid='job-description']",
            "div[data-cy='jobDescription']",
            "section.job-description",
            "div.offer-description",
            "div.tw-prose"  # Nouveau sélecteur pour HelloWork
        ]
        
        for selector in description_selectors:
            description_element = soup.select_one(selector)
            if description_element:
                return description_element.get_text(strip=True)
        
        # Si on ne trouve pas la description avec les sélecteurs spécifiques,
        # essayons de récupérer tout le contenu principal
        main_content = soup.select_one("main, article, div.main-content")
        if main_content:
            return main_content.get_text(strip=True)
        
        # Dernier recours: prendre tout ce qui ressemble à une description
        all_paragraphs = soup.find_all('p')
        if all_paragraphs and len(all_paragraphs) > 5:  # Au moins quelques paragraphes
            content = "\n".join([p.get_text(strip=True) for p in all_paragraphs if len(p.get_text(strip=True)) > 50])
            if content:
                return content
        
        return "Description non trouvée sur la page de l'offre."
        
    except Exception as e:
        print_error(f"Erreur lors de la récupération des détails de l'offre: {str(e)}")
        return f"Erreur: {str(e)}"

def extract_skills(description):
    """
    Extrait les compétences potentielles d'un texte de description d'offre
    
    Args:
        description (str): Description de l'offre d'emploi
        
    Returns:
        list: Liste des compétences identifiées
    """
    tech_skills = [
        "Python", "SQL", "Java", "JavaScript", "TypeScript", "C#", "C\\+\\+", "PHP", "Ruby",
        "Angular", "React", "Vue", "Node.js", "Django", "Flask", "Spring", "Laravel", "Ruby on Rails",
        "AWS", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes", "Terraform",
        "MySQL", "PostgreSQL", "Oracle", "MongoDB", "Cassandra", "Redis",
        "Hadoop", "Spark", "Kafka", "Airflow", "Databricks", "dbt",
        "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "Data Mining",
        "Agile", "Scrum", "DevOps", "CI/CD", "Jenkins", "Git"
    ]
    
    found_skills = []
    for skill in tech_skills:
        if re.search(r'\b' + skill + r'\b', description, re.IGNORECASE):
            found_skills.append(skill)
    
    return found_skills

def generate_cover_letter(job_data, cv_path="cv.txt", parcours_path="parcours.txt", infos_perso_path="infos_perso.json"):
    """
    Génère une lettre de motivation personnalisée basée sur l'offre d'emploi et le CV.
    
    Args:
        job_data (dict): Informations sur l'offre d'emploi
        cv_path (str): Chemin vers le fichier CV
        parcours_path (str): Chemin vers le fichier parcours
        infos_perso_path (str): Chemin vers le fichier d'informations personnelles
        
    Returns:
        str: Lettre de motivation générée
    """
    try:
        # Récupérer les informations personnelles
        infos_perso = {}
        if os.path.exists(infos_perso_path):
            try:
                with open(infos_perso_path, 'r', encoding='utf-8') as file:
                    infos_perso = json.load(file)
                print_success(f"Informations personnelles chargées depuis {infos_perso_path}")
            except json.JSONDecodeError:
                print_warning(f"Le fichier {infos_perso_path} n'est pas un JSON valide.")
        
        # Récupérer le CV
        cv_text = ""
        if os.path.exists(cv_path):
            with open(cv_path, 'r', encoding='utf-8') as file:
                cv_text = file.read()
        else:
            print_warning(f"Attention: Le fichier CV {cv_path} n'existe pas.")
            
        # Récupérer le parcours
        parcours_text = ""
        if os.path.exists(parcours_path):
            with open(parcours_path, 'r', encoding='utf-8') as file:
                parcours_text = file.read()
        else:
            print_warning(f"Attention: Le fichier parcours {parcours_path} n'existe pas.")
        
        # Récupérer les détails complets de l'offre si pas déjà disponibles
        if 'job_details_text' in job_data:
            job_description = job_data['job_details_text']
        else:
            job_description = fetch_job_details(job_data["link"])
        
        # Extraire les compétences de l'offre et du CV pour personnalisation
        job_skills = extract_skills(job_description)
        cv_skills = extract_skills(cv_text)
        
        # Trouver les compétences communes
        common_skills = [skill for skill in cv_skills if skill in job_skills]
        
        # Date du jour
        today = datetime.now().strftime("%d/%m/%Y")
        
        # Créer un destinataire
        destinataire = f"Service recrutement {job_data['company']}" if job_data['company'] != "Non spécifié" else "Service recrutement"
        
        # Créer un objet
        objet = f"Candidature au poste de {job_data['title']}"
        
        # Personnaliser la lettre en fonction du type de contrat
        contract_intro = ""
        if job_data.get('is_alternance', False) or 'alternance' in job_data.get('contract_type', '').lower():
            contract_intro = "en alternance "
          # Générer la lettre (sans en-tête, directement avec la salutation)
        letter = f"""Madame, Monsieur,

"""
          # Utiliser le texte personnalisé si disponible, sinon générer un texte standard
        if infos_perso and 'texte_motivation' in infos_perso:
            # Remplacer "EDF" par le nom de l'entreprise
            texte_motivation = infos_perso['texte_motivation'].replace("EDF", job_data['company'])
            letter += texte_motivation
            letter += "\n\n"
        else:            # Introduction standard
            location_text = f"à {job_data['location']}" if job_data['location'] != 'Non spécifié' else ''
            letter += f"Suite à votre offre d'emploi pour le poste de {job_data['title']} {contract_intro}{location_text}, je vous présente ma candidature avec enthousiasme.\n\n"
            
            # Ajouter des compétences communes si trouvées
            if common_skills:
                skills_text = ", ".join(common_skills[:-1])
                if len(common_skills) > 1:
                    skills_text += f" et {common_skills[-1]}"
                else:
                    skills_text = common_skills[0]
                
                letter += f"Mon profil correspond aux qualifications que vous recherchez, notamment en ce qui concerne {skills_text} comme le montre mon CV ci-joint.\n\n"
            else:
                letter += "Mon profil correspond aux qualifications que vous recherchez comme le montre mon CV ci-joint.\n\n"
            
            # Ajouter un extrait du CV
            if cv_text:
                # Extraire le début du CV (première partie significative)
                cv_extract = cv_text.split('\n\n')[0] if '\n\n' in cv_text else cv_text[:200]
                letter += f"{cv_extract}\n\n"
            
            # Ajouter un extrait du parcours
            if parcours_text:
                # Extraire le début du parcours (première partie significative)
                parcours_extract = parcours_text.split('\n\n')[0] if '\n\n' in parcours_text else parcours_text[:200]
                letter += f"{parcours_extract}\n\n"
            
            # Conclusion personnalisée
            letter += f"Particulièrement intéressé(e) par {job_data['company']}, je souhaite mettre à profit mon expertise pour contribuer à vos projets. Votre recherche de {job_data['title']} correspond parfaitement à mon parcours professionnel et à mes aspirations.\n\n"
            letter += "Je serais ravi(e) de vous rencontrer pour vous présenter ma motivation et mes compétences lors d'un entretien.\n\n"
            letter += "Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.\n\n"
        
        # Signature
        if infos_perso and 'signature' in infos_perso:
            letter += infos_perso['signature']
        elif infos_perso and 'nom' in infos_perso:
            letter += f"{infos_perso.get('nom', '[Votre nom]')}\n{infos_perso.get('coordonnees', '[Vos coordonnées]')}"
        else:
            letter += "[Votre nom]\n[Vos coordonnées]"
            
        return letter
        
    except Exception as e:
        print_error(f"Erreur lors de la génération de la lettre: {str(e)}")
        return f"Erreur: Impossible de générer la lettre - {str(e)}"

def save_cover_letter(job_data, letter_text):
    """
    Enregistre la lettre de motivation dans un fichier texte.
    
    Args:
        job_data (dict): Informations sur l'offre d'emploi
        letter_text (str): Contenu de la lettre de motivation
        
    Returns:
        str: Chemin du fichier créé
    """
    # Créer le dossier pour les lettres s'il n'existe pas
    letters_dir = "lettres"
    if not os.path.exists(letters_dir):
        os.makedirs(letters_dir)
    
    # Créer un nom de fichier à partir de l'entreprise et du titre du poste
    company_name = re.sub(r'[^\w\s-]', '', job_data['company']).strip()
    job_title = re.sub(r'[^\w\s-]', '', job_data['title']).strip()
    
    company_name = company_name.replace(' ', '_')
    job_title = job_title.replace(' ', '_')
    
    # Ajouter la date pour éviter les doublons
    date_str = datetime.now().strftime("%Y%m%d")
    
    filename = f"{date_str}_{company_name}_{job_title}.txt"
    filepath = os.path.join(letters_dir, filename)
    
    # Écrire la lettre dans le fichier
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(letter_text)
        
        return filepath
    except Exception as e:
        print_error(f"Erreur lors de l'enregistrement de la lettre: {str(e)}")
        return None

def save_to_google_sheets(job_listings, letters_paths=None, sheet_name="Offres HelloWork"):
    """
    Sauvegarde les offres d'emploi et les liens vers les lettres de motivation dans Google Sheets
    
    Args:
        job_listings (list): Liste des offres d'emploi
        letters_paths (dict): Dictionnaire associant les offres aux chemins des lettres de motivation
        sheet_name (str): Nom de la feuille Google Sheets
        
    Returns:
        bool: True si la sauvegarde a réussi, False sinon
    """
    try:
        # Vérifier si le fichier credentials.json existe
        if not os.path.exists('credentials.json'):
            print_error("Fichier credentials.json non trouvé. Impossible de sauvegarder dans Google Sheets.")
            print_info("Créez un projet Google Cloud Platform et téléchargez les credentials au format JSON.")
            return False
        
        print_info("Connexion à Google Sheets...")
        
        # Définir l'étendue (scope) d'accès à l'API
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        
        # Authentification avec le fichier de credentials
        credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        
        # Créer une instance du client gspread
        client = gspread.authorize(credentials)
        
        try:
            # Tenter d'ouvrir la feuille existante
            sheet = client.open(sheet_name).sheet1
            print_info(f"Feuille existante '{sheet_name}' ouverte avec succès")
        except gspread.exceptions.SpreadsheetNotFound:
            # Si la feuille n'existe pas, en créer une nouvelle
            sheet = client.create(sheet_name).sheet1
            print_info(f"Nouvelle feuille '{sheet_name}' créée avec succès")
            
            # Définir les en-têtes
            headers = ["Date", "Titre", "Entreprise", "Localisation", "Type de contrat", "Description", "Lien vers l'offre", "Lien vers la lettre de motivation"]
            sheet.append_row(headers)
            
            # Formater les en-têtes
            sheet.format('A1:H1', {'textFormat': {'bold': True}})
        
        # Préparer les données à ajouter
        rows_to_add = []
        for i, job in enumerate(job_listings):
            # Déterminer le lien vers la lettre de motivation
            letter_link = ""
            if letters_paths and i in letters_paths:
                letter_path = letters_paths[i]
                letter_link = os.path.abspath(letter_path) if letter_path else ""
            
            row = [
                datetime.now().strftime("%Y-%m-%d"),
                job.get('title', ""),
                job.get('company', ""),
                job.get('location', ""),
                job.get('contract_type', ""),
                job.get('description', ""),
                job.get('link', ""),
                letter_link
            ]
            rows_to_add.append(row)
          # Ajouter les données à la feuille
        if rows_to_add:
            sheet.append_rows(rows_to_add)
            print_success(f"{len(rows_to_add)} offres ajoutées à Google Sheets")
        
        # Obtenir l'URL de la feuille pour l'afficher à l'utilisateur
        # Dans les versions récentes de gspread, on accède au spreadsheet différemment
        try:
            # Méthode moderne
            spreadsheet_id = sheet.spreadsheet.id
        except AttributeError:
            # Méthode alternative pour les versions plus récentes
            spreadsheet_id = sheet.url.split('/')[-2] if hasattr(sheet, 'url') else "spreadsheet"
        
        spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        print_success(f"Les données ont été sauvegardées avec succès dans Google Sheets: {spreadsheet_url}")
        
        return True
        
    except Exception as e:
        print_error(f"Erreur lors de la sauvegarde dans Google Sheets: {str(e)}")
        return False

def generate_and_save_all_cover_letters(job_listings):
    """
    Génère des lettres de motivation pour toutes les offres d'emploi listées et les sauvegarde.
    
    Args:
        job_listings (list): Liste des offres d'emploi
        
    Returns:
        dict: Dictionnaire associant les index des offres aux chemins des lettres de motivation
    """
    letter_paths = {}
    
    print_section("Génération des lettres de motivation")
    
    if not job_listings:
        print_warning("Aucune offre d'emploi trouvée pour générer des lettres de motivation.")
        return letter_paths
    
    print_info(f"Génération des lettres de motivation pour {len(job_listings)} offres...")
    
    # Demander les chemins vers les fichiers CV et parcours
    cv_path = get_user_input("Chemin vers le fichier CV", "cv.txt")
    parcours_path = get_user_input("Chemin vers le fichier parcours", "parcours.txt")
    infos_perso_path = get_user_input("Chemin vers le fichier d'informations personnelles", "infos_perso.json")
    
    # Vérifier que les fichiers existent
    if not os.path.exists(cv_path):
        print_error(f"Fichier CV introuvable: {cv_path}")
        if not get_yes_no("Voulez-vous continuer sans fichier CV ?"):
            return letter_paths
    
    if not os.path.exists(parcours_path):
        print_error(f"Fichier parcours introuvable: {parcours_path}")
        if not get_yes_no("Voulez-vous continuer sans fichier parcours ?"):
            return letter_paths
    
    if not os.path.exists(infos_perso_path):
        print_warning(f"Fichier d'informations personnelles introuvable: {infos_perso_path}")
        print_info("Les lettres seront générées avec des placeholders [Votre nom] et [Vos coordonnées].")
    
    # Générer les lettres avec une barre de progression
    for i, job in enumerate(job_listings):
        try:
            print_progress(i + 1, len(job_listings), "Génération des lettres de motivation")
            
            # Générer la lettre
            letter = generate_cover_letter(job, cv_path, parcours_path, infos_perso_path)
            
            # Enregistrer la lettre
            filepath = save_cover_letter(job, letter)
            
            if filepath:
                letter_paths[i] = filepath
                
        except Exception as e:
            print_error(f"Erreur lors du traitement de l'offre {job['title']}: {str(e)}")
    
    print_success(f"\n{len(letter_paths)} lettres de motivation ont été générées avec succès.")
    return letter_paths

def save_scraping_state(job_listings, search_params):
    """
    Sauvegarde l'état actuel du scraping pour permettre une reprise ultérieure
    
    Args:
        job_listings (list): Liste des offres d'emploi déjà scrapées
        search_params (dict): Paramètres de recherche utilisés
    """
    if not os.path.exists('saves'):
        os.makedirs('saves')
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"saves/scraping_state_{timestamp}.json"
    
    state = {
        "job_listings": job_listings,
        "search_params": search_params,
        "timestamp": timestamp
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        print_success(f"État du scraping sauvegardé dans {filename}")
        return filename
    except Exception as e:
        print_error(f"Erreur lors de la sauvegarde de l'état: {str(e)}")
        return None

def load_scraping_state(filename=None):
    """
    Charge un état de scraping précédemment sauvegardé
    
    Args:
        filename (str, optional): Chemin du fichier de sauvegarde. Si None, liste les sauvegardes disponibles.
        
    Returns:
        tuple: (job_listings, search_params) ou (None, None) en cas d'échec
    """
    if not os.path.exists('saves'):
        print_warning("Aucune sauvegarde trouvée.")
        return None, None
    
    if not filename:
        # Lister les sauvegardes disponibles
        saves = [f for f in os.listdir('saves') if f.startswith('scraping_state_')]
        if not saves:
            print_warning("Aucune sauvegarde trouvée.")
            return None, None
        
        print_section("Sauvegardes disponibles")
        for i, save in enumerate(saves, 1):
            # Extraire la date/heure du nom de fichier
            timestamp = save.replace('scraping_state_', '').replace('.json', '')
            try:
                # Convertir en objet datetime pour un affichage plus lisible
                dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                readable_date = dt.strftime("%d/%m/%Y à %H:%M:%S")
            except:
                readable_date = timestamp
            
            # Lire les infos de base de la sauvegarde
            try:
                with open(os.path.join('saves', save), 'r', encoding='utf-8') as f:
                    state = json.load(f)
                job_count = len(state.get('job_listings', []))
                search = state.get('search_params', {})
                job_title = search.get('job_title', 'Inconnu')
                location = search.get('location', 'Non spécifié')
                
                print(f"{i}. {save} - {readable_date}")
                print(f"   Recherche: {job_title} à {location}, {job_count} offres trouvées")
            except:
                print(f"{i}. {save} - {readable_date} (Erreur de lecture)")
        
        choice = get_user_input("Numéro de la sauvegarde à charger (ou 'q' pour annuler)")
        if choice.lower() == 'q':
            return None, None
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(saves):
                filename = os.path.join('saves', saves[index])
            else:
                print_error("Numéro de sauvegarde invalide.")
                return None, None
        except:
            print_error("Entrée invalide.")
            return None, None
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        job_listings = state.get('job_listings', [])
        search_params = state.get('search_params', {})
        
        print_success(f"Sauvegarde chargée avec succès: {len(job_listings)} offres.")
        return job_listings, search_params
    except Exception as e:
        print_error(f"Erreur lors du chargement de la sauvegarde: {str(e)}")
        return None, None

def identify_contract_type(title, description):
    """
    Identifie le type de contrat à partir du titre et de la description
    
    Args:
        title (str): Titre de l'offre
        description (str): Description de l'offre
        
    Returns:
        dict: Dictionnaire avec le type de contrat identifié et des indicateurs booléens
    """
    text = (title + " " + description).lower()
    
    # Dictionnaire des types de contrat avec leurs mots-clés associés
    contract_types = {
        "CDI": ["cdi", "contrat à durée indéterminée", "permanent", "indéterminée"],
        "CDD": ["cdd", "contrat à durée déterminée", "déterminée", "temporaire"],
        "Alternance": ["altern", "apprentissage", "apprenti", "contrat pro", "professionnalisation"],
        "Stage": ["stage", "stagiaire", "internship", "intern"],
        "Freelance": ["freelance", "indépendant", "consultant externe", "auto-entrepreneur"],
        "Intérim": ["intérim", "mission temporaire", "mission d'intérim"],
        "Temps partiel": ["temps partiel", "mi-temps", "part-time"],
        "Temps plein": ["temps plein", "temps complet", "full-time"]
    }
    
    # Recherche des mots-clés dans le texte
    detected_types = []
    for contract_type, keywords in contract_types.items():
        for keyword in keywords:
            if keyword in text:
                detected_types.append(contract_type)
                break
    
    # Si plusieurs types détectés, prioriser
    if "CDI" in detected_types and "CDD" in detected_types:
        # Si les deux sont mentionnés, regarder lequel est mentionné en premier
        if "cdi" in text.split("cdd")[0]:
            primary_type = "CDI"
        else:
            primary_type = "CDD"
    elif detected_types:
        primary_type = detected_types[0]
    else:
        primary_type = "Non spécifié"
    
    # Construire le résultat
    result = {
        "contract_type": primary_type,
        "is_alternance": "Alternance" in detected_types,
        "is_cdi": "CDI" in detected_types,
        "is_cdd": "CDD" in detected_types,
        "is_stage": "Stage" in detected_types,
        "is_freelance": "Freelance" in detected_types,
        "is_interim": "Intérim" in detected_types,
        "is_part_time": "Temps partiel" in detected_types,
        "is_full_time": "Temps plein" in detected_types,
        "all_detected_types": detected_types
    }
    
    return result
    text = (title + " " + description).lower()
    
    # Dictionnaire des types de contrat avec leurs mots-clés associés
    contract_types = {
        "CDI": ["cdi", "contrat à durée indéterminée", "permanent", "indéterminée"],
        "CDD": ["cdd", "contrat à durée déterminée", "déterminée", "temporaire"],
        "Alternance": ["altern", "apprentissage", "apprenti", "contrat pro", "professionnalisation"],
        "Stage": ["stage", "stagiaire", "internship", "intern"],
        "Freelance": ["freelance", "indépendant", "consultant externe", "auto-entrepreneur"],
        "Intérim": ["intérim", "mission temporaire", "mission d'intérim"],
        "Temps partiel": ["temps partiel", "mi-temps", "part-time"],
        "Temps plein": ["temps plein", "temps complet", "full-time"]
    }
    
    # Recherche des mots-clés dans le texte
    detected_types = []
    for contract_type, keywords in contract_types.items():
        for keyword in keywords:
            if keyword in text:
                detected_types.append(contract_type)
                break
    
    # Si plusieurs types détectés, prioriser
    if "CDI" in detected_types and "CDD" in detected_types:
        # Si les deux sont mentionnés, regarder lequel est mentionné en premier
        if "cdi" in text.split("cdd")[0]:
            primary_type = "CDI"
        else:
            primary_type = "CDD"
    elif detected_types:
        primary_type = detected_types[0]
    else:
        primary_type = "Non spécifié"
    
    # Construire le résultat
    result = {
        "contract_type": primary_type,
        "is_alternance": "Alternance" in detected_types,
        "is_cdi": "CDI" in detected_types,
        "is_cdd": "CDD" in detected_types,
        "is_stage": "Stage" in detected_types,
        "is_freelance": "Freelance" in detected_types,
        "is_interim": "Intérim" in detected_types,
        "is_part_time": "Temps partiel" in detected_types,
        "is_full_time": "Temps plein" in detected_types,
        "all_detected_types": detected_types
    }
    
    return result

def interactive_mode():
    """Mode interactif pour le scraper avec interface conviviale"""
    print_header()
    
    # Vérifier s'il y a des sessions précédentes à reprendre
    if os.path.exists('saves') and os.listdir('saves'):
        if get_yes_no("Des sessions précédentes ont été trouvées. Voulez-vous reprendre une session ?"):
            job_listings, search_params = load_scraping_state()
            if job_listings and search_params:
                print_info(f"Session chargée avec {len(job_listings)} offres.")
                
                # Afficher un résumé des offres trouvées
                print_section("Résumé des offres chargées")
                for i, job in enumerate(job_listings, 1):
                    contract_info = ""
                    if job.get('is_alternance', False):
                        contract_info = f" {Fore.CYAN}[Alternance]{Style.RESET_ALL}"
                    elif job.get('contract_type', "") != "Non spécifié" and job.get('contract_type', "") != "À déterminer":
                        contract_info = f" {Fore.CYAN}[{job.get('contract_type', '')}]{Style.RESET_ALL}"
                        
                    print(f"{i}. {Fore.YELLOW}{job['title']}{Style.RESET_ALL} - {job['company']} - {job['location']}{contract_info}")
                    print(f"   {Fore.BLUE}{job['link']}{Style.RESET_ALL}")
                
                # Aller directement aux actions
                goto_actions(job_listings)
                return
    
    print_section("Configuration de la recherche")
    
    # Récupérer les informations de recherche
    job_title = get_user_input("Titre du poste recherché", "data engineer")
    location = get_user_input("Localisation (optionnel)")
    contract_type = get_user_input("Type de contrat (ex: alternance, cdi, cdd, stage) (optionnel)")
    max_pages = int(get_user_input("Nombre de pages à scraper", "1"))
    
    # Options avancées
    advanced_options = get_yes_no("Voulez-vous configurer des options avancées ?", "non")
    use_proxies = False
    proxies = []
    
    if advanced_options:
        print_section("Options avancées")
        use_proxies = get_yes_no("Utiliser des proxies pour éviter d'être bloqué ?", "non")
        if use_proxies:
            proxy_file = get_user_input("Fichier de proxies", "proxies.txt")
            proxies = load_proxies(proxy_file)
    
    # Construire les paramètres de recherche
    search_params = {
        "job_title": job_title,
        "location": location,
        "contract_type": contract_type,
        "max_pages": max_pages,
        "use_proxies": use_proxies
    }
    
    print_section("Scraping des offres d'emploi")
    
    # Scraper les offres d'emploi
    job_listings = scrape_job_listings(job_title, location, max_pages, contract_type, proxies if use_proxies else None)
    
    if not job_listings:
        print_warning("Aucune offre d'emploi trouvée correspondant à vos critères.")
        if get_yes_no("Voulez-vous essayer une nouvelle recherche ?"):
            return interactive_mode()
        return
    
    # Sauvegarder l'état pour pouvoir reprendre plus tard
    save_file = save_scraping_state(job_listings, search_params)
    
    # Afficher un résumé des offres trouvées
    print_section("Résumé des offres trouvées")
    for i, job in enumerate(job_listings, 1):
        contract_info = ""
        if job.get('is_alternance', False):
            contract_info = f" {Fore.CYAN}[Alternance]{Style.RESET_ALL}"
        elif job.get('contract_type', "") != "Non spécifié" and job.get('contract_type', "") != "À déterminer":
            contract_info = f" {Fore.CYAN}[{job.get('contract_type', '')}]{Style.RESET_ALL}"
            
        print(f"{i}. {Fore.YELLOW}{job['title']}{Style.RESET_ALL} - {job['company']} - {job['location']}{contract_info}")
        print(f"   {Fore.BLUE}{job['link']}{Style.RESET_ALL}")
    
    # Passer aux actions
    goto_actions(job_listings)

def goto_actions(job_listings):
    """
    Gère les actions possibles sur les offres d'emploi
    
    Args:
        job_listings (list): Liste des offres d'emploi
    """
    # Demander ce que l'utilisateur veut faire avec les offres
    print_section("Actions")
    
    # Générer des lettres de motivation
    generate_letters = get_yes_no("Voulez-vous générer des lettres de motivation pour ces offres ?")
    letter_paths = {}
    if generate_letters:
        letter_paths = generate_and_save_all_cover_letters(job_listings)
    
    # Enregistrer dans Google Sheets
    save_sheets = get_yes_no("Voulez-vous sauvegarder les résultats dans Google Sheets ?")
    if save_sheets:
        sheet_name = get_user_input("Nom de la feuille Google Sheets", "Offres HelloWork")
        result = save_to_google_sheets(job_listings, letter_paths, sheet_name)
        if result:
            print_success("Sauvegarde dans Google Sheets terminée avec succès!")
        else:
            print_error("Échec de la sauvegarde dans Google Sheets.")
    
    # Enregistrer en CSV local
    save_csv = get_yes_no("Voulez-vous sauvegarder les offres dans un fichier CSV local ?")
    if save_csv:
        csv_filename = get_user_input("Nom du fichier CSV", f"offres_{job_listings[0].get('title', 'hellowork').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv")
        
        try:
            # Créer un DataFrame pandas
            df = pd.DataFrame(job_listings)
            
            # Ajouter les liens vers les lettres de motivation
            if letter_paths:
                df['cover_letter_path'] = df.index.map(lambda i: letter_paths.get(i, ""))
            
            # Sauvegarder en CSV
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print_success(f"Offres sauvegardées dans {csv_filename}!")
        except Exception as e:
            print_error(f"Erreur lors de la sauvegarde en CSV: {str(e)}")
    
    # Demander si l'utilisateur veut faire une autre recherche
    if get_yes_no("Voulez-vous faire une autre recherche ?"):
        return interactive_mode()
    else:
        print_section("Fin du programme")
        print_success("Merci d'avoir utilisé HelloWork Job Scraper!")

def main():
    """Fonction principale exécutant le programme en mode interactif ou par ligne de commande."""
    parser = argparse.ArgumentParser(description='Scraper les offres d\'emploi HelloWork et générer des lettres de motivation')
    parser.add_argument('--interactive', action='store_true', help='Exécuter en mode interactif (recommandé)')
    parser.add_argument('--job', help='Titre du poste à rechercher')
    parser.add_argument('--location', default='', help='Localisation de la recherche')
    parser.add_argument('--contrat', default='', help='Filtrer par type de contrat (ex: alternance, cdi, cdd, stage)')
    parser.add_argument('--pages', type=int, default=1, help='Nombre de pages à scraper')
    parser.add_argument('--generate-letters', action='store_true', help='Générer des lettres de motivation pour chaque offre')
    parser.add_argument('--sheet-name', default='Offres HelloWork', help='Nom de la feuille Google Sheets')
    
    args = parser.parse_args()
    
    try:
        # Mode interactif (par défaut)
        if args.interactive or not args.job:
            interactive_mode()
            return
        
        # Mode ligne de commande
        print_header()
        
        # Scraper les offres d'emploi
        job_listings = scrape_job_listings(args.job, args.location, args.pages, args.contrat)
        
        if not job_listings:
            print_warning("Aucune offre d'emploi trouvée.")
            return
        
        # Afficher un résumé des offres trouvées
        print_section("Résumé des offres trouvées")
        for i, job in enumerate(job_listings, 1):
            print(f"{i}. {job['title']} - {job['company']} - {job['location']}")
            print(f"   {job['link']}")
        
        # Générer des lettres de motivation si demandé
        letter_paths = {}
        if args.generate_letters:
            letter_paths = generate_and_save_all_cover_letters(job_listings)
        
        # Sauvegarder dans Google Sheets
        save_to_google_sheets(job_listings, letter_paths, args.sheet_name)
        
    except KeyboardInterrupt:
        print_warning("\nOpération interrompue par l'utilisateur.")
    except Exception as e:
        print_error(f"Une erreur est survenue dans le processus principal: {str(e)}")

if __name__ == "__main__":
    main()
