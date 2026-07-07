import time
import requests
import portfolio_manager
import data_fetcher
import core_math
import fee_estimator

# --- CONFIGURAZIONE TELEGRAM ---
TELEGRAM_BOT_TOKEN = "8779936791:AAEWTCCxDOyVqK05eXGc07_yMdz0QJfGvfY"
TELEGRAM_CHAT_ID = "5955452088"

def invia_messaggio_telegram(testo):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": testo,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload, timeout=10)

def esegui_controllo_posizione():
    print("\n--- AVVIO CONTROLLO POSIZIONE ---")
    indirizzo_pool = "0xcdac0d6c6c59727a65f871236188350531885c43"
    indirizzo_gauge = "0x519BBD1Dd8C6A94C46080E24f316c14Ee758C025"
    
    pos = portfolio_manager.get_posizione(indirizzo_pool)
    if not pos:
        print("❌ Nessuna posizione trovata nel JSON.")
        return

    # Log Dati JSON
    print(f"📖 Dati JSON Letti -> Range: {pos['limite_inf']:.4f} a {pos['limite_sup']:.4f}")

    pool_data = data_fetcher.get_pool_data_by_address(indirizzo_pool)
    if not pool_data:
        print("❌ Impossibile leggere dati da internet.")
        return
        
    live_price = pool_data['prezzo_usd']
    print(f"📡 Prezzo Live Letto: {live_price:.4f} $")

    p_a = pos["limite_inf"]
    p_b = pos["limite_sup"]
    
    # Valutazione Booleana
    fuori_range = live_price <= p_a or live_price >= p_b
    print(f"⚖️ Esito Valutazione: Fuori Range? {fuori_range}")

    if fuori_range:
        # Per ora mandiamo un messaggio semplice per confermare l'innesco
        invia_messaggio_telegram(f"TEST INNESCO: Il prezzo ({live_price:.4f}) ha superato il range ({p_a} - {p_b})!")
        print("✅ Allarme inviato a Telegram.")
    else:
        print("🛑 Prezzo in range. Nessuna azione richiesta.")
    print("----------------------------------\n")

if __name__ == "__main__":
    print("Avvio controllo schedulato da GitHub Actions...")
    esegui_controllo_posizione()