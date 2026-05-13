import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Konfiguration
st.set_page_config(page_title="Allergie-Tracker Pro", layout="centered")

# 2. Importe
from utils.data_manager import DataManager
from utils.login_manager import LoginManager
from functions.data_handler import load_tracker_data, save_to_csv

# --- 3. INITIALISIERUNG ---
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager()

dm = st.session_state.data_manager
login_manager = LoginManager(dm)

# --- 4. LOGIN PROZESS ---
login_manager.login_register()

if not (st.session_state.get('logged_in') or st.session_state.get('authentication_status')):
    st.stop()

user_name = st.session_state.get('username', 'Nutzer')

# --- 5. NAVIGATION LOGIK ---
if 'nav_index' not in st.session_state:
    st.session_state.nav_index = 0

options = ["Home", "Mahlzeit tracken", "Übersicht & Grafik", "Gut zu wissen", "Arzt-Modus"]

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown(f"### User: **{user_name}**")
    
    # Der Status wird automatisch vom DataManager in der Sidebar angezeigt
    
    page = st.radio("Navigation", options, index=st.session_state.nav_index)
    st.session_state.nav_index = options.index(page)
    
    st.divider()
    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- 7. SEITEN-LOGIK ---
if page == "Home":
    st.title("🚀 Allergie-Tracker Dashboard")
    st.subheader(f"Willkommen zurück, {user_name}!")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🍴 Mahlzeit erfassen", width='stretch'):
            st.session_state.nav_index = 1
            st.rerun()
    with col2:
        if st.button("📊 Grafiken & Trends", width='stretch'):
            st.session_state.nav_index = 2
            st.rerun()
            
    st.divider()
    data = load_tracker_data(dm, user_name)
    if data is not None and not data.empty:
        last = data.iloc[-1]
        st.info(f"Dein letzter Eintrag: **{last['Mahlzeit']}** ({last['Datum']})")
    else:
        st.write("Noch keine Einträge vorhanden.")

elif page == "Mahlzeit tracken":
    st.header("🍴 Neue Mahlzeit erfassen")
    d_val = st.date_input("Datum", datetime.now())
    m_val = st.text_input("Was hast du gegessen?")
    intens = st.select_slider("Stärke der Reaktion", options=range(0, 11), value=0)
    
    if st.button("Speichern auf SwitchDrive"):
        if m_val:
            save_to_csv(dm, {
                "Nutzer": user_name, "Datum": d_val.strftime('%Y-%m-%d'),
                "Uhrzeit": datetime.now().strftime('%H:%M'), "Mahlzeit": m_val,
                "Symptome": "Check", "Intensität": intens, "Bemerkungen": ""
            })
            st.success("Erfolgreich gespeichert!")
        else:
            st.error("Bitte Mahlzeit eingeben.")

elif page == "Übersicht & Grafik":
    st.header("📊 Deine Analyse")
    data = load_tracker_data(dm, user_name)
    if data is not None and not data.empty:
        st.dataframe(data.drop(columns=["Nutzer"]), width='stretch')
    else:
        st.info("Keine Daten vorhanden.")
