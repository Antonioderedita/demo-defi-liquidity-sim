import time
import requests

# L'endpoint centrale del tuo database Cloud
FIREBASE_URL = "https://aerodrome-slipstream-default-rtdb.europe-west1.firebasedatabase.app"

def salva_posizione(indirizzo_pool, capitale_iniziale, limite_inf, limite_sup, prezzo_ingresso, apr_ingresso):
    """Salva i dati della posizione direttamente sul database Cloud Firebase."""
    posizione = {
        "capitale_iniziale": float(capitale_iniziale),
        "limite_inf": float(limite_inf),
        "limite_sup": float(limite_sup),
        "prezzo_ingresso": float(prezzo_ingresso),
        "apr_ingresso": float(apr_ingresso),
        "timestamp": time.time()
    }
    
    # In Firebase, aggiungiamo .json alla fine del path per usare l'API REST
    url = f"{FIREBASE_URL}/posizioni/{indirizzo_pool}.json"
    
    try:
        # Usiamo PUT per creare o sovrascrivere la singola posizione
        risposta = requests.put(url, json=posizione, timeout=10)
        risposta.raise_for_status()
        print(f"Posizione salvata su Cloud per {indirizzo_pool}")
        return True
    except Exception as e:
        print(f"Errore scrittura Firebase: {e}")
        return False

def get_posizione(indirizzo_pool):
    """Recupera i dati della posizione dal database Cloud Firebase."""
    url = f"{FIREBASE_URL}/posizioni/{indirizzo_pool}.json"
    
    try:
        risposta = requests.get(url, timeout=10)
        risposta.raise_for_status()
        dati = risposta.json()
        return dati # Restituisce il dizionario, o None se la pool non è salvata
    except Exception as e:
        print(f"Errore lettura Firebase: {e}")
        return None