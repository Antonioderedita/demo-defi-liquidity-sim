import streamlit as st
import time
import data_fetcher
import range_builder
import core_math
import portfolio_manager
import numpy as np
import pandas as pd

st.set_page_config(page_title="Slipstream Autopilota", page_icon="⚡", layout="wide")
st.title("Aerodrome Autopilot")
st.markdown("---")

if 'conferma_eliminazione' not in st.session_state:
    st.session_state['conferma_eliminazione'] = None

POOLS = {
    "WETH / USDC (Pool Dollaro)": {
        "pool": "0x3fe04a59ebd38cf06080a6f60a98d124eb59392a",
        "gauge": "0xA0B61fdB9f1FB9b917Fe38b49427Fd4D87472D28"
    },
    "WETH / cbBTC (Cross-Crypto)": {
        "pool": "0x42d4a22cad0f5a49681a5715ce994af73a43b76b", 
        "gauge": "0x61E0B10423a0009C3f83ab4313813d29437d0817" 
    }
}

with st.sidebar:
    st.header("⚙️ Selezione Pool")
    scelta_pool = st.selectbox("Seleziona la Pool da gestire:", list(POOLS.keys()))
    indirizzo_pool = POOLS[scelta_pool]["pool"]
    indirizzo_gauge = POOLS[scelta_pool]["gauge"]
    
    st.markdown("---")
    st.caption("Vuoi inserire una pool non in lista?")
    custom_pool = st.text_input("Smart Contract Pool Custom")
    custom_gauge = st.text_input("Smart Contract Gauge Custom")
    
    if custom_pool:
        indirizzo_pool = custom_pool
        indirizzo_gauge = custom_gauge

@st.cache_data(ttl=60)
def fetch_live_data(address):
    return data_fetcher.get_pool_data_by_address(address)

@st.cache_data(ttl=3600)
def fetch_historical_metrics(s_base, s_quote):
    return range_builder.calcola_metriche_storiche(s_base, s_quote, giorni=14)

@st.cache_data(ttl=3600)
def fetch_chart_data(s_base, s_quote, period):
    return range_builder.get_chart_data(s_base, s_quote, periodo=period)

# --- NUOVA CACHE PER MOTORE MONTE CARLO ---
@st.cache_data(ttl=3600)
def fetch_mc_scenarios(prezzo, vol, trend, giorni=14, simulazioni=10000):
    return range_builder.genera_scenari_montecarlo(prezzo, vol, trend, giorni, simulazioni)

pool_data = fetch_live_data(indirizzo_pool)
if not pool_data:
    st.error(f"🔴 ERRORE: Nessun dato trovato per l'indirizzo Pool {indirizzo_pool}.")
    st.stop()

live_price = pool_data['prezzo_nativo']
nome_coppia = pool_data['coppia_reale']
simboli = nome_coppia.split('/')
simbolo_base = simboli[0].strip()
simbolo_quote = simboli[1].strip() if len(simboli) > 1 else "USDC"

with st.sidebar:
    st.markdown("---")
    st.header("🔧 Opzioni Visualizzazione")
    inverti_prezzo = st.checkbox("🔄 Inverti Prezzo (es. mostra 1 WETH in cbBTC)", value=(simbolo_base.upper()=="CBBTC"))
    
    st.markdown("---")
    st.header("📁 Monitoraggi Attivi")
    posizioni_salvate = portfolio_manager.get_tutte_posizioni()
    
    if not posizioni_salvate:
        st.info("Nessun monitoraggio attivo.")
    else:
        for p_id, p_data in posizioni_salvate.items():
            nome_pool_salvata = p_data.get("nome_coppia", "Pool Sconosciuta")
            with st.expander(f"🟢 {nome_pool_salvata}"):
                st.write(f"Range: {p_data.get('limite_inf', 0):.4f} - {p_data.get('limite_sup', 0):.4f}")
                if st.session_state['conferma_eliminazione'] == p_id:
                    st.warning("Confermi di voler eliminare?")
                    col_y, col_n = st.columns(2)
                    if col_y.button("✔️ Sì", key=f"yes_{p_id}", type="primary"):
                        portfolio_manager.elimina_posizione(p_id)
                        st.session_state['conferma_eliminazione'] = None
                        st.rerun()
                    if col_n.button("❌ No", key=f"no_{p_id}"):
                        st.session_state['conferma_eliminazione'] = None
                        st.rerun()
                else:
                    if st.button("🗑️ Elimina", key=f"del_{p_id}", use_container_width=True):
                        st.session_state['conferma_eliminazione'] = p_id
                        st.rerun()

# INVERSIONE PREZZO LIVE
if inverti_prezzo and live_price > 0:
    live_price = 1 / live_price
    nome_coppia = f"{simbolo_quote}/{simbolo_base}"
    simbolo_base, simbolo_quote = simbolo_quote, simbolo_base

valuta_ui = "$" if simbolo_quote.upper() in ["USDC", "USD"] else simbolo_quote.upper()
vol_daily, trend_suggerito = fetch_historical_metrics(simbolo_base, simbolo_quote)

# Generazione background dei 10.000 cammini Monte Carlo
mc_paths = fetch_mc_scenarios(live_price, vol_daily, trend_suggerito, 14, 10000)

col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("Mercato Live", nome_coppia, f"{live_price:.6f} {valuta_ui}")
col_m2.metric("Volatilità (14d)", f"{(vol_daily*100):.2f}%")
col_m3.metric("Trend Stimato (14d)", f"{(trend_suggerito*100):.2f}%")
st.markdown("---")

tab_setup, tab_live = st.tabs(["🎯 Configura Ingresso", "📊 Dashboard Monitoraggio"])

with tab_setup:
    # --- 1. ZONA GRAFICO INTERATTIVO ---
    st.subheader(f"📈 Analisi Andamento: {nome_coppia}")
    
    periodi_mappa = {
        "1 Giorno": "1d", "1 Settimana": "1w", "1 Mese": "1mo", 
        "6 Mesi": "6mo", "1 Anno": "1y", "5 Anni": "5y", "Max": "max"
    }
    scelta_label = st.radio("Seleziona Orizzonte Temporale:", list(periodi_mappa.keys()), horizontal=True, index=2)
    
    dati_grafico = fetch_chart_data(simbolo_base, simbolo_quote, periodi_mappa[scelta_label])
    if not dati_grafico.empty:
        now = pd.Timestamp.now(tz=dati_grafico.index.tz)
        nuovo_punto = pd.Series({now: float(live_price)})
        dati_grafico = pd.concat([dati_grafico, nuovo_punto])
        
        st.line_chart(dati_grafico, use_container_width=True)
    else:
        st.warning("Dati storici non disponibili per questo orizzonte temporale.")
        
    st.markdown("---")
    
    # --- 2. ZONA MASTER CONTROLS E CONSIGLI ---
    st.subheader("🛡️ Calibrazione Modello Matematico")
    
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        capitale = st.number_input("Capitale (USD)", min_value=0.01, value=100.0, step=10.0)
    with col_c2:
        z_score_scelto = st.slider("Master Z-Score (Cuscinetto di Sicurezza)", min_value=0.5, max_value=4.0, value=1.5, step=0.1)
    with col_c3:
        apr_manuale = st.number_input("APR Concentrato % Stimato", min_value=0.0, value=25.0, step=1.0)
        fee_day_stimate = (capitale * (apr_manuale / 100)) / 365

    st.markdown("<br>", unsafe_allow_html=True)
    
    inf_sim, sup_sim, _ = range_builder.suggerisci_range_ottimale(live_price, vol_daily, 14, z_score_scelto, 0.0)
    inf_asim, sup_asim, _ = range_builder.suggerisci_range_ottimale(live_price, vol_daily, 14, z_score_scelto, trend_suggerito)
    
    col_adv1, col_adv2 = st.columns(2)
    with col_adv1:
        st.info(f"**⚖️ Opzione Neutra (Simmetrica):**\n\nCentrato sul prezzo live. Ideale per mercato laterale.\n\n### {inf_sim:.6f} ↔️ {sup_sim:.6f}")
    with col_adv2:
        st.success(f"**🚀 Opzione Trend-Adjusted ({(trend_suggerito*100):.2f}%):**\n\nSpostato sul trend a 14gg. Ideale per assecondare la direzione.\n\n### {inf_asim:.6f} ↔️ {sup_asim:.6f}")
    
    st.markdown("---")
    
    # --- 3. ZONA OPERATIVA E SIMULAZIONE REAL-TIME ---
    st.subheader("🎯 Imposta Range Finale")
    st.caption("Usa i consigli qui sopra per impostare i limiti operativi. Le metriche di sicurezza si aggiorneranno in tempo reale con 10.000 simulazioni Monte Carlo.")
    
    step_val = 5.0 if valuta_ui == "$" else 0.00001
    formato = "%.2f" if valuta_ui == "$" else "%.6f"
    
    price_a, price_b = st.slider(
        f"Limiti della tua posizione ({valuta_ui})", 
        min_value=float(live_price*0.5), max_value=float(live_price*1.5), 
        value=(float(inf_sim), float(sup_sim)), step=step_val, format=formato
    )
    
    # --- COMPOSIZIONE PORTAFOGLIO RICHIESTA ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### ⚖️ Composizione Portafoglio Richiesta")
    st.caption("Per aprire questa pool senza rimanenze, dovrai avere questa esatta proporzione di controvalore nel tuo wallet:")
    
    bilanciamento = core_math.calcola_bilanciamento_token(capitale, live_price, price_a, price_b)
    val_usd_base = capitale * (bilanciamento["perc_base"] / 100)
    val_usd_quote = capitale * (bilanciamento["perc_quote"] / 100)
    
    col_bil1, col_bil2 = st.columns(2)
    with col_bil1:
        st.info(f"**{simbolo_base}**\n\nControvalore da depositare: **{val_usd_base:.2f} $**\n\nPeso nella pool: **{bilanciamento['perc_base']:.1f}%**")
    with col_bil2:
        st.info(f"**{simbolo_quote}**\n\nControvalore da depositare: **{val_usd_quote:.2f} $**\n\nPeso nella pool: **{bilanciamento['perc_quote']:.1f}%**")
    
    st.markdown("---")
    
    # Calcoli Real-Time Z-Score implicito
    vol_periodo_14 = vol_daily * np.sqrt(14)
    z_effettivo_inf = abs(live_price - price_a) / live_price / max(vol_periodo_14, 0.0001)
    z_effettivo_sup = abs(price_b - live_price) / live_price / max(vol_periodo_14, 0.0001)
    z_effettivo_medio = (z_effettivo_inf + z_effettivo_sup) / 2
    
    # Calcolo Probabilità Real-Time via Monte Carlo
    risultato_mc = range_builder.valuta_probabilita_mc(mc_paths, live_price, price_a, price_b)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_rt1, col_rt2, col_rt3, col_rt4 = st.columns(4)
    col_rt1.metric("Z-Score Effettivo", f"{z_effettivo_medio:.1f}")
    col_rt4.metric("Fee Giornaliere Stimate", f"~{fee_day_stimate:.2f} $")
    
    # UI Dinamica in base allo stato del range (Dentro/Fuori)
    if risultato_mc["stato"] == "IN_RANGE":
        col_rt2.metric("Probabilità 14gg (In Range)", f"{risultato_mc['prob_in_range']}%")
        col_rt3.metric("Probabilità Sicurezza (No Touch)", f"{risultato_mc['prob_no_touch']}%")
    elif risultato_mc["stato"] == "OUT_OF_RANGE":
        col_rt2.metric("Stato Range", "🔴 FUORI RANGE")
        col_rt3.metric("Probabilità Rientro 14gg", f"{risultato_mc['prob_rientro']}%")
    else:
        col_rt2.metric("Errore", "Dati insufficienti")
        col_rt3.metric("-", "-")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 SALVA E INIZIA MONITORAGGIO", use_container_width=True, type="primary"):
        portfolio_manager.salva_posizione(indirizzo_pool, nome_coppia, capitale, price_a, price_b, live_price, apr_manuale)
        st.success(f"Posizione fissata per {nome_coppia}! Passa alla Dashboard di Monitoraggio.")

with tab_live:
    tutte_le_posizioni = portfolio_manager.get_tutte_posizioni()
    
    posizioni_correnti = {}
    if tutte_le_posizioni:
        for p_id, p_data in tutte_le_posizioni.items():
            ind_salvato = p_data.get("indirizzo_pool", p_id if str(p_id).startswith("0x") else "")
            if ind_salvato.lower() == indirizzo_pool.lower():
                posizioni_correnti[p_id] = p_data

    if not posizioni_correnti:
        st.info("Nessuna posizione salvata per questa pool. Vai in 'Configura Ingresso' per iniziare.")
    else:
        st.subheader(f"⏱️ Posizioni Attive: {nome_coppia}")
        st.markdown("<br>", unsafe_allow_html=True)
        
        for p_id, pos in posizioni_correnti.items():
            titolo = "Principale (Vecchia)" if str(p_id).startswith("0x") else f"ID: {p_id}"
            st.markdown(f"#### 🔹 Monitoraggio {titolo}")
            
            cap_in = pos.get("capitale_iniziale", 0)
            p_in = pos.get("prezzo_ingresso", live_price)
            p_a = pos["limite_inf"]
            p_b = pos["limite_sup"]
            apr_salvato = pos.get("apr_ingresso", 0)
            timestamp_in = pos.get("timestamp", time.time())
            
            giorni_reali_trascorsi = max(0.0001, (time.time() - timestamp_in) / 86400.0)
            
            L = core_math.get_liquidity_for_capital(cap_in, p_in, p_a, p_b)
            il_perc, il_usd, lp_value = core_math.calculate_impermanent_loss(L, live_price, p_in, p_a, p_b)
            
            fee_day_attuali = (cap_in * (apr_salvato / 100)) / 365
            
            st.caption(f"Aperta da {giorni_reali_trascorsi:.2f} giorni. APR Impostato: {apr_salvato}%")
            
            col_pos1, col_pos2, col_pos3 = st.columns(3)
            col_pos1.metric("Capitale Investito", f"{cap_in:.2f} $")
            col_pos2.metric("Limite Inferiore", f"{p_a:.6f} {valuta_ui}")
            col_pos3.metric("Limite Superiore", f"{p_b:.6f} {valuta_ui}")
            
            st.markdown("<br>", unsafe_allow_html=True)

            fee_maturate_reali = fee_day_attuali * giorni_reali_trascorsi
            profitto_netto_reale = fee_maturate_reali - il_usd
            
            cr1, cr2, cr3 = st.columns(3)
            cr1.metric("Prezzo Attuale", f"{live_price:.6f} {valuta_ui}", f"vs Ingresso: {(live_price - p_in):.6f} {valuta_ui}")
            cr2.metric("Impermanent Loss Reale", f"- {il_usd:.2f} $")
            cr3.metric("Profitto Netto Stimato", f"{profitto_netto_reale:.2f} $", f"Fee incassate (Stima): +{fee_maturate_reali:.2f}$")
            
            st.markdown("---")
            
            # Valutazione Live Dashboard via Monte Carlo
            risultato_mc_dash = range_builder.valuta_probabilita_mc(mc_paths, live_price, p_a, p_b)

            col_proj, col_prob = st.columns(2)
            
            with col_proj:
                st.subheader("🔮 Proiezioni (Forecast)")
                st.caption(f"Assumendo che il prezzo resti nel range")
                st.metric("Prossime 24 Ore", f"+ {fee_day_attuali:.2f} $")
                st.metric("Prossimi 7 Giorni", f"+ {(fee_day_attuali * 7):.2f} $")
                st.metric("Prossimi 30 Giorni", f"+ {(fee_day_attuali * 30):.2f} $")
                
            with col_prob:
                st.subheader("🎯 Stato di Sicurezza (Prox 14gg)")
                st.caption("Basato su 10.000 simulazioni stocastiche (Monte Carlo)")
                
                if risultato_mc_dash["stato"] == "IN_RANGE":
                    st.metric("Probabilità di rimanere nel range", f"{risultato_mc_dash['prob_in_range']}%")
                    st.metric("Probabilità di non toccare i bordi", f"{risultato_mc_dash['prob_no_touch']}%")
                    
                    if risultato_mc_dash['prob_in_range'] < 50:
                        st.warning("⚠️ Probabilità di uscita elevata. Tieni d'occhio le notifiche Telegram.")
                    else:
                        st.success("✔️ La posizione è statisticamente solida.")
                        
                elif risultato_mc_dash["stato"] == "OUT_OF_RANGE":
                    st.metric("Stato Attuale", "🔴 FUORI RANGE")
                    st.metric("Probabilità stimata di rientro", f"{risultato_mc_dash['prob_rientro']}%")
                    
                    if risultato_mc_dash['prob_rientro'] > 50:
                        st.info("📉 Buone probabilità statistiche di rientro a breve termine.")
                    else:
                        st.error("⚠️ Probabilità di rientro molto basse. Valuta il ribilanciamento.")
            
            st.markdown("<hr style='border: 2px solid #ccc; border-radius: 5px;' />", unsafe_allow_html=True)