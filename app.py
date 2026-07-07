import streamlit as st
import data_fetcher
import range_builder
import core_math
import fee_estimator

st.set_page_config(page_title="DeFi Optimizer", page_icon="⚡", layout="centered")
st.title("Ottimizzatore Liquidità Concentrata")
st.markdown("---")

st.subheader("Configurazione Pool (Base Network)")
indirizzo_pool = st.text_input("Inserisci Smart Contract Pair (es. 0xcdac...)", value="0xcdac0d6c6c59727a65f871236188350531885c43")
fee_scelta = st.selectbox("Fee Tier della Pool (%)", options=[0.01, 0.05, 0.3, 1.0], index=2)

@st.cache_data(ttl=60)
def fetch_live_data(address):
    return data_fetcher.get_pool_data_by_address(address)

@st.cache_data(ttl=3600)
def fetch_volatility():
    return range_builder.calcola_volatilita_storica("ETH-USD", giorni=14)

pool_data = fetch_live_data(indirizzo_pool)
vol_daily = fetch_volatility()

if not pool_data:
    st.error(f"🔴 ERRORE DEXSCREENER: Nessun dato trovato per l'indirizzo {indirizzo_pool}. Verifica che la rete sia Base.")
    st.stop()

if not vol_daily:
    st.error("🔴 ERRORE YAHOO FINANCE: Impossibile scaricare la volatilità di ETH-USD. Il server Streamlit potrebbe essere stato bloccato da Yahoo.")
    st.stop()

live_price = pool_data['prezzo_usd']
tvl = pool_data['liquidita_totale_usd']
vol_24h = pool_data['volume_24h_usd']
nome_coppia = pool_data['coppia_reale']

st.subheader(f"Dati di Mercato ({nome_coppia} - {pool_data['dex_rilevato'].capitalize()})")
col1, col2, col3 = st.columns(3)
col1.metric("Prezzo Token Base", f"{live_price:.2f} $")
col2.metric("Volumi (24h)", f"{vol_24h/1e6:.2f} M $")
col3.metric("Volatilità Giornaliera", f"{(vol_daily*100):.2f}%")

st.caption("Nota: La volatilità storica è calcolata utilizzando un proxy matematico generico.")
st.markdown("---")

st.subheader("1. Simulazione Dinamica")
capitale = st.number_input("Capitale da investire ($)", min_value=10.0, value=1000.0, step=100.0)

inf_bil, sup_bil, _ = range_builder.suggerisci_range_ottimale(live_price, vol_daily, giorni_target=7, z_score=1.5)
st.info(f"💡 **Range Statistico Consigliato:** {inf_bil} $ - {sup_bil} $")

min_slider = float(live_price * 0.7)
max_slider = float(live_price * 1.3)

price_a, price_b = st.slider(
    "Modella il tuo Range di Prezzo:",
    min_value=min_slider,
    max_value=max_slider,
    value=(float(inf_bil), float(sup_bil)),
    step=10.0
)
st.markdown("---")

st.subheader("2. Proiezioni e Analisi del Rischio")

# Calcoli matematici centralizzati ed esenti da divisione per zero
L = core_math.get_liquidity_for_capital(capitale, live_price, price_a, price_b) if price_b > price_a else 0
weth, usdc = core_math.get_amounts_for_liquidity(L, live_price, price_a, price_b) if L > 0 else (0, 0)

# Chiamata al calcolo delle fee con parametro percentuale dinamico
fee_giornaliere, apr_stimato = fee_estimator.stima_rendimenti_cl(
    capitale, live_price, price_a, price_b, vol_24h, tvl, fee_scelta
)

# Calcolo probabilità statistica di NON toccare mai le barriere (orizzonte 7 giorni)
probabilita_in_range = range_builder.calcola_probabilita_no_touch(
    live_price, price_a, price_b, vol_daily, giorni_target=7
)

# Calcolo dell'APR pesato per il rischio (Valore Atteso reale)
apr_risk_adjusted = apr_stimato * (probabilita_in_range / 100)

col_w, col_u, col_f, col_a = st.columns(4)
col_w.metric("Asset 1 Reali", f"{weth:.4f}")
col_u.metric("Asset 2 Reali", f"{usdc:.2f} $")
col_f.metric("Stima $/Giorno", f"{fee_giornaliere:.2f} $")
col_a.metric("APR Grezzo", f"{apr_stimato:.1f} %")

st.markdown("---")
st.subheader("3. Modello di Rischio e Rendimento Atteso")

col_p, col_r = st.columns(2)
col_p.metric("Probabilità in Range (7 gg)", f"{probabilita_in_range:.1f} %")
col_r.metric("Risk-Adjusted APR", f"{apr_risk_adjusted:.1f} %")

# Allarme trasparenza per APR speculativi
if apr_stimato > 150.0:
    st.warning("⚠️ L'APR Grezzo è superiore al 150%. Questa è un'estrapolazione lineare di un istante di mercato altalenante. Non è un rendimento annuo garantito: il prezzo romperà il range molto prima.")

st.caption("Il Risk-Adjusted APR rappresenta il vero 'Valore Atteso': abbatte i ritorni stratosferici dei range troppo stretti in base all'alta probabilità di uscire dal limite.")

dist_inf = ((live_price - price_a) / price_a) * 100 if price_a > 0 else 0
dist_sup = ((price_b - live_price) / live_price) * 100 if live_price > 0 else 0
min_dist = min(dist_inf, dist_sup)

if live_price <= price_a or live_price >= price_b:
    st.error("🔴 **FUORI RANGE:** Il capitale non genera commissioni.")
elif min_dist <= 5.0:
    st.warning(f"🟡 **RISCHIO ALTO:** Sei a {min_dist:.2f}% dal limite.")
else:
    st.success(f"🟢 **ZONA SICURA:** Distanza dal limite: {min_dist:.2f}%.")