import math

def stima_rendimenti_cl(capitale, live_price, price_a, price_b, vol_24h, tvl_pool):
    """
    Calcola le commissioni giornaliere stimate e l'APR.
    """
    # Guard 1: Range invalido o pool vuota
    if price_b <= price_a or tvl_pool == 0:
        return 0.0, 0.0
        
    # Guard 2: Prezzo fuori range (Nessuna fee generata)
    if live_price <= price_a or live_price >= price_b:
        return 0.0, 0.0
        
    spread = (price_b - price_a) / live_price
    
    if spread > 0:
        moltiplicatore_dinamico = 1.0 + (0.2 / (spread + 0.02))
    else:
        moltiplicatore_dinamico = 1.0
        
    fattore_competizione = 0.3
    quota_base = min(capitale / tvl_pool, 1.0)
    fee_totali_pool = vol_24h * 0.0005 
    
    fee_giornaliere = fee_totali_pool * quota_base * moltiplicatore_dinamico * fattore_competizione
    apr_stimato = (fee_giornaliere * 365 / capitale) * 100
    
    return fee_giornaliere, apr_stimato