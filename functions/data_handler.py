import pandas as pd
import streamlit as st

def load_tracker_data(dm, username):
    """Lädt die Daten von SwitchDrive und filtert nach dem aktuellen Nutzer."""
    # Definiere die Spalten zentral, damit sie überall gleich sind
    columns = ["Nutzer", "Datum", "Uhrzeit", "Mahlzeit", "Symptome", "Intensität", "Bemerkungen"]
    
    df = dm.load_user_data(
        'allergie_daten.csv',
        initial_value=pd.DataFrame(columns=columns)
    )
    
    # Falls der DataManager ein leeres Objekt liefert, das kein DataFrame ist
    if df is None or not isinstance(df, pd.DataFrame):
        return pd.DataFrame(columns=columns)

    if not df.empty and "Nutzer" in df.columns:
        # Bereinigung: Strings konvertieren, Leerzeichen entfernen
        df["Nutzer"] = df["Nutzer"].astype(str).str.strip()
        # Filter (Case Insensitive)
        filtered_df = df[df["Nutzer"].str.lower() == username.lower()].copy()
        return filtered_df
        
    return pd.DataFrame(columns=columns)

def save_to_csv(dm, new_row_dict):
    """Speichert einen neuen Eintrag direkt auf SwitchDrive."""
    filename = 'allergie_daten.csv'
    columns = ["Nutzer", "Datum", "Uhrzeit", "Mahlzeit", "Symptome", "Intensität", "Bemerkungen"]
    
    # 1. Bestehende Daten laden
    df = dm.load_user_data(filename, initial_value=pd.DataFrame(columns=columns))
    
    # Sicherstellen, dass df ein DataFrame ist
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(columns=columns)
    
    # 2. Neuen Eintrag hinzufügen (Sicherstellen, dass Nutzername sauber ist)
    new_row_dict["Nutzer"] = str(new_row_dict["Nutzer"]).strip()
    df_new = pd.DataFrame([new_row_dict])
    
    # Kombinieren
    df = pd.concat([df, df_new], ignore_index=True)
    
    # 3. Zurück in die Cloud schreiben
    dm.save_user_data(df, filename)