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

user_name = st.session_state.get('username')

# --- 5. NAVIGATION LOGIK ---
if 'nav_index' not in st.session_state:
    st.session_state.nav_index = 0

# Exakt die 5 gewohnten Seiten beibehalten
options = ["Home", "Mahlzeit tracken", "Übersicht & Grafik", "Gut zu wissen", "Arzt-Modus"]

# Schutz vor Index-Fehlern beim Versionswechsel
if st.session_state.nav_index >= len(options):
    st.session_state.nav_index = 0

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

# --- SEITE 1: HOME ---
if page == "Home":
    st.title("Allergie-Tracker")
    st.subheader(f"Willkommen zurück, {user_name}! 👋")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🍴 Mahlzeit erfassen", use_container_width=True):
            st.session_state.nav_index = 1
            st.rerun()
    with col2:
        if st.button("📊 Übersicht & Grafik", use_container_width=True):
            st.session_state.nav_index = 2
            st.rerun()
            
    st.divider()
    data = load_tracker_data(dm, user_name)
    if data is not None and not data.empty:
        last = data.iloc[-1]
        uhrzeit_str = last['Uhrzeit'] if 'Uhrzeit' in last else '--:--'
        st.info(f"Dein letzter Eintrag: **{last['Mahlzeit']}** ({last['Datum']} um {uhrzeit_str})")
    else:
        st.write("Noch keine Einträge vorhanden.")

# --- SEITE 2: MAHLZEIT TRACKEN ---
elif page == "Mahlzeit tracken":
    st.header("🍴 Neue Mahlzeit erfassen")
    
    col_date, col_time = st.columns(2)
    with col_date:
        d_val = st.date_input("Datum", datetime.now())
    with col_time:
        if 'selected_time' not in st.session_state:
            st.session_state.selected_time = datetime.now().time()
        t_val = st.time_input("Uhrzeit", value=st.session_state.selected_time)
        st.session_state.selected_time = t_val
    
    m_val = st.text_input("Was hast du gegessen / getrunken?")
    
    # Interaktive Abfrage: Bei "Ja" ploppen weitere Fragen auf
    symptome_ja_nein = st.radio("Traten Beschwerden / Symptome auf?", ["Nein", "Ja"], index=0)
    
    selected_symptom = "Keine Beschwerden"
    intens = 0
    bemerkung = ""
    
    # DYNAMISCHES AUFPLOPPEN BEI "JA"
    if symptome_ja_nein == "Ja":
        st.markdown("#### ⚠️ Details zu den Beschwerden")
        symptom_liste = [
            "Juckreiz (Mund/Rachen/Lippen)",
            "Anschwellen der Zunge/Lippen",
            "Kribbeln auf der Haut / Ausschlag",
            "Quaddeln / Nesselsucht / Rötungen",
            "Bauchschmerzen / Magenknurren",
            "Blähungen / Völlegefühl",
            "Krampfartige Schmerzen (Unterleib)",
            "Übelkeit / Sodbrennen",
            "Erbrechen",
            "Durchfall",
            "Atemnot / Pfeifender Atem / Asthma",
            "Hustenreiz / Kratzen im Hals",
            "Fliessschnupfen / Verstopfte Nase",
            "Augenjucken / Tränende Augen",
            "Kopfschmerzen / Migräne",
            "Schwindel / Kreislaufbeschwerden / Schwäche",
            "Müdigkeit (Extremer Leistungsknick)"
        ]
        selected_symptom = st.selectbox("Welches Hauptsymptom ist aufgetreten?", symptom_liste)
        intens = st.select_slider("Stärke der Reaktion (1 = kaum spürbar, 10 = extrem stark)", options=range(0, 11), value=3)
        bemerkung = st.text_area("Zusätzliche Notizen (z.B. Medikamente genommen?)")
    
    st.divider()
    
    col_save, col_view = st.columns(2)
    with col_save:
        if st.button("💾 Eintrag speichern", use_container_width=True, type="primary"):
            if m_val:
                save_to_csv(dm, {
                    "Nutzer": user_name, 
                    "Datum": d_val.strftime('%Y-%m-%d'),
                    "Uhrzeit": t_val.strftime('%H:%M'), 
                    "Mahlzeit": m_val,
                    "Symptome": symptome_ja_nein, 
                    "Details": selected_symptom,
                    "Intensität": intens, 
                    "Bemerkungen": bemerkung
                })
                # Erfolgsmeldung, die auch nach dem st.rerun() für den Nutzer sichtbar bleibt
                st.toast("🎉 Erfolgreich gespeichert!", icon="💾")
                st.rerun()
            else:
                st.error("Bitte gib ein, was du gegessen hast.")
                
    with col_view:
        if st.button("🔍 Zur Übersicht springen", use_container_width=True):
            st.session_state.nav_index = 2
            st.rerun()

# --- SEITE 3: ÜBERSICHT & GRAFIK ---
elif page == "Übersicht & Grafik":
    st.header("📊 Deine Analyse & Historie")
    
    if st.button("🍴 Neuen Eintrag hinzufügen", use_container_width=True):
        st.session_state.nav_index = 1
        st.rerun()
        
    st.divider()
    data = load_tracker_data(dm, user_name)
    
    if data is not None and not data.empty:
        st.subheader("Deine bisherigen Einträge")
        display_df = data.drop(columns=["Nutzer"]) if "Nutzer" in data.columns else data
        st.dataframe(display_df, use_container_width=True)
        
        st.divider()
        st.subheader("Welche Mahlzeiten verursachen Probleme?")
        
        fig = px.bar(
            data,
            x='Mahlzeit',
            y='Intensität',
            color='Details' if 'Details' in data.columns else None, 
            title="Symptom-Intensität pro Mahlzeit",
            labels={'Intensität': 'Stärke der Reaktion', 'Details': 'Symptom'},
            hover_data=['Datum', 'Bemerkungen'] if 'Bemerkungen' in data.columns else ['Datum'],
            barmode='group' 
        )
        
        fig.update_layout(xaxis_title="Gegessene Mahlzeit", yaxis_title="Reaktionsstärke (0-10)", legend_title="Symptom-Typ")
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        st.subheader("Top Trigger (Durchschnittliche Intensität)")
        avg_data = data.groupby('Mahlzeit')['Intensität'].mean().sort_values(ascending=False).reset_index()
        avg_data.columns = ['Mahlzeit', 'Ø Intensität']
        st.table(avg_data)
    else:
        st.info("Noch keine Daten vorhanden. Erfasse zuerst eine Mahlzeit!")

# --- SEITE 4: GUT ZU WISSEN (Wieder als sauberes Dropdown) ---
elif page == "Gut zu wissen":
    st.title("💡 Allergie-Lexikon")
    st.write("Wähle ein Allergen oder einen Auslöser aus dem Dropdown aus, um Details zu sehen:")

    allergien_info = {
        "Bitte auswählen...": {"Symptome": "-", "Lebensmittel": "-", "Tipp": "Wähle ein Allergen aus der Liste aus."},
        "Laktose (Milchzucker)": {
            "Symptome": "Blähungen, Bauchschmerzen, krampfartige Magenbeschwerden, wässriger Durchfall.",
            "Lebensmittel": "Kuhmilch, Joghurt, Quark, Sahne, Milchschokolade, viele Fertiggerichte und Backwaren.",
            "Tipp": "Achte auf 'Molkenpulver' oder 'Magermilchpulver' in den Zutaten. Laktase-Tabletten können helfen."
        },
        "Fruktose (Fruchtzucker)": {
            "Symptome": "Blähbauch ('Schwangerschaftsbauch'), Bauchschmerzen, weicher Stuhl bis Durchfall, Übelkeit.",
            "Lebensmittel": "Äpfel, Birnen, Kirschen, Trockenobst, Honig, Softdrinks (HFCS-Sirup), Süssigkeiten.",
            "Tipp": "Haushaltszucker wird oft besser vertragen als reine Fruktose. Traubenzucker hilft bei der Aufnahme."
        },
        "Histamin (Intoleranz)": {
            "Symptome": "Flushing (Hautrötung/Heisswerden im Gesicht), Kopfschmerzen/Migräne, Fliessschnupfen, Herzrasen.",
            "Lebensmittel": "Gereifter Käse, Rotwein, Salami, Tomaten, Meeresfrüchte, Sauerkraut, Schokolade.",
            "Tipp": "Histamin baut sich in Lebensmitteln auf, je älter oder gereifter sie sind. Immer fangfrisch essen!"
        },
        "Gluten / Zöliakie": {
            "Symptome": "Chronischer Durchfall, Gewichtsverlust, Nährstoffmangel, extreme Müdigkeit, Blähungen.",
            "Lebensmittel": "Weizen, Roggen, Gerste, Dinkel, Pizza, Pasta, Brot, Bier, konventionelle Saucen.",
            "Tipp": "Zöliakie ist eine Autoimmunerkrankung, keine reine Allergie. Hier hilft nur strikter Verzicht."
        },
        "Nüsse & Schalenfrüchte": {
            "Symptome": "Sofortiges Jucken im Mund, Anschwellen von Atemwegen, Nesselsucht, anaphylaktischer Schock.",
            "Lebensmittel": "Haselnüsse, Walnüsse, Cashews, Mandeln, Pesto, Müsli, Backwaren, Nougat-Aufstrich.",
            "Tipp": "Spurenkennzeichnungen ('Kann Nüsse enthalten') müssen bei hochgradigen Allergikern beachtet werden."
        },
        "Erdnüsse": {
            "Symptome": "Massiver Juckreiz, Atemnot, Schwellungen, extrem hohes Risiko für allergischen Schock.",
            "Lebensmittel": "Erdnussbutter, Erdnussöl, asiatische Gerichte (Saucen), Knabberzeug/Flips.",
            "Tipp": "Erdnüsse gehören botanisch zu den Hülsenfrüchten, nicht zu den echten Baumnüssen!"
        }
    }

    wahl = st.selectbox("Auslöser auswählen:", list(allergien_info.keys()))
    if wahl != "Bitte auswählen...":
        details = allergien_info[wahl]
        st.divider()
        st.subheader(f"Ergebnisse für: {wahl}")
        st.markdown(f"**🔴 Typische Symptome:**\n{details['Symptome']}")
        st.markdown(f"**🛒 Häufig enthalten in:**\n{details['Lebensmittel']}")
        st.info(f"**ℹ️ Gut zu wissen:** {details['Tipp']}")

# --- SEITE 5: ARZT-MODUS (Mit Textfeld für PDF-Notizen) ---
elif page == "Arzt-Modus":
    st.title("👨‍⚕️ Arzt-Modus")
    st.write("Bereite hier die Daten optimal für dein nächstes Arztgespräch vor.")

    data = load_tracker_data(dm, user_name)

    if data is not None and not data.empty:
        st.subheader("📝 Zusätzliche Bemerkungen für den Arzt")
        arzt_notiz = st.text_area(
            "Schreibe hier Notizen, die ganz oben auf das PDF gedruckt werden sollen:",
            placeholder="z.B. Fragen an den Arzt, Medikamente, die du nimmst, oder wann Beschwerden besonders stark sind..."
        )
        
        st.divider()
        
        if st.button("PDF-Report erstellen", type="primary"):
            from fpdf import FPDF
            
            pdf = FPDF()
            pdf.add_page()
            
            # Haupttitel
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, f"Allergie-Protokoll: {user_name}", ln=True, align='C')
            pdf.set_font("Arial", size=10)
            pdf.cell(190, 10, f"Erstellt am: {datetime.now().strftime('%d.%m.%Y')}", ln=True, align='C')
            pdf.ln(5)
            
            # Freitext / Notiz einfügen, wenn ausgefüllt
            if arzt_notiz:
                pdf.set_font("Arial", 'B', 11)
                pdf.cell(190, 8, "Persoenliche Anmerkungen & Fragen an den Arzt:", ln=True)
                pdf.set_font("Arial", size=10)
                notiz_safe = arzt_notiz.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(190, 5, notiz_safe)
                pdf.ln(5)

            # Trennlinie
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

            # Tabelle Überschrift
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(190, 8, "Erfasste Historie (Ernaehrungs- und Symptomtagebuch):", ln=True)
            pdf.ln(2)

            # Tabellen-Header formatieren
            pdf.set_fill_color(200, 220, 255)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(25, 8, "Datum", 1, 0, 'C', True)
            pdf.cell(45, 8, "Mahlzeit", 1, 0, 'C', True)
            pdf.cell(45, 8, "Symptom", 1, 0, 'C', True)
            pdf.cell(15, 8, "Intens.", 1, 0, 'C', True)
            pdf.cell(60, 8, "Bemerkung", 1, 1, 'C', True)

            # Zeilen befüllen
            pdf.set_font("Arial", size=9)
            for _, row in data.iterrows():
                datum_text = str(row.get('Datum', '')).encode('latin-1', 'replace').decode('latin-1')
                mahlzeit_text = str(row.get('Mahlzeit', ''))[:22].encode('latin-1', 'replace').decode('latin-1')
                details_text = str(row.get('Details', ''))[:22].encode('latin-1', 'replace').decode('latin-1')
                intens_text = str(row.get('Intensität', '0'))
                bemerkung_text = str(row.get('Bemerkungen', ''))[:30].encode('latin-1', 'replace').decode('latin-1')

                pdf.cell(25, 8, datum_text, 1)
                pdf.cell(45, 8, mahlzeit_text, 1)
                pdf.cell(45, 8, details_text, 1)
                pdf.cell(15, 8, intens_text, 1, 0, 'C')
                pdf.cell(60, 8, bemerkung_text, 1, 1)

            try:
                pdf_output = pdf.output(dest='S').encode('latin-1')
            except AttributeError:
                pdf_output = bytes(pdf.output(dest='S'))

            st.download_button(
                label="📥 PDF inklusive Arzt-Notizen herunterladen",
                data=pdf_output,
                file_name=f"Allergie_Report_{user_name}.pdf",
                mime="application/pdf"
            )
            st.success