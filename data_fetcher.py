import requests

def get_pool_data_by_address(pair_address):
    """
    Recupera i dati da qualsiasi pool su Base passando l'indirizzo esatto.
    """
    url = f"https://api.dexscreener.com/latest/dex/pairs/base/{pair_address}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # FIX: DexScreener restituisce sempre un array 'pairs', anche per un singolo indirizzo
        pairs = data.get('pairs')
        if not pairs or len(pairs) == 0:
            return None
            
        pair = pairs[0]
            
        quote_sym = pair.get('quoteToken', {}).get('symbol', '')
        base_sym = pair.get('baseToken', {}).get('symbol', '')
            
        return {
            "prezzo_usd": float(pair.get('priceUsd', 0)),
            "volume_24h_usd": float(pair.get('volume', {}).get('h24', 0)),
            "liquidita_totale_usd": float(pair.get('liquidity', {}).get('usd', 0)),
            "pair_address": pair_address,
            "dex_rilevato": pair.get('dexId', 'sconosciuto'),
            "coppia_reale": f"{base_sym}/{quote_sym}"
        }
                    
    except requests.exceptions.RequestException:
        return None