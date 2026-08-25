import streamlit as st
import time
import data_fetcher
import range_builder
import core_math
import portfolio_manager

st.set_page_config(page_title="Slipstream Autopilota", page_icon="⚡", layout="wide")
st.title("Aerodrome Autopilot")
st.markdown("---")

# --- INIZIALIZZAZIONE VARIABILE DI CONFERMA ELIMINAZIONE ---
if 'conferma_eliminazione' not in st.session_state:
    st.session_state['conferma_eliminazione'] = None

# Definiamo le pool preconfigurate per evitare di copiare/incollare indirizzi a mano
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

# --- SIDEBAR PER LA CONFIGURAZIONE ---
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
def fetch_volatility(s_base, s_quote):
    return range_builder.calcola_volatilita_storica(s_base, s_quote, giorni=14)

@st.cache_data(ttl=3600)
def fetch_historical_prices(address):
    return data_fetcher.get_historical_prices(address, days=14)

# --- FASE DI RECUPERO DATI ---
pool_data = fetch_live_data(indirizzo_pool)
if not pool_data:
    st.error(f"🔴 ERRORE: Nessun dato trovato per l'indirizzo Pool {indirizzo_pool}.")
    st.stop()

live_price = pool_data['prezzo_nativo']
nome_coppia = pool_data['coppia_reale']
simboli = nome_coppia.split('/')
simbolo_base = simboli[0]
simbolo_quote = simboli[1] if len(simboli) > 1 else "USDC"

# --- FIX INVERSIONE PREZZO & GESTIONE POSIZIONI ATTIVE ---
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
                
                # --- BLOCCO CONFERMA ELIMINAZIONE AGGIORNATO ---
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
                # --- FINE BLOCCO CONFERMA ---

# Estrazione dello storico prezzi PRIMA di invertire la stringa della coppia
storico_prezzi = fetch_historical_prices(indirizzo_pool)

if inverti_prezzo and live_price > 0:
    live_price = 1 / live_price
    nome_coppia = f"{simbolo_quote}/{simbolo_base}"
    simbolo_base, simbolo_quote = simbolo_quote, simbolo_base
    # Se il prezzo è invertito, capovolgiamo anche l'array dello storico per il calcolo del trend
    if storico_prezzi:
        storico_prezzi = [1/p for p in storico_prezzi if p > 0]

valuta_ui = "$" if simbolo_quote.upper() in ["USDC", "USD"] else simbolo_quote.upper()
vol_daily = fetch_volatility(simbolo_base, simbolo_quote)
trend_suggerito = range_builder.calcola_trend_asimmetria(storico_prezzi) if storico_prezzi else 0.0

# --- HEADER INFORMAZIONI DI MERCATO ---
col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("Mercato Live", nome_coppia, f"{live_price:.6f} {valuta_ui}")
col_m2.metric("Volatilità (14d)", f"{(vol_daily*100):.2f}%")
col_m3.metric("Trend Stimato", f"{(trend_suggerito*100):.2f}%")
st.markdown("---")

# --- CREAZIONE SCHEDE PRINCIPALI ---
tab_setup, tab_live = st.tabs(["🎯 Configura Ingresso", "📊 Dashboard Monitoraggio"])

with tab_setup:
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.subheader("Parametri di Liquidità")
        capitale = st.number_input("Capitale da investire (Controvalore in USD)", min_value=0.01, value=100.0, step=10.0)
        
        st.markdown("---")
        st.markdown("**🛡️ Strategia Statistica (Z-Score)**")
        # CONTROLLO Z-SCORE
        z_score_scelto = st.slider(
            "Ampiezza del range (1.0 = Aggressivo, 1.5 = Bilanciato, 2.0 = Conservativo)", 
            min_value=0.0, max_value=4.0, value=1.5, step=0.1
        )
        
        # NUOVO CONTROLLO ASIMMETRIA
        st.markdown("**📈 Direzione Trend (Asimmetria)**")
        st.caption(f"Sposta il baricentro del range basandoti sul trend storico.")
        offset_scelto_perc = st.slider(
            "Offset asimmetrico (%) [0 = Simmetrico]", 
            min_value=-20.0, max_value=20.0, value=float(trend_suggerito * 100), step=0.5
        )
        offset_scelto = offset_scelto_perc / 100.0
        
        # Calcolo dinamico basato sulla scelta degli slider
        inf_bil, sup_bil, _ = range_builder.suggerisci_range_ottimale(
            live_price, vol_daily, giorni_target=14, z_score=z_score_scelto, offset_asimmetria=offset_scelto
        )
        
        step_val = 5.0 if valuta_ui == "$" else 0.00001
        formato = "%.2f" if valuta_ui == "$" else "%.6f"
        
        st.markdown("---")
        price_a, price_b = st.slider(
            f"Imposta Range di Prezzo ({valuta_ui})", 
            min_value=float(live_price*0.5), max_value=float(live_price*1.5), 
            value=(float(inf_bil), float(sup_bil)), step=step_val, format=formato
        )
        
        st.markdown("---")
        st.subheader("Rendimento Atteso")
        apr_manuale = st.number_input("Inserisci l'APR Concentrato Stimato % (letto su Aerodrome)", min_value=0.0, value=25.0, step=1.0)
        
        fee_day_stimate = (capitale * (apr_manuale / 100)) / 365
        st.info(f"📊 **Le fee giornaliere previste sono:** ~{fee_day_stimate:.2f} $")
    
    with col_s2:
        st.subheader("Salvataggio Stato")
        st.info("Salvando la posizione, il bot Telegram inizierà il monitoraggio su questa coppia specifica.")
        if st.button("💾 SALVA E INIZIA MONITORAGGIO", use_container_width=True):
            portfolio_manager.salva_posizione(indirizzo_pool, nome_coppia, capitale, price_a, price_b, live_price, apr_manuale)
            st.success(f"Posizione fissata per {nome_coppia}! Passa alla Dashboard.")

with tab_live:
    tutte_le_posizioni = portfolio_manager.get_tutte_posizioni()
    
    # Filtriamo per raccogliere solo le posizioni della pool attualmente selezionata
    posizioni_correnti = {}
    if tutte_le_posizioni:
        for p_id, p_data in tutte_le_posizioni.items():
            # Controllo di retrocompatibilità: gestisce vecchi salvataggi (indirizzo pool) e nuovi (ID uuid)
            ind_salvato = p_data.get("indirizzo_pool", p_id if str(p_id).startswith("0x") else "")
            if ind_salvato.lower() == indirizzo_pool.lower():
                posizioni_correnti[p_id] = p_data

    if not posizioni_correnti:
        st.info("Nessuna posizione salvata per questa pool. Vai in 'Configura Ingresso' per iniziare.")
    else:
        st.subheader(f"⏱️ Posizioni Attive: {nome_coppia}")
        st.markdown("<br>", unsafe_allow_html=True)
        
        for p_id, pos in posizioni_correnti.items():
            # Titolo scheda differenziato per vecchi e nuovi salvataggi
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
            
            prob_live_in_range = range_builder.calcola_probabilita_in_range(live_price, p_a, p_b, vol_daily, giorni_target=14)
            prob_live_no_touch = range_builder.calcola_probabilita_no_touch(live_price, p_a, p_b, vol_daily, giorni_target=14)

            col_proj, col_prob = st.columns(2)
            
            with col_proj:
                st.subheader("🔮 Proiezioni (Forecast)")
                st.caption(f"Assumendo che il prezzo resti nel range")
                st.metric("Prossime 24 Ore", f"+ {fee_day_attuali:.2f} $")
                st.metric("Prossimi 7 Giorni", f"+ {(fee_day_attuali * 7):.2f} $")
                st.metric("Prossimi 30 Giorni", f"+ {(fee_day_attuali * 30):.2f} $")
                
            with col_prob:
                st.subheader("🎯 Stato di Sicurezza (Prox 14gg)")
                st.caption("Ricalcolato in base al prezzo live odierno")
                st.metric("Probabilità di rimanere nel range", f"{prob_live_in_range:.1f}%")
                st.metric("Probabilità di non toccare i bordi", f"{prob_live_no_touch:.1f}%")
                if prob_live_in_range < 50:
                    st.warning("La probabilità di uscire dal range è elevata. Tieni d'occhio Telegram.")
                else:
                    st.success("La posizione è statisticamente solida.")
            
            # Linea di separazione robusta se ci sono più posizioni
            st.markdown("<hr style='border: 2px solid #ccc; border-radius: 5px;' />", unsafe_allow_html=True)