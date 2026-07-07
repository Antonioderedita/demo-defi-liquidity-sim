import yfinance as yf
import numpy as np
import data_fetcher
import math

def calcola_volatilita_storica(simbolo_base, giorni=14):
    """
    Scarica la volatilità dinamicamente mappando il token della pool 
    al ticker corretto su Yahoo Finance.
    """
    # Dizionario di conversione token -> ticker Yahoo Finance
    mappa_ticker = {
        "WETH": "ETH-USD",
        "ETH": "ETH-USD",
        "CBBTC": "BTC-USD",
        "WBTC": "BTC-USD",
        "AERO": "AERO-USD",
        "USDC": "USDC-USD"
    }
    
    # Se il token non è in mappa, prova il formato standard SIMBOLO-USD
    ticker_yf = mappa_ticker.get(simbolo_base.upper(), f"{simbolo_base.upper()}-USD")
    
    try:
        storico = yf.download(ticker_yf, period=f"{giorni + 5}d", interval="1d", progress=False)
        if storico.empty:
            return 0.03 # Fallback 3%
            
        prezzi = storico['Close'].dropna()
        log_ret = np.log(prezzi / prezzi.shift(1)).dropna()
        volatilita_giornaliera = np.std(log_ret)
        
        return float(volatilita_giornaliera)
    except Exception:
        return 0.03

def calcola_probabilita_no_touch(prezzo_attuale, price_a, price_b, volatilita_giornaliera, giorni_target=7):
    """
    (NUOVA METRICA) Calcola la probabilità che il prezzo NON tocchi MAI i limiti 
    durante l'intero orizzonte temporale, usando il Principio di Riflessione.
    """
    if volatilita_giornaliera <= 0 or prezzo_attuale <= 0 or price_a >= price_b:
        return 0.0
        
    if prezzo_attuale <= price_a or prezzo_attuale >= price_b:
        return 0.0

    vol_periodo = volatilita_giornaliera * math.sqrt(giorni_target)
    
    # Distanze percentuali dai limiti
    dist_inf = (prezzo_attuale - price_a) / prezzo_attuale
    dist_sup = (price_b - prezzo_attuale) / prezzo_attuale
    
    z_inf = dist_inf / vol_periodo
    z_sup = dist_sup / vol_periodo
    
    # P(toccare la barriera) = 2 * P(terminale oltre la barriera)
    # math.erfc(x) = 1 - math.erf(x), ottimizzato per precisione
    prob_touch_inf = math.erfc(z_inf / math.sqrt(2.0))
    prob_touch_sup = math.erfc(z_sup / math.sqrt(2.0))
    
    # Probabilità di sopravvivenza (approssimazione conservativa a doppia barriera)
    prob_no_touch = 1.0 - (prob_touch_inf + prob_touch_sup)
    
    return max(0.0, prob_no_touch) * 100.0

def calcola_probabilita_in_range(prezzo_attuale, price_a, price_b, volatilita_giornaliera, giorni_target=7):
    """
    Calcola la probabilità statistica (0-100%) che il prezzo rimanga 
    all'interno del range selezionato per l'orizzonte temporale dato.
    """
    if volatilita_giornaliera <= 0 or prezzo_attuale <= 0:
        return 0.0

    # Volatilità proiettata sull'orizzonte temporale
    vol_periodo = volatilita_giornaliera * math.sqrt(giorni_target)

    # Distanza percentuale dei limiti dal prezzo attuale
    dist_a = (price_a - prezzo_attuale) / prezzo_attuale
    dist_b = (price_b - prezzo_attuale) / prezzo_attuale

    # Calcolo degli Z-score
    z_a = dist_a / vol_periodo
    z_b = dist_b / vol_periodo

    # Calcolo probabilità usando la Funzione di Errore (CDF normale)
    cdf_a = (1.0 + math.erf(z_a / math.sqrt(2.0))) / 2.0
    cdf_b = (1.0 + math.erf(z_b / math.sqrt(2.0))) / 2.0

    probabilita = cdf_b - cdf_a
    return max(0.0, probabilita) * 100

def suggerisci_range_ottimale(prezzo_attuale, volatilita_giornaliera, giorni_target=7, z_score=1.5):
    """
    Calcola i limiti inferiore e superiore basati sulla probabilità statistica.
    z_score = 1.5 copre circa l'86% degli scenari possibili (ottimo compromesso rischio/rendimento per DeFi).
    """
    volatilita_periodo = volatilita_giornaliera * np.sqrt(giorni_target)
    
    limite_inf = prezzo_attuale * (1 - (z_score * volatilita_periodo))
    limite_sup = prezzo_attuale * (1 + (z_score * volatilita_periodo))
    
    return round(limite_inf, 2), round(limite_sup, 2), volatilita_periodo

if __name__ == "__main__":
    print("=== COSTRUTTORE RANGE INIZIALE ===")
    
    # FIX: Chiamata aggiornata alla nuova funzione dinamica con l'indirizzo di default
    pool_data = data_fetcher.get_pool_data_by_address("0xcdac0d6c6c59727a65f871236188350531885c43")
    
    if pool_data:
        prezzo_live = pool_data['prezzo_usd']
        print(f"\nPrezzo Live Token Base: {prezzo_live:.2f} $")
        
        # FIX: Passiamo il simbolo estratto dinamicamente invece dell'hardcoded "ETH-USD"
        simbolo_base = pool_data['coppia_reale'].split('/')[0]
        vol_daily = calcola_volatilita_storica(simbolo_base, giorni=14)
        
        if vol_daily:
            print(f"Volatilità giornaliera rilevata ({simbolo_base}): {(vol_daily * 100):.2f}%")
            
            inf_agg, sup_agg, _ = suggerisci_range_ottimale(prezzo_live, vol_daily, giorni_target=7, z_score=1.0)
            inf_bil, sup_bil, _ = suggerisci_range_ottimale(prezzo_live, vol_daily, giorni_target=7, z_score=1.5)
            
            print("\n--- SUGGERIMENTI RANGE (Orizzonte stimato: 7 giorni) ---")
            print(f"🔥 Profilo Aggressivo (Z=1.0): {inf_agg} $ - {sup_agg} $")
            print(f"⚖️ Profilo Bilanciato (Z=1.5): {inf_bil} $ - {sup_bil} $")