import streamlit as st
import time

def get_tutte_posizioni():
    """
    Recupera le posizioni salvate nella sessione corrente dell'utente.
    Nessun dato viene scritto su disco, garantendo la privacy multi-utente.
    """
    if 'portafoglio_virtuale' not in st.session_state:
        st.session_state['portafoglio_virtuale'] = {}
    return st.session_state['portafoglio_virtuale']

def salva_posizione(indirizzo_pool, nome_coppia, capitale, limite_inf, limite_sup, prezzo_ingresso, apr_ingresso):
    """
    Salva una nuova posizione nella RAM (session_state).
    """
    if 'portafoglio_virtuale' not in st.session_state:
        st.session_state['portafoglio_virtuale'] = {}
        
    p_id = str(int(time.time() * 1000))
    
    nuova_posizione = {
        "indirizzo_pool": indirizzo_pool,
        "nome_coppia": nome_coppia,
        "capitale_iniziale": capitale,
        "limite_inf": limite_inf,
        "limite_sup": limite_sup,
        "prezzo_ingresso": prezzo_ingresso,
        "apr_ingresso": apr_ingresso,
        "timestamp": time.time()
    }
    
    st.session_state['portafoglio_virtuale'][p_id] = nuova_posizione
    return p_id

def elimina_posizione(p_id):
    """
    Rimuove la posizione dalla sessione utente.
    """
    if 'portafoglio_virtuale' in st.session_state:
        if p_id in st.session_state['portafoglio_virtuale']:
            del st.session_state['portafoglio_virtuale'][p_id]
            
def aggiorna_posizione(p_id, nuovi_dati):
    """
    Aggiorna i dati di una posizione esistente in RAM.
    """
    if 'portafoglio_virtuale' in st.session_state:
        if p_id in st.session_state['portafoglio_virtuale']:
            st.session_state['portafoglio_virtuale'][p_id].update(nuovi_dati)
