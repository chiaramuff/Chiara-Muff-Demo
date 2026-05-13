import pandas as pd
import streamlit as st
import json
from fsspec import filesystem

class DataManager:
    def __init__(self, fs_protocol='webdav', fs_root_folder="Allergie-Tracker"):
        self.fs_protocol = fs_protocol
        self.fs_root_folder = fs_root_folder.strip("/")
        self.fs = None

        try:
            conf = st.secrets["webdav"]
            
            # Wir nutzen die Domain direkt aus den Secrets
            host = conf['hostname'] 
            url = f"https://{host}/remote.php/dav/files/{conf['username']}/"
            
            self.fs = filesystem(
                'webdav',
                base_url=url,
                username=conf['username'],
                password=conf['password']
            )

            # Ein einfacher Test-Zugriff
            self.fs.ls("/") 
            st.sidebar.success("✅ SwitchDrive aktiv")

        except Exception as e:
            # Hier stand dein "[Errno -2]" Fehler
            st.sidebar.error(f"Verbindung fehlgeschlagen: {e}")
            self.fs = None
        except Exception as e:
            # Das zeigt uns den exakten Grund direkt in der App an
            st.sidebar.error(f"Fehler-Details: {e}")
            self.fs = None

    # --- Ab hier: Die Standard-Funktionen für deine App ---
    def load_app_data(self, filename, initial_value=None):
        path = f"{self.fs_root_folder}/{filename}"
        try:
            if self.fs and self.fs.exists(path):
                with self.fs.open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except: pass
        return initial_value if initial_value is not None else {}

    def save_app_data(self, data, filename):
        path = f"{self.fs_root_folder}/{filename}"
        if self.fs:
            try:
                with self.fs.open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                return True
            except: pass
        return False

    def load_user_data(self, filename, initial_value=None):
        path = f"{self.fs_root_folder}/{filename}"
        try:
            if self.fs and self.fs.exists(path):
                with self.fs.open(path, 'rb') as f:
                    return pd.read_csv(f)
        except: pass
        return initial_value if initial_value is not None else pd.DataFrame()

    def save_user_data(self, df, filename):
        path = f"{self.fs_root_folder}/{filename}"
        if self.fs:
            try:
                with self.fs.open(path, 'wb') as f:
                    df.to_csv(f, index=False)
                return True
            except: pass
        return False