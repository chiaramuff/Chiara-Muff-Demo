import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. KONFIGURATION & DATENSPEICHERUNG ---
st.set_page_config(page_title="Allergie-Tracker", layout="centered")

USER_DB = "users.csv"

def load_users():
    if os.path.exists(USER_DB):
        return pd.read_csv(USER_DB)
    return pd.DataFrame(columns=["username", "password"])

def save_user(username, password):
    users = load_users()
    if username in users["username"].values:
        return False
    new_user = pd.DataFrame([[username, password]], columns=["username", "password"])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USER_DB, index=False)
    return True

# Session State für Login und Daten initialisieren
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'tracker_data' not in st.session_state:
    st.session_state.tracker_data = pd.DataFrame(
        columns=["Datum", "Uhrzeit", "Mahlzeit", "Symptome", "Intensität", "Bemerkungen"]
    )

# --- 2. LOGIN / REGISTRIERUNG (Wireframe Seite 1) ---
if not st.session_state.logged_in:
    st.title("Willkommen beim Allergie-Tracker")
    auth_mode = st.radio("Aktion wählen:", ["Login", "Registrieren"], horizontal=True)
    
    username = st.text_input("Benutzername")
    password = st.text_input("Passwort", type="password")

    if auth_mode == "Registrieren":
        if st.button("Konto erstellen"):
            if username and password:
                if save_user(username, password):
                    st.success("Konto erstellt! Du kannst dich jetzt einloggen.")
                else:
                    st.error("Benutzername existiert bereits.")
            else:
                st.warning("Bitte fülle alle Felder aus.")
    else:
        if st.button("Einloggen"):
            users = load_users()
            if ((users["username"] == username) & (users["password"] == password)).any():
                st.session_state.logged_in = True
                st.session_state.user_name = username
                st.rerun()
            else:
                st.error("Falscher Benutzername oder Passwort.")
    st.stop()

# --- 3. HAUPTAPP (Nach erfolgreichem Login) ---
st.title("Allergie-Tracker")
st.write(f"Eingeloggt als: **{st.session_state.user_name}** | Heute ist der {datetime.now().strftime('%d.%m.%Y')}")

tab1, tab2, tab3 = st.tabs(["Mahlzeit tracken", "Übersicht", "Wissen"])

# TAB 1: TRACKING (Wireframe Seite 2 & Nutzertest-Optimierung)
with tab1:
    st.header("Mahlzeit & Symptome erfassen")
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Datum", datetime.now())
            meal = st.text_input("Was hast du gegessen?", placeholder="z.B. Pasta Carbonara")
        with col2:
            time = st.time_input("Uhrzeit", datetime.now())
        
        # Trigger für dynamische Felder
        has_symptoms = st.radio("Symptome vorhanden?", ["Nein", "Ja"], horizontal=True)
        
        intensity = 0
        symptom_list = []
        
        # DYNAMISCHE FELDER: Erscheinen sofort innerhalb des Formulars
        if has_symptoms == "Ja":
            symptom_options = [
                "Blähungen", "Bauchschmerzen", "Magenkrämpfe", "Übelkeit", "Sodbrennen", 
                "Durchfall", "Verstopfung", "Hautausschlag", "Rötung", "Juckreiz", 
                "Quaddeln", "Atemnot", "Husten", "Schnupfen", "Kopfschmerzen", 
                "Schwindel", "Müdigkeit", "Herzrasen", "Schwellungen"
            ]
            symptom_list = st.multiselect(
                "Welche Symptome treten auf?", 
                options=sorted(symptom_options),
                help="Wähle alle Beschwerden aus, die du spürst."
            )
            intensity = st.select_slider(
                "Intensität der Beschwerden (1-10)", 
                options=range(1, 11), 
                value=5
            )
        
        notes = st.text_area("Bemerkungen / Inhaltsstoffe (z.B. enthält Laktose)")
        submit = st.form_submit_button("Eintrag speichern")
        
        if submit:
            new_row = {
                "Datum": date.strftime('%Y-%m-%d'),
                "Uhrzeit": time.strftime('%H:%M'),
                "Mahlzeit": meal,
                "Symptome": ", ".join(symptom_list) if symptom_list else "Keine",
                "Intensität": intensity,
                "Bemerkungen": notes
            }
            st.session_state.tracker_data = pd.concat(
                [st.session_state.tracker_data, pd.DataFrame([new_row])], 
                ignore_index=True
            )
            st.success("Eintrag erfolgreich in der Übersicht gespeichert!")

# TAB 2: ÜBERSICHT (Wireframe Seite 3)
with tab2:
    st.header(f"Datenhistorie von {st.session_state.user_name}")
    if not st.session_state.tracker_data.empty:
        # Anzeige der Rohdaten für Theo
        st.dataframe(st.session_state.tracker_data, use_container_width=True)
        
        # Export-Funktion für den Arzt (Roadmap Ziel)
        csv = st.session_state.tracker_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Bericht für Arzt erstellen (CSV)",
            data=csv,
            file_name=f"allergie_export_{st.session_state.user_name}.csv",
            mime="text/csv"
        )
    else:
        st.info("Noch keine Daten vorhanden. Nutze den Tab 'Mahlzeit tracken'.")

# TAB 3: WISSEN & LOGOUT (Wireframe Seite 4)
with tab3:
    st.header("Gut zu wissen")
    st.info("Diese Sektion wird in Version 1.2 der Roadmap mit Allergen-Informationen gefüllt.")
    
    st.divider()
    if st.button("Abmelden"):
        st.session_state.logged_in = False
        st.rerun()