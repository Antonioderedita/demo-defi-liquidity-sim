def stima_rendimenti_cl(capitale, live_price, price_a, price_b, vol_24h, tvl_pool, fee_tier_perc):
    # Guard 1: Range invalido o pool vuota
    if price_b <= price_a or tvl_pool == 0:
        return 0.0, 0.0
        
    # Guard 2: Prezzo fuori range
    if live_price <= price_a or live_price >= price_b:
        return 0.0, 0.0
        
    spread = (price_b - price_a) / live_price
    moltiplicatore_dinamico = 1.0 + (0.2 / (spread + 0.02)) if spread > 0 else 1.0
    fattore_competizione = 0.3
    quota_base = min(capitale / tvl_pool, 1.0)
    
    # MATEMATICA DINAMICA: usa la fee passata dall'utente (es. 0.3 -> 0.003)
    fee_totali_pool = vol_24h * (fee_tier_perc / 100) 
    
    fee_giornaliere = fee_totali_pool * quota_base * moltiplicatore_dinamico * fattore_competizione
    apr_stimato = (fee_giornaliere * 365 / capitale) * 100
    
    return fee_giornaliere, apr_stimato