import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from fpdf import FPDF

# Import aus dem Ordner 'functions' und der Datei 'data_handler'
from functions.data_handler import load_users, save_user, load_tracker_data, save_to_csv

st.set_page_config(page_title="Allergie-Tracker Pro", layout="centered")

# --- ALLERGEN DATENBANK ---
a_info = {
    "Gluten": {"Info": "Protein in Getreide.", "Beschwerden": "Bauchschmerzen, Blähungen.", "Quellen": "Brot, Pasta, Pizza.", "Keywords": ["Brot", "Nudeln", "Pizza", "Weizen"]},
    "Laktose": {"Info": "Milchzucker-Unverträglichkeit.", "Beschwerden": "Krämpfe, Durchfall.", "Quellen": "Milch, Käse, Joghurt.", "Keywords": ["Milch", "Käse", "Sahne", "Joghurt"]},
    "Histamin": {"Info": "Abbaustörung von Histamin im Körper.", "Beschwerden": "Kopfschmerz, Hautrötung.", "Quellen": "Wein, Salami, Tomaten.", "Keywords": ["Wein", "Salami", "Tomaten", "Essig"]},
    "Nüsse": {"Info": "Allergie gegen Schalenfrüchte.", "Beschwerden": "Schwellung, Atemnot.", "Quellen": "Müsli, Pesto, Snacks.", "Keywords": ["Nuss", "Erdnuss", "Mandel", "Pesto"]},
    "Hühnerei": {"Info": "Reaktion auf Ei-Proteine.", "Beschwerden": "Ausschlag, Übelkeit.", "Quellen": "Kuchen, Mayonnaise, Omelett.", "Keywords": ["Ei", "Eier", "Kuchen", "Mayonnaise"]},
    "Fruktose": {"Info": "Fruchtzucker-Malabsorption.", "Beschwerden": "Blähungen, Übelkeit.", "Quellen": "Obst, Honig, Säfte.", "Keywords": ["Apfel", "Birne", "Saft", "Honig"]},
    "Soja": {"Info": "Pflanzliches Eiweiß.", "Beschwerden": "Juckreiz, Magenprobleme.", "Quellen": "Tofu, Sojasauce.", "Keywords": ["Soja", "Tofu", "Sojasauce"]},
    "Fisch": {"Info": "Allergie gegen Fischeiweiß.", "Beschwerden": "Erbrechen, Hautrötung.", "Quellen": "Sushi, Fischstäbchen.", "Keywords": ["Fisch", "Lachs", "Thunfisch"]},
    "Sellerie": {"Info": "In Suppen/Gewürzen.", "Beschwerden": "Juckreiz, Schwellung.", "Quellen": "Suppen, Fertiggerichte.", "Keywords": ["Sellerie", "Bouillon"]},
    "Senf": {"Info": "Scharfes Allergen.", "Beschwerden": "Magenprobleme.", "Quellen": "Dressings, Saucen.", "Keywords": ["Senf", "Dressing"]},
    "Sesam": {"Info": "In Backwaren/Ölen.", "Beschwerden": "Schwellung.", "Quellen": "Hummus, Burgerbrötchen.", "Keywords": ["Sesam", "Tahini", "Hummus"]},
    "Krebstiere": {"Info": "Garnelen, Krabben.", "Beschwerden": "Übelkeit, Atemnot.", "Quellen": "Meeresfrüchte, Paella.", "Keywords": ["Garnele", "Krabbe", "Scampi"]}
}

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'nav_index' not in st.session_state: st.session_state.nav_index = 0
if 'show_success_nav' not in st.session_state: st.session_state.show_success_nav = False

# --- LOGIN ---
if not st.session_state.logged_in:
    st.title("Allergie - Tracker")
    auth_mode = st.radio("Aktion wählen:", ["Login", "Registrieren"], horizontal=True)
    u_in = st.text_input("Benutzername")
    p_in = st.text_input("Passwort", type="password")

    if auth_mode == "Registrieren":
        if st.button("Konto erstellen"):
            if u_in and p_in:
                if save_user(u_in, p_in): st.success("Konto erstellt!")
                else: st.error("Benutzername existiert bereits.")
    else:
        if st.button("Enter"):
            users = load_users()
            if not users.empty and ((users["username"] == u_in) & (users["password"] == p_in)).any():
                st.session_state.logged_in, st.session_state.user_name = True, u_in
                st.rerun()
            else: st.error("Falsche Logindaten.")
    st.stop()

# --- NAVIGATION ---
with st.sidebar:
    st.title("Menü")
    options = ["Home", "Mahlzeit tracken", "Übersicht & Grafik", "Gut zu wissen", "Arzt-Modus"]
    page = st.radio("Navigation", options, index=st.session_state.nav_index)
    st.session_state.nav_index = options.index(page)
    if st.button("Logout"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- SEITEN ---
if page == "Home":
    st.title("Home")
    st.write(f"Hallo **{st.session_state.user_name}**")
    c1, c2 = st.columns(2)
    if c1.button("🍴 Tracken", use_container_width=True): 
        st.session_state.nav_index = 1
        st.rerun()
    if c2.button("💡 Wissen", use_container_width=True): 
        st.session_state.nav_index = 3
        st.rerun()
    data = load_tracker_data(st.session_state.user_name)
    if not data.empty:
        avg = data["Intensität"].astype(int).mean()
        st.select_slider("Wohlbefinden", options=range(1, 11), value=int(11-avg), disabled=True)

elif page == "Mahlzeit tracken":
    st.header("Mahlzeit tracken")
    with st.form("save_form"):
        d_val = st.date_input("Datum", datetime.now())
        m_val = st.text_input("Speise")
        t_val = st.time_input("Uhrzeit", datetime.now())
        s_list = st.multiselect("Symptome", ["Magenbeschwerden", "Hautausschlag", "Atembeschwerden", "Blähungen", "Übelkeit", "Kopfschmerzen", "Juckreiz"])
        intens = st.select_slider("Intensität (1-10)", options=range(1, 11), value=5)
        n_val = st.text_area("Bemerkungen")
        if st.form_submit_button("Eintrag speichern"):
            if m_val:
                save_to_csv({"Nutzer": st.session_state.user_name, "Datum": d_val.strftime('%Y-%m-%d'), "Uhrzeit": t_val.strftime('%H:%M'), "Mahlzeit": m_val, "Symptome": ", ".join(s_list) if s_list else "Keine", "Intensität": intens, "Bemerkungen": n_val})
                st.session_state.show_success_nav = True
                st.rerun()
    if st.session_state.show_success_nav:
        st.success("Gespeichert!")
        if st.button("📊 Zur Übersicht"):
            st.session_state.nav_index = 2
            st.session_state.show_success_nav = False
            st.rerun()

elif page == "Übersicht & Grafik":
    st.header("Analyse & Historie")
    u1, u2 = st.columns(2)
    if u1.button("💡 Gut zu wissen", use_container_width=True): st.session_state.nav_index = 3; st.rerun()
    if u2.button("🩺 Arzt-Dashboard", use_container_width=True): st.session_state.nav_index = 4; st.rerun()
    data = load_tracker_data(st.session_state.user_name)
    if not data.empty:
        st.dataframe(data.drop(columns=["Nutzer"]), use_container_width=True)
        df_p = data.copy()
        df_p['Datum'] = pd.to_datetime(df_p['Datum'])
        st.plotly_chart(px.area(df_p.sort_values('Datum'), x="Datum", y="Intensität", line_shape="spline"), use_container_width=True)

elif page == "Gut zu wissen":
    st.title("Gut zu wissen")
    data = load_tracker_data(st.session_state.user_name)
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        if st.button("🏠 Zur Startseite", use_container_width=True): st.session_state.nav_index = 0; st.rerun()
    with col_g2:
        if st.button("🩺 Zum Arzt-Dashboard", use_container_width=True): st.session_state.nav_index = 4; st.rerun()
    st.divider()
    sel = st.selectbox("Wähle ein Allergen für Details:", ["Bitte wählen"] + list(a_info.keys()))
    if sel != "Bitte wählen":
        info = a_info[sel]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**💡 Info:** {info['Info']}")
            st.markdown(f"**🍔 Quellen:** {info.get('Quellen', 'Keine Info')}")
        with c2: st.error(f"**⚠️ Beschwerden:** {info['Beschwerden']}")
        matches = data[(data['Mahlzeit'].str.contains('|'.join(info["Keywords"]), case=False, na=False)) & (data['Symptome'] != "Keine")]
        if not matches.empty:
            st.warning(f"**Deine Treffer für {sel}:**")
            for _, r in matches.iterrows(): st.write(f"- {r['Mahlzeit']} (am {r['Datum']})")

elif page == "Arzt-Modus":
    st.title("🩺 Arztbericht")
    data = load_tracker_data(st.session_state.user_name)
    if not data.empty:
        avg = data["Intensität"].astype(int).mean()
        st.metric("Ø Schmerz-Level", f"{avg:.1f} / 10")
        notes = st.text_area("Fragen für den Arzt")
        def create_pdf(df, n):
            pdf = FPDF()
            pdf.add_page(); pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, f"Bericht für {st.session_state.user_name}", ln=True)
            pdf.set_font("Arial", size=10); pdf.multi_cell(0, 10, f"Notizen: {n}")
            for _, r in df.tail(10).iterrows():
                pdf.cell(0, 8, f"{r['Datum']}: {r['Mahlzeit']} - {r['Symptome']} (Int: {r['Intensität']})", ln=True)
            return pdf.output(dest='S').encode('latin-1')
        st.download_button("📄 PDF generieren", data=create_pdf(data, notes), file_name="Arztbericht.pdf")