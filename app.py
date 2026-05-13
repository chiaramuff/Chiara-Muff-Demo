import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from fpdf import FPDF

# 1. MUSS GANZ OBEN STEHEN
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

# 4. LOGIN (Stoppt die App, bis Login/Registrierung erfolgt ist)
login_manager.login_register()

# Check ob eingeloggt (Tolerant für verschiedene LoginManager-Versionen)
is_logged_in = st.session_state.get('logged_in') or st.session_state.get('authentication_status')

if not is_logged_in:
    st.warning("Bitte logge dich ein oder registriere dich.")
    st.stop()

# Ab hier ist der User sicher eingeloggt
user_name = st.session_state.get('username', 'Nutzer')

# --- 5. ALLERGEN DATENBANK ---
a_info = {
    "Gluten": {"Info": "Protein in Getreidearten wie Weizen, Roggen oder Gerste.", "Beschwerden": "Bauchschmerzen, Blähungen, Müdigkeit.", "Keywords": ["Brot", "Nudeln", "Pizza", "Weizen", "Pasta"]},
    "Laktose": {"Info": "Unverträglichkeit gegen Milchzucker.", "Beschwerden": "Krämpfe, Blähungen, Durchfall.", "Keywords": ["Milch", "Käse", "Sahne", "Joghurt", "Quark"]},
    "Histamin": {"Info": "Abbaustörung von Histamin im Körper.", "Beschwerden": "Kopfschmerz, Hautrötung, Schwindel.", "Keywords": ["Wein", "Salami", "Tomaten", "Essig", "Bier"]},
    "Nüsse": {"Info": "Allergie gegen Schalenfrüchte.", "Beschwerden": "Schwellung im Mund, Atemnot.", "Keywords": ["Nuss", "Erdnuss", "Mandel", "Pesto", "Haselnuss"]},
    "Hühnerei": {"Info": "Reaktion auf Proteine im Ei.", "Beschwerden": "Hautausschlag, Übelkeit.", "Keywords": ["Ei", "Eier", "Kuchen", "Mayonnaise"]},
    "Fruktose": {"Info": "Fruchtzucker-Malabsorption.", "Beschwerden": "Blähungen, Bauchschmerzen.", "Keywords": ["Apfel", "Birne", "Saft", "Honig", "Obst"]},
    "Soja": {"Info": "Pflanzliches Eiweiß.", "Beschwerden": "Juckreiz, Magenbeschwerden.", "Keywords": ["Soja", "Tofu", "Sojasauce"]},
    "Fisch": {"Info": "Allergie gegen Fischeiweiße.", "Beschwerden": "Erbrechen, Hautrötung.", "Keywords": ["Fisch", "Lachs", "Thunfisch", "Sushi"]},
    "Sellerie": {"Info": "Verstecktes Allergen in Gewürzen.", "Beschwerden": "Juckreiz, Schwellung.", "Keywords": ["Sellerie", "Suppengrün", "Bouillon"]},
    "Senf": {"Info": "Scharfes Allergen in Saucen.", "Beschwerden": "Atembeschwerden, Magenprobleme.", "Keywords": ["Senf", "Dressing", "Marinade"]},
    "Sesam": {"Info": "Allergen in Backwaren.", "Beschwerden": "Hautprobleme, Schwellungen.", "Keywords": ["Sesam", "Hummus", "Tahini"]},
    "Krebstiere": {"Info": "Garnelen, Krabben, Hummer.", "Beschwerden": "Übelkeit, Atemnot.", "Keywords": ["Garnele", "Krabbe", "Scampi", "Meeresfrüchte"]}
}

# --- 6. NAVIGATION (Sidebar) ---
if 'nav_index' not in st.session_state:
    st.session_state.nav_index = 0

with st.sidebar:
    st.markdown(f"### Angemeldet als: **{user_name}**")
    options = ["Home", "Mahlzeit tracken", "Übersicht & Grafik", "Gut zu wissen", "Arzt-Modus"]
    page = st.radio("Navigation", options, index=st.session_state.nav_index)
    st.session_state.nav_index = options.index(page)
    
    st.divider()
    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- 7. SEITEN-LOGIK ---

if page == "Home":
    st.title("Home")
    st.write(f"Hallo **{user_name}** | Heute ist der {datetime.now().strftime('%d.%m.%Y')}")
    data = load_tracker_data(dm, user_name)
    if not data.empty:
        avg = data["Intensität"].astype(int).mean()
        wellness = 11 - avg
        st.write("Dein Wohlbefinden (basierend auf Symptomen):")
        st.select_slider("Skala", options=range(1, 11), value=int(wellness), disabled=True)
    else:
        st.info("Noch keine Daten auf SwitchDrive vorhanden. Beginne mit deinem ersten Eintrag!")

elif page == "Mahlzeit tracken":
    st.header("🍴 Mahlzeit tracken")
    col1, col2 = st.columns(2)
    with col1:
        d_val = st.date_input("Datum", datetime.now())
        m_val = st.text_input("Was hast du gegessen?", placeholder="z.B. Käsebrot")
    with col2:
        t_val = st.time_input("Uhrzeit", datetime.now())
        all_val = st.selectbox("Allergen Verdacht:", ["Unbekannt"] + list(a_info.keys()))

    has_sym = st.radio("Symptome bemerkt?", ["Nein", "Ja"], horizontal=True)
    s_list, intens = [], 0
    if has_sym == "Ja":
        s_list = st.multiselect("Symptome:", ["Magenbeschwerden", "Hautausschlag", "Blähungen", "Übelkeit", "Kopfschmerzen", "Juckreiz"])
        intens = st.select_slider("Stärke (1-10)", options=range(1, 11), value=5)

    with st.form("save_form"):
        n_val = st.text_area("Zusätzliche Notizen")
        if st.form_submit_button("Auf SwitchDrive speichern"):
            if m_val:
                save_to_csv(dm, {
                    "Nutzer": user_name, "Datum": d_val.strftime('%Y-%m-%d'),
                    "Uhrzeit": t_val.strftime('%H:%M'), "Mahlzeit": m_val,
                    "Symptome": ", ".join(s_list) if s_list else "Keine",
                    "Intensität": intens, "Bemerkungen": f"[{all_val}] {n_val}"
                })
                st.success("Erfolgreich auf SwitchDrive gesichert!")
                st.rerun()
            else:
                st.error("Bitte gib an, was du gegessen hast.")

elif page == "Übersicht & Grafik":
    st.header("📊 Deine Analyse")
    data = load_tracker_data(dm, user_name)
    if not data.empty:
        st.dataframe(data.drop(columns=["Nutzer"]), use_container_width=True)
        st.subheader("Verlauf der Intensität")
        df_p = data.copy()
        df_p['Datum'] = pd.to_datetime(df_p['Datum'])
        st.plotly_chart(px.area(df_p.sort_values('Datum'), x="Datum", y="Intensität", color_discrete_sequence=['#FF4B4B']), use_container_width=True)
    else:
        st.info("Noch keine Daten vorhanden.")

elif page == "Gut zu wissen":
    st.title("💡 Allergen-Lexikon")
    data = load_tracker_data(dm, user_name)
    sel = st.selectbox("Wähle ein Allergen:", ["Bitte wählen"] + list(a_info.keys()))
    if sel != "Bitte wählen":
        info = a_info[sel]
        st.markdown(f"### {sel}")
        st.write(info['Info'])
        st.error(f"**Typische Beschwerden:** {info['Beschwerden']}")
        
        # Automatische Mustersuche
        matches = data[((data['Mahlzeit'].str.contains('|'.join(info["Keywords"]), case=False, na=False)) | (data['Bemerkungen'].str.contains(sel, case=False, na=False))) & (data['Symptome'] != "Keine")]
        if not matches.empty:
            st.warning(f"Gefundene Vorfälle für {sel}:")
            st.plotly_chart(px.bar(matches, x="Datum", y="Intensität", color="Intensität", color_continuous_scale="Reds"), use_container_width=True)
        else:
            st.success(f"Bisher keine Symptome bei {sel} dokumentiert.")

elif page == "Arzt-Modus":
    st.title("🩺 Arztbericht")
    data = load_tracker_data(dm, user_name)
    if not data.empty:
        notes = st.text_area("Fragen an den Arzt:")
        def create_pdf(df, n):
            pdf = FPDF()
            pdf.add_page(); pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, f"Bericht für {user_name}", ln=True, align='C')
            pdf.ln(10); pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 10, f"Notizen: {n}")
            pdf.ln(5); pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, "Letzte Einträge:", ln=True)
            for _, r in df.tail(10).iterrows():
                pdf.set_font("Arial", size=9)
                pdf.cell(0, 8, f"{r['Datum']}: {r['Mahlzeit']} (Stärke: {r['Intensität']})", ln=True)
            return pdf.output(dest='S').encode('latin-1')
        
        st.download_button("📄 PDF generieren", data=create_pdf(data, notes), file_name=f"Arztbericht_{user_name}.pdf")
    else:
        st.info("Keine Daten zum Exportieren vorhanden.")