import streamlit as st
import pandas as pd
import os
import plotly.express as px
from datetime import datetime
from fpdf import FPDF

# --- 1. KONFIGURATION & DATENBANK-PFADE ---
st.set_page_config(page_title="Allergie-Tracker Pro", layout="centered")

USER_DB = "users.csv"
DATA_DB = "allergie_daten.csv"

# --- 2. FUNKTIONEN FÜR PERSISTENZ ---

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
    # Online-Sicherheit: Falls Datei leer oder korrupt, leeren DF zurückgeben
    cols = ["Nutzer", "Datum", "Uhrzeit", "Mahlzeit", "Symptome", "Intensität", "Bemerkungen"]
    if os.path.exists(DATA_DB):
        try:
            df = pd.read_csv(DATA_DB)
            # Sicherstellen, dass alle Spalten existieren
            for c in cols:
                if c not in df.columns:
                    df[c] = ""
            return df[df["Nutzer"] == username].copy()
        except:
            return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

def save_to_csv(new_row_dict):
    df_new = pd.DataFrame([new_row_dict])
    if not os.path.exists(DATA_DB):
        df_new.to_csv(DATA_DB, index=False)
    else:
        df_new.to_csv(DATA_DB, mode='a', header=False, index=False)

# --- 3. SESSION STATE ---
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
            if not users.empty and ((users["username"] == u_in) & (users["password"] == p_in)).any():
                st.session_state.logged_in = True
                st.session_state.user_name = u_in
                st.session_state.tracker_data = load_tracker_data(u_in)
                st.rerun()
            else:
                st.error("Falsche Logindaten.")
    st.stop()

# --- 5. NAVIGATION ---
with st.sidebar:
    st.title("Menü")
    options = ["Home", "Mahlzeit tracken", "Übersicht & Grafik", "Gut zu wissen", "Arzt-Modus"]
    # Der Index wird über den Session State gesteuert
    page = st.radio("Navigation", options, index=st.session_state.nav_index)
    st.session_state.nav_index = options.index(page)
    
    st.divider()
    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- 6. ALLERGEN DATENBANK ---
a_info = {
    "Gluten": {"Info": "Protein in Weizen, Roggen, Gerste.", "Beschwerden": "Bauchschmerzen, Blähungen, Durchfall.", "Quellen": "Brot, Pasta, Bier, Pizza, Gebäck.", "Keywords": ["Brot", "Nudeln", "Pizza", "Gebäck", "Weizen"]},
    "Laktose": {"Info": "Milchzucker-Unverträglichkeit.", "Beschwerden": "Blähungen, Krämpfe, Durchfall.", "Keywords": ["Milch", "Käse", "Sahne", "Joghurt", "Eis"]},
    "Histamin": {"Info": "Abbaustörung von Histamin.", "Beschwerden": "Kopfschmerzen, Hautrötungen, Herzrasen.", "Keywords": ["Wein", "Salami", "Tomaten", "Bier", "Essig"]},
    "Nüsse": {"Info": "Allergie gegen Schalenfrüchte.", "Beschwerden": "Juckreiz, Schwellungen, Atemnot.", "Keywords": ["Nuss", "Erdnuss", "Mandel", "Pesto", "Haselnuss"]},
    "Hühnerei": {"Info": "Reaktion auf Proteine im Ei.", "Beschwerden": "Hautausschlag, Übelkeit, Atembeschwerden.", "Keywords": ["Ei", "Eier", "Omelett", "Mayonnaise", "Kuchen"]},
    "Fruktose": {"Info": "Fruchtzucker-Malabsorption.", "Beschwerden": "Blähungen, Bauchschmerzen, Übelkeit.", "Keywords": ["Apfel", "Birne", "Saft", "Honig", "Datteln"]},
    "Soja": {"Info": "Pflanzliches Eiweiß.", "Beschwerden": "Juckreiz, Magenbeschwerden.", "Keywords": ["Soja", "Tofu", "Sojasauce", "Edamame"]},
    "Fisch": {"Info": "Allergie gegen Fischeiweiß.", "Beschwerden": "Hautrötungen, Erbrechen.", "Keywords": ["Fisch", "Lachs", "Thunfisch", "Forelle"]},
    "Sellerie": {"Info": "Häufiges Allergen in Suppen.", "Beschwerden": "Schwellungen, Nesselsucht.", "Keywords": ["Sellerie", "Suppengrün", "Bouillon"]},
    "Senf": {"Info": "Scharfes Allergen.", "Beschwerden": "Atembeschwerden, Magenprobleme.", "Keywords": ["Senf", "Dressing", "Marinade"]},
    "Sesam": {"Info": "Backwaren und Öle.", "Beschwerden": "Hautprobleme, Schwellungen.", "Keywords": ["Sesam", "Tahini", "Hummus"]},
    "Krebstiere": {"Info": "Garnelen, Krabben etc.", "Beschwerden": "Übelkeit, Atembeschwerden.", "Keywords": ["Garnele", "Krabbe", "Hummer", "Meeresfrüchte"]}
}

# --- 7. SEITEN-LOGIK ---

if page == "Home":
    st.title("Home")
    st.write(f"Hallo **{st.session_state.user_name}** | {datetime.now().strftime('%d.%m.%Y')}")
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("🍴 Mahlzeit tracken", use_container_width=True):
            st.session_state.nav_index = 1
            st.rerun()
    with col_nav2:
        if st.button("💡 Gut zu wissen", use_container_width=True):
            st.session_state.nav_index = 3
            st.rerun()
    st.divider()
    st.session_state.tracker_data = load_tracker_data(st.session_state.user_name)
    if not st.session_state.tracker_data.empty:
        avg_int = st.session_state.tracker_data["Intensität"].astype(int).mean()
        wellness_score = 11 - avg_int 
        st.write("Dein Wohlbefinden (basierend auf Symptomen):")
        st.select_slider("Skala", options=range(1, 11), value=int(wellness_score), disabled=True)
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
        dur_val = st.text_input("Dauer der Beschwerden", placeholder="optional")
    
    has_sym = st.radio("Symptome?", ["Nein", "Ja"], horizontal=True)
    s_list, intens = [], 0
    if has_sym == "Ja":
        s_list = st.multiselect("Symptome", ["Magenbeschwerden", "Hautausschlag", "Atembeschwerden", "Blähungen", "Übelkeit", "Sodbrennen", "Durchfall", "Kopfschmerzen", "Juckreiz", "Schwellungen"])
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
                st.session_state.show_success_nav = False
                st.rerun()
        with c_n2:
            if st.button("📊 Zur Übersicht", use_container_width=True):
                st.session_state.show_success_nav = False
                st.session_state.nav_index = 2
                st.rerun()

elif page == "Übersicht & Grafik":
    st.header("Analyse & Historie")
    if st.button("🩺 Zum Arzt-Dashboard springen", use_container_width=True):
        st.session_state.nav_index = 4
        st.rerun()
    st.divider()
    st.session_state.tracker_data = load_tracker_data(st.session_state.user_name)
    if not st.session_state.tracker_data.empty:
        st.subheader("Alle Einträge")
        st.dataframe(st.session_state.tracker_data.drop(columns=["Nutzer"]), use_container_width=True)
        df_p = st.session_state.tracker_data.copy()
        df_p['Datum'] = pd.to_datetime(df_p['Datum'])
        df_p = df_p.sort_values('Datum')
        st.subheader("Intensitäts-Trend")
        st.plotly_chart(px.area(df_p, x="Datum", y="Intensität", line_shape="spline"), use_container_width=True)
    else:
        st.info("Noch keine Daten vorhanden.")

elif page == "Gut zu wissen":
    st.title("Gut zu wissen")
    st.session_state.tracker_data = load_tracker_data(st.session_state.user_name)
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
    st.subheader("Allergen-Lexikon & Check")
    sel = st.selectbox("Wähle ein Allergen für Details:", ["Bitte wählen"] + list(a_info.keys()))
    if sel != "Bitte wählen":
        info = a_info[sel]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**💡 Info:** {info['Info']}")
            st.markdown(f"**🍔 Quellen:** {info['Quellen']}")
        with c2:
            st.error(f"**⚠️ Häufige Beschwerden:**\n{info['Beschwerden']}")
        matches = st.session_state.tracker_data[
            (st.session_state.tracker_data['Mahlzeit'].str.contains('|'.join(info["Keywords"]), case=False, na=False)) & 
            (st.session_state.tracker_data['Symptome'] != "Keine")
        ]
        if not matches.empty:
            st.warning(f"**Deine Treffer für {sel}:**")
            for i, r in matches.iterrows():
                st.write(f"- **{r['Mahlzeit']}** (am {r['Datum']})")
        else:
            st.success(f"✅ Bisher keine Symptome bei {sel} gefunden.")
    st.divider()
    st.subheader("Deine Top Allergen-Auslöser")
    if not st.session_state.tracker_data.empty:
        counts = {}
        for allergen, data in a_info.items():
            cnt = st.session_state.tracker_data[
                (st.session_state.tracker_data['Mahlzeit'].str.contains('|'.join(data["Keywords"]), case=False, na=False)) & 
                (st.session_state.tracker_data['Symptome'] != "Keine")
            ].shape[0]
            if cnt > 0: counts[allergen] = cnt
        if counts:
            df_c = pd.DataFrame(list(counts.items()), columns=['Allergen', 'Anzahl']).sort_values(by='Anzahl', ascending=False)
            st.plotly_chart(px.bar(df_c, x='Anzahl', y='Allergen', orientation='h'), use_container_width=True)

elif page == "Arzt-Modus":
    st.title("🩺 Arzt-Dashboard")
    st.write("Bereite deine Daten optimal für den nächsten Arztbesuch vor.")
    st.session_state.tracker_data = load_tracker_data(st.session_state.user_name)
    if not st.session_state.tracker_data.empty:
        df = st.session_state.tracker_data.copy()
        avg_int = df["Intensität"].astype(int).mean()
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Ø Schmerz-Level", f"{avg_int:.1f} / 10")
        sym_check = df[df["Symptome"] != "Keine"]
        if not sym_check.empty:
            top_sym = sym_check["Symptome"].str.split(", ").explode().value_counts().idxmax()
            col_m2.metric("Hauptbeschwerde", top_sym)
        st.divider()
        arzt_notes = st.text_area("Fragen für den Arzt", placeholder="Z.B. Treten die Symptome immer nach Brot auf?")
        def create_doc_pdf(df, notes):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 18)
            pdf.cell(0, 15, "Medizinischer Befundbericht", ln=True, align='C')
            pdf.set_font("Arial", size=11)
            pdf.cell(0, 10, f"Patient: {st.session_state.user_name} | Stand: {datetime.now().strftime('%d.%m.%Y')}", ln=True)
            pdf.ln(5)
            pdf.set_font("Arial", "B", 13)
            pdf.cell(0, 10, "Notizen/Fragen:", ln=True)
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 8, notes if notes else "Keine Notizen.")
            pdf.ln(5)
            pdf.set_font("Arial", "B", 13)
            pdf.cell(0, 10, "Historie (Auszug):", ln=True)
            pdf.set_font("Arial", size=9)
            for _, r in df.tail(15).iterrows():
                pdf.cell(0, 7, f"{r['Datum']} - {r['Mahlzeit']}: {r['Symptome']} (Intensität: {r['Intensität']})", ln=True)
            return pdf.output(dest='S').encode('latin-1')
        st.download_button("📄 PDF für Arzt generieren", data=create_doc_pdf(df, arzt_notes), file_name=f"Arztbericht_{st.session_state.user_name}.pdf", mime="application/pdf", use_container_width=True)
    else:
        st.info("Bitte erfasse zuerst Daten.")