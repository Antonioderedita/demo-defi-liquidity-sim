import core_math
import data_fetcher
import fee_estimator

GAS_COST_USD = 1.50   

def analyze_position(capital, price_a, price_b, entry_price=None):
    """Esegue l'analisi ibrida della posizione con stime centralizzate."""
    print("Recupero dati live...")
    pool_data = data_fetcher.get_aerodrome_pool_data()
    
    if not pool_data:
        print("Impossibile recuperare i dati. Analisi interrotta.")
        return
        
    live_price = pool_data['prezzo_usd']
    volume_24h = pool_data['volume_24h_usd']
    tvl = pool_data['liquidita_totale_usd']
    
    print(f"\n=== ANALISI IBRIDA POSIZIONE ===")
    print(f"Prezzo: {live_price:.2f} $ | Range: {price_a}$ - {price_b}$")
    
    dist_inf = ((live_price - price_a) / price_a) * 100
    dist_sup = ((price_b - live_price) / live_price) * 100
    min_dist = min(dist_inf, dist_sup)
    
    # CONDIZIONE 1: Fuori Range
    if live_price <= price_a or live_price >= price_b:
        print("\nSTATO: 🔴 FUORI RANGE.")
        print("AZIONE OGGETTIVA: REBALANCING IMMEDIATO.")
        
    # CONDIZIONE 2: Allarme Innescato
    elif min_dist <= 5.0:
        print(f"\nSTATO: 🟡 ALLARME ATTIVATO (Distanza: {min_dist:.2f}%).")
        
        # Uso della logica centralizzata da fee_estimator
        fee_giornaliere, apr = fee_estimator.stima_rendimenti_cl(
            capital, live_price, price_a, price_b, volume_24h, tvl
        )
        print(f"-> Commissioni stimate prodotte: {fee_giornaliere:.2f} $/giorno (APR: {apr:.1f}%)")
        
        if fee_giornaliere > (GAS_COST_USD * 1.5):
            print("AZIONE OGGETTIVA: MANTENERE. I volumi giustificano il rischio.")
        else:
            print("AZIONE OGGETTIVA: REBALANCING PREVENTIVO. Volumi troppo bassi.")
            
    # CONDIZIONE 3: Zona Sicura
    else:
        print(f"\nSTATO: 🟢 ZONA SICURA (Distanza dal bordo: {min_dist:.2f}%).")

if __name__ == "__main__":
    CAPITALE = 1000.0
    LIMITE_INFERIORE = 1580.0 
    LIMITE_SUPERIORE = 1800.0
    PREZZO_INGRESSO = 1615.0
    analyze_position(CAPITALE, LIMITE_INFERIORE, LIMITE_SUPERIORE, PREZZO_INGRESSO)