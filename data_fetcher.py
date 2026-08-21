import requests
from web3 import Web3

def get_pool_data_by_address(pair_address):
    """
    Recupera i dati da qualsiasi pool su Base passando l'indirizzo esatto.
    """
    url = f"https://api.dexscreener.com/latest/dex/pairs/base/{pair_address}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # DexScreener restituisce sempre un array 'pairs', anche per un singolo indirizzo
        pairs = data.get('pairs')
        if not pairs or len(pairs) == 0:
            return None
            
        pair = pairs[0]
            
        quote_sym = pair.get('quoteToken', {}).get('symbol', '')
        base_sym = pair.get('baseToken', {}).get('symbol', '')
            
        return {
            "prezzo_usd": float(pair.get('priceUsd', 0)),
            # FIX: Aggiunto priceNative. Restituisce il valore del token Base espresso in token Quote.
            "prezzo_nativo": float(pair.get('priceNative', 0)), 
            "volume_24h_usd": float(pair.get('volume', {}).get('h24', 0)),
            "liquidita_totale_usd": float(pair.get('liquidity', {}).get('usd', 0)),
            "pair_address": pair_address,
            "dex_rilevato": pair.get('dexId', 'sconosciuto'),
            "coppia_reale": f"{base_sym}/{quote_sym}"
        }
                    
    except requests.exceptions.RequestException:
        return None
    
def get_apr_from_web3(gauge_address, tvl_pool_usd):
    """
    Legge le emissioni direttamente dallo Smart Contract del Gauge su Base Network.
    """
    if not gauge_address or tvl_pool_usd <= 0:
        return None
        
    try:
        # Connessione al nodo pubblico di Base
        w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
        gauge_address = w3.to_checksum_address(gauge_address)
        
        abi = [{
            "inputs": [],
            "name": "rewardRate",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }]
        
        gauge_contract = w3.eth.contract(address=gauge_address, abi=abi)
        
        # 1. Lettura On-Chain
        reward_rate_wei = gauge_contract.functions.rewardRate().call()
        aero_per_sec = reward_rate_wei / (10**18)
        
        if aero_per_sec == 0:
            return 0.0
            
        # 2. Ottenimento prezzo AERO tramite l'indirizzo del Token (più stabile della Pool)
        aero_token_address = "0x940181a94A35A4569E4529A3CDfB74e38FD98631"
        resp = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{aero_token_address}", timeout=10).json()
        
        # Controllo di sicurezza strutturale
        pairs = resp.get('pairs')
        if not pairs:
            print("DexScreener non ha restituito dati validi per AERO.")
            return None
            
        prezzo_aero = float(pairs[0]['priceUsd'])
        
        # 3. Calcolo Matematico dell'APR
        emissioni_annue_usd = aero_per_sec * 31536000 * prezzo_aero # (60 * 60 * 24 * 365)
        apr_reale = (emissioni_annue_usd / tvl_pool_usd) * 100
        
        return float(apr_reale)
        
    except Exception as e:
        print(f"Errore lettura Web3: {e}")
        return None