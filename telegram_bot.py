import time
import requests
import portfolio_manager
import data_fetcher
import core_math
import fee_estimator
import os

# --- CONFIGURAZIONE TELEGRAM E DATABASE ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
FIREBASE_URL = "https://aerodrome-slipstream-default-rtdb.europe-west1.firebasedatabase.app"

def invia_messaggio_telegram(testo):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": testo,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload, timeout=10)

def aggiorna_status_allarme(indirizzo_pool, stato_allarme):
    """Aggiorna il flag su Firebase per evitare lo spam di messaggi."""
    url = f"{FIREBASE_URL}/posizioni/{indirizzo_pool}.json"
    requests.patch(url, json={"allarme_inviato": stato_allarme}, timeout=10)

def esegui_controllo_posizione():
    print("\n--- AVVIO CONTROLLO POSIZIONE ---")
    indirizzo_pool = "0xcdac0d6c6c59727a65f871236188350531885c43"
    
    pos = portfolio_manager.get_posizione(indirizzo_pool)
    if not pos:
        print("❌ Nessuna posizione trovata nel JSON/Database.")
        return

    pool_data = data_fetcher.get_pool_data_by_address(indirizzo_pool)
    if not pool_data:
        print("❌ Impossibile leggere dati da internet.")
        return
        
    # --- Estrazione Dati ---
    live_price = pool_data['prezzo_usd']
    p_a = pos["limite_inf"]
    p_b = pos["limite_sup"]
    
    # Variabili aggiuntive dal database per i calcoli
    capitale_iniziale = pos.get("capitale_iniziale", 0)
    prezzo_ingresso = pos.get("prezzo_ingresso", live_price)
    apr_ingresso = pos.get("apr_ingresso", 0)
    timestamp_ingresso = pos.get("timestamp", time.time())

    print(f"📖 Dati Letti -> Range: {p_a:.4f} a {p_b:.4f} | Capitale: {capitale_iniziale}")
    print(f"📡 Prezzo Live Letto: {live_price:.4f} $")

    # --- Logica Decisionale e Anti-Spam ---
    fuori_range = live_price <= p_a or live_price >= p_b
    allarme_gia_inviato = pos.get("allarme_inviato", False)
    
    print(f"⚖️ Esito Valutazione: Fuori Range? {fuori_range} | Già inviato? {allarme_gia_inviato}")

    if fuori_range:
        if not allarme_gia_inviato:
            
            # INSERISCI QUI I PARAMETRI CORRETTI PER LE TUE FUNZIONI
            il_loss = core_math.calculate_impermanent_loss(...) 
            
            # INSERISCI QUI I PARAMETRI CORRETTI PER LE TUE FUNZIONI
            aero_earned = fee_estimator.calcola_emissioni(...)  
            
            net_balance = aero_earned + il_loss
            
            testo = (
                f"🚨 <b>ATTENZIONE: FUORI RANGE</b> 🚨\n\n"
                f"Prezzo attuale: {live_price:.4f} $\n"
                f"Range: {p_a:.4f} - {p_b:.4f}\n\n"
                f"💸 <b>Metriche Posizione:</b>\n"
                f"Impermanent Loss: {il_loss:.2f} $\n"
                f"AERO Maturati: +{aero_earned:.2f} $\n"
                f"<b>Bilancio Netto: {net_balance:.2f} $</b>"
            )
            
            invia_messaggio_telegram(testo)
            aggiorna_status_allarme(indirizzo_pool, True)
            print("✅ Allarme inviato e status aggiornato su Firebase.")
        else:
            print("🛑 Prezzo fuori range, ma allarme già inviato. Nessun blocco spam.")
            
    else:
        if allarme_gia_inviato:
            aggiorna_status_allarme(indirizzo_pool, False)
            print("✅ Prezzo rientrato nel range. Status allarme resettato.")
        else:
            print("🟢 Prezzo in range. Nessuna azione richiesta.")
            
    print("----------------------------------\n")

if __name__ == "__main__":
    print("Avvio controllo schedulato da GitHub Actions...")
    esegui_controllo_posizione()