import time
import requests
import portfolio_manager
import data_fetcher
import core_math
import os

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

def aggiorna_flag_firebase(p_id, payload):
    # La chiave nel database ora è p_id (l'ID univoco UUID o il vecchio indirizzo)
    url = f"{FIREBASE_URL}/posizioni/{p_id}.json"
    requests.patch(url, json=payload, timeout=10)

def esegui_controllo_posizioni():
    print("\n--- AVVIO CONTROLLO POSIZIONI ---")
    
    posizioni = portfolio_manager.get_tutte_posizioni()
    
    if not posizioni:
        print("❌ Nessuna posizione trovata nel JSON/Database.")
        return

    # Sostituito indirizzo_pool con p_id perché la chiave ora è l'ID
    for p_id, pos in posizioni.items():
        # Estrae l'indirizzo vero della pool. Se è un vecchio salvataggio usa p_id
        indirizzo_pool = pos.get("indirizzo_pool", p_id if str(p_id).startswith("0x") else "")
        
        if not indirizzo_pool:
            print(f"❌ Errore: indirizzo smart contract mancante per la posizione {p_id}.")
            continue

        nome_coppia = pos.get("nome_coppia", "Sconosciuta")
        print(f"\n🔎 Analizzo pool: {nome_coppia} (ID: {p_id[:8]})")
        
        pool_data = data_fetcher.get_pool_data_by_address(indirizzo_pool)
        if not pool_data:
            print("❌ Impossibile leggere dati da internet per questa pool.")
            continue
            
        simboli = nome_coppia.split('/')
        simbolo_quote = simboli[1] if len(simboli) > 1 else "USDC"
        valuta_ui = "$" if simbolo_quote.upper() in ["USDC", "USD"] else simbolo_quote.upper()
        
        # --- Estrazione Dati e Fix Inversione ---
        live_price = pool_data['prezzo_nativo']
        coppia_dexscreener = pool_data['coppia_reale']
        
        # Se l'utente ha salvato "WETH/cbBTC" ma DexScreener restituisce "cbBTC/WETH", capovolge il prezzo
        if nome_coppia != coppia_dexscreener and live_price > 0:
            live_price = 1 / live_price
            
        p_a = pos["limite_inf"]
        p_b = pos["limite_sup"]
        
        capitale_iniziale = pos.get("capitale_iniziale", 0)
        prezzo_ingresso = pos.get("prezzo_ingresso", live_price)
        apr_ingresso = pos.get("apr_ingresso", 0)
        timestamp_ingresso = pos.get("timestamp", time.time())

        print(f"📖 Range: {p_a:.6f} a {p_b:.6f} | Capitale: {capitale_iniziale} $")
        print(f"📡 Prezzo Live Letto: {live_price:.6f} {valuta_ui}")

        # --- Calcolo Distanze ---
        dist_inf_perc = abs(live_price - p_a) / live_price * 100
        dist_sup_perc = abs(p_b - live_price) / live_price * 100
        dist_minima = min(dist_inf_perc, dist_sup_perc)

        # --- Logica Decisionale ---
        fuori_range = live_price <= p_a or live_price >= p_b
        in_pre_allarme = (not fuori_range) and (dist_minima <= 5.0)

        allarme_gia_inviato = pos.get("allarme_inviato", False)
        pre_allarme_gia_inviato = pos.get("pre_allarme_inviato", False)
        
        print(f"⚖️ Esito: Fuori Range? {fuori_range} | Pre-Allarme (<=5%)? {in_pre_allarme}")

        if fuori_range:
            if not allarme_gia_inviato:
                giorni_trascorsi = max(0.0001, (time.time() - timestamp_ingresso) / 86400.0)
                L = core_math.get_liquidity_for_capital(capitale_iniziale, prezzo_ingresso, p_a, p_b)
                il_perc, il_usd, lp_value = core_math.calculate_impermanent_loss(L, live_price, prezzo_ingresso, p_a, p_b)
                
                fee_day_attuali = (capitale_iniziale * (apr_ingresso / 100)) / 365
                aero_earned = fee_day_attuali * giorni_trascorsi
                net_balance = aero_earned - il_usd
                
                testo = (
                    f"🚨 <b>ATTENZIONE: FUORI RANGE CRITICO</b> 🚨\n\n"
                    f"<b>Pool:</b> {nome_coppia}\n"
                    f"<b>ID Monitoraggio:</b> {p_id[:8]}\n"
                    f"Prezzo attuale: {live_price:.6f} {valuta_ui}\n"
                    f"Range: {p_a:.6f} - {p_b:.6f}\n\n"
                    f"💸 <b>Metriche Posizione:</b>\n"
                    f"Impermanent Loss: -{il_usd:.2f} $\n"
                    f"Fee Maturate stima: +{aero_earned:.2f} $\n"
                    f"<b>Bilancio Netto: {net_balance:.2f} $</b>"
                )
                
                invia_messaggio_telegram(testo)
                # Passiamo p_id per aggiornare i flag sul corretto ID
                aggiorna_flag_firebase(p_id, {"allarme_inviato": True, "pre_allarme_inviato": False})
                print("✅ Allarme CRITICO inviato.")
            else:
                print("🛑 Già fuori range. Nessun blocco spam.")

        elif in_pre_allarme:
            if not pre_allarme_gia_inviato:
                testo = (
                    f"⚠️ <b>PRE-ALLARME PROSSIMITÀ: {nome_coppia}</b> ⚠️\n\n"
                    f"<b>ID Monitoraggio:</b> {p_id[:8]}\n"
                    f"Il prezzo di {live_price:.6f} {valuta_ui} è arrivato al <b>{dist_minima:.1f}%</b> dal limite del range.\n"
                    f"Range impostato: {p_a:.6f} - {p_b:.6f}\n\n"
                    f"<i>Preparati a valutare un riposizionamento se il trend continua.</i>"
                )
                invia_messaggio_telegram(testo)
                aggiorna_flag_firebase(p_id, {"pre_allarme_inviato": True, "allarme_inviato": False})
                print("✅ Pre-Allarme 5% inviato.")
            else:
                print("🛑 Già in zona pre-allarme. Nessun messaggio ripetuto.")
                
        else:
            if allarme_gia_inviato or pre_allarme_gia_inviato:
                aggiorna_flag_firebase(p_id, {"allarme_inviato": False, "pre_allarme_inviato": False})
                print("✅ Prezzo rientrato in ZONA SICURA. Status allarmi resettati.")
            else:
                print("🟢 Prezzo in zona sicura. Nessuna azione richiesta.")
                
        print("----------------------------------\n")

if __name__ == "__main__":
    print("Avvio controllo schedulato da GitHub Actions...")
    esegui_controllo_posizioni()