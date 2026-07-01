import requests

def get_aerodrome_pool_data():
    """
    Recupera i dati della pool utilizzando lo Smart Contract Address di WETH su Base.
    Ordina per liquidità decrescente per garantire la selezione della pool principale.
    """
    weth_base_address = "0x4200000000000000000000000000000000000006"
    url = f"https://api.dexscreener.com/latest/dex/tokens/{weth_base_address}"
    
    try:
        # Aggiunto timeout rigido a 10 secondi per evitare freeze dell'applicazione
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        pairs = data.get('pairs', [])
        if not pairs:
            print("Nessuna pool trovata per l'indirizzo fornito.")
            return None
            
        # Correzione Claude: Ordina le pool per liquidità USD decrescente
        pairs_ordinate = sorted(
            pairs, 
            key=lambda p: float(p.get('liquidity', {}).get('usd', 0)), 
            reverse=True
        )
        
        for pair in pairs_ordinate:
            chain = pair.get('chainId', '')
            dex = pair.get('dexId', '').lower()
            
            if chain == 'base' and 'aerodrome' in dex:
                quote_sym = pair.get('quoteToken', {}).get('symbol', '').upper()
                
                if 'USD' in quote_sym:
                    return {
                        "prezzo_usd": float(pair.get('priceUsd', 0)),
                        "volume_24h_usd": float(pair.get('volume', {}).get('h24', 0)),
                        "liquidita_totale_usd": float(pair.get('liquidity', {}).get('usd', 0)),
                        "pair_address": pair.get('pairAddress'),
                        "dex_rilevato": dex,
                        "coppia_reale": f"WETH/{quote_sym}"
                    }
                    
        print("Pool Aerodrome/Base valida non trovata dopo il filtraggio.")
        return None
        
    except requests.exceptions.Timeout:
        print("Errore: La richiesta a DexScreener è andata in timeout.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Errore di connessione API: {e}")
        return None