import yfinance as yf
import numpy as np
import math
import pandas as pd

def calcola_metriche_storiche(simbolo_base, simbolo_quote="USDC", giorni=14):
    """
    Scarica storico da Yahoo Finance. Calcola volatilità e trend direzionale a 14 giorni.
    Gestisce automaticamente cross-pair e stablecoin.
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
            storico = yf.download(ticker_base, period=f"{giorni + 5}d", interval="1d", progress=False)
            prezzi = storico['Close'].dropna().squeeze()
        else:
            storico_base = yf.download(ticker_base, period=f"{giorni + 5}d", interval="1d", progress=False)
            storico_quote = yf.download(ticker_quote, period=f"{giorni + 5}d", interval="1d", progress=False)
            
            if storico_base.empty or storico_quote.empty:
                return 0.03, 0.0
                
            prezzi = (storico_base['Close'].squeeze() / storico_quote['Close'].squeeze()).dropna()

        if prezzi.empty:
            return 0.03, 0.0
            
        # 1. Calcolo Volatilità
        log_ret = np.log(prezzi / prezzi.shift(1)).dropna()
        volatilita_giornaliera = float(np.std(log_ret))
        
        # 2. Calcolo Trend (Regressione Lineare sugli ultimi N giorni)
        y = prezzi.values[-giorni:] 
        if len(y) < 2:
            return volatilita_giornaliera, 0.0
            
        x = np.arange(len(y))
        m, q = np.polyfit(x, y, 1)
        
        if q == 0:
            trend_perc = 0.0
        else:
            valore_inizio = q
            valore_fine = (m * (len(y) - 1)) + q
            trend_perc = (valore_fine - valore_inizio) / valore_inizio
            
        trend_limitato = float(np.clip(trend_perc, -0.15, 0.15))
        
        return volatilita_giornaliera, trend_limitato
        
    except Exception as e:
        print(f"Errore calcolo metriche storiche: {e}")
        return 0.03, 0.0

def get_chart_data(simbolo_base, simbolo_quote="USDC", periodo="1mo"):
    """
    Recupera i dati storici per il grafico interattivo in Streamlit.
    Supporta periodi come '1mo', '6mo', '1y', 'max'.
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
            storico = yf.download(ticker_base, period=periodo, interval="1d", progress=False)
            prezzi = storico['Close'].dropna().squeeze()
        else:
            storico_base = yf.download(ticker_base, period=periodo, interval="1d", progress=False)
            storico_quote = yf.download(ticker_quote, period=periodo, interval="1d", progress=False)
            
            if storico_base.empty or storico_quote.empty:
                return pd.Series(dtype=float)
                
            prezzi = (storico_base['Close'].squeeze() / storico_quote['Close'].squeeze()).dropna()
            
        return prezzi
    except Exception as e:
        print(f"Errore recupero dati grafico: {e}")
        return pd.Series(dtype=float)


def calcola_probabilita_no_touch(prezzo_attuale, price_a, price_b, volatilita_giornaliera, giorni_target=7):
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

def suggerisci_range_ottimale(prezzo_attuale, volatilita_giornaliera, giorni_target=7, z_score=1.5, offset_asimmetria=0.0):
    """
    Calcola i limiti inferiore e superiore.
    L'offset sposta il baricentro del range senza dilatarlo, mantenendo intatto l'APR potenziale.
    """
    volatilita_periodo = volatilita_giornaliera * np.sqrt(giorni_target)
    buffer_sicurezza = z_score * volatilita_periodo
    
    # Trasliamo il centro del range in base al trend atteso (es: prezzo + 8%)
    centro_traslato = prezzo_attuale * (1 + offset_asimmetria)
    
    # Costruiamo il range simmetrico attorno al NUOVO centro traslato
    limite_inf = centro_traslato * (1 - buffer_sicurezza)
    limite_sup = centro_traslato * (1 + buffer_sicurezza)
    
    return round(limite_inf, 6), round(limite_sup, 6), volatilita_periodo

if __name__ == "__main__":
    print("=== TEST METRICHE E CHART ===")
    vol, trend = calcola_metriche_storiche("WETH", "CBBTC", 14)
    print(f"Volatilità: {vol*100:.2f}% | Trend Asimmetrico: {trend*100:.2f}%")