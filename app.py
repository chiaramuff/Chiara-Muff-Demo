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
# Das löscht den alten Manager und erzwingt eine neue Verbindung bei jedem Laden
st.session_state.data_manager = DataManager()

dm = st.session_state.data_manager
login_manager = LoginManager(dm)

# Login Prozess
login_manager.login_register()
if not (st.session_state.get('logged_in') or st.session_state.get('authentication_status')):
    st.stop()

user_name = st.session_state.get('username', 'Nutzer')

# Navigation Logik
if 'nav_index' not in st.session_state:
    st.session_state.nav_index = 0

options = ["Home", "Mahlzeit tracken", "Übersicht & Grafik", "Gut zu wissen", "Arzt-Modus"]

with st.sidebar:
    st.markdown(f"### User: **{user_name}**")
    # Verbindungs-Status anzeigen
    if dm.fs is not None:
        st.success("✅ SwitchDrive aktiv")
    else:
        st.error("❌ Keine Verbindung")
    
    page = st.radio("Navigation", options, index=st.session_state.nav_index)
    st.session_state.nav_index = options.index(page)
    
    if st.button("Logout"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- 7. SEITEN-LOGIK ---

if page == "Home":
    st.title("🚀 Allergie-Tracker Dashboard")
    st.subheader(f"Willkommen zurück, {user_name}!")
    
    # Dashboard Buttons (Navigation)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🍴 Mahlzeit erfassen", use_container_width=True):
            st.session_state.nav_index = 1
            st.rerun()
    with col2:
        if st.button("📊 Grafiken & Trends", use_container_width=True):
            st.session_state.nav_index = 2
            st.rerun()
            
    st.divider()
    
    # Letzte Aktivität anzeigen
    data = load_tracker_data(dm, user_name)
    if not data.empty:
        last = data.iloc[-1]
        st.info(f"Dein letzter Eintrag: **{last['Mahlzeit']}** ({last['Datum']})")
    else:
        st.write("Noch keine Einträge vorhanden. Klicke auf 'Mahlzeit erfassen'!")

elif page == "Mahlzeit tracken":
    st.header("🍴 Neue Mahlzeit erfassen")
    with st.container():
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
                st.success("Daten wurden erfolgreich in die Cloud übertragen!")
                # Optional: Nach dem Speichern zur Grafik springen
                # st.session_state.nav_index = 2
                # st.rerun()
            else:
                st.error("Bitte gib eine Mahlzeit ein.")

elif page == "Übersicht & Grafik":
    st.header("📊 Deine Analyse")
    data = load_tracker_data(dm, user_name)
    if not data.empty:
        st.dataframe(data.drop(columns=["Nutzer"]), use_container_width=True)
    else:
        st.info("Noch keine Daten zum Anzeigen verfügbar.")

# (Hier kannst du die restlichen Seiten "Gut zu wissen" und "Arzt-Modus" wie gehabt einfügen)