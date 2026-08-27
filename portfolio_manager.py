import time
import requests

FIREBASE_URL = "https://aerodrome-slipstream-default-rtdb.europe-west1.firebasedatabase.app"

def get_tutte_posizioni():
    """Recupera tutte le posizioni da Firebase filtrando record sporchi."""
    url = f"{FIREBASE_URL}/posizioni.json"
    try:
        risposta = requests.get(url, timeout=10)
        risposta.raise_for_status()
        dati_grezzi = risposta.json() or {}
        
        # Filtro di sicurezza per scartare vecchi salvataggi anomali
        posizioni_pulite = {
            k: v for k, v in dati_grezzi.items() 
            if v and isinstance(v, dict) and "/" not in str(k) and " " not in str(k)
        }
        return posizioni_pulite
    except Exception as e:
        print(f"Errore lettura Firebase GET: {e}")
        return {}

def salva_posizione(indirizzo_pool, nome_coppia, capitale, lim_inf, lim_sup, prezzo_in, apr_in, soglia_allarme=5.0):
    """Aggiunge una nuova posizione su Firebase tramite PATCH senza sovrascrivere il DB."""
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
    
    url = f"{FIREBASE_URL}/posizioni.json"
    try:
        # PATCH aggiunge la singola posizione identificata dal suo ID univoco
        requests.patch(url, json={nuovo_id: nuova_posizione}, timeout=5)
    except Exception as e:
        print(f"Errore salvataggio Firebase PATCH: {e}")

def get_posizione(p_id):
    """Recupera i dati di una posizione specifica."""
    url = f"{FIREBASE_URL}/posizioni/{p_id}.json"
    try:
        risposta = requests.get(url, timeout=10)
        risposta.raise_for_status()
        return risposta.json() 
    except Exception as e:
        print(f"Errore lettura posizione singola: {e}")
        return None

def elimina_posizione(p_id):
    """Elimina definitivamente una posizione da Firebase."""
    url = f"{FIREBASE_URL}/posizioni/{p_id}.json"
    try:
        requests.delete(url, timeout=10)
        return True
    except Exception as e:
        print(f"Errore eliminazione Firebase: {e}")
        return False