import pandas as pd
import streamlit as st

def load_users(dm):
    """Lädt die Nutzerliste via DataManager von SwitchDrive."""
    return dm.load_user_data(
        'users.csv', 
        initial_value=pd.DataFrame(columns=["username", "password"])
    )

def save_user(dm, username, password):
    """Speichert einen neuen Nutzer via DataManager."""
    users = load_users(dm)
    if username in users["username"].values:
        return False
    new_user = pd.DataFrame([[username, password]], columns=["username", "password"])
    users = pd.concat([users, new_user], ignore_index=True)
    dm.save_user_data(users, 'users.csv')
    return True

def load_tracker_data(dm, username):
    """Lädt die Allergie-Einträge via DataManager."""
    df = dm.load_user_data(
        'allergie_daten.csv',
        initial_value=pd.DataFrame(columns=["Nutzer", "Datum", "Uhrzeit", "Mahlzeit", "Symptome", "Intensität", "Bemerkungen"])
    )
    if not df.empty and "Nutzer" in df.columns:
        return df[df["Nutzer"] == username].copy()
    return df

def save_to_csv(dm, new_row_dict):
    """Speichert einen neuen Eintrag via DataManager auf SwitchDrive."""
    df = dm.load_user_data('allergie_daten.csv', initial_value=pd.DataFrame(columns=["Nutzer", "Datum", "Uhrzeit", "Mahlzeit", "Symptome", "Intensität", "Bemerkungen"]))
    df_new = pd.DataFrame([new_row_dict])
    df = pd.concat([df, df_new], ignore_index=True)
    dm.save_user_data(df, 'allergie_daten.csv')