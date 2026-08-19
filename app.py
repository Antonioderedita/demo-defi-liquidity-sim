import streamlit as st
import time
import data_fetcher
import range_builder
import core_math
import fee_estimator
import portfolio_manager

st.set_page_config(page_title="Slipstream Autopilota", page_icon="⚡", layout="wide")
st.title("Aerodrome autopilot")
st.markdown("---")

# --- SIDEBAR PER LA CONFIGURAZIONE ---
# Spostiamo gli input tecnici di lato per lasciare pulita la schermata centrale
with st.sidebar:
    st.header("⚙️ Sorgenti Dati")
    indirizzo_pool = st.text_input("Smart Contract Pool", value="0x3fe04a59ebd38cf06080a6f60a98d124eb59392a")
    indirizzo_gauge = st.text_input("Smart Contract Gauge", value="0xA0B61fdB9f1FB9b917Fe38b49427Fd4D87472D28")

@st.cache_data(ttl=60)
def fetch_live_data(address):
    return data_fetcher.get_pool_data_by_address(address)

@st.cache_data(ttl=3600)
def fetch_volatility(simbolo):
    return range_builder.calcola_volatilita_storica(simbolo, giorni=14)

@st.cache_data(ttl=300) 
def fetch_apr_onchain(gauge_addr, tvl):
    return data_fetcher.get_apr_from_web3(gauge_addr, tvl)

# --- FASE DI RECUPERO DATI ---
pool_data = fetch_live_data(indirizzo_pool)
if not pool_data:
    st.error(f"🔴 ERRORE: Nessun dato trovato per l'indirizzo Pool {indirizzo_pool}.")
    st.stop()

live_price = pool_data['prezzo_usd']
tvl = pool_data['liquidita_totale_usd']
simbolo_base = pool_data['coppia_reale'].split('/')[0]
vol_daily = fetch_volatility(simbolo_base)
nome_coppia = pool_data['coppia_reale']

apr_dinamico = fetch_apr_onchain(indirizzo_gauge, tvl)
if apr_dinamico is None:
    apr_dinamico = 25.0 

# --- HEADER INFORMAZIONI DI MERCATO ---
col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("Mercato Live", nome_coppia, f"{live_price:.4f} $")
col_m2.metric("Volatilità (14d)", f"{(vol_daily*100):.2f}%")
col_m3.metric("Emission APR On-Chain", f"{apr_dinamico:.2f}%", "Aggiornato" if apr_dinamico else "Manuale")
st.markdown("---")


# --- CREAZIONE SCHEDE PRINCIPALI ---
tab_setup, tab_live = st.tabs(["🎯 Configura Ingresso", "📊 Dashboard Monitoraggio"])

with tab_setup:
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.subheader("Parametri di Liquidità")
        capitale = st.number_input("Capitale da investire ($)", min_value=0.01, value=100.0, step=10.0)
        
        inf_bil, sup_bil, _ = range_builder.suggerisci_range_ottimale(live_price, vol_daily, giorni_target=7, z_score=1.5)
        price_a, price_b = st.slider(
            "Imposta Range di Prezzo ($)", 
            min_value=float(live_price*0.7), max_value=float(live_price*1.3), 
            value=(float(inf_bil), float(sup_bil)), step=5.0
        )
        # --- NUOVO BLOCCO: CALCOLO E VISUALIZZAZIONE APR CONCENTRATO ---
        fee_day_stimate, _ = fee_estimator.stima_rendimenti_cl(capitale, live_price, price_a, price_b, apr_dinamico)
        apr_concentrato_stimato = (fee_day_stimate * 365 / capitale) * 100
        
        st.info(f"📊 **APR Stimato per questo Range:** {apr_concentrato_stimato:.2f}%")
        # ---------------------------------------------------------------
    
    with col_s2:
        st.subheader("Salvataggio Stato")
        st.info("Salvando la posizione, il sistema fisserà il prezzo attuale e inizierà a contare il tempo reale trascorso per calcolare i guadagni esatti.")
        if st.button("💾 INIZIA MONITORAGGIO", use_container_width=True):
            portfolio_manager.salva_posizione(indirizzo_pool, capitale, price_a, price_b, live_price, apr_dinamico)
            st.success("Posizione fissata! Passa alla Dashboard.")


with tab_live:
    pos = portfolio_manager.get_posizione(indirizzo_pool)
    
    if not pos:
        st.info("Nessuna posizione salvata. Vai in 'Configura Ingresso' per iniziare.")
    else:
        # Estrazione dati salvati
        cap_in = pos["capitale_iniziale"]
        p_in = pos["prezzo_ingresso"]
        p_a = pos["limite_inf"]
        p_b = pos["limite_sup"]
        timestamp_in = pos.get("timestamp", time.time())
        
        # Calcolo tempo reale trascorso
        giorni_reali_trascorsi = max(0.0001, (time.time() - timestamp_in) / 86400.0)
        
        # Matematica Core
        L = core_math.get_liquidity_for_capital(cap_in, p_in, p_a, p_b)
        il_perc, il_usd, lp_value = core_math.calculate_impermanent_loss(L, live_price, p_in, p_a, p_b)
        fee_day_attuali, _ = fee_estimator.stima_rendimenti_cl(cap_in, live_price, p_a, p_b, apr_dinamico)
        
        # --- SEZIONE 1: PERFORMANCE REALE (FINO AD ORA) ---
        st.subheader("⏱️ Maturato in Tempo Reale")
        st.caption(f"Posizione aperta da {giorni_reali_trascorsi:.2f} giorni.")
        # Griglia ordinata per mostrare capitale e range
        col_pos1, col_pos2, col_pos3 = st.columns(3)
        col_pos1.metric("Capitale Investito", f"{cap_in:.2f} $")
        col_pos2.metric("Limite Inferiore", f"{p_a:.4f} $")
        col_pos3.metric("Limite Superiore", f"{p_b:.4f} $")
        
        st.markdown("<br>", unsafe_allow_html=True) # Spazio per dividere le sezioni

        fee_maturate_reali = fee_day_attuali * giorni_reali_trascorsi
        profitto_netto_reale = fee_maturate_reali - il_usd
        
        cr1, cr2, cr3 = st.columns(3)
        cr1.metric("Prezzo Attuale (vs Ingresso)", f"{live_price:.2f}$", f"{(live_price - p_in):.2f}$")
        cr2.metric("Impermanent Loss Reale", f"- {il_usd:.2f} $")
        cr3.metric("Profitto Netto Attuale", f"{profitto_netto_reale:.2f} $", f"Fee incassate: +{fee_maturate_reali:.2f}$")
        
        st.markdown("---")
        
        # --- SEZIONE 2: PROIEZIONI FUTURE ---
        st.subheader("🔮 Proiezioni (Forecast)")
        st.caption(f"Basato sull'APR attuale del {apr_dinamico:.2f}% e assumendo che il prezzo resti nel range.")
        
        cp1, cp2, cp3 = st.columns(3)
        cp1.metric("Prossime 24 Ore", f"+ {fee_day_attuali:.2f} $")
        cp2.metric("Prossimi 7 Giorni", f"+ {(fee_day_attuali * 7):.2f} $")
        cp3.metric("Prossimi 30 Giorni", f"+ {(fee_day_attuali * 30):.2f} $")
        
        st.markdown("---")
        
        # --- SEZIONE 3: AREA DI STRESS TEST (Nascosta in un Expander) ---
        with st.expander("🧪 Area di Stress Test (Simulazione Manuale)"):
            st.markdown("Forza i parametri per vedere come si comporterebbe il portafoglio in scenari estremi.")
            
            c_test1, c_test2 = st.columns(2)
            giorni_sim = c_test1.slider("Giorni simulati", 1.0, 30.0, 5.0)
            prezzo_sim = c_test2.number_input("Prezzo simulato ($)", value=float(live_price))
            
            # Ricalcolo basato sui dati simulati
            _, il_usd_sim, _ = core_math.calculate_impermanent_loss(L, prezzo_sim, p_in, p_a, p_b)
            fee_tot_sim = fee_day_attuali * giorni_sim
            net_sim = fee_tot_sim - il_usd_sim
            
            st.metric("Profitto Netto nello scenario", f"{net_sim:.2f} $")
