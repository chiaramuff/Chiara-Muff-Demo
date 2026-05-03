import streamlit as st
import pandas as pd
import os
import plotly.express as px
from datetime import datetime
from fpdf import FPDF

# --- 1. KONFIGURATION & DATENBANK-PFADE ---
st.set_page_config(page_title="Allergie-Tracker", layout="centered")

USER_DB = "users.csv"
DATA_DB = "allergie_daten.csv"

# --- 2. FUNKTIONEN FÜR PERSISTENZ (DATEI-SYSTEM) ---

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

def load_tracker_data(username):
    if os.path.exists(DATA_DB):
        df = pd.read_csv(DATA_DB)
        return df[df["Nutzer"] == username].copy()
    return pd.DataFrame(columns=["Nutzer", "Datum", "Uhrzeit", "Mahlzeit", "Symptome", "Intensität", "Bemerkungen"])

def save_to_csv(new_row_dict):
    df_new = pd.DataFrame([new_row_dict])
    if not os.path.exists(DATA_DB):
        df_new.to_csv(DATA_DB, index=False)
    else:
        df_new.to_csv(DATA_DB, mode='a', header=False, index=False)

# --- 3. SESSION STATE INITIALISIERUNG ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'nav_index' not in st.session_state:
    st.session_state.nav_index = 0
if 'show_success_nav' not in st.session_state:
    st.session_state.show_success_nav = False

# --- 4. LOGIN / REGISTRIERUNG ---
if not st.session_state.logged_in:
    st.title("Allergie - Tracker")
    auth_mode = st.radio("Aktion wählen:", ["Login", "Registrieren"], horizontal=True)
    u_in = st.text_input("Benutzername")
    p_in = st.text_input("Passwort", type="password")

    if auth_mode == "Registrieren":
        if st.button("Konto erstellen"):
            if u_in and p_in:
                if save_user(u_in, p_in):
                    st.success("Konto erstellt! Bitte jetzt einloggen.")
                else:
                    st.error("Benutzername existiert bereits.")
    else:
        if st.button("Enter"):
            users = load_users()
            if ((users["username"] == u_in) & (users["password"] == p_in)).any():
                st.session_state.logged_in = True
                st.session_state.user_name = u_in
                st.session_state.tracker_data = load_tracker_data(u_in)
                st.rerun()
            else:
                st.error("Falsche Logindaten.")
    st.stop()

# --- 5. NAVIGATION (Sidebar) ---
with st.sidebar:
    st.title("Menü")
    options = ["Home", "Mahlzeit tracken", "Übersicht & Grafik", "Gut zu wissen"]
    page = st.radio("Navigation", options, index=st.session_state.nav_index, key="nav_radio")
    st.session_state.nav_index = options.index(page)
    
    st.divider()
    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- 6. SEITEN-LOGIK ---

if page == "Home":
    st.title("Home")
    st.write(f"Hallo **{st.session_state.user_name}** | {datetime.now().strftime('%d.%m.%Y')}")
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("🍴 Mahlzeit tracken", use_container_width=True):
            st.session_state.nav_index = 1
            st.session_state.show_success_nav = False
            st.rerun()
    with col_nav2:
        if st.button("💡 Gut zu wissen", use_container_width=True):
            st.session_state.nav_index = 3
            st.rerun()
    st.divider()
    st.subheader("Tagesübersicht")
    st.session_state.tracker_data = load_tracker_data(st.session_state.user_name)
    if not st.session_state.tracker_data.empty:
        avg_int = st.session_state.tracker_data["Intensität"].astype(int).mean()
        wellness_score = 11 - avg_int 
        st.write("Dein Wohlbefinden (basierend auf Symptomen):")
        st.select_slider("Skala", options=range(1, 11), value=int(wellness_score), disabled=True, label_visibility="collapsed")
    else:
        st.info("Noch keine Daten vorhanden.")

elif page == "Mahlzeit tracken":
    st.header("Mahlzeit tracken")
    col1, col2 = st.columns(2)
    with col1:
        d_val = st.date_input("Datum", datetime.now())
        m_val = st.text_input("Speise", placeholder="Was hast du gegessen?")
    with col2:
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
                new_e = {"Nutzer": st.session_state.user_name, "Datum": d_val.strftime('%Y-%m-%d'), "Uhrzeit": t_val.strftime('%H:%M'), "Mahlzeit": m_val, "Symptome": ", ".join(s_list) if s_list else "Keine", "Intensität": intens, "Bemerkungen": n_val}
                save_to_csv(new_e)
                st.session_state.tracker_data = load_tracker_data(st.session_state.user_name)
                st.session_state.show_success_nav = True 
                st.rerun()
            else:
                st.error("Bitte Mahlzeit angeben.")

    if st.session_state.show_success_nav:
        st.divider(); st.success("Gespeichert!")
        c_n1, c_n2 = st.columns(2)
        with c_n1:
            if st.button("➕ Nächste Mahlzeit", use_container_width=True):
                st.session_state.show_success_nav = False; st.rerun()
        with c_n2:
            if st.button("📊 Zur Übersicht", use_container_width=True):
                st.session_state.show_success_nav = False; st.session_state.nav_index = 2; st.rerun()

elif page == "Übersicht & Grafik":
    st.header("Analyse & Historie")
    st.session_state.tracker_data = load_tracker_data(st.session_state.user_name)
    if not st.session_state.tracker_data.empty:
        st.subheader("Alle Einträge")
        st.dataframe(st.session_state.tracker_data.drop(columns=["Nutzer"]), use_container_width=True)
        
        def create_pdf(df):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, f"Bericht: {st.session_state.user_name}", ln=True)
            pdf.set_font("Arial", size=10); pdf.ln(10)
            pdf.cell(30, 10, "Datum", 1); pdf.cell(50, 10, "Mahlzeit", 1); pdf.cell(70, 10, "Symptome", 1); pdf.cell(20, 10, "Int.", 1); pdf.ln()
            for _, r in df.iterrows():
                pdf.cell(30, 10, str(r['Datum']), 1); pdf.cell(50, 10, str(r['Mahlzeit'])[:25], 1); pdf.cell(70, 10, str(r['Symptome'])[:35], 1); pdf.cell(20, 10, str(r['Intensität']), 1); pdf.ln()
            return pdf.output(dest='S').encode('latin-1')

        st.download_button("📄 PDF Bericht erstellen", data=create_pdf(st.session_state.tracker_data), file_name=f"Bericht_{st.session_state.user_name}.pdf", mime="application/pdf", use_container_width=True)
        st.divider()
        df_p = st.session_state.tracker_data.copy()
        df_p['Datum'] = pd.to_datetime(df_p['Datum'])
        df_p = df_p.sort_values('Datum')
        st.subheader("Intensitäts-Trend")
        st.plotly_chart(px.area(df_p, x="Datum", y="Intensität", line_shape="spline", color_discrete_sequence=['#FF4B4B']), use_container_width=True)
        st.subheader("Top Auslöser")
        trig = df_p[df_p["Symptome"] != "Keine"]
        if not trig.empty:
            st.plotly_chart(px.bar(trig["Mahlzeit"].value_counts().reset_index(), x='count', y='Mahlzeit', orientation='h', color='count', color_continuous_scale='Reds'), use_container_width=True)
    else:
        st.info("Noch keine Daten vorhanden.")

# --- GUT ZU WISSEN (VOLLSTÄNDIG) ---
elif page == "Gut zu wissen":
    st.title("Gut zu wissen")
    st.session_state.tracker_data = load_tracker_data(st.session_state.user_name)
    
    st.subheader("Informationsportal Allergene")
    a_info = {
        "Gluten": {"Symptome": "Bauchschmerzen, Blähungen, Müdigkeit.", "Quellen": "Saucen, Bier, Fertiggerichte, Teigwaren.", "Tipp": "Achte auf das Symbol mit der durchgestrichenen Ähre.", "Keywords": ["Brot", "Nudeln", "Pizza", "Gebäck", "Weizen", "Mehl"]},
        "Laktose": {"Symptome": "Blähungen, Krämpfe, Übelkeit.", "Quellen": "Wurstwaren, Backwaren, Fertiggerichte.", "Tipp": "Laktase-Tabletten können unterwegs helfen.", "Keywords": ["Milch", "Käse", "Sahne", "Quark", "Joghurt", "Eis"]},
        "Histamin": {"Symptome": "Migräne, Hautrötungen, Herzrasen.", "Quellen": "Rotwein, Salami, reifer Käse, Tomaten.", "Tipp": "Frische Lebensmittel enthalten weniger Histamin.", "Keywords": ["Wein", "Käse", "Salami", "Tomaten", "Sauerkraut", "Bier"]},
        "Nüsse": {"Symptome": "Juckreiz, Schwellungen, Atemnot.", "Quellen": "Pesto, Schokolade, asiatische Saucen.", "Tipp": "Trage immer dein Notfallset bei dir.", "Keywords": ["Nuss", "Erdnuss", "Mandel", "Pesto", "Haselnuss"]}
    }
    
    sel = st.selectbox("Allergen wählen:", ["Bitte wählen"] + list(a_info.keys()))
    
    if sel != "Bitte wählen":
        # Anzeige der Infos
        info = a_info[sel]
        c1, c2 = st.columns(2)
        with c1: st.warning(f"**Symptome:**\n{info['Symptome']}")
        with c2: st.info(f"**Versteckte Quellen:**\n{info['Quellen']}")
        st.success(f"**Profi-Tipp:** {info['Tipp']}")
        
        # Persönliche Verknüpfung
        if not st.session_state.tracker_data.empty:
            kw = info["Keywords"]
            matches = st.session_state.tracker_data[(st.session_state.tracker_data['Mahlzeit'].str.contains('|'.join(kw), case=False, na=False)) & (st.session_state.tracker_data['Symptome'] != "Keine")]
            if not matches.empty:
                st.error(f"⚠️ **Check:** Du hast {len(matches)} Einträge mit Symptomen, die {sel} enthalten könnten:")
                for i, r in matches.iterrows(): st.write(f"- {r['Mahlzeit']} (Intensität: {r['Intensität']})")
            else:
                st.success(f"✅ Bisher keine Symptome bei {sel}-haltigen Speisen bei dir gefunden.")

    st.divider()
    st.subheader("Deine häufigsten Symptome")
    if not st.session_state.tracker_data.empty:
        all_s = st.session_state.tracker_data["Symptome"].str.split(", ").explode()
        all_s = all_s[all_s != "Keine"]
        if not all_s.empty:
            st.plotly_chart(px.bar(all_s.value_counts().head(5), orientation='h', color_discrete_sequence=['#FFA500']), use_container_width=True)
    else: st.info("Trage Daten ein für deine Statistik.")
    st.caption("⚠️ Diese App dient nur der Information und ersetzt keine Diagnose durch einen Arzt.")