import core_math
import data_fetcher

# --- COSTANTI OPERATIVE DEL SISTEMA (Rete Base) ---
GAS_COST_USD = 1.50   # Costo medio stimato per chiudere e riaprire una pool su Base
FEE_TIER = 0.0005     # 0.05% fee standard della pool Aerodrome WETH/USDC
EFFICIENZA_CL = 50.0  # Moltiplicatore empirico di efficienza del capitale per Liquidità Concentrata

def stima_commissioni_giornaliere(capitale_utente, volume_24h, tvl_pool):
    """
    Calcola la stima oggettiva delle commissioni giornaliere generate.
    """
    if tvl_pool == 0: 
        return 0.0
    
    # 1. Quante fee totali ha generato l'intera pool oggi?
    fee_totali_pool = volume_24h * FEE_TIER
    
    # 2. Qual è la quota dell'utente? (Considerando l'efficienza della liquidità concentrata)
    quota_utente = (capitale_utente / tvl_pool) * EFFICIENZA_CL
    
    # 3. Commissioni giornaliere stimate in dollari
    return fee_totali_pool * quota_utente

def analyze_position(capital, price_a, price_b, entry_price=None):
    """
    Esegue l'analisi ibrida della posizione (Percentuale -> Volumetrica).
    """
    print("Recupero dati live dal sensore on-chain (DexScreener)...")
    pool_data = data_fetcher.get_aerodrome_pool_data()
    
    if not pool_data:
        print("Impossibile recuperare i dati. Analisi interrotta.")
        return
        
    live_price = pool_data['prezzo_usd']
    volume_24h = pool_data['volume_24h_usd']
    tvl = pool_data['liquidita_totale_usd']
    
    print(f"\n=== ANALISI IBRIDA POSIZIONE ===")
    print(f"Prezzo Attuale: {live_price:.2f} $ | Range Impostato: {price_a}$ - {price_b}$")
    
    # Calcolo della distanza percentuale dal bordo più vicino
    dist_inf = ((live_price - price_a) / price_a) * 100
    dist_sup = ((price_b - live_price) / live_price) * 100
    min_dist = min(dist_inf, dist_sup)
    
    # --- LOGICA A CASCATA (EVENT-DRIVEN) ---
    
    # CONDIZIONE 1: Fuori Range (Matematica = Perdita di Efficienza 100%)
    if live_price <= price_a or live_price >= price_b:
        print("\nSTATO: 🔴 FUORI RANGE.")
        print("Commissioni in generazione: 0.00 $/giorno.")
        print(f"AZIONE OGGETTIVA: REBALANCING IMMEDIATO.")
        print("Stai assorbendo tutta l'Impermanent Loss senza incassare i rendimenti per compensarla.")
        
    # CONDIZIONE 2: Allarme Innescato (Sotto il 5%) -> Avvio Analisi Complessa
    elif min_dist <= 5.0:
        print(f"\nSTATO: 🟡 ALLARME ATTIVATO (Distanza: {min_dist:.2f}%).")
        print("Soglia di sicurezza violata. Avvio calcolo volumetrico dei costi opportunità...")
        
        fee_giornaliere = stima_commissioni_giornaliere(capital, volume_24h, tvl)
        print(f"-> Commissioni stimate prodotte: {fee_giornaliere:.2f} $/giorno.")
        
        # Risoluzione della disuguaglianza: Fees > Costo Operativo
        if fee_giornaliere > (GAS_COST_USD * 1.5):
            print("\nAZIONE OGGETTIVA: MANTENERE LA POSIZIONE.")
            print(f"I volumi di scambio attuali sono altissimi. Generare {fee_giornaliere:.2f}$ al giorno giustifica il rischio di rimanere vicini al limite. Attendere.")
        else:
            print("\nAZIONE OGGETTIVA: REBALANCING PREVENTIVO.")
            print(f"I volumi sono troppo bassi ({fee_giornaliere:.2f}$/giorno) per giustificare il rischio di rottura. Smontare e ricentrare la pool ora.")
            
    # CONDIZIONE 3: Zona Sicura (Nessun calcolo pesante richiesto)
    else:
        print(f"\nSTATO: 🟢 ZONA SICURA (Distanza dal bordo: {min_dist:.2f}%).")
        print("Il sistema non richiede ottimizzazioni. Monitoraggio leggero in corso.")
        
    # --- CALCOLO IMPERMANENT LOSS ---
    if entry_price:
        L = core_math.get_liquidity_for_capital(capital, entry_price, price_a, price_b)
        il_perc, v_pool, v_hodl = core_math.calculate_impermanent_loss(L, entry_price, live_price, price_a, price_b)
        print(f"\n--- METRICHE DI EFFICIENZA (Ingresso: {entry_price}$) ---")
        print(f"Valore se avessi fatto HODL: {v_hodl:.2f} $")
        print(f"Valore reale nella Pool: {v_pool:.2f} $")
        print(f"Impermanent Loss netta: {il_perc:.2f}%")

if __name__ == "__main__":
    # Parametri per il test
    CAPITALE = 1000.0
    PREZZO_INGRESSO = 1615.0
    
    # Imposta un limite inferiore appositamente vicino al prezzo attuale (es. 1580 se ETH è a 1615)
    # per forzare matematicamente l'innesco dell'allarme giallo sotto il 5%
    LIMITE_INFERIORE = 1580.0 
    LIMITE_SUPERIORE = 1800.0
    
    analyze_position(CAPITALE, LIMITE_INFERIORE, LIMITE_SUPERIORE, PREZZO_INGRESSO)