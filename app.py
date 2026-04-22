import streamlit as st
import pandas as pd
from datetime import datetime

# Konfiguration: Clean & Professionell
st.set_page_config(page_title="Allergie-Tracker", layout="centered")

# Datenstruktur und Nutzername initialisieren
if 'tracker_data' not in st.session_state:
    st.session_state.tracker_data = pd.DataFrame(
        columns=["Datum", "Uhrzeit", "Mahlzeit", "Symptome", "Intensität", "Bemerkungen"]
    )

if 'user_name' not in st.session_state:
    st.session_state.user_name = ""

# Login-Bereich (falls noch kein Name vergeben wurde)
if not st.session_state.user_name:
    st.title("Willkommen beim Allergie-Tracker")
    name_input = st.text_input("Bitte gib deinen Namen ein, um zu starten:")
    if st.button("Starten"):
        if name_input:
            st.session_state.user_name = name_input
            st.rerun()
        else:
            st.warning("Bitte gib einen Namen ein.")
else:
    # Hauptanwendung, wenn Name bekannt ist
    st.title(f"Allergie-Tracker")
    st.write(f"Hallo *{st.session_state.user_name}*, heute ist der {datetime.now().strftime('%d.%m.%Y')}.")

    # Navigation mittels Tabs
    tab1, tab2, tab3 = st.tabs(["Mahlzeit tracken", "Übersicht", "Wissen"])

    with tab1:
        st.header("Mahlzeit & Symptome erfassen")
        
        with st.form("entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("Datum", datetime.now())
                meal = st.text_input("Was hast du gegessen?", placeholder="z.B. Dinkelbrot")
            with col2:
                time = st.time_input("Uhrzeit", datetime.now())
            
            has_symptoms = st.radio("Symptome vorhanden?", ["Nein", "Ja"], horizontal=True)
            
            intensity = 0
            symptom_list = []
            if has_symptoms == "Ja":
                intensity = st.select_slider("Intensität (1-10)", options=range(1, 11), value=5)
                symptom_list = st.multiselect(
                    "Art der Symptome", 
                    ["Magenbeschwerden", "Hautausschlag", "Atembeschwerden", "Kopfschmerzen"]
                )
            
            notes = st.text_area("Bemerkungen (Zutaten oder spezielle Beschwerden)")
            
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
                st.success("Eintrag erfolgreich gespeichert!")

    with tab2:
        st.header(f"Werte-Übersicht für {st.session_state.user_name}")
        if not st.session_state.tracker_data.empty:
            st.dataframe(st.session_state.tracker_data, use_container_width=True)
            
            # Export-Funktion
            csv = st.session_state.tracker_data.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Daten für den Arzt exportieren (CSV)",
                data=csv,
                file_name=f"allergie_report_{st.session_state.user_name}.csv",
                mime="text/csv"
            )
            
            if st.button("Logout / Name ändern"):
                st.session_state.user_name = ""
                st.rerun()
        else:
            st.info("Noch keine Daten vorhanden.")

    with tab3:
        st.header("Gut zu wissen")
        st.info("Hier entstehen in Kürze Informationen zu Allergenen (Roadmap V1.2).")
