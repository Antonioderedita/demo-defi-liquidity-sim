import json
import os
import time

FILE_PATH = "posizioni_attive.json"

def salva_posizione(indirizzo_pool, capitale, price_a, price_b, entry_price, apr_emissioni):
    """Salva i parametri di ingresso della posizione in un database JSON."""
    dati = carica_tutte_posizioni()
    
    dati[indirizzo_pool] = {
        "capitale_iniziale": capitale,
        "limite_inf": price_a,
        "limite_sup": price_b,
        "prezzo_ingresso": entry_price,
        "apr_ingresso": apr_emissioni,
        "timestamp": time.time()
    }
    
    with open(FILE_PATH, "w") as f:
        json.dump(dati, f, indent=4)
    return True

def carica_tutte_posizioni():
    """Legge il database JSON."""
    if not os.path.exists(FILE_PATH):
        return {}
    with open(FILE_PATH, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def get_posizione(indirizzo_pool):
    """Recupera la singola posizione salvata per una pool specifica."""
    dati = carica_tutte_posizioni()
    return dati.get(indirizzo_pool)