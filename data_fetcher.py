import requests

def get_aerodrome_pool_data():
    """
    Recupera i dati della pool utilizzando lo Smart Contract Address di WETH su Base.
    Questo elimina qualsiasi ambiguità con altre blockchain (Solana, Scroll, ecc.).
    """
    # Smart Contract Address ufficiale di WETH su rete Base
    weth_base_address = "0x4200000000000000000000000000000000000006"
    
    # Endpoint specifico per token address
    url = f"https://api.dexscreener.com/latest/dex/tokens/{weth_base_address}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        for pair in data.get('pairs', []):
            chain = pair.get('chainId', '')
            dex = pair.get('dexId', '').lower()
            
            # Filtriamo esattamente per Base e Aerodrome
            if chain == 'base' and 'aerodrome' in dex:
                quote_sym = pair.get('quoteToken', {}).get('symbol', '').upper()
                
                # Cerchiamo la controparte in dollari (USDC o USDbC)
                if 'USD' in quote_sym:
                    return {
                        "prezzo_usd": float(pair.get('priceUsd', 0)),
                        "volume_24h_usd": float(pair.get('volume', {}).get('h24', 0)),
                        "liquidita_totale_usd": float(pair.get('liquidity', {}).get('usd', 0)),
                        "pair_address": pair.get('pairAddress'),
                        "dex_rilevato": dex,
                        "coppia_reale": f"WETH/{quote_sym}"
                    }
                    
        print("Pool non trovata nemmeno cercando per Smart Contract.")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Errore di connessione API: {e}")
        return None

if __name__ == "__main__":
    print("Connessione a DexScreener tramite Smart Contract in corso...")
    pool_data = get_aerodrome_pool_data()
    
    if pool_data:
        print("\n--- DATI REALI DELLA POOL ---")
        print(f"DEX Rilevato: {pool_data['dex_rilevato']}")
        print(f"Coppia On-Chain: {pool_data['coppia_reale']}")
        print(f"Indirizzo Pool: {pool_data['pair_address']}")
        print(f"Prezzo (WETH): {pool_data['prezzo_usd']:.2f} $")
        print(f"Volume Scambi (24h): {pool_data['volume_24h_usd']:,.2f} $")
        print(f"Liquidità Totale (TVL): {pool_data['liquidita_totale_usd']:,.2f} $")