import requests

def get_aerodrome_pool_data():
    """
    Recupera i dati esclusivamente dalla pool WETH/USDC (0.05% fee tier) su Base.
    Indirizzo univoco: 0xcdac0d6c6c59727a65f871236188350531885c43
    """
    pair_address = "0xcdac0d6c6c59727a65f871236188350531885c43"
    url = f"https://api.dexscreener.com/latest/dex/pairs/base/{pair_address}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        pair = data.get('pair')
        if not pair:
            print("Pool non trovata all'indirizzo specificato.")
            return None
            
        return {
            "prezzo_usd": float(pair.get('priceUsd', 0)),
            "volume_24h_usd": float(pair.get('volume', {}).get('h24', 0)),
            "liquidita_totale_usd": float(pair.get('liquidity', {}).get('usd', 0)),
            "pair_address": pair_address,
            "dex_rilevato": pair.get('dexId', 'aerodrome'),
            "coppia_reale": "WETH/USDC"
        }
                    
    except requests.exceptions.RequestException as e:
        print(f"Errore di connessione API: {e}")
        return None