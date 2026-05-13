import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from fpdf import FPDF

# 1. SEITENKONFIGURATION (Muss zwingend der erste Streamlit-Befehl sein)
st.set_page_config(page_title="Allergie-Tracker Pro", layout="centered")

# 2. IMPORTE
from utils.data_manager import DataManager
from utils.login_manager import LoginManager
from functions.data_handler import load_tracker_data, save_to_csv

# --- 3. INITIALISIERUNG ---
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = DataManager(
        fs_protocol='webdav',
        fs_root_folder="Allergie-Tracker" 
    )

dm = st.session_state.data_manager
login_manager = LoginManager(dm)

dm = st.session_state.data_manager

# DEBUG-CHECK (Nur für euch jetzt zum Testen)
if st.sidebar.checkbox("Verbindung prüfen"):
    if dm.fs is None:
        st.sidebar.error("❌ Keine Verbindung zu SwitchDrive (FS ist None)")
    else:
        st.sidebar.success("✅ Verbindung zu SwitchDrive steht")
        # Teste ob der Ordner sichtbar ist
        try:
            files = dm.fs.ls(dm.fs_root_folder)
            st.sidebar.write("Dateien gefunden:", files)
        except Exception as e:
            st.sidebar.error(f"Ordner nicht lesbar: {e}")

# 4. LOGIN PROZESS
# Zeigt die Login/Registrierungs-Maske an
login_manager.login_register()

# Überprüfung des Login-Status (unterstützt verschiedene Versionen des LoginManagers)
is_logged_in = st.session_state.get('logged_in') or st.session_state.get('authentication_status')

if not is_logged_in:
    # Falls nicht eingeloggt, stoppt das Skript hier und zeigt nichts weiter an
    st.stop()

# Ab hier ist der User sicher eingeloggt
user_name = st.session_state.get('username', 'Nutzer')

# --- 5. ALLERGEN DATENBANK ---
a_info = {
    "Gluten": {"Info": "Protein in Getreidearten wie Weizen, Roggen oder Gerste.", "Keywords": ["Brot", "Nudeln", "Pizza", "Weizen", "Pasta"]},
    "Laktose": {"Info": "Unverträglichkeit gegen Milchzucker.", "Keywords": ["Milch", "Käse", "Sahne", "Joghurt", "Quark"]},
    "Histamin": {"Info": "Abbaustörung von Histamin im Körper.", "Keywords": ["Wein", "Salami", "Tomaten", "Essig", "Bier"]},
    "Nüsse": {"Info": "Allergie gegen Schalenfrüchte.", "Keywords": ["Nuss", "Erdnuss", "Mandel", "Pesto", "Haselnuss"]},
    "Hühnerei": {"Info": "Reaktion auf Proteine im Ei.", "Keywords": ["Ei", "Eier", "Kuchen", "Mayonnaise"]},
    "Fruktose": {"Info": "Fruchtzucker-Malabsorption.", "Keywords": ["Apfel", "Birne", "Saft", "Honig", "Obst"]},
    "Soja": {"Info": "Pflanzliches Eiweiß.", "Keywords": ["Soja", "Tofu", "Sojasauce"]},
    "Fisch": {"Info": "Allergie gegen Fischeiweiße.", "Keywords": ["Fisch", "Lachs", "Thunfisch", "Sushi"]},
    "Sellerie": {"Info": "Verstecktes Allergen in Gewürzen.", "Keywords": ["Sellerie", "Suppengrün", "Bouillon"]},
    "Senf": {"Info": "Scharfes Allergen in Saucen.", "Keywords": ["Senf", "Dressing", "Marinade"]},
    "Sesam": {"Info": "Allergen in Backwaren.", "Keywords": ["Sesam", "Hummus", "Tahini"]},
    "Krebstiere": {"Info": "Garnelen, Krabben, Hummer.", "Keywords": ["Garnele", "Krabbe", "Scampi", "Meeresfrüchte"]}
}

# --- 6. NAVIGATION (Sidebar) ---
if 'nav_index' not in st.session_state:
    st.session_state.nav_index = 0

options = ["Home", "Mahlzeit tracken", "Übersicht & Grafik", "Gut zu wissen", "Arzt-Modus"]

with st.sidebar:
    st.markdown(f"### Angemeldet als: **{user_name}**")
    # Das Radio-Menü wird über den nav_index gesteuert
    page = st.radio("Navigation", options, index=st.session_state.nav_index)
    st.session_state.nav_index = options.index(page)
    
    st.divider()
    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- 7. SEITEN-LOGIK ---

# --- SEITE: HOME ---
if page == "Home":
    st.title("🚀 Allergie-Tracker Pro")
    st.subheader(f"Willkommen zurück, {user_name}!")
    
    data = load_tracker_data(dm, user_name)
    
    if not data.empty:
        avg = data["Intensität"].astype(int).mean()
        wellness = 11 - avg
        st.write(f"Dein Wohlbefinden aktuell: **{int(wellness)}/10**")
        st.progress(min(max(int(wellness * 10), 0), 100) / 100)
    else:
        st.info("Noch keine Daten vorhanden. Nutze die Buttons unten, um deinen ersten Eintrag zu erstellen!")

    st.divider()
    st.markdown("### Schnellzugriff")
    
    # Dashboard-Layout mit Spalten
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    with col1:
        if st.button("🍴 Mahlzeit erfassen", use_container_width=True):
            st.session_state.nav_index = 1
            st.rerun()

    with col2:
        if st.button("📊 Historie & Trends", use_container_width=True):
            st.session_state.nav_index = 2
            st.rerun()

    with col3:
        if st.button("💡 Allergen-Lexikon", use_container_width=True):
            st.session_state.nav_index = 3
            st.rerun()

    with col4:
        if st.button("🩺 Arztbericht erstellen", use_container_width=True):
            st.session_state.nav_index = 4
            st.rerun()

    if not data.empty:
        st.divider()
        st.markdown("### Letzter Eintrag")
        last_entry = data.iloc[-1]
        st.info(f"**{last_entry['Mahlzeit']}** am {last_entry['Datum']} um {last_entry['Uhrzeit']} (Stärke: {last_entry['Intensität']})")


# --- SEITE: MAHLZEIT TRACKEN ---
elif page == "Mahlzeit tracken":
    st.header("🍴 Mahlzeit tracken")
    
    col1, col2 = st.columns(2)
    with col1:
        d_val = st.date_input("Datum", datetime.now())
        m_val = st.text_input("Was hast du gegessen?", placeholder="z.B. Käsebrot")
    with col2:
        t_val = st.time_input("Uhrzeit", datetime.now())
        all_val = st.selectbox("Vermutetes Allergen:", ["Unbekannt"] + list(a_info.keys()))

    has_sym = st.radio("Symptome bemerkt?", ["Nein", "Ja"], horizontal=True)
    s_list, intens = [], 0
    if has_sym == "Ja":
        s_list = st.multiselect("Symptome auswählen:", ["Magenbeschwerden", "Hautausschlag", "Blähungen", "Übelkeit", "Kopfschmerzen", "Juckreiz"])
        intens = st.select_slider("Stärke der Symptome (1-10)", options=range(1, 11), value=5)

    with st.form("save_form"):
        n_val = st.text_area("Zusätzliche Notizen")
        submit = st.form_submit_button("Auf SwitchDrive speichern")
        
        if submit:
            if m_val:
                save_to_csv(dm, {
                    "Nutzer": user_name, 
                    "Datum": d_val.strftime('%Y-%m-%d'),
                    "Uhrzeit": t_val.strftime('%H:%M'), 
                    "Mahlzeit": m_val,
                    "Symptome": ", ".join(s_list) if s_list else "Keine",
                    "Intensität": intens, 
                    "Bemerkungen": f"[{all_val}] {n_val}"
                })
                st.success(f"Eintrag '{m_val}' wurde auf SwitchDrive gespeichert!")
                # Hier bleiben wir auf der Seite (Index 1), damit man nicht zurückgeworfen wird
                st.session_state.nav_index = 1 
                st.rerun()
            else:
                st.error("Bitte gib an, was du gegessen hast.")


# --- SEITE: ÜBERSICHT & GRAFIK ---
elif page == "Übersicht & Grafik":
    st.header("📊 Deine Historie & Analyse")
    data = load_tracker_data(dm, user_name)
    
    if not data.empty:
        st.dataframe(data.drop(columns=["Nutzer"]), use_container_width=True)
        
        st.subheader("Verlauf der Intensität")
        df_p = data.copy()
        df_p['Datum'] = pd.to_datetime(df_p['Datum'])
        fig = px.area(df_p.sort_values('Datum'), x="Datum", y="Intensität", color_discrete_sequence=['#FF4B4B'])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Noch keine Daten vorhanden.")


# --- SEITE: GUT ZU WISSEN (LEXIKON) ---
elif page == "Gut zu wissen":
    st.title("💡 Allergen-Lexikon")
    data = load_tracker_data(dm, user_name)
    
    sel = st.selectbox("Wähle ein Allergen aus:", ["Bitte wählen"] + list(a_info.keys()))
    if sel != "Bitte wählen":
        info = a_info[sel]
        st.markdown(f"### {sel}")
        st.write(info['Info'])
        
        # Mustersuche in den eigenen Daten
        matches = data[((data['Mahlzeit'].str.contains('|'.join(info["Keywords"]), case=False, na=False)) | 
                        (data['Bemerkungen'].str.contains(sel, case=False, na=False))) & 
                       (data['Symptome'] != "Keine")]
        
        if not matches.empty:
            st.warning(f"Achtung: Du hattest bereits {len(matches)} Vorfälle in Verbindung mit {sel}:")
            fig = px.bar(matches, x="Datum", y="Intensität", color="Intensität", color_continuous_scale="Reds")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success(f"Super! Bisher keine Symptome bei {sel} in deinen Daten gefunden.")


# --- SEITE: ARZT-MODUS ---
elif page == "Arzt-Modus":
    st.title("🩺 Arztbericht")
    data = load_tracker_data(dm, user_name)
    
    if not data.empty:
        st.write("Generiere eine Zusammenfassung deiner Daten für deinen nächsten Arztbesuch.")
        notes = st.text_area("Zusätzliche Anmerkungen für den Arzt:")
        
        def create_pdf(df, user, extra_notes):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, f"Medizinischer Bericht: {user}", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 10, f"Zusätzliche Notizen: {extra_notes}")
            pdf.ln(5)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Historie der letzten 10 Einträge:", ln=True)
            pdf.set_font("Arial", size=9)
            for _, r in df.tail(10).iterrows():
                pdf.cell(0, 8, f"{r['Datum']} - {r['Mahlzeit']}: Intensität {r['Intensität']} (Symptome: {r['Symptome']})", ln=True)
            return pdf.output(dest='S').encode('latin-1')
        
        st.download_button(
            label="📄 Bericht als PDF herunterladen",
            data=create_pdf(data, user_name, notes),
            file_name=f"Allergie_Bericht_{user_name}.pdf",
            mime="application/pdf"
        )
    else:
        st.info("Keine Daten zum Exportieren vorhanden.")