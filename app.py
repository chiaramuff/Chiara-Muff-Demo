import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. KONFIGURATION ---
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

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'tracker_data' not in st.session_state:
    st.session_state.tracker_data = pd.DataFrame(
        columns=["Datum", "Uhrzeit", "Mahlzeit", "Symptome", "Intensität", "Bemerkungen"]
    )

# --- 2. LOGIN / REGISTRIERUNG ---
if not st.session_state.logged_in:
    st.title("Willkommen beim Allergie-Tracker")
    auth_mode = st.radio("Aktion wählen:", ["Login", "Registrieren"], horizontal=True)
    username = st.text_input("Benutzername")
    password = st.text_input("Passwort", type="password")

    if auth_mode == "Registrieren":
        if st.button("Konto erstellen"):
            if username and password:
                if save_user(username, password):
                    st.success("Konto erstellt! Bitte jetzt einloggen.")
                else:
                    st.error("Benutzername existiert bereits.")
    else:
        if st.button("Einloggen"):
            users = load_users()
            if ((users["username"] == username) & (users["password"] == password)).any():
                st.session_state.logged_in = True
                st.session_state.user_name = username
                st.rerun()
            else:
                st.error("Falsche Logindaten.")
    st.stop()

# --- 3. HAUPTAPP ---
st.title("Allergie-Tracker")
st.write(f"Hallo **{st.session_state.user_name}** | {datetime.now().strftime('%d.%m.%Y')}")

tab1, tab2, tab3 = st.tabs(["Mahlzeit tracken", "Übersicht", "Wissen"])

with tab1:
    st.header("Mahlzeit erfassen")
    
    # 1. Diese Felder stehen oben (außerhalb des Forms für sofortige Reaktion)
    col1, col2 = st.columns(2)
    with col1:
        date_val = st.date_input("Datum", datetime.now())
        meal_val = st.text_input("Was hast du gegessen?", placeholder="z.B. Käse-Omelett")
    with col2:
        time_val = st.time_input("Uhrzeit", datetime.now())
    
    # DER TRIGGER: Steht außerhalb des Forms, damit die App sofort neu lädt
    has_symptoms = st.radio("Traten Symptome auf?", ["Nein", "Ja"], horizontal=True)
    
    # Initialisierung
    symptom_list = []
    intensity = 0
    
    # DYNAMISCHE FELDER: Erscheinen SOFORT bei Klick auf "Ja"
    if has_symptoms == "Ja":
        st.info("Bitte gib die Details zu deinen Symptomen an:")
        symptom_options = [
            "Blähungen", "Bauchschmerzen", "Magenkrämpfe", "Übelkeit", "Sodbrennen", 
            "Durchfall", "Verstopfung", "Hautausschlag", "Rötung", "Juckreiz", 
            "Quaddeln", "Atemnot", "Husten", "Schnupfen", "Kopfschmerzen", 
            "Schwindel", "Müdigkeit", "Herzrasen", "Schwellungen"
        ]
        symptom_list = st.multiselect("Welche Symptome?", options=sorted(symptom_options))
        intensity = st.select_slider("Intensität (1-10)", options=range(1, 11), value=5)

    # 2. Das Formular dient jetzt nur noch als "Speicher-Container"
    with st.form("save_form"):
        notes_val = st.text_area("Bemerkungen / Zutaten")
        submit = st.form_submit_button("Eintrag speichern")
        
        if submit:
            if meal_val: # Validierung: Theo will keine leeren Daten
                new_row = {
                    "Datum": date_val.strftime('%Y-%m-%d'),
                    "Uhrzeit": time_val.strftime('%H:%M'),
                    "Mahlzeit": meal_val,
                    "Symptome": ", ".join(symptom_list) if symptom_list else "Keine",
                    "Intensität": intensity,
                    "Bemerkungen": notes_val
                }
                st.session_state.tracker_data = pd.concat(
                    [st.session_state.tracker_data, pd.DataFrame([new_row])], 
                    ignore_index=True
                )
                st.success("Erfolgreich gespeichert!")
                st.balloons() # Kleines visuelles Feedback
            else:
                st.error("Bitte gib an, was du gegessen hast.")

with tab2:
    st.header("Deine Historie")
    if not st.session_state.tracker_data.empty:
        st.dataframe(st.session_state.tracker_data, use_container_width=True)
        csv = st.session_state.tracker_data.to_csv(index=False).encode('utf-8')
        st.download_button("Als CSV exportieren", data=csv, file_name="export.csv", mime="text/csv")
    else:
        st.info("Noch keine Daten vorhanden.")

with tab3:
    st.header("Wissen")
    st.info("Informationen zu Allergenen folgen in V1.2.")
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()