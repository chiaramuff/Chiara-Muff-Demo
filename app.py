import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from fpdf import FPDF

# Import der ausgelagerten Logik aus eurem neuen utils-Ordner
from utils.data_handler import load_users, save_user, load_tracker_data, save_to_csv

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Allergie-Tracker Pro", layout="centered")

# --- 2. ALLERGEN DATENBANK ---
a_info = {
    "Gluten": {"Info": "Protein in Getreide.", "Beschwerden": "Bauchschmerzen, Blähungen.", "Quellen": "Brot, Pasta, Pizza.", "Keywords": ["Brot", "Nudeln", "Pizza", "Weizen"]},
    "Laktose": {"Info": "Milchzucker-Unverträglichkeit.", "Beschwerden": "Krämpfe, Durchfall.", "Quellen": "Milch, Käse, Joghurt.", "Keywords": ["Milch", "Käse", "Sahne", "Joghurt"]},
    "Histamin": {"Info": "Abbaustörung von Histamin.", "Beschwerden": "Kopfschmerz, Hautrötung.", "Quellen": "Wein, Salami, Tomaten.", "Keywords": ["Wein", "Salami", "Tomaten", "Essig"]},
    "Nüsse": {"Info": "Allergie gegen Schalenfrüchte.", "Beschwerden": "Schwellung, Atemnot.", "Quellen": "Müsli, Pesto, Snacks.", "Keywords": ["Nuss", "Erdnuss", "Mandel", "Pesto"]},
    "Hühnerei": {"Info": "Reaktion auf Ei-Proteine.", "Beschwerden": "Ausschlag, Übelkeit.", "Quellen": "Kuchen, Mayonnaise, Omelett.", "Keywords": ["Ei", "Eier", "Kuchen", "Mayonnaise"]},
    "Fruktose": {"Info": "Fruchtzucker-Malabsorption.", "Beschwerden": "Blähungen, Übelkeit.", "Quellen": "Obst, Honig, Säfte.", "Keywords": ["Apfel", "Birne", "Saft", "Honig"]},
    "Soja": {"Info": "Pflanzliches Eiweiß.", "Beschwerden": "Juckreiz, Magenprobleme.", "Quellen": "Tofu, Sojasauce.", "Keywords": ["Soja", "Tofu", "Sojasauce"]},
    "Fisch": {"Info": "Allergie gegen Fischeiweiß.", "Beschwerden": "Erbrechen, Hautrötung.", "Quellen": "Sushi, Fischstäbchen.", "Keywords": ["Fisch", "Lachs", "Thunfisch"]},
    "Sellerie": {"Info": "In Suppen/Gewürzen.", "Beschwerden": "Juckreiz, Schwellung.", "Quellen": "Suppen, Fertiggerichte.", "Keywords": ["Sellerie", "Bouillon"]},
    "Senf": {"Info": "Scharfes Allergen.", "Beschwerden": "Magenprobleme.", "Quellen": "Dressings, Saucen.", "Keywords": ["Senf", "Dressing"]},
    "Sesam": {"Info": "In Backwaren/Ölen.", "Beschwerden": "Schwellung.", "Quellen": "Hummus, Burgerbrötchen.", "Keywords": ["Sesam", "Hummus"]},
    "Krebstiere": {"Info": "Garnelen, Krabben.", "Beschwerden": "Übelkeit, Atemnot.", "Quellen": "Meeresfrüchte, Paella.", "Keywords": ["Garnele", "Krabbe", "Scampi"]}
}

# --- 3. SESSION STATE INITIALISIERUNG ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'nav_index' not in st.session_state: st.session_state.nav_index = 0
if 'show_success_nav' not in st.session_state: st.session_state.show_success_nav = False

# --- 4. AUTHENTIFIZIERUNG (LOGIN/REGISTRIERUNG) ---
if not st.session_state.logged_in:
    st.title("Allergie - Tracker")
    auth_mode = st.radio("Aktion wählen:", ["Login", "Registrieren"], horizontal=True)
    u_in = st.text_input("Benutzername")
    p_in = st.text_input("Passwort", type="password")

    if auth_mode == "Registrieren":
        if st.button("Konto erstellen"):
            if u_in and p_in:
                if save_user(u_in, p_in): st.success("Konto erstellt! Bitte jetzt einloggen.")
                else: st.error("Benutzername existiert bereits.")
    else:
        if st.button("Enter"):
            users = load_users()
            if not users.empty and ((users["username"] == u_in) & (users["password"] == p_in)).any():
                st.session_state.logged_in = True
                st.session_state.user_name = u_in
                st.rerun()
            else:
                st.error("Falsche Logindaten.")
    st.stop()

# --- 5. NAVIGATION ---
with st.sidebar:
    st.title("Menü")
    options = ["Home", "Mahlzeit tracken", "Übersicht & Grafik", "Gut zu wissen", "Arzt-Modus"]
    page = st.radio("Navigation", options, index=st.session_state.nav_index)
    st.session_state.nav_index = options.index(page)
    
    st.divider()
    if st.button("Logout"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- 6. SEITEN-LOGIK ---

# --- HOME ---
if page == "Home":
    st.title("Home")
    st.write(f"Hallo **{st.session_state.user_name}** | {datetime.now().strftime('%d.%m.%Y')}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🍴 Mahlzeit tracken", use_container_width=True):
            st.session_state.nav_index = 1
            st.rerun()
    with col2:
        if st.button("💡 Gut zu wissen", use_container_width=True):
            st.session_state.nav_index = 3
            st.rerun()
    st.divider()
    data = load_tracker_data(st.session_state.user_name)
    if not data.empty:
        avg = data["Intensität"].astype(int).mean()
        st.write("Dein Wohlbefinden (basierend auf Symptomen):")
        st.select_slider("Skala", options=range(1, 11), value=int(11-avg), disabled=True)
    else:
        st.info("Noch keine Daten vorhanden.")

# --- MAHLZEIT TRACKEN ---
elif page == "Mahlzeit tracken":
    st.header("Mahlzeit tracken")
    c1, c2 = st.columns(2)
    with c1:
        d_val = st.date_input("Datum", datetime.now())
        m_val = st.text_input("Speise", placeholder="Was hast du gegessen?")
    with c2:
        t_val = st.time_input("Uhrzeit", datetime.now())
        st.text_input("Dauer", placeholder="optional")
    
    has_sym = st.radio("Symptome?", ["Nein", "Ja"], horizontal=True)
    s_list, intens = [], 0
    if has_sym == "Ja":
        s_list = st.multiselect("Symptome", ["Magenbeschwerden", "Hautausschlag", "Atembeschwerden", "Blähungen", "Übelkeit", "Sodbrennen", "Durchfall", "Kopfschmerzen", "Juckreiz"])
        intens = st.select_slider("Intensität (1-10)", options=range(1, 11), value=5)

    with st.form("save_form"):
        n_val = st.text_area("Bemerkungen")
        if st.form_submit_button("Eintrag speichern"):
            if m_val:
                new_e = {
                    "Nutzer": st.session_state.user_name, 
                    "Datum": d_val.strftime('%Y-%m-%d'), 
                    "Uhrzeit": t_val.strftime('%H:%M'), 
                    "Mahlzeit": m_val, 
                    "Symptome": ", ".join(s_list) if s_list else "Keine", 
                    "Intensität": intens, 
                    "Bemerkungen": n_val
                }
                save_to_csv(new_e)
                st.session_state.show_success_nav = True 
                st.rerun()
            else:
                st.error("Bitte Mahlzeit angeben.")

    if st.session_state.show_success_nav:
        st.success("Gespeichert!")
        if st.button("📊 Zur Übersicht"):
            st.session_state.nav_index = 2
            st.session_state.show_success_nav = False
            st.rerun()

# --- ÜBERSICHT & GRAFIK ---
elif page == "Übersicht & Grafik":
    st.header("Analyse & Historie")
    u1, u2 = st.columns(2)
    with u1:
        if st.button("💡 Gut zu wissen", use_container_width=True):
            st.session_state.nav_index = 3
            st.rerun()
    with u2:
        if st.button("🩺 Arzt-Dashboard", use_container_width=True):
            st.session_state.nav_index = 4
            st.rerun()
    st.divider()
    data = load_tracker_data(st.session_state.user_name)
    if not data.empty:
        st.dataframe(data.drop(columns=["Nutzer"]), use_container_width=True)
        df_p = data.copy()
        df_p['Datum'] = pd.to_datetime(df_p['Datum'])
        st.plotly_chart(px.area(df_p.sort_values('Datum'), x="Datum", y="Intensität"), use_container_width=True)
    else:
        st.info("Noch keine Daten vorhanden.")

# --- GUT ZU WISSEN ---
elif page == "Gut zu wissen":
    st.title("Gut zu wissen")
    data = load_tracker_data(st.session_state.user_name)
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        if st.button("🏠 Zur Startseite", use_container_width=True):
            st.session_state.nav_index = 0
            st.rerun()
    with col_g2:
        if st.button("🩺 Zum Arzt-Dashboard", use_container_width=True):
            st.session_state.nav_index = 4
            st.rerun()
    st.divider()
    sel = st.selectbox("Wähle ein Allergen:", ["Bitte wählen"] + list(a_info.keys()))
    if sel != "Bitte wählen":
        info = a_info[sel]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**💡 Info:** {info['Info']}")
            st.markdown(f"**🍔 Quellen:** {info.get('Quellen', 'Keine Info')}")
        with c2:
            st.error(f"**⚠️ Beschwerden:** {info['Beschwerden']}")
        
        matches = data[(data['Mahlzeit'].str.contains('|'.join(info["Keywords"]), case=False, na=False)) & (data['Symptome'] != "Keine")]
        if not matches.empty:
            st.warning(f"**Deine Treffer für {sel}:**")
            for i, r in matches.iterrows(): st.write(f"- {r['Mahlzeit']} (am {r['Datum']})")
        else:
            st.success(f"✅ Keine Symptome bei {sel} gefunden.")

# --- ARZT MODUS ---
elif page == "Arzt-Modus":
    st.title("🩺 Arzt-Dashboard")
    data = load_tracker_data(st.session_state.user_name)
    if not data.empty:
        avg = data["Intensität"].astype(int).mean()
        st.metric("Ø Schmerz-Level", f"{avg:.1f} / 10")
        notes = st.text_area("Fragen für den Arzt")
        
        def create_pdf(df, n):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, f"Bericht für {st.session_state.user_name}", ln=True)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 10, f"Notizen: {n}")
            pdf.ln(5)
            for _, r in df.tail(10).iterrows():
                pdf.cell(0, 8, f"{r['Datum']}: {r['Mahlzeit']} - {r['Symptome']} (Int: {r['Intensität']})", ln=True)
            return pdf.output(dest='S').encode('latin-1')
            
        st.download_button("📄 PDF für Arzt generieren", data=create_pdf(data, notes), file_name=f"Bericht_{st.session_state.user_name}.pdf", mime="application/pdf")
    else:
        st.info("Bitte erfasse zuerst Daten.")