#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HelloWork Job Scraper Plus - V2
Script pour extraire les offres d'emploi de HelloWork et générer des lettres de motivation personnalisées.
"""

import os
import sys
import time
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import argparse

# Configuration
BASE_URL = "https://www.hellowork.com"
SEARCH_URL_PATTERN = "https://www.hellowork.com/fr-fr/emploi/recherche.html?k={job}&l={location}"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"

def scrape_job_listings(job_title, location="", max_pages=1):
    """
    Scrape les offres d'emploi depuis HelloWork.
    
    Args:
        job_title (str): Le titre du poste recherché
        location (str, optional): La localisation. Par défaut "".
        max_pages (int, optional): Nombre maximum de pages à scraper. Par défaut 1.
    
    Returns:
        list: Liste des offres d'emploi
    """
    job_listings = []
    
    # Préparer les paramètres de l'URL
    job_param = job_title.replace(" ", "+")
    location_param = location.replace(" ", "+") if location else ""
    
    # Construire l'URL de recherche
    search_url = SEARCH_URL_PATTERN.format(job=job_param, location=location_param)
    
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    }
    
    print(f"Recherche d'offres pour: {job_title}")
    print(f"URL de recherche: {search_url}")
    
    for page in range(1, max_pages + 1):
        try:
            # Ajout du paramètre de pagination si nécessaire
            if page > 1:
                page_url = f"{search_url}&page={page}"
            else:
                page_url = search_url
            
            print(f"Scraping de la page {page}...")
            response = requests.get(page_url, headers=headers)
            
            if response.status_code != 200:
                print(f"Erreur lors de la requête: {response.status_code}")
                break
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Sauvegarder la page pour analyse (en mode debug)
            with open(f"debug_page_{page}.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"Page {page} sauvegardée pour analyse")
            
            # 1. Chercher des éléments qui pourraient contenir des offres d'emploi par data-cy="serpCard"
            job_cards = soup.select('div[data-cy="serpCard"]')
            
            # 2. Si aucune offre trouvée, chercher des liens d'offres
            if not job_cards:
                print("Pas d'offres trouvées avec les sélecteurs standards, essai avec les liens...")
                job_links = soup.find_all('a', href=lambda href: href and '/emplois/' in href)
                
                # Filtrer pour ne garder que les liens qui semblent être des offres
                job_links = [link for link in job_links if not any(exclude in link.get('href', '') for exclude in ['recherche', 'page='])]
                
                if job_links:
                    print(f"Trouvé {len(job_links)} liens directs vers des offres")
                
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
                    contract_type = "À déterminer"
                    if 'altern' in title.lower() or 'apprentissage' in title.lower():
                        is_alternance = True
                        contract_type = "Potentiellement alternance/apprentissage"
                    
                    job_listings.append({
                        "title": title,
                        "company": company,
                        "location": job_location,
                        "description": f"Type de contrat: {contract_type}",
                        "link": full_url,
                        "contract_type": contract_type,
                        "is_alternance": is_alternance
                    })
            
            # 3. Si des offres ont été trouvées avec les sélecteurs standards
            else:
                print(f"Nombre d'offres trouvées sur la page {page}: {len(job_cards)}")
                
                for job in job_cards:
                    try:
                        # Trouver le lien principal de l'offre
                        link_element = job.select_one('a[href*="/emplois/"]')
                        
                        if not link_element:
                            link_element = job.find('a')
                            if not link_element or not link_element.get('href'):
                                continue
                        
                        link = link_element.get('href')
                        
                        # S'assurer que le lien est absolu
                        if not link.startswith(('http://', 'https://')):
                            link = BASE_URL + link
                        
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
                        contract_type = contract_element.get_text(strip=True) if contract_element else "Non spécifié"
                        
                        # Chercher une description ou extrait
                        description = f"Type de contrat: {contract_type}"
                        
                        # Vérifier si c'est une alternance (peut être dans le titre ou type de contrat)
                        is_alternance = False
                        if 'altern' in contract_type.lower() or 'apprentissage' in contract_type.lower():
                            is_alternance = True
                            description += " (Alternance)"
                        elif 'altern' in title.lower() or 'apprentissage' in title.lower():
                            is_alternance = True
                            description += " (Alternance mentionnée dans le titre)"
                        
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
                            "contract_type": contract_type,
                            "is_alternance": is_alternance
                        })
                        
                    except Exception as e:
                        print(f"Erreur lors de l'extraction d'une offre: {str(e)}")
            
            # Pause pour éviter de surcharger le serveur
            time.sleep(2)
            
        except Exception as e:
            print(f"Erreur lors du scraping de la page {page}: {str(e)}")
    
    print(f"Nombre total d'offres trouvées: {len(job_listings)}")
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
        "User-Agent": USER_AGENT,
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    try:
        print(f"Récupération des détails de l'offre : {url}")
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Erreur lors de la récupération des détails: {response.status_code}")
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
        print(f"Erreur lors de la récupération des détails de l'offre: {str(e)}")
        return f"Erreur: {str(e)}"

def generate_cover_letter(job_data, cv_path="cv.txt", parcours_path="parcours.txt"):
    """
    Génère une lettre de motivation personnalisée basée sur l'offre d'emploi et le CV.
    
    Args:
        job_data (dict): Informations sur l'offre d'emploi
        cv_path (str): Chemin vers le fichier CV
        parcours_path (str): Chemin vers le fichier parcours
        
    Returns:
        str: Lettre de motivation générée
    """
    try:
        # Récupérer le CV
        cv_text = ""
        if os.path.exists(cv_path):
            with open(cv_path, 'r', encoding='utf-8') as file:
                cv_text = file.read()
        else:
            print(f"Attention: Le fichier CV {cv_path} n'existe pas.")
            
        # Récupérer le parcours
        parcours_text = ""
        if os.path.exists(parcours_path):
            with open(parcours_path, 'r', encoding='utf-8') as file:
                parcours_text = file.read()
        else:
            print(f"Attention: Le fichier parcours {parcours_path} n'existe pas.")
            
        # Récupérer les détails complets de l'offre
        job_description = fetch_job_details(job_data["link"])
        
        # Date du jour
        today = datetime.now().strftime("%d/%m/%Y")
        
        # Créer un destinataire
        destinataire = f"Service recrutement {job_data['company']}" if job_data['company'] != "Non spécifié" else "Service recrutement"
        
        # Créer un objet
        objet = f"Candidature au poste de {job_data['title']}"
        
        # Générer la lettre
        letter = f"""
{today}

{destinataire}
{job_data['company']}

Objet : {objet}

Madame, Monsieur,

Suite à votre offre d'emploi pour le poste de {job_data['title']} {f"à {job_data['location']}" if job_data['location'] != "Non spécifié" else ""}, je vous présente ma candidature avec enthousiasme.

Mon profil correspond aux qualifications que vous recherchez comme le montre mon CV ci-joint.

{cv_text[:200] if cv_text else ""}

{parcours_text[:200] if parcours_text else ""}

Particulièrement intéressé(e) par {job_data['company']}, je souhaite mettre à profit mon expertise pour contribuer à vos projets. Votre recherche de {job_data['title']} correspond parfaitement à mon parcours professionnel et à mes aspirations.

Je serais ravi(e) de vous rencontrer pour vous présenter ma motivation et mes compétences lors d'un entretien.

Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées.

[Votre nom]
[Vos coordonnées]
        """
            
        return letter
        
    except Exception as e:
        print(f"Erreur lors de la génération de la lettre: {str(e)}")
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
        print(f"Lettre de motivation enregistrée dans {filepath}")
        return filepath
    except Exception as e:
        print(f"Erreur lors de l'enregistrement de la lettre: {str(e)}")
        return None

def generate_all_cover_letters(job_listings):
    """
    Génère des lettres de motivation pour toutes les offres d'emploi listées.
    
    Args:
        job_listings (list): Liste des offres d'emploi
        
    Returns:
        int: Nombre de lettres générées avec succès
    """
    count = 0
    
    print(f"\nGénération des lettres de motivation pour {len(job_listings)} offres...")
    
    for job in job_listings:
        try:
            # Générer la lettre
            letter = generate_cover_letter(job)
            
            # Enregistrer la lettre
            filepath = save_cover_letter(job, letter)
            
            if filepath:
                count += 1
                print(f"Lettre générée pour: {job['title']} - {job['company']}")
                
        except Exception as e:
            print(f"Erreur lors du traitement de l'offre {job['title']}: {str(e)}")
    
    print(f"\n{count} lettres de motivation ont été générées avec succès.")
    return count

def main():
    """Fonction principale exécutant le processus de scraping et d'enregistrement."""
    parser = argparse.ArgumentParser(description='Scraper les offres d\'emploi HelloWork et générer des lettres de motivation')
    parser.add_argument('--job', required=True, help='Titre du poste à rechercher')
    parser.add_argument('--location', default='', help='Localisation de la recherche')
    parser.add_argument('--pages', type=int, default=1, help='Nombre de pages à scraper')
    parser.add_argument('--generate-letters', action='store_true', help='Générer des lettres de motivation pour chaque offre')
    parser.add_argument('--contrat', default='', help='Filtrer par type de contrat (ex: alternance, cdi, cdd, stage)')
    
    args = parser.parse_args()
    
    try:
        # 1. Scraper les offres d'emploi
        job_listings = scrape_job_listings(args.job, args.location, args.pages)
        
        if not job_listings:
            print("Aucune offre d'emploi trouvée.")
            return
            
        # Filtrer par type de contrat si spécifié
        if args.contrat:
            contrat_lower = args.contrat.lower()
            filtered_listings = []
            print(f"\nFiltrage des offres pour le type de contrat '{args.contrat}'...")
            
            for job in job_listings:
                # Vérifier si le type de contrat est dans la description
                if 'description' in job and contrat_lower in job['description'].lower():
                    filtered_listings.append(job)
                # Si la description ne contient pas le type de contrat, récupérer les détails pour vérifier
                else:
                    # Récupérer les détails pour voir si le type de contrat est mentionné
                    details = fetch_job_details(job['link'])
                    if contrat_lower in details.lower():
                        filtered_listings.append(job)
            
            job_listings = filtered_listings
            print(f"{len(job_listings)} offres correspondent au type de contrat '{args.contrat}'")
            
            if not job_listings:
                print("Aucune offre ne correspond au filtre de contrat spécifié.")
                return
        
        # Afficher un résumé des offres trouvées
        print("\nRésumé des offres trouvées:")
        for i, job in enumerate(job_listings, 1):
            print(f"{i}. {job['title']} - {job['company']} - {job['location']}")
            print(f"   {job['link']}")
        
        # 2. Générer des lettres de motivation si demandé
        if args.generate_letters:
            generated_count = generate_all_cover_letters(job_listings)
            print(f"{generated_count} lettres de motivation ont été générées.")
        
    except Exception as e:
        print(f"Une erreur est survenue dans le processus principal: {str(e)}")

if __name__ == "__main__":
    main()
