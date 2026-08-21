import yfinance as yf
import numpy as np
import data_fetcher
import math

def calcola_volatilita_storica(simbolo_base, simbolo_quote="USDC", giorni=14):
    """
    Scarica la volatilità dinamicamente. Supporta coppie contro USD e 
    cross pair crypto-crypto (calcolando la volatilità del loro rapporto).
    """
    mappa_ticker = {
        "WETH": "ETH-USD",
        "ETH": "ETH-USD",
        "CBBTC": "BTC-USD",
        "WBTC": "BTC-USD",
        "AERO": "AERO-USD",
        "USDC": "USDC-USD",
        "USD": "USDC-USD"
    }
    
    ticker_base = mappa_ticker.get(simbolo_base.upper(), f"{simbolo_base.upper()}-USD")
    ticker_quote = mappa_ticker.get(simbolo_quote.upper(), f"{simbolo_quote.upper()}-USD")
    
    try:
        is_stablecoin = simbolo_quote.upper() in ["USDC", "USDT", "USD", "DAI", "EURC"]
        
        if is_stablecoin:
            # Calcolo standard per pool contro dollaro
            storico = yf.download(ticker_base, period=f"{giorni + 5}d", interval="1d", progress=False)
            prezzi = storico['Close'].dropna().squeeze()
        else:
            # Calcolo per cross pair (es. WETH/cbBTC) -> Rapporto Base/Quote
            storico_base = yf.download(ticker_base, period=f"{giorni + 5}d", interval="1d", progress=False)
            storico_quote = yf.download(ticker_quote, period=f"{giorni + 5}d", interval="1d", progress=False)
            
            if storico_base.empty or storico_quote.empty:
                return 0.03
                
            prezzi_base = storico_base['Close'].squeeze()
            prezzi_quote = storico_quote['Close'].squeeze()
            
            # Crea la serie storica del rapporto (es. quanti BTC servono per 1 ETH)
            prezzi = (prezzi_base / prezzi_quote).dropna()

        if prezzi.empty:
            return 0.03
            
        log_ret = np.log(prezzi / prezzi.shift(1)).dropna()
        volatilita_giornaliera = np.std(log_ret)
        
        return float(volatilita_giornaliera)
    except Exception as e:
        print(f"Errore calcolo volatilità: {e}")
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
    
    dist_inf = (prezzo_attuale - price_a) / prezzo_attuale
    dist_sup = (price_b - prezzo_attuale) / prezzo_attuale
    
    z_inf = dist_inf / vol_periodo
    z_sup = dist_sup / vol_periodo
    
    prob_touch_inf = math.erfc(z_inf / math.sqrt(2.0))
    prob_touch_sup = math.erfc(z_sup / math.sqrt(2.0))
    
    prob_no_touch = 1.0 - (prob_touch_inf + prob_touch_sup)
    
    return max(0.0, prob_no_touch) * 100.0

def calcola_probabilita_in_range(prezzo_attuale, price_a, price_b, volatilita_giornaliera, giorni_target=7):
    """
    Calcola la probabilità statistica (0-100%) che il prezzo rimanga 
    all'interno del range selezionato per l'orizzonte temporale dato.
    """
    if volatilita_giornaliera <= 0 or prezzo_attuale <= 0:
        return 0.0

    vol_periodo = volatilita_giornaliera * math.sqrt(giorni_target)

    dist_a = (price_a - prezzo_attuale) / prezzo_attuale
    dist_b = (price_b - prezzo_attuale) / prezzo_attuale

    z_a = dist_a / vol_periodo
    z_b = dist_b / vol_periodo

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
    
    # FIX: Arrotondamento portato a 6 cifre per gestire i micro-rapporti (es. ETH/BTC = 0.0385)
    return round(limite_inf, 6), round(limite_sup, 6), volatilita_periodo

if __name__ == "__main__":
    print("=== COSTRUTTORE RANGE INIZIALE ===")
    
    pool_data = data_fetcher.get_pool_data_by_address("0x3fe04a59ebd38cf06080a6f60a98d124eb59392a")
    
    if pool_data:
        # Nota: in __main__ usiamo un blocco generico, ma il prezzo deve riflettere il rapporto corretto
        simboli = pool_data['coppia_reale'].split('/')
        simbolo_base = simboli[0]
        simbolo_quote = simboli[1] if len(simboli) > 1 else "USDC"
        
        # Testiamo se è la pool WETH/cbBTC (indirizzo placeholder) o simili
        prezzo_live = pool_data['prezzo_usd'] 
        
        print(f"\nCoppia rilevata: {simbolo_base}/{simbolo_quote}")
        
        vol_daily = calcola_volatilita_storica(simbolo_base, simbolo_quote, giorni=14)
        
        if vol_daily:
            print(f"Volatilità giornaliera rilevata: {(vol_daily * 100):.2f}%")
            
            inf_agg, sup_agg, _ = suggerisci_range_ottimale(prezzo_live, vol_daily, giorni_target=7, z_score=1.0)
            inf_bil, sup_bil, _ = suggerisci_range_ottimale(prezzo_live, vol_daily, giorni_target=7, z_score=1.5)
            
            print("\n--- SUGGERIMENTI RANGE (Orizzonte stimato: 7 giorni) ---")
            print(f"🔥 Profilo Aggressivo (Z=1.0): {inf_agg} - {sup_agg}")
            print(f"⚖️ Profilo Bilanciato (Z=1.5): {inf_bil} - {sup_bil}")