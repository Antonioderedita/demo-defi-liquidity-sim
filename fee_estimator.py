def stima_rendimenti_cl(capitale, live_price, price_a, price_b, apr_emissioni_base):
    """
    Calcola rendimenti basati sulle emissioni veAERO di Slipstream.
    Ignora i volumi di scambio e applica il moltiplicatore di concentrazione.
    """
    if price_b <= price_a or apr_emissioni_base <= 0:
        return 0.0, 0.0
        
    if live_price <= price_a or live_price >= price_b:
        return 0.0, 0.0
        
    # Calcolo della concentrazione rispetto a un LP standard full-range
    spread = (price_b - price_a) / live_price
    
    # Più stringi il range, più le tue emissioni vengono moltiplicate
    moltiplicatore_dinamico = 1.0 + (0.2 / (spread + 0.02)) if spread > 0 else 1.0
    
    apr_stimato = apr_emissioni_base * moltiplicatore_dinamico
    
    # Calcolo dollari generati al giorno
    fee_giornaliere = (capitale * (apr_stimato / 100)) / 365
    
    return fee_giornaliere, apr_stimato


# Force cache invalidation