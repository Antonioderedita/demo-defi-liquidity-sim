import math

def get_liquidity_for_capital(capital, price, price_a, price_b):
    if price_b <= price_a or price <= 0: 
        return 0.0
    
    # Se fuori range, usiamo i limiti per il calcolo virtuale
    price_calc = max(min(price, price_b), price_a)
    
    sqrt_p = math.sqrt(price_calc)
    sqrt_a = math.sqrt(price_a)
    sqrt_b = math.sqrt(price_b)
    
    if price_calc == price_a:
        L = capital / (sqrt_b - sqrt_p)
    elif price_calc == price_b:
        L = capital / ((sqrt_p - sqrt_a) * price_calc)
    else:
        L = capital / ((sqrt_p - sqrt_a) * price_calc + (sqrt_b - sqrt_p))
    return L

def get_amounts_for_liquidity(L, price, price_a, price_b):
    if L <= 0: 
        return 0.0, 0.0
    
    price_calc = max(min(price, price_b), price_a)
    
    sqrt_p = math.sqrt(price_calc)
    sqrt_a = math.sqrt(price_a)
    sqrt_b = math.sqrt(price_b)
    
    weth = L * (sqrt_b - sqrt_p) / (sqrt_p * sqrt_b) if price < price_b else 0.0
    usdc = L * (sqrt_p - sqrt_a) if price > price_a else 0.0
    
    return weth, usdc

def calculate_impermanent_loss(L, current_price, entry_price, price_a, price_b):
    """
    Calcola l'Impermanent Loss reale: (Valore HODL - Valore LP Attuale)
    """
    if L <= 0 or current_price == entry_price:
        return 0.0, 0.0, 0.0
        
    # 1. Quanti token avevamo all'ingresso?
    weth_0, usdc_0 = get_amounts_for_liquidity(L, entry_price, price_a, price_b)
    valore_ingresso = (weth_0 * entry_price) + usdc_0
    
    # 2. Quanti token abbiamo adesso (LP)?
    weth_1, usdc_1 = get_amounts_for_liquidity(L, current_price, price_a, price_b)
    valore_attuale_lp = (weth_1 * current_price) + usdc_1
    
    # 3. Quanto varrebbero i token iniziali se NON li avessimo messi nella pool (HODL)?
    valore_hodl = (weth_0 * current_price) + usdc_0
    
    il_usd = valore_hodl - valore_attuale_lp
    il_perc = (il_usd / valore_ingresso) * 100 if valore_ingresso > 0 else 0.0
    
    return max(0.0, il_perc), max(0.0, il_usd), valore_attuale_lp