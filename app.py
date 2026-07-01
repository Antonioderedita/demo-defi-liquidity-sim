import streamlit as st
import data_fetcher
import range_builder
import core_math

# 1. SETUP ESTETICO E STRUTTURALE (versione ufficiale)
# Layout centrato e minimale, rimozione di sidebar complesse
st.set_page_config(page_title="DeFi Optimizer", page_icon="⚡", layout="centered")

st.title("Ottimizzatore Liquidità Concentrata")
st.markdown("---")

# 2. RECUPERO DATI LIVE
@st.cache_data(ttl=60) # Cacha i dati per 60 secondi per non saturare l'API
def fetch_live_data():
    return data_fetcher.get_aerodrome_pool_data()

@st.cache_data(ttl=3600) # Cacha la volatilità per un'ora
def fetch_volatility():
    return range_builder.calcola_volatilita_storica("ETH-USD", giorni=14)

pool_data = fetch_live_data()
vol_daily = fetch_volatility()

if not pool_data or not vol_daily:
    st.error("Errore di connessione ai dati on-chain. Riprova più tardi.")
    st.stop()

live_price = pool_data['prezzo_usd']

# 3. SEZIONE CRUSCOTTO (METRICHE PRINCIPALI)
st.subheader("Dati di Mercato (Rete Base - Aerodrome)")
col1, col2, col3 = st.columns(3)
col1.metric("Prezzo WETH", f"{live_price:.2f} $")
col2.metric("Volumi (24h)", f"{pool_data['volume_24h_usd']/1e6:.2f} M $")
col3.metric("Volatilità Giornaliera", f"{(vol_daily*100):.2f}%")

st.markdown("---")

# 4. CALCOLO RANGE OTTIMALE
st.subheader("1. Setup Iniziale")
capitale = st.number_input("Capitale da investire ($)", min_value=100.0, value=1000.0, step=100.0)

# Suggerimenti statistici
inf_bil, sup_bil, _ = range_builder.suggerisci_range_ottimale(live_price, vol_daily, giorni_target=7, z_score=1.5)

st.info(f"**Range Consigliato (Bilanciato 7 giorni):** {inf_bil} $ - {sup_bil} $")

col_a, col_b = st.columns(2)
price_a = col_a.number_input("Limite Inferiore ($)", value=float(inf_bil))
price_b = col_b.number_input("Limite Superiore ($)", value=float(sup_bil))

st.markdown("---")

# 5. MOTORE DI ANALISI E ALLARME IBRIDO
st.subheader("2. Analisi Posizione e Rischio")

# Calcolo composizione wallet virtuale
L = core_math.get_liquidity_for_capital(capitale, live_price, price_a, price_b)
weth, usdc = core_math.get_amounts_for_liquidity(L, live_price, price_a, price_b)

st.write("**Composizione stimata del portafoglio:**")
col_w, col_u = st.columns(2)
col_w.metric("WETH", f"{weth:.4f}")
col_u.metric("USDC", f"{usdc:.2f} $")

# Logica Predittiva
dist_inf = ((live_price - price_a) / price_a) * 100
dist_sup = ((price_b - live_price) / live_price) * 100
min_dist = min(dist_inf, dist_sup)

st.write("**Stato di Salute del Range:**")
if live_price <= price_a or live_price >= price_b:
    st.error(f"🔴 FUORI RANGE. Commissioni generate: 0$. È richiesto un rebalancing immediato.")
elif min_dist <= 5.0:
    st.warning(f"🟡 ALLARME ATTIVATO (Distanza dal bordo: {min_dist:.2f}%)")
    
    # Calcolo volumetrico on-demand
    efficienza = 50.0
    quota = (capitale / pool_data['liquidita_totale_usd']) * efficienza
    fee_giornaliere = (pool_data['volume_24h_usd'] * 0.0005) * quota
    
    st.write(f"Commissioni stimate attuali: **{fee_giornaliere:.2f} $/giorno**")
    
    if fee_giornaliere > 2.25: # Assumendo 1.5$ costo gas * 1.5
        st.success("AZIONE OGGETTIVA: Mantenere la posizione. I rendimenti giustificano il rischio.")
    else:
        st.error("AZIONE OGGETTIVA: Rebalancing preventivo consigliato. Volumi troppo bassi.")
else:
    st.success(f"🟢 ZONA SICURA (Distanza dal bordo: {min_dist:.2f}%). Nessuna ottimizzazione necessaria.")