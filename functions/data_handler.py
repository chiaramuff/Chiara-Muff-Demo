import pandas as pd

def load_tracker_data(dm, username):
    df = dm.load_app_data('allergie_daten.csv')
    if df is not None and not df.empty and "Nutzer" in df.columns:
        return df[df["Nutzer"] == username]
    return pd.DataFrame()

def save_to_csv(dm, new_row_dict):
    df = dm.load_app_data('allergie_daten.csv')
    if df is None:
        df = pd.DataFrame()
    
    df_new = pd.DataFrame([new_row_dict])
    df = pd.concat([df, df_new], ignore_index=True)
    return dm.save_app_data(df, 'allergie_daten.csv')
