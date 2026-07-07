import requests
from web3 import Web3

def diagnostica_web3():
    gauge_address = "0x519BBD1Dd8C6A94C46080E24f316c14Ee758C025"
    
    print("1. Test Connessione al Nodo Base...")
    w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
    if not w3.is_connected():
        print("❌ FALLITO: Impossibile connettersi al nodo. Rate limit o RPC down.")
        return
    print("✅ Nodo connesso.")
    
    try:
        gauge_checksum = w3.to_checksum_address(gauge_address)
        abi = [{
            "inputs": [],
            "name": "rewardRate",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }]
        
        contract = w3.eth.contract(address=gauge_checksum, abi=abi)
        
        print("2. Test Lettura Variabile On-Chain...")
        reward_rate_wei = contract.functions.rewardRate().call()
        print(f"✅ Reward Rate Estratto: {reward_rate_wei}")
        
        print("3. Test API Prezzo AERO...")
        aero_pool = "0x2073d8035bb2b0f2e85aaf5a8732c6f40d1f71ee"
        resp = requests.get(f"https://api.dexscreener.com/latest/dex/pairs/base/{aero_pool}").json()
        prezzo_aero = float(resp['pairs'][0]['priceUsd'])
        print(f"✅ Prezzo AERO letto: {prezzo_aero} $")
        
    except Exception as e:
        print(f"\n❌ ERRORE CRITICO INDIVIDUATO: {e}")

if __name__ == "__main__":
    diagnostica_web3()