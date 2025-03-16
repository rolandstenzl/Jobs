import requests
from bs4 import BeautifulSoup
import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Lokale Dateien für gespeicherte Daten
COMPANIES_FILE = "companies.json"  # Datei mit Unternehmens-URLs
DATA_FILE = "jobs_data.json"  # Datei zur Speicherung alter Job-Links

# E-Mail-Benachrichtigungseinstellungen
EMAIL_SENDER = "dein.email@gmail.com"  # Absender-E-Mail-Adresse
EMAIL_PASSWORD = "dein_app_passwort"   # App-spezifisches Passwort für SMTP
EMAIL_RECEIVER = "deine.ziel.email@gmail.com"  # Empfänger der Job-Benachrichtigungen
SMTP_SERVER = "smtp.gmail.com"  # SMTP-Server für den Versand der E-Mail
SMTP_PORT = 587  # SMTP-Port für verschlüsselte Verbindung

# Unternehmensdaten aus externer JSON-Datei laden
def load_companies():
    if os.path.exists(COMPANIES_FILE):
        with open(COMPANIES_FILE, "r") as file:
            return json.load(file)  # Unternehmens-URLs laden
    return {}  # Falls Datei nicht existiert, leere Liste zurückgeben

# Bestehende Jobs aus der Datei laden, um doppelte Benachrichtigungen zu verhindern
def load_old_jobs():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as file:
            return json.load(file)  # Alte Jobs aus der Datei laden
    return {}  # Falls Datei nicht existiert, leere Liste zurückgeben

# Neue Jobs speichern, damit zukünftige Läufe wissen, welche Jobs bereits bekannt sind
def save_jobs(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)  # Speichert neue Jobs in JSON-Datei

# Jobs von einer Unternehmensseite extrahieren
def scrape_jobs(url):
    headers = {"User-Agent": "Mozilla/5.0"}  # Verhindert Blockierung durch Webseiten
    response = requests.get(url, headers=headers)  # Website abrufen
    soup = BeautifulSoup(response.text, "html.parser")  # HTML parsen
    
    jobs = []
    for job in soup.find_all("a", href=True):  # Alle Links auf der Seite durchsuchen
        if "job" in job["href"]:  # Prüfen, ob es sich um einen Job-Link handelt
            jobs.append(job["href"])
    return jobs  # Liste der gefundenen Job-Links zurückgeben

# E-Mail senden, falls neue Jobs gefunden wurden
def send_email(new_jobs):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg["Subject"] = "Neue Jobangebote gefunden!"  # Betreff der E-Mail
    
    # Nachrichtentext mit den gefundenen Job-Links
    body = "\n".join([f"{company}: {url}" for company, urls in new_jobs.items() for url in urls])
    msg.attach(MIMEText(body, "plain"))  # Text in die E-Mail einfügen
    
    # Verbindung zum SMTP-Server herstellen und E-Mail senden
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()  # Verschlüsselte Verbindung starten
    server.login(EMAIL_SENDER, EMAIL_PASSWORD)  # Anmeldung am E-Mail-Server
    server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())  # E-Mail senden
    server.quit()  # Verbindung schließen

# Hauptfunktion zur Überprüfung der Jobs und Benachrichtigung
def main():
    companies = load_companies()  # Unternehmens-URLs laden
    old_jobs = load_old_jobs()  # Vorherige Job-Liste laden
    new_jobs = {}  # Hier werden neue Jobs gespeichert
    
    for company, url in companies.items():  # Durch alle Unternehmen iterieren
        jobs = scrape_jobs(url)  # Aktuelle Jobs abrufen
        if company not in old_jobs:
            old_jobs[company] = []  # Falls das Unternehmen neu ist, eine leere Liste erstellen
        
        # Neue Jobs identifizieren, die noch nicht gespeichert wurden
        new_job_links = [job for job in jobs if job not in old_jobs[company]]
        if new_job_links:  # Falls neue Jobs gefunden wurden
            new_jobs[company] = new_job_links
            old_jobs[company].extend(new_job_links)  # Neue Jobs zur gespeicherten Liste hinzufügen
    
    if new_jobs:  # Falls neue Jobs gefunden wurden
        send_email(new_jobs)  # E-Mail-Benachrichtigung senden
        save_jobs(old_jobs)  # Neue Jobs speichern
        print("Neue Jobs gefunden und E-Mail gesendet!")
    else:
        print("Keine neuen Jobs gefunden.")  # Falls keine neuen Jobs vorhanden sind

if __name__ == "__main__":
    main()  # Skript ausführen
