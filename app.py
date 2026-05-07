import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from fpdf import FPDF

# Import der Funktionen aus eurem aufgeräumten functions-Ordner
from functions.data_handler import load_users, save_user, load_tracker_data, save_to_csv

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Allergie-Tracker Pro", layout="centered")

# --- 2. ALLERGEN DATENBANK ---
a_info = {
    "Gluten": {"Info": "Protein in Getreidearten wie Weizen, Roggen oder Gerste.", "Beschwerden": "Bauchschmerzen, Blähungen, chronische Müdigkeit.", "Quellen": "Brot, Pasta, Pizza, Gebäck, Bier.", "Keywords": ["Brot", "Nudeln", "Pizza", "Weizen", "Gebäck", "Pasta"]},
    "Laktose": {"Info": "Unverträglichkeit gegen Milchzucker.", "Beschwerden": "Krämpfe, Blähungen, Durchfall.", "Quellen": "Milch, Käse, Sahne, Joghurt, Quark, Eiscreme.", "Keywords": ["Milch", "Käse", "Sahne", "Joghurt", "Quark", "Eis"]},
    "Histamin": {"Info": "Abbaustörung von Histamin im Körper.", "Beschwerden": "Kopfschmerz, Hautrötung, Herzrasen, Schwindel.", "Quellen": "Rotwein, Salami, reifer Käse, Tomaten, Essig, Bier.", "Keywords": ["Wein", "Salami", "Tomaten", "Essig", "Bier", "Sauerkraut"]},
    "Nüsse": {"Info": "Allergie gegen Schalenfrüchte.", "Beschwerden": "Schwellung im Mund, Atemnot, Juckreiz.", "Quellen": "Müsli, Pesto, Snacks, Schokolade, Kuchen.", "Keywords": ["Nuss", "Erdnuss", "Mandel", "Pesto", "Haselnuss", "Walnuss"]},
    "Hühnerei": {"Info": "Reaktion auf Proteine im Eigelb oder Eiweiß.", "Beschwerden": "Hautausschlag, Übelkeit, Schwellungen.", "Quellen": "Kuchen, Mayonnaise, Omelett, Panaden.", "Keywords": ["Ei", "Eier", "Kuchen", "Mayonnaise", "Omelett"]},
    "Fruktose": {"Info": "Fruchtzucker-Malabsorption im Dünndarm.", "Beschwerden": "Blähungen, Bauchschmerzen, Übelkeit.", "Quellen": "Obst, Honig, Säfte, Trockenfrüchte.", "Keywords": ["Apfel", "Birne", "Saft", "Honig", "Frucht", "Obst"]},
    "Soja": {"Info": "Pflanzliches Eiweiß, oft in Ersatzprodukten.", "Beschwerden": "Juckreiz, Magenbeschwerden, Schwellung.", "Quellen": "Tofu, Sojasauce, Sojamilch, Edamame.", "Keywords": ["Soja", "Tofu", "Sojasauce", "Miso"]},
    "Fisch": {"Info": "Allergie gegen spezifische Fischeiweiße.", "Beschwerden": "Erbrechen, Hautrötung, Atemnot.", "Quellen": "Sushi, Fischstäbchen, Meeresfrüchte-Salat.", "Keywords": ["Fisch", "Lachs", "Thunfisch", "Forelle", "Dorsch"]},
    "Sellerie": {"Info": "Häufiges verstecktes Allergen in Gewürzmischungen.", "Beschwerden": "Juckreiz, Nesselsucht, Schwellung.", "Quellen": "Suppen, Fertiggerichte, Brühe, Salate.", "Keywords": ["Sellerie", "Bouillon", "Suppengrün", "Gewürz"]},
    "Senf": {"Info": "Scharfes Allergen in Saucen und Dressings.", "Beschwerden": "Atembeschwerden, Magenprobleme.", "Quellen": "Dressings, Saucen, Marinaden, Wurst.", "Keywords": ["Senf", "Dressing", "Marinade", "Mayonnaise"]},
    "Sesam": {"Info": "Allergen in Backwaren und orientalischer Küche.", "Beschwerden": "Hautprobleme, Schwellungen.", "Quellen": "Hummus, Burgerbrötchen, Knäckebrot, Halva.", "Keywords": ["Sesam", "Tahini", "Hummus", "Knäckebrot"]},
    "Krebstiere": {"Info": "Garnelen, Krabben, Hummer oder Krebse.", "Beschwerden": "Übelkeit, Atembeschwerden, Schwellung.", "Quellen": "Meeresfrüchte, Paella, Asiatische Gerichte.", "Keywords": ["Garnele", "Krabbe", "Scampi", "Hummer", "Krebs"]}
}

# --- 3. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'nav_index' not in st.session_state: st.session_state.nav_index = 0
if 'show_success_nav' not in st.session_state: st.session_state.show_success_nav = False

# --- 4. LOGIN / AUTH ---
if not st.session_state.logged_in:
    st.title("Allergie - Tracker")
    auth_mode = st.radio("Aktion wählen:", ["Login", "Registrieren"], horizontal=True)
    u_in = st.text_input("Benutzername")
    p_in = st.text_input("Passwort", type="password")

    if auth_mode == "Registrieren":
        if st.button("Konto erstellen"):
            if u_in and p_in:
                if save_user(u_in, p_in): st.success("Konto erstellt! Bitte einloggen.")
                else: st.error("Benutzername existiert bereits.")
    else:
        if st.button("Enter"):
            users = load_users()
            if not users.empty and ((users["username"] == u_in) & (users["password"] == p_in)).any():
                st.session_state.logged_in, st.session_state.user_name = True, u_in
                st.rerun()
            else: st.error("Falsche Logindaten.")
    st.stop()

# --- 5. NAVIGATION (Sidebar) ---
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

if page == "Home":
    st.title("Home")
    st.write(f"Hallo **{st.session_state.user_name}** | Heute ist der {datetime.now().strftime('%d.%m.%Y')}")
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
        wellness = 11 - avg
        st.write("Dein allgemeines Wohlbefinden (basierend auf Symptomen):")
        st.select_slider("Skala", options=range(1, 11), value=int(wellness), disabled=True)
    else:
        st.info("Noch keine Daten vorhanden. Beginne mit deinem ersten Eintrag!")

elif page == "Mahlzeit tracken":
    st.header("🍴 Mahlzeit tracken")
    col1, col2 = st.columns(2)
    with col1:
        d_val = st.date_input("Datum", datetime.now())
        m_val = st.text_input("Was hast du gegessen?", placeholder="z.B. Pizza mit Salami")
    with col2:
        t_val = st.time_input("Uhrzeit", datetime.now())
        allergen_val = st.selectbox("Vermutetes Allergen (optional):", ["Unbekannt"] + list(a_info.keys()))

    has_sym = st.radio("Hast du Symptome bemerkt?", ["Nein", "Ja"], horizontal=True)
    s_list, intens = [], 0
    if has_sym == "Ja":
        s_list = st.multiselect("Symptome auswählen:", [
            "Magenbeschwerden", "Hautausschlag", "Atembeschwerden", "Blähungen", 
            "Übelkeit", "Sodbrennen", "Durchfall", "Kopfschmerzen", "Juckreiz", 
            "Schwellungen", "Müdigkeit", "Schwindel", "Kreislaufprobleme", "Gliederschmerzen"
        ])
        intens = st.select_slider("Wie stark sind die Beschwerden? (1=leicht, 10=extrem)", options=range(1, 11), value=5)

    with st.form("save_form"):
        n_val = st.text_area("Zusätzliche Notizen (Inhaltsstoffe, Dauer etc.)")
        if st.form_submit_button("Eintrag speichern"):
            if m_val:
                bemerkung_final = f"[Allergen-Verdacht: {allergen_val}] " + n_val
                save_to_csv({
                    "Nutzer": st.session_state.user_name, 
                    "Datum": d_val.strftime('%Y-%m-%d'), 
                    "Uhrzeit": t_val.strftime('%H:%M'), 
                    "Mahlzeit": m_val, 
                    "Symptome": ", ".join(s_list) if s_list else "Keine", 
                    "Intensität": intens, 
                    "Bemerkungen": bemerkung_final
                })
                st.session_state.show_success_nav = True
                st.rerun()
            else:
                st.error("Bitte gib an, was du gegessen hast.")

    if st.session_state.show_success_nav:
        st.divider(); st.success("Daten wurden erfolgreich gespeichert!")
        c_n1, c_n2 = st.columns(2)
        with c_n1:
            if st.button("➕ Weiteren Eintrag", use_container_width=True):
                st.session_state.show_success_nav = False
                st.rerun()
        with c_n2:
            if st.button("📊 Zur Analyse", use_container_width=True):
                st.session_state.show_success_nav = False
                st.session_state.nav_index = 2
                st.rerun()

elif page == "Übersicht & Grafik":
    st.header("📊 Deine Historie & Analyse")
    u1, u2 = st.columns(2)
    with u1:
        if st.button("💡 Lexikon & Details", use_container_width=True): st.session_state.nav_index = 3; st.rerun()
    with u2:
        if st.button("🩺 Arzt-Dashboard", use_container_width=True): st.session_state.nav_index = 4; st.rerun()
    st.divider()
    data = load_tracker_data(st.session_state.user_name)
    if not data.empty:
        st.subheader("Tabellarische Übersicht")
        st.dataframe(data.drop(columns=["Nutzer"]), use_container_width=True)
        
        st.subheader("Verlauf der Intensität")
        df_p = data.copy()
        df_p['Datum'] = pd.to_datetime(df_p['Datum'])
        st.plotly_chart(px.area(df_p.sort_values('Datum'), x="Datum", y="Intensität", color_discrete_sequence=['#FF4B4B'], line_shape="spline"), use_container_width=True)
    else:
        st.info("Noch keine Daten vorhanden.")

elif page == "Gut zu wissen":
    st.title("💡 Allergen-Wissen")
    data = load_tracker_data(st.session_state.user_name)
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        if st.button("🏠 Startseite", use_container_width=True): st.session_state.nav_index = 0; st.rerun()
    with col_g2:
        if st.button("🩺 Arzt-Dashboard", use_container_width=True): st.session_state.nav_index = 4; st.rerun()
    st.divider()
    
    sel = st.selectbox("Wähle ein Allergen für Informationen und Analyse:", ["Bitte wählen"] + list(a_info.keys()))
    if sel != "Bitte wählen":
        info = a_info[sel]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"### Info zu {sel}")
            st.write(info['Info'])
            st.markdown(f"**Vorkommen:** {info.get('Quellen', 'Keine Info')}")
        with c2:
            st.error(f"**Typische Symptome:**\n{info['Beschwerden']}")
        
        # Grafik-Logik
        matches = data[
            ((data['Mahlzeit'].str.contains('|'.join(info["Keywords"]), case=False, na=False)) | 
             (data['Bemerkungen'].str.contains(sel, case=False, na=False))) & 
            (data['Symptome'] != "Keine")
        ]
        
        st.divider()
        if not matches.empty:
            st.subheader(f"Statistik: Deine Vorfälle mit {sel}")
            fig = px.bar(matches, x="Datum", y="Intensität", color="Intensität", title=f"Symptom-Stärke im Zeitverlauf ({sel})", color_continuous_scale="Reds")
            st.plotly_chart(fig, use_container_width=True)
            
            st.warning(f"Gefundene Treffer in deiner Liste ({len(matches)}):")
            for _, r in matches.iterrows():
                st.write(f"- **{r['Mahlzeit']}** am {r['Datum']} (Intensität: {r['Intensität']})")
        else:
            st.success(f"✅ Bisher keine Symptome bei **{sel}** in deiner Historie gefunden.")

elif page == "Arzt-Modus":
    st.title("🩺 Arzt-Dashboard")
    data = load_tracker_data(st.session_state.user_name)
    if not data.empty:
        avg = data["Intensität"].astype(int).mean()
        st.metric("Durchschnittliche Schmerz-Intensität", f"{avg:.1f} / 10")
        
        st.subheader("Vorbereitung für das Gespräch")
        notes = st.text_area("Notizen oder spezifische Fragen an den Arzt:", placeholder="z.B. Treten die Symptome immer erst 2 Stunden später auf?")
        
        def create_pdf(df, n):
            pdf = FPDF()
            pdf.add_page(); pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, f"Medizinischer Bericht: {st.session_state.user_name}", ln=True, align='C')
            pdf.ln(5); pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 10, f"Erstellt am: {datetime.now().strftime('%d.%m.%Y')}\nPatienten-Notizen: {n if n else 'Keine'}")
            pdf.ln(5); pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, "Historie (Letzte 10 Einträge):", ln=True)
            pdf.set_font("Arial", size=9)
            for _, r in df.tail(10).iterrows():
                pdf.cell(0, 8, f"{r['Datum']}: {r['Mahlzeit']} - Symptome: {r['Symptome']} (Int: {r['Intensität']})", ln=True)
            return pdf.output(dest='S').encode('latin-1')
        
        st.download_button("📄 Medizinischen Bericht als PDF exportieren", data=create_pdf(data, notes), file_name=f"Arztbericht_{st.session_state.user_name}.pdf", mime="application/pdf", use_container_width=True)
    else:
        st.info("Bitte erfasse zuerst Daten in deinem Tracker.")