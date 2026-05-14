import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px


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

# --- 4. LOGIN-PROZESS ---
if not st.session_state.get("authentication_status"):
    login_manager.login_register()
    st.stop()

# AB HIER fängt das eigentliche Dashboard an
user_name = st.session_state.get('username')

# --- 5. NAVIGATION LOGIK ---
if 'nav_index' not in st.session_state:
    st.session_state.nav_index = 0

options = ["Home", "Mahlzeit tracken", "Übersicht & Grafik", "Gut zu wissen", "Arzt-Modus"]

# --- 6. SIDEBAR ---
with st.sidebar:
    st.success(f"Eingeloggt als {user_name}")
    st.markdown(f"### User: **{user_name}**")
    
    page = st.radio("Navigation", options, index=st.session_state.nav_index)
    st.session_state.nav_index = options.index(page)
    
    st.divider()
    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- 7. SEITEN-LOGIK ---
if page == "Home":
    st.title("Allergie-Tracker")
    st.subheader(f"Willkommen zurück, {user_name}!")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🍴 Mahlzeit erfassen", use_container_width=True):
            st.session_state.nav_index = 1
            st.rerun()
    with col2:
        if st.button("Übersicht & Grafik", use_container_width=True):
            st.session_state.nav_index = 2
            st.rerun()
            
    st.divider()
    data = load_tracker_data(dm, user_name)
    if data is not None and not data.empty:
        last = data.iloc[-1]
        st.info(f"Dein letzter Eintrag: **{last['Mahlzeit']}** ({last['Datum']} um {last['Uhrzeit']})")
    else:
        st.write("Noch keine Einträge vorhanden.")

elif page == "Mahlzeit tracken":
    st.header("🍴 Neue Mahlzeit erfassen")
    
    col_date, col_time = st.columns(2)
    with col_date:
        d_val = st.date_input("Datum", datetime.now())
    with col_time:
        # Prüfen, ob schon eine Zeit gespeichert wurde, sonst jetztige Zeit nehmen
        if 'selected_time' not in st.session_state:
            st.session_state.selected_time = datetime.now().time()
            
        t_val = st.time_input("Uhrzeit", value=st.session_state.selected_time)
        # Speichern der neuen Auswahl im Gedächtnis
        st.session_state.selected_time = t_val
    
    m_val = st.text_input("Was hast du gegessen?")
    
    symptome_ja_nein = st.radio("Traten Symptome auf?", ["Nein", "Ja"], index=0)
    
    selected_symptom = "Keine"
    if symptome_ja_nein == "Ja":
        symptom_liste = [
            "Juckreiz (Haut/Mund)",
            "Quaddeln/Nesselsucht",
            "Anschwellen der Lippen/Zunge",
            "Bauchschmerzen",
            "Blähungen",
            "Krampfartige Schmerzen",
            "Übelkeit/Erbrechen",
            "Durchfall",
            "Atemnot/Husten",
            "Fliessschnupfen",
            "Schwindel/Kreislaufbeschwerden"
        ]
        selected_symptom = st.selectbox("Welches Symptom ist aufgetreten?", symptom_liste)
    
    intens = st.select_slider("Stärke der Reaktion (0 = keine)", options=range(0, 11), value=0)
    bemerkung = st.text_area("Zusätzliche Bemerkungen")
    
    if st.button("Speichern"):
        if m_val:
            save_to_csv(dm, {
                "Nutzer": user_name, 
                "Datum": d_val.strftime('%Y-%m-%d'),
                "Uhrzeit": t_val.strftime('%H:%M'), # Hier wird die gewählte Zeit gespeichert
                "Mahlzeit": m_val,
                "Symptome": symptome_ja_nein, 
                "Details": selected_symptom,
                "Intensität": intens, 
                "Bemerkungen": bemerkung
            })
            st.success("Erfolgreich auf SwitchDrive gespeichert!")
        else:
            st.error("Bitte Mahlzeit eingeben.")

elif page == "Übersicht & Grafik":
    st.header("Deine Analyse")
    data = load_tracker_data(dm, user_name)
    
    if data is not None and not data.empty:
        st.subheader("Historie")
        st.dataframe(data.drop(columns=["Nutzer"]), use_container_width=True)
        
        st.divider()
        
        # --- NEUE GRAFIK: Mahlzeiten vs. Symptome ---
        st.subheader("Welche Mahlzeiten verursachen Probleme?")
        
        # Wir erstellen ein Balkendiagramm
        # x = Mahlzeit, y = Intensität, Farbe = Symptom-Detail
        fig = px.bar(
            data,
            x='Mahlzeit',
            y='Intensität',
            color='Details', # Hier nutzen wir das Dropdown-Symptom für die Farbe
            title="Symptom-Intensität pro Mahlzeit",
            labels={'Intensität': 'Stärke der Reaktion', 'Details': 'Symptom'},
            hover_data=['Datum', 'Uhrzeit', 'Bemerkungen'],
            barmode='group' # Balken stehen nebeneinander, wenn man die gleiche Mahlzeit öfter isst
        )
        
        # Layout-Anpassung für bessere Lesbarkeit
        fig.update_layout(
            xaxis_title="Gegessene Mahlzeit",
            yaxis_title="Reaktionsstärke (0-10)",
            legend_title="Symptom-Typ"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # --- ZUSATZ-ANALYSE: Top Trigger ---
        st.divider()
        st.subheader("Top Trigger (Durchschnittliche Intensität)")
        # Hier gruppieren wir die Daten, um zu sehen, was im Schnitt am schlimmsten ist
        avg_data = data.groupby('Mahlzeit')['Intensität'].mean().sort_values(ascending=False).reset_index()
        st.table(avg_data)

    else:
        st.info("Noch keine Daten vorhanden. Tracke erst ein paar Mahlzeiten!")

elif page == "Gut zu wissen":
    st.title("Gut zu wissen: Allergien verstehen")
    st.write("Wähle ein Allergen aus, um mehr darüber zu erfahren:")

    # 1. Datenquelle für die Informationen
    allergien_info = {
        "Laktose": {
            "Symptome": "Bauchschmerzen, Blähungen, Durchfall, Hautausschlag, Atemnot.",
            "Lebensmittel": "Käse, Joghurt, Butter, Sahne, viele Fertiggerichte, Backwaren.",
            "Tipp": "Achte auf Begriffe wie Molke, Casein oder Laktose auf der Verpackung."
        },
        "Nüsse": {
            "Symptome": "Jucken im Mund, Schwellungen von Lippen und Rachen, schwere Atemnot (Anaphylaxie).",
            "Lebensmittel": "Pesto, Schokolade, Müslis, Gebäck, asiatische Saucen, Öle.",
            "Tipp": "Erdnüsse sind botanisch gesehen Hülsenfrüchte, keine Nüsse!"
        },
        "Eier": {
            "Symptome": "Hautreaktionen (Ekzeme), Übelkeit, Erbrechen, allergischer Schnupfen.",
            "Lebensmittel": "Mayonnaise, Panaden, Teigwaren, Saucen (z.B. Hollandaise), Baiser.",
            "Tipp": "Oft versteckt in Impfstoffen oder als Klärungsmittel in Wein."
        },
        "Gluten": {
            "Symptome": "Verdauungsbeschwerden, Müdigkeit, Kopfschmerzen, Nesselsucht.",
            "Lebensmittel": "Brot, Pasta, Pizza, Couscous, Bier, gebundene Saucen.",
            "Tipp": "Es gibt verschiedene Formen von Glutenunverträglichkeit."
        },
        "Fisch": {
            "Symptome": "Hautrötungen, Schwellungen, Magen-Darm-Beschwerden, Kreislaufprobleme.",
            "Lebensmittel": "Sushi, Worcester-Sauce, Caesar-Dressing, Fischstäbchen, Surimi.",
            "Tipp": "Schon der Dampf beim Kochen kann bei hochsensiblen Personen Reaktionen auslösen."
        }
    }

    # 2. Buttons in Spalten nebeneinander erstellen
    cols = st.columns(5)
    selected_allergen = None

    for i, (name, info) in enumerate(allergien_info.items()):
        if cols[i].button(name, use_container_width=True):
            st.session_state.selected_allergy_info = name

    # 3. Informationen anzeigen, wenn ein Button geklickt wurde
    if 'selected_allergy_info' in st.session_state:
        allergen = st.session_state.selected_allergy_info
        details = allergien_info[allergen]

        st.divider()
        st.subheader(f"Informationen zu: {allergen}")
        
        col_img, col_txt = st.columns([1, 2])
        
        with col_txt:
            st.markdown(f"**Typische Symptome:**\n{details['Symptome']}")
            st.markdown(f"**Enthalten in:**\n{details['Lebensmittel']}")
            st.info(f"**Gut zu wissen:** {details['Tipp']}")

elif page == "Arzt-Modus":
    st.title("👨‍⚕️ Arzt-Modus")
    st.write("Hier kannst du deine Daten für das nächste Arztgespräch zusammenfassen.")

    data = load_tracker_data(dm, user_name)

    if data is not None and not data.empty:
        st.info("Generiere einen PDF-Report deiner gesamten Historie.")
        
        # Button zum PDF generieren
        if st.button("PDF-Report erstellen"):
            from fpdf import FPDF
            
            # PDF Setup
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, f"Allergie-Protokoll: {user_name}", ln=True, align='C')
            pdf.set_font("Arial", size=10)
            pdf.cell(190, 10, f"Erstellt am: {datetime.now().strftime('%d.%m.%Y')}", ln=True, align='C')
            pdf.ln(10)

            # Tabelle Header
            pdf.set_fill_color(200, 220, 255)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(30, 8, "Datum", 1, 0, 'C', True)
            pdf.cell(50, 8, "Mahlzeit", 1, 0, 'C', True)
            pdf.cell(40, 8, "Symptom", 1, 0, 'C', True)
            pdf.cell(20, 8, "Intens.", 1, 0, 'C', True)
            pdf.cell(50, 8, "Bemerkung", 1, 1, 'C', True)

            # Tabelleninhalt
            pdf.set_font("Arial", size=9)
            for _, row in data.iterrows():
                pdf.cell(30, 8, str(row['Datum']), 1)
                pdf.cell(50, 8, str(row['Mahlzeit'])[:25], 1)
                pdf.cell(40, 8, str(row['Details']), 1)
                pdf.cell(20, 8, str(row['Intensität']), 1, 0, 'C')
                pdf.cell(50, 8, str(row['Bemerkungen'])[:30], 1, 1)

            # PDF als Download anbieten
            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.download_button(
                label="📥 PDF herunterladen",
                data=pdf_output,
                file_name=f"Allergie_Report_{user_name}.pdf",
                mime="application/pdf"
            )
            st.success("PDF wurde erfolgreich generiert!")
    else:
        st.warning("Noch keine Daten zum Exportieren vorhanden.")