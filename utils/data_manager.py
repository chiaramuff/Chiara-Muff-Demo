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
            # Wir bauen das Konfigurations-Paket exakt wie der Dozent
            # Aber wir bereiten beide Varianten vor (login und username)
            conf = st.secrets["webdav"]
            
            # Das ist der Kern der Samuel-Wehrli-Logik:
            webdav_options = {
                'base_url': conf['hostname'],
                'password': conf['password']
            }

            # Wir probieren es erst mit 'login' (SwitchDrive Standard)
            try:
                webdav_options['login'] = conf['username']
                self.fs = filesystem(self.fs_protocol, **webdav_options)
            except TypeError:
                # Falls dein System 'login' nicht mag, wechseln wir auf 'username'
                del webdav_options['login']
                webdav_options['username'] = conf['username']
                self.fs = filesystem(self.fs_protocol, **webdav_options)

            # Prüfen ob der Ordner da ist
            if not self.fs.exists(self.fs_root_folder):
                self.fs.mkdir(self.fs_root_folder)
                
            st.sidebar.success("✅ Verbindung steht!")

        except Exception as e:
            st.error(f"Verbindungsfehler: {e}")

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