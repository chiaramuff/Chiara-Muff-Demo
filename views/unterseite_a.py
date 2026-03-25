import pandas as pd

import streamlit as st
from functions.ph_calculator import calculate_ph
from utils.data_manager import DataManager # Importiert deine Formel

st.title("PH-Wert Rechner")

st.write("Dies ist ein Rechner um den pH-Wert basierend auf der Konzentration von $H_3O^+$ zu berechnen. Gib die Konzentration in mol/L ein und klicke auf 'Berechnen'.")

st.header("pH-Wert Rechner")
st.write("Gib die $H_3O^+$ Konzentration ein, um den pH-Wert zu bestimmen.")

with st.form("rechner_form"):
    c = st.number_input("Konzentration (mol/L)", 
                            format="%.10f", 
                            value=0.001, 
                            step=0.0001)
    
    submitted = st.form_submit_button("Berechnen")

if submitted:
    res = calculate_ph(c)
    
    if res is not None:
        st.success(f"Der berechnete pH-Wert ist: *{res["h3o_concentration"]:.2f}*")
        
        if res["h3o_concentration"] < 7:
            st.warning("Bereich: *Sauer* (z.B. Zitronensaft)")
        elif res["h3o_concentration"] > 7:
            st.info("Bereich: *Basisch* (z.B. Seifenlauge)")
        else:
            st.success("Bereich: *Neutral* (reines Wasser)")
    else:
            st.error("Bitte gib einen Wert größer als 0 ein.")

    st.write(res["h3o_concentration"])

    if submitted:
        res = calculate_ph(c)
        
        if res is not None:
            # Das Ergebnis groß anzeigen
            st.metric("Berechneter pH-Wert", f"{res["h3o_concentration"]:.2f}")

            # Farbauswahl basierend auf dem Wert
            if res["h3o_concentration"] < 7:
                st.error(f"pH {res["h3o_concentration"]:.2f}: Die Lösung ist SAUER 🍋")
            elif res["h3o_concentration"] > 7:
                st.info(f"pH {res["h3o_concentration"]:.2f}: Die Lösung ist BASISCH 🧼")
            else:
                st.success(f"pH {res["h3o_concentration"]:.2f}: Die Lösung ist NEUTRAL 💧")
        else:
            st.error("Bitte gib einen gültigen Konzentrationswert ein!")
        
    st.session_state['data_df'] = pd.concat([st.session_state['data_df'], pd.DataFrame([res])])

    # --- CODE UPDATE: save data to data manager ---
    data_manager = DataManager()
    data_manager.save_user_data(st.session_state['data_df'], 'data.csv')
    # --- END OF CODE UPDATE ---
        
# display the data frame in a table
st.dataframe(st.session_state['data_df'])

# 1. Daten bereinigen: Nur Zeilen behalten, die wirklich Zahlen in 'h3o_concentration' haben
chart_data = st.session_state['data_df'].copy()
chart_data['h3o_concentration'] = pd.to_numeric(chart_data['h3o_concentration'], errors='coerce')
chart_data = chart_data.dropna(subset=['h3o_concentration'])

# 2. Grafik anzeigen
if not chart_data.empty:
    st.markdown("### 📈 Verlauf der pH-Werte")
    # Wir plotten den pH-Wert über die Zeit
    st.line_chart(data=chart_data, x='timestamp', y='h3o_concentration')
else:
    st.info("Noch keine validen Daten für die Grafik verfügbar.")  