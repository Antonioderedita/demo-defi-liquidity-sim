import streamlit as st
import time
import data_fetcher
import range_builder
import core_math
import fee_estimator
import portfolio_manager

st.set_page_config(page_title="DeFi Optimizer Pro", page_icon="⚡", layout="centered")
st.title("Aerodrome Slipstream: Autopilota")
st.markdown("---")

st.subheader("Configurazione Pool (Aerodrome - Base)")
indirizzo_pool = st.text_input("Inserisci Smart Contract Pair (Pool)", value="0xcdac0d6c6c59727a65f871236188350531885c43")
indirizzo_gauge = st.text_input("Inserisci Smart Contract Gauge (Emissioni)", value="0x519BBD1Dd8C6A94C46080E24f316c14Ee758C025")

@st.cache_data(ttl=60)
def fetch_live_data(address):
    return data_fetcher.get_pool_data_by_address(address)

@st.cache_data(ttl=3600)
def fetch_volatility(simbolo):
    return range_builder.calcola_volatilita_storica(simbolo, giorni=14)

@st.cache_data(ttl=300) # Aggiorna l'APR ogni 5 minuti
def fetch_apr_onchain(gauge_addr, tvl):
    return data_fetcher.get_apr_from_web3(gauge_addr, tvl)

# --- FASE DI RECUPERO DATI ---
pool_data = fetch_live_data(indirizzo_pool)
if not pool_data:
    st.error(f"🔴 ERRORE: Nessun dato trovato per l'indirizzo Pool {indirizzo_pool}.")
    st.stop()

live_price = pool_data['prezzo_usd']
tvl = pool_data['liquidita_totale_usd']

# Tentativo di recupero APR leggendo direttamente la blockchain
apr_dinamico = fetch_apr_onchain(indirizzo_gauge, tvl)

if apr_dinamico is not None:
    st.success(f"✅ APR Emissioni estratto On-Chain dalla Blockchain: {apr_dinamico:.2f}%")
else:
    st.warning("⚠️ Lettura On-Chain fallita. Usa l'inserimento manuale.")
    apr_dinamico = 25.0 

apr_emissioni = st.number_input("Emission APR (%) [Sincronizzato col nodo]", min_value=0.0, value=float(apr_dinamico), step=1.0)

simbolo_base = pool_data['coppia_reale'].split('/')[0]
vol_daily = fetch_volatility(simbolo_base)
live_price = pool_data['prezzo_usd']
nome_coppia = pool_data['coppia_reale']

st.caption(f"**Dati Live:** {nome_coppia} | Prezzo: {live_price:.2f} $ | Volatilità: {(vol_daily*100):.2f}%")
st.markdown("---")

# Creazione delle Schede (Tabs)
tab_setup, tab_monitor = st.tabs(["⚙️ Setup Simulazione", "📊 Monitoraggio & Diagnosi"])

with tab_setup:
    st.subheader("1. Modella e Salva la Posizione")
    capitale = st.number_input("Capitale da investire ($)", min_value=10.0, value=1000.0, step=100.0)
    
    inf_bil, sup_bil, _ = range_builder.suggerisci_range_ottimale(live_price, vol_daily, giorni_target=7, z_score=1.5)
    
    price_a, price_b = st.slider("Seleziona Range di Prezzo:", min_value=float(live_price*0.7), max_value=float(live_price*1.3), value=(float(inf_bil), float(sup_bil)), step=10.0)
    
    if st.button("💾 SIMULA E SALVA POSIZIONE"):
        portfolio_manager.salva_posizione(indirizzo_pool, capitale, price_a, price_b, live_price, apr_emissioni)
        st.success("Fotografia della posizione salvata con successo! Passa alla scheda Monitoraggio.")

with tab_monitor:
    pos = portfolio_manager.get_posizione(indirizzo_pool)
    
    if not pos:
        st.info("Nessuna posizione salvata per questa pool. Vai nel Setup e salvala.")
    else:
        st.subheader("Diagnostica di Ribilanciamento")
        
        # Macchina del tempo per simulare il passaggio dei giorni (solo a scopo di test)
        giorni_simulati = st.slider("Simula giorni trascorsi dall'ingresso:", min_value=0.0, max_value=30.0, value=5.0, step=0.5)
        
        # Recupero dati salvati
        cap_in = pos["capitale_iniziale"]
        p_in = pos["prezzo_ingresso"]
        p_a = pos["limite_inf"]
        p_b = pos["limite_sup"]
        apr_in = pos["apr_ingresso"]
        
        # Matematica: IL e Fee
        L = core_math.get_liquidity_for_capital(cap_in, p_in, p_a, p_b)
        il_perc, il_usd, lp_value = core_math.calculate_impermanent_loss(L, live_price, p_in, p_a, p_b)
        
        fee_day, _ = fee_estimator.stima_rendimenti_cl(cap_in, live_price, p_a, p_b, apr_in)
        fee_totali = fee_day * giorni_simulati
        
        # Costo Gas stimato per il rebalancing (Prelievo + Swap + Deposito)
        costo_gas = 1.50
        profitto_netto = fee_totali - il_usd - costo_gas
        
        # UI Metriche
        col1, col2, col3 = st.columns(3)
        col1.metric("Prezzo Ingresso -> Attuale", f"{p_in:.2f}$ -> {live_price:.2f}$")
        col2.metric("Emissioni Maturate (Stima)", f"+ {fee_totali:.2f} $", "Guadagno")
        col3.metric("Impermanent Loss", f"- {il_usd:.2f} $", "- Perdita")
        
        st.markdown("---")
        
        # DIRETTIVA PRO DELL'ANALISTA: Valutazione Azione
        st.subheader("Consiglio Algoritmico")
        
        fuori_range = (live_price <= p_a) or (live_price >= p_b)
        
        if profitto_netto > 0:
            st.success(f"🟢 **PROFITTO NETTO: + {profitto_netto:.2f} $** (Incluse {costo_gas}$ di Gas)")
            if fuori_range:
                st.markdown("**AZIONE:** 🛠️ **RIBILANCIA ORA**. Sei fuori range, ma le emissioni hanno coperto abbondantemente l'Impermanent Loss. Puoi chiudere e riaprire a un nuovo prezzo generando puro profitto.")
            else:
                st.markdown("**AZIONE:** 🧘‍♂️ **HOLD**. Sei nel range e in netto profitto. Lascia correre l'interesse composto.")
        else:
            st.error(f"🔴 **PERDITA NETTA: {profitto_netto:.2f} $** (Incluse {costo_gas}$ di Gas)")
            if fuori_range:
                st.markdown("**AZIONE:** 🛑 **ATTENDI (NON RIBILANCIARE)**. Sei fuori range, ma le fee non hanno ancora coperto l'IL. Se chiudi ora la posizione, incassi una perdita matematica definitiva. Attendi un ritracciamento del prezzo verso il range originale.")
            else:
                st.markdown("**AZIONE:** ⏳ **HOLD E ACCUMULA**. Il prezzo si è mosso, ma sei ancora nel range. Devi tenere la posizione aperta più a lungo per permettere alle emissioni di assorbire l'Impermanent Loss.")