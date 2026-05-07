import pandas as pd
import os

USER_DB = "users.csv"
DATA_DB = "allergie_daten.csv"

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
    cols = ["Nutzer", "Datum", "Uhrzeit", "Mahlzeit", "Symptome", "Intensität", "Bemerkungen"]
    if os.path.exists(DATA_DB):
        try:
            df = pd.read_csv(DATA_DB)
            for c in cols:
                if c not in df.columns: df[c] = ""
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