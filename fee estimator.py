import math

def stima_rendimenti_cl(capitale, live_price, price_a, price_b, vol_24h, tvl_pool):
    """
    Calcola le commissioni giornaliere stimate e l'APR applicando un modello
    smorzato per evitare asintoti e clippando la quota massima riproducibile.
    """
    # Guard esplicito contro la divisione per zero se i limiti coincidono
    if price_b <= price_a or tvl_pool == 0:
        return 0.0, 0.0
        
    spread = (price_b - price_a) / live_price
    
    # Moltiplicatore dinamico smorzato per simulare la concentrazione nel tick
    if spread > 0:
        moltiplicatore_dinamico = 1.0 + (0.2 / (spread + 0.02))
    else:
        moltiplicatore_dinamico = 1.0
        
    fattore_competizione = 0.3
    
    # Correzione Claude: Quota utente clippata per non superare mai il 100% della pool (1.0)
    quota_base = min(capitale / tvl_pool, 1.0)
    
    fee_totali_pool = vol_24h * 0.0005  # Fee tier dello 0.05%
    
    fee_giornaliere = fee_totali_pool * quota_base * moltiplicatore_dinamico * fattore_competizione
    apr_stimato = (fee_giornaliere * 365 / capitale) * 100
    
    return fee_giornaliere, apr_stimato