import yfinance as yf
import numpy as np
import pandas as pd

def calcola_metriche_storiche(simbolo_base, simbolo_quote="USDC", giorni=14):
    """
    Scarica storico da Yahoo Finance usando Ticker.history() per maggiore stabilità.
    Restituisce: (volatilita_giornaliera, trend_reale, trend_limitato_per_math)
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
            # FIX: Ticker().history è immune ai crash di formato di yf.download()
            storico = yf.Ticker(ticker_base).history(period=f"{giorni + 5}d", interval="1d")
            prezzi = storico['Close'].dropna()
        else:
            t_base = yf.Ticker(ticker_base).history(period=f"{giorni + 5}d", interval="1d")
            t_quote = yf.Ticker(ticker_quote).history(period=f"{giorni + 5}d", interval="1d")
            
            if t_base.empty or t_quote.empty:
                return 0.03, 0.0, 0.0
                
            prezzi = (t_base['Close'] / t_quote['Close']).dropna()

        if prezzi.empty:
            return 0.03, 0.0, 0.0
            
        # 1. Calcolo Volatilità
        log_ret = np.log(prezzi / prezzi.shift(1)).dropna()
        volatilita_giornaliera = float(np.std(log_ret))
        
        # 2. Calcolo Trend (Regressione Lineare)
        y = prezzi.values[-giorni:] 
        if len(y) < 2:
            return volatilita_giornaliera, 0.0, 0.0
            
        x = np.arange(len(y))
        m, q = np.polyfit(x, y, 1)
        
        if q == 0:
            trend_perc = 0.0
        else:
            valore_inizio = q
            valore_fine = (m * (len(y) - 1)) + q
            trend_perc = (valore_fine - valore_inizio) / valore_inizio
            
        trend_limitato = float(np.clip(trend_perc, -0.15, 0.15))
        
        return volatilita_giornaliera, float(trend_perc), trend_limitato
        
    except Exception as e:
        print(f"Errore calcolo metriche storiche: {e}")
        return 0.03, 0.0, 0.0

def get_chart_data(simbolo_base, simbolo_quote="USDC", periodo="1mo"):
    """
    Recupera i dati storici per il grafico interattivo in Streamlit usando yf.Ticker().
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
    
    config_temporale = {
        "1d": {"period": "1d", "interval": "5m"},
        "1w": {"period": "5d", "interval": "1h"}, 
        "1mo": {"period": "1mo", "interval": "1d"},
        "6mo": {"period": "6mo", "interval": "1d"},
        "1y": {"period": "1y", "interval": "1d"},
        "5y": {"period": "5y", "interval": "1d"},
        "max": {"period": "max", "interval": "1d"}
    }
    
    cfg = config_temporale.get(periodo, {"period": "1mo", "interval": "1d"})
    
    try:
        is_stablecoin = simbolo_quote.upper() in ["USDC", "USDT", "USD", "DAI", "EURC"]
        
        if is_stablecoin:
            storico = yf.Ticker(ticker_base).history(period=cfg["period"], interval=cfg["interval"])
            prezzi = storico['Close'].dropna()
        else:
            t_base = yf.Ticker(ticker_base).history(period=cfg["period"], interval=cfg["interval"])
            t_quote = yf.Ticker(ticker_quote).history(period=cfg["period"], interval=cfg["interval"])
            
            if t_base.empty or t_quote.empty:
                return pd.Series(dtype=float)
                
            prezzi = (t_base['Close'] / t_quote['Close']).dropna()
            
        return prezzi
    except Exception as e:
        print(f"Errore recupero dati grafico: {e}")
        return pd.Series(dtype=float)

def genera_scenari_montecarlo(prezzo_attuale, volatilita_giornaliera, trend_periodo, giorni_target=14, num_simulazioni=10000):
    if prezzo_attuale <= 0 or volatilita_giornaliera <= 0:
        return np.array([])
        
    mu_daily = trend_periodo / giorni_target
    Z = np.random.standard_normal((giorni_target, num_simulazioni))
    daily_returns = np.exp((mu_daily - 0.5 * volatilita_giornaliera**2) + volatilita_giornaliera * Z)
    price_paths = prezzo_attuale * np.cumprod(daily_returns, axis=0)
    prezzo_iniziale_array = np.full((1, num_simulazioni), prezzo_attuale)
    full_paths = np.vstack([prezzo_iniziale_array, price_paths])
    
    return full_paths

def valuta_probabilita_mc(paths, prezzo_attuale, price_a, price_b):
    if paths.size == 0 or price_a >= price_b:
        return {"stato": "ERROR", "prob_in_range": 0.0, "prob_no_touch": 0.0, "prob_rientro": 0.0}
        
    num_simulazioni = paths.shape[1]
    
    if price_a <= prezzo_attuale <= price_b:
        prezzi_finali = paths[-1, :]
        in_range_finali = np.sum((prezzi_finali >= price_a) & (prezzi_finali <= price_b))
        prob_in_range = (in_range_finali / num_simulazioni) * 100.0
        
        minimi_cammini = np.min(paths, axis=0)
        massimi_cammini = np.max(paths, axis=0)
        mai_usciti = np.sum((minimi_cammini >= price_a) & (massimi_cammini <= price_b))
        prob_no_touch = (mai_usciti / num_simulazioni) * 100.0
        
        return {
            "stato": "IN_RANGE",
            "prob_in_range": round(prob_in_range, 1),
            "prob_no_touch": round(prob_no_touch, 1),
            "prob_rientro": 0.0
        }
    else:
        if prezzo_attuale < price_a:
            massimi_cammini = np.max(paths, axis=0)
            rientrati = np.sum(massimi_cammini >= price_a)
        else:
            minimi_cammini = np.min(paths, axis=0)
            rientrati = np.sum(minimi_cammini <= price_b)
            
        prob_rientro = (rientrati / num_simulazioni) * 100.0
        
        return {
            "stato": "OUT_OF_RANGE",
            "prob_in_range": 0.0,
            "prob_no_touch": 0.0,
            "prob_rientro": round(prob_rientro, 1)
        }

def suggerisci_range_ottimale(prezzo_attuale, volatilita_giornaliera, giorni_target=7, z_score=1.5, offset_asimmetria=0.0):
    volatilita_periodo = volatilita_giornaliera * np.sqrt(giorni_target)
    buffer_sicurezza = z_score * volatilita_periodo
    
    # Safety lock dinamico: impedisce allo shift del trend di sputare il prezzo fuori
    max_shift_consentito = buffer_sicurezza * 0.80
    offset_effettivo = np.clip(offset_asimmetria, -max_shift_consentito, max_shift_consentito)
    
    centro_traslato = prezzo_attuale * (1 + offset_effettivo)
    limite_inf = centro_traslato * (1 - buffer_sicurezza)
    limite_sup = centro_traslato * (1 + buffer_sicurezza)
    
    return round(limite_inf, 6), round(limite_sup, 6), volatilita_periodo