import streamlit as st
from functions.ph_calculator import calculate_ph # Importiert deine Formel

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
        st.success(f"Der berechnete pH-Wert ist: *{res:.2f}*")
        
        if res < 7:
            st.warning("Bereich: *Sauer* (z.B. Zitronensaft)")
        elif res > 7:
            st.info("Bereich: *Basisch* (z.B. Seifenlauge)")
        else:
            st.success("Bereich: *Neutral* (reines Wasser)")
    else:
        st.error("Bitte gib einen Wert größer als 0 ein.")

    st.write(res)

    if submitted:
        res = calculate_ph(c)
        
        if res is not None:
            # Das Ergebnis groß anzeigen
            st.metric("Berechneter pH-Wert", f"{res:.2f}")

            # Farbauswahl basierend auf dem Wert
            if res < 7:
                st.error(f"pH {res:.2f}: Die Lösung ist SAUER 🍋")
            elif res > 7:
                st.info(f"pH {res:.2f}: Die Lösung ist BASISCH 🧼")
            else:
                st.success(f"pH {res:.2f}: Die Lösung ist NEUTRAL 💧")
        else:
            st.error("Bitte gib einen gültigen Konzentrationswert ein!")