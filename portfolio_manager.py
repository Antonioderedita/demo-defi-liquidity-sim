import json
import os
import time
import requests

FILE_POSIZIONI = "posizioni_attive.json"
FIREBASE_URL = "https://aerodrome-slipstream-default-rtdb.europe-west1.firebasedatabase.app"

def carica_dati():
    if os.path.exists(FILE_POSIZIONI):
        with open(FILE_POSIZIONI, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def salva_dati(dati):
    with open(FILE_POSIZIONI, "w") as f:
        json.dump(dati, f, indent=4)
        
    try:
        requests.put(f"{FIREBASE_URL}/posizioni.json", json=dati, timeout=5)
    except Exception as e:
        print(f"Errore Firebase: {e}")

def salva_posizione(indirizzo_pool, nome_coppia, capitale, lim_inf, lim_sup, prezzo_in, apr_in, soglia_allarme=5.0):
    posizioni = carica_dati()
    nuovo_id = str(int(time.time()))
    
    nuova_posizione = {
        "indirizzo_pool": indirizzo_pool,
        "nome_coppia": nome_coppia,
        "capitale_iniziale": capitale,
        "limite_inf": lim_inf,
        "limite_sup": lim_sup,
        "prezzo_ingresso": prezzo_in,
        "apr_ingresso": apr_in,
        "soglia_allarme": soglia_allarme,
        "timestamp": time.time()
    }
    
    posizioni[nuovo_id] = nuova_posizione
    salva_dati(posizioni)

def get_posizione(p_id):
    url = f"{FIREBASE_URL}/posizioni/{p_id}.json"
    try:
        risposta = requests.get(url, timeout=10)
        risposta.raise_for_status()
        return risposta.json() 
    except Exception as e:
        print(f"Errore lettura Firebase: {e}")
        return None

def get_tutte_posizioni():
    url = f"{FIREBASE_URL}/posizioni.json"
    try:
        risposta = requests.get(url, timeout=10)
        risposta.raise_for_status()
        dati_grezzi = risposta.json() or {}
        
        # Filtro per scartare record anomali o chiavi basate sul nome della pool
        posizioni_pulite = {
            k: v for k, v in dati_grezzi.items() 
            if v and isinstance(v, dict) and "/" not in str(k) and " " not in str(k)
        }
        return posizioni_pulite
    except Exception as e:
        print(f"Errore lettura posizioni: {e}")
        return {}

def elimina_posizione(p_id):
    posizioni = carica_dati()
    if str(p_id) in posizioni:
        del posizioni[str(p_id)]
        salva_dati(posizioni)
        
    url = f"{FIREBASE_URL}/posizioni/{p_id}.json"
    try:
        requests.delete(url, timeout=10)
        return True
    except Exception as e:
        print(f"Errore eliminazione Firebase: {e}")
        return False