import math

def get_liquidity_for_capital(capital, price, price_a, price_b):
    """
    Calcola la liquidità L dato il capitale iniziale in USD, il prezzo attuale
    e i limiti inferiore (price_a) e superiore (price_b).
    Assume che il prezzo sia espresso in Token1/Token0 (es. USDC per WETH).
    """
    if price_a >= price_b or capital <= 0:
        return 0.0
    
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
def calculate_impermanent_loss(L, price_0, price_1, price_a, price_b):
    """
    Calcola l'Impermanent Loss confrontando il valore della posizione nella pool
    con il valore che si avrebbe facendo HODL dei token iniziali.
    Restituisce la percentuale di IL e i due valori in dollari.
    """
    # 1. Calcolo dei token iniziali al prezzo price_0
    weth_0, usdc_0 = get_amounts_for_liquidity(L, price_0, price_a, price_b)
    
    # 2. Calcolo dei token finali al nuovo prezzo price_1
    weth_1, usdc_1 = get_amounts_for_liquidity(L, price_1, price_a, price_b)
    
    # 3. Valore HODL (Token iniziali valorizzati al nuovo prezzo)
    v_hodl = (weth_0 * price_1) + usdc_0
    
    # 4. Valore Pool (Token attuali valorizzati al nuovo prezzo)
    v_pool = (weth_1 * price_1) + usdc_1
    
    # 5. Calcolo percentuale dell'Impermanent Loss
    if v_hodl == 0:
        il_percent = 0.0
    else:
        il_percent = ((v_pool / v_hodl) - 1) * 100
        
    return il_percent, v_pool, v_hodl

# Test rapido di validazione dell'Impermanent Loss
if __name__ == "__main__":
    # Parametri iniziali
    capitale_test = 1000.0
    prezzo_iniziale = 3400.0
    limite_inf = 3000.0
    limite_sup = 4000.0
    
    # Nuovo scenario di mercato: ETH scende a 2800$ (completamente fuori range)
    prezzo_futuro = 2800.0
    
    # Calcolo Liquidità Iniziale
    L = get_liquidity_for_capital(capitale_test, prezzo_iniziale, limite_inf, limite_sup)
    
    # Calcolo IL
    il_perc, valore_pool, valore_hodl = calculate_impermanent_loss(
        L, prezzo_iniziale, prezzo_futuro, limite_inf, limite_sup
    )
    
    print("--- TEST IMPERMANENT LOSS ---")
    print(f"Prezzo scende da {prezzo_iniziale}$ a {prezzo_futuro}$")
    print(f"Valore se avessi fatto HODL: {valore_hodl:.2f}$")
    print(f"Valore reale nella Pool: {valore_pool:.2f}$")
    print(f"Impermanent Loss Netta: {il_perc:.2f}%")