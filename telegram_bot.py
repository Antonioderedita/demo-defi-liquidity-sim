import time
import requests
import portfolio_manager
import data_fetcher
import core_math
import fee_estimator

# --- CONFIGURAZIONE TELEGRAM ---
# Inserisci qui i dati che otterrai da BotFather
TELEGRAM_BOT_TOKEN = "8779936791:AAEWTCCxDOyVqK05eXGc07_yMdz0QJfGvfY"
TELEGRAM_CHAT_ID = "5955452088"

def invia_messaggio_telegram(testo):
    """Invia un messaggio di testo formattato in HTML tramite l'API di Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": testo,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Errore invio Telegram: {e}")

def esegui_controllo_posizione():
    print("Avvio controllo posizione...")
    
    # Per ora testiamo sulla pool salvata di default
    indirizzo_pool = "0xcdac0d6c6c59727a65f871236188350531885c43"
    indirizzo_gauge = "0x519BBD1Dd8C6A94C46080E24f316c14Ee758C025"
    
    pos = portfolio_manager.get_posizione(indirizzo_pool)
    if not pos:
        print("Nessuna posizione trovata nel database.")
        return

    # 1. Recupero dati live
    pool_data = data_fetcher.get_pool_data_by_address(indirizzo_pool)
    if not pool_data:
        return
        
    live_price = pool_data['prezzo_usd']
    tvl = pool_data['liquidita_totale_usd']
    apr_dinamico = data_fetcher.get_apr_from_web3(indirizzo_gauge, tvl) or pos["apr_ingresso"]

    # 2. Estrazione dati salvati
    cap_in = pos["capitale_iniziale"]
    p_in = pos["prezzo_ingresso"]
    p_a = pos["limite_inf"]
    p_b = pos["limite_sup"]
    timestamp_in = pos.get("timestamp", time.time())
    
    # 3. Matematica Core
    giorni_reali = max(0.0001, (time.time() - timestamp_in) / 86400.0)
    L = core_math.get_liquidity_for_capital(cap_in, p_in, p_a, p_b)
    _, il_usd, _ = core_math.calculate_impermanent_loss(L, live_price, p_in, p_a, p_b)
    fee_day_attuali, _ = fee_estimator.stima_rendimenti_cl(cap_in, live_price, p_a, p_b, apr_dinamico)
    
    fee_totali = fee_day_attuali * giorni_reali
    net_profit = fee_totali - il_usd
    
    fuori_range = live_price <= p_a or live_price >= p_b
    
    # 4. Logica di Innesco Allarme
    # Mandiamo il messaggio SOLO se siamo fuori range. Finché è dentro, lasciamo lavorare l'interesse composto.
    if fuori_range:
        status_icon = "🟢" if net_profit > 0 else "🔴"
        consiglio = "RIBILANCIA ORA (Sei in profitto netto)" if net_profit > 0 else "ATTENDI (L'IL supera le fee)"
        
        messaggio = (
            f"⚠️ <b>ALLARME SLIPSTREAM: FUORI RANGE</b>\n\n"
            f"Prezzo Attuale: <b>{live_price:.4f} $</b>\n"
            f"Range Impostato: {p_a} - {p_b} $\n\n"
            f"📊 <b>DIAGNOSTICA:</b>\n"
            f"• Tempo trascorso: {giorni_reali:.1f} giorni\n"
            f"• Fee Incassate: +{fee_totali:.2f} $\n"
            f"• Impermanent Loss: -{il_usd:.2f} $\n"
            f"• Net Profit: {status_icon} <b>{net_profit:.2f} $</b>\n\n"
            f"🎯 <b>AZIONE:</b> {consiglio}"
        )
        
        invia_messaggio_telegram(messaggio)
        print("Allarme inviato con successo.")
    else:
        print(f"Prezzo in range ({live_price:.4f} $). Nessuna azione richiesta.")

if __name__ == "__main__":
    esegui_controllo_posizione()