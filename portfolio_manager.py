import time
import requests
import uuid

# L'endpoint centrale del tuo database Cloud
FIREBASE_URL = "https://aerodrome-slipstream-default-rtdb.europe-west1.firebasedatabase.app"

def salva_posizione(indirizzo_pool, nome_coppia, capitale_iniziale, limite_inf, limite_sup, prezzo_ingresso, apr_ingresso):
    """Salva i dati della posizione generando un ID univoco indipendente."""
    # Genera un ID univoco di 8 caratteri
    position_id = str(uuid.uuid4())[:8]
    
    posizione = {
        "id_posizione": position_id,
        "indirizzo_pool": indirizzo_pool,
        "nome_coppia": nome_coppia,
        "capitale_iniziale": float(capitale_iniziale),
        "limite_inf": float(limite_inf),
        "limite_sup": float(limite_sup),
        "prezzo_ingresso": float(prezzo_ingresso),
        "apr_ingresso": float(apr_ingresso),
        "timestamp": time.time(),
        "allarme_inviato": False
    }
    
    # Salviamo usando il nuovo ID univoco invece dell'indirizzo pool
    url = f"{FIREBASE_URL}/posizioni/{position_id}.json"
    
    try:
        risposta = requests.put(url, json=posizione, timeout=10)
        risposta.raise_for_status()
        print(f"Nuova posizione salvata su Cloud: {position_id} per {indirizzo_pool}")
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
        return dati 
    except Exception as e:
        print(f"Errore lettura Firebase: {e}")
        return None

def get_tutte_posizioni():
    """Recupera tutte le pool salvate per permettere al bot Telegram di ciclarle."""
    url = f"{FIREBASE_URL}/posizioni.json"
    
    try:
        risposta = requests.get(url, timeout=10)
        risposta.raise_for_status()
        return risposta.json() or {}
    except Exception as e:
        print(f"Errore lettura di tutte le posizioni: {e}")
        return {}

def elimina_posizione(indirizzo_pool):
    """Elimina definitivamente una posizione da Firebase."""
    url = f"{FIREBASE_URL}/posizioni/{indirizzo_pool}.json"
    try:
        risposta = requests.delete(url, timeout=10)
        risposta.raise_for_status()
        return True
    except Exception as e:
        print(f"Errore eliminazione Firebase: {e}")
        return False