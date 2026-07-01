import streamlit as st
import data_fetcher
import range_builder
import core_math

st.set_page_config(page_title="DeFi Optimizer", page_icon="⚡", layout="centered")
st.title("Ottimizzatore Liquidità Concentrata")
st.markdown("---")

# 1. RECUPERO DATI LIVE (Ottimizzato con cache per non saturare le API)
@st.cache_data(ttl=60)
def fetch_live_data():
    return data_fetcher.get_aerodrome_pool_data()

@st.cache_data(ttl=3600)
def fetch_volatility():
    return range_builder.calcola_volatilita_storica("ETH-USD", giorni=14)

pool_data = fetch_live_data()
vol_daily = fetch_volatility()

if not pool_data or not vol_daily:
    st.error("Errore di connessione ai dati on-chain. Riprova più tardi.")
    st.stop()

live_price = pool_data['prezzo_usd']
tvl = pool_data['liquidita_totale_usd']
vol_24h = pool_data['volume_24h_usd']

# 2. CRUSCOTTO MERCATO
st.subheader("Dati di Mercato (WETH/USDC - Base)")
col1, col2, col3 = st.columns(3)
col1.metric("Prezzo WETH", f"{live_price:.2f} $")
col2.metric("Volumi (24h)", f"{vol_24h/1e6:.2f} M $")
col3.metric("Volatilità (14d)", f"{(vol_daily*100):.2f}%")
st.markdown("---")

# 3. INPUT UTENTE E SUGGERIMENTI STATISTICI
st.subheader("1. Simulazione Dinamica")
capitale = st.number_input("Capitale da investire ($)", min_value=10.0, value=1000.0, step=100.0)

# Calcolo del range statistico di base (86% probabilità a 7 giorni)
inf_bil, sup_bil, _ = range_builder.suggerisci_range_ottimale(live_price, vol_daily, giorni_target=7, z_score=1.5)
st.info(f"💡 **Range Statistico Consigliato:** {inf_bil} $ - {sup_bil} $")

# Slider dinamico limitato a +/- 30% del prezzo attuale per mantenere la UI pulita
min_slider = float(live_price * 0.7)
max_slider = float(live_price * 1.3)

price_a, price_b = st.slider(
    "Modella il tuo Range di Prezzo (Trascina i bordi per vedere l'impatto sui rendimenti):",
    min_value=min_slider,
    max_value=max_slider,
    value=(float(inf_bil), float(sup_bil)),
    step=10.0
)
st.markdown("---")

# 4. PROIEZIONI IN TEMPO REALE E METRICHE
st.subheader("2. Proiezioni in Tempo Reale")

# Calcoli matematici core
L = core_math.get_liquidity_for_capital(capitale, live_price, price_a, price_b)
weth, usdc = core_math.get_amounts_for_liquidity(L, live_price, price_a, price_b)

# Stima volumetrica dinamica e smorzata
if tvl > 0:
    # 1. Calcolo dell'ampiezza percentuale del range (spread)
    spread = (price_b - price_a) / live_price
    
    # 2. Modello logico di smorzamento
    # Evita asintoti verticali e modella in modo più fluido la concentrazione
    if spread > 0:
        moltiplicatore_dinamico = 1.0 + (0.2 / (spread + 0.02))
    else:
        moltiplicatore_dinamico = 1.0
        
    # 3. Fattore di competizione
    # Compensa il fatto che il TVL visibile è già parzialmente concentrato dagli altri utenti
    fattore_competizione = 0.3
    
    # 4. Calcolo quota e profitti netti
    quota_base = capitale / tvl
    fee_totali_pool = vol_24h * 0.0005 # 0.05% fee tier della pool
    
    fee_giornaliere = fee_totali_pool * quota_base * moltiplicatore_dinamico * fattore_competizione
    apr_stimato = (fee_giornaliere * 365 / capitale) * 100
else:
    fee_giornaliere = 0.0
    apr_stimato = 0.0

# Layout a 4 colonne per i dati crudi
col_w, col_u, col_f, col_a = st.columns(4)
col_w.metric("WETH Reali", f"{weth:.4f}")
col_u.metric("USDC Reali", f"{usdc:.2f} $")
col_f.metric("Stima $/Giorno", f"{fee_giornaliere:.2f} $")
col_a.metric("APR Stimato", f"{apr_stimato:.1f} %")

# 5. DIAGNOSTICA DEL RISCHIO
dist_inf = ((live_price - price_a) / price_a) * 100
dist_sup = ((price_b - live_price) / live_price) * 100
min_dist = min(dist_inf, dist_sup)

st.write("**Diagnostica di Rischio:**")
if live_price <= price_a or live_price >= price_b:
    st.error("🔴 **FUORI RANGE:** Il capitale non è operativo. Commissioni annullate.")
elif min_dist <= 5.0:
    st.warning(f"🟡 **RISCHIO ALTO:** Sei a {min_dist:.2f}% dal limite. L'APR è massimizzato, ma la probabilità di rottura del range è critica.")
else:
    st.success(f"🟢 **ZONA SICURA:** Distanza dal limite: {min_dist:.2f}%. Configurazione adatta a un monitoraggio passivo.")