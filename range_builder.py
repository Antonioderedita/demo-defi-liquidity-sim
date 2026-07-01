import yfinance as yf
import numpy as np
import data_fetcher

def calcola_volatilita_storica(ticker="ETH-USD", giorni=14):
    """
    Scarica lo storico dei prezzi e calcola la deviazione standard (volatilità)
    dei rendimenti giornalieri.
    """
    print(f"Scaricamento dati storici per {ticker} (Ultimi {giorni} giorni)...")
    dati = yf.download(ticker, period=f"{giorni+5}d", progress=False)
    
    if dati.empty:
        print("Errore nello scaricamento dei dati storici.")
        return None
        
    # Estraiamo i prezzi, li convertiamo in un array NumPy e li appiattiamo in 1D
    # Questo risolve in modo definitivo l'errore di broadcasting (shape mismatch)
    prezzi = dati['Close'].to_numpy().flatten()
    
    # Calcolo dei rendimenti giornalieri percentuali in puro NumPy 1D
    rendimenti = np.diff(prezzi) / prezzi[:-1]
    
    # La deviazione standard dei rendimenti è la nostra volatilità giornaliera
    volatilita_giornaliera = np.std(rendimenti)
    
    return volatilita_giornaliera

def suggerisci_range_ottimale(prezzo_attuale, volatilita_giornaliera, giorni_target=7, z_score=1.5):
    """
    Calcola i limiti inferiore e superiore basati sulla probabilità statistica.
    z_score = 1.5 copre circa l'86% degli scenari possibili (ottimo compromesso rischio/rendimento per DeFi).
    """
    # Proiettiamo la volatilità giornaliera sull'orizzonte temporale scelto dall'utente
    volatilita_periodo = volatilita_giornaliera * np.sqrt(giorni_target)
    
    limite_inf = prezzo_attuale * (1 - (z_score * volatilita_periodo))
    limite_sup = prezzo_attuale * (1 + (z_score * volatilita_periodo))
    
    # Arrotondiamo per comodità visiva e operativa
    return round(limite_inf, 2), round(limite_sup, 2), volatilita_periodo

if __name__ == "__main__":
    print("=== COSTRUTTORE RANGE INIZIALE ===")
    
    # 1. Recuperiamo il prezzo live esatto da Aerodrome
    pool_data = data_fetcher.get_aerodrome_pool_data()
    
    if pool_data:
        prezzo_live = pool_data['prezzo_usd']
        print(f"\nPrezzo Live WETH (Aerodrome): {prezzo_live:.2f} $")
        
        # 2. Calcoliamo la volatilità
        vol_daily = calcola_volatilita_storica("ETH-USD", giorni=14)
        
        if vol_daily:
            print(f"Volatilità giornaliera rilevata: {(vol_daily * 100):.2f}%")
            
            # 3. Generiamo i range raccomandati
            # Profilo Aggressivo: z=1 (Cattura più fee, ma rischio uscita più alto)
            # Profilo Bilanciato: z=1.5 (Standard DeFi)
            inf_agg, sup_agg, _ = suggerisci_range_ottimale(prezzo_live, vol_daily, giorni_target=7, z_score=1.0)
            inf_bil, sup_bil, _ = suggerisci_range_ottimale(prezzo_live, vol_daily, giorni_target=7, z_score=1.5)
            
            print("\n--- SUGGERIMENTI RANGE (Orizzonte stimato: 7 giorni) ---")
            print(f"🔥 Profilo Aggressivo (Z=1.0): {inf_agg} $ - {sup_agg} $")
            print(f"⚖️ Profilo Bilanciato (Z=1.5): {inf_bil} $ - {sup_bil} $")
            print("\nNOTA: Il profilo bilanciato copre l'86% dei movimenti storici previsti.")