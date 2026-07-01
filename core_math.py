import math

def get_liquidity_for_capital(capital, price, price_a, price_b):
    """
    Calcola la liquidità L dato il capitale iniziale in USD, il prezzo attuale
    e i limiti inferiore (price_a) e superiore (price_b).
    Assume che il prezzo sia espresso in Token1/Token0 (es. USDC per WETH).
    """
    sqrt_p = math.sqrt(price)
    sqrt_a = math.sqrt(price_a)
    sqrt_b = math.sqrt(price_b)
    
    if price <= price_a:
        # Fuori range inferiore: la pool contiene solo Token 0 (WETH)
        x = capital / price
        L = x / ((1 / sqrt_a) - (1 / sqrt_b))
    elif price >= price_b:
        # Fuori range superiore: la pool contiene solo Token 1 (USDC)
        L = capital / (sqrt_b - sqrt_a)
    else:
        # Dentro il range: la pool contiene entrambi i token
        # Formula derivata dal valore totale della posizione V = x * P + y
        L = capital / (2 * sqrt_p - (price / sqrt_b) - sqrt_a)
        
    return L

def get_amounts_for_liquidity(L, price, price_a, price_b):
    """
    Calcola le quantità esatte di Token 0 (WETH) e Token 1 (USDC) 
    attualmente detenute nella pool per una determinata liquidità L.
    """
    sqrt_p = math.sqrt(price)
    sqrt_a = math.sqrt(price_a)
    sqrt_b = math.sqrt(price_b)
    
    if price <= price_a:
        x = L * ((1 / sqrt_a) - (1 / sqrt_b))
        y = 0.0
    elif price >= price_b:
        x = 0.0
        y = L * (sqrt_b - sqrt_a)
    else:
        x = L * ((1 / sqrt_p) - (1 / sqrt_b))
        y = L * (sqrt_p - sqrt_a)
        
    return x, y

# Test rapido di validazione dell'algoritmo
if __name__ == "__main__":
    # Esempio: 1000$ di capitale, ETH a 3400$, range 3000$ - 4000$
    capitale_test = 1000.0
    prezzo_test = 3400.0
    limite_inf = 3000.0
    limite_sup = 4000.0
    
    L = get_liquidity_for_capital(capitale_test, prezzo_test, limite_inf, limite_sup)
    weth, usdc = get_amounts_for_liquidity(L, prezzo_test, limite_inf, limite_sup)
    
    print(f"Liquidità (L) calcolata: {L}")
    print(f"Token nel wallet virtuale -> WETH: {weth:.4f}, USDC: {usdc:.2f}")
    print(f"Valore totale verificato: {(weth * prezzo_test) + usdc:.2f}$")