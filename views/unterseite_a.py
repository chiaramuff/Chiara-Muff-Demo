import streamlit as st
from functions.ph_calculator import calculate_ph # Importiert deine Formel

st.title("PH-Wert Rechner")

st.write("Diese Seite ist eine Unterseite der Startseite.")

st.header("🧪 pH-Wert Rechner")
st.write("Gib die $H_3O^+$ Konzentration ein, um den pH-Wert zu bestimmen.")

# Formular wie in der Aufgabe gefordert
with st.form("rechner_form"):
    # Eingabefeld
    c = st.number_input("Konzentration (mol/L)", 
                            format="%.10f", 
                            value=0.001, 
                            step=0.0001)
    
    # Bestätigungsbutton
    submitted = st.form_submit_button("Berechnen")

if submitted:
    res = calculate_ph(c)
    
    if res is not None:
        st.success(f"Der berechnete pH-Wert ist: *{res:.2f}*")
        
        # Ein kleiner visueller Vergleich
        if res < 7:
            st.warning("Bereich: *Sauer* (z.B. Zitronensaft)")
        elif res > 7:
            st.info("Bereich: *Basisch* (z.B. Seifenlauge)")
        else:
            st.success("Bereich: *Neutral* (reines Wasser)")
    else:
        st.error("Bitte gib einen Wert größer als 0 ein.")

    st.write(res)