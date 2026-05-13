import pandas as pd
import streamlit as st
from io import StringIO

class DataManager:
    def __init__(self, fs_protocol='webdav', fs_root_folder="Allergie-Tracker"):
        self.fs_protocol = fs_protocol
        self.fs_root_folder = fs_root_folder
        # Hier werden die Zugangsdaten aus den Streamlit Secrets geladen
        try:
            from fsspec import filesystem
            self.fs = filesystem(
                self.fs_protocol,
                host=st.secrets["webdav"]["hostname"],
                username=st.secrets["webdav"]["username"],
                password=st.secrets["webdav"]["password"]
            )
        except Exception as e:
            st.error(f"Fehler bei der Verbindung zu SwitchDrive: {e}")
            self.fs = None

    def exists(self, filename):
        path = f"{self.fs_root_folder}/{filename}"
        return self.fs.exists(path) if self.fs else False

    def load_user_data(self, filename, initial_value=None):
        path = f"{self.fs_root_folder}/{filename}"
        if self.fs and self.fs.exists(path):
            with self.fs.open(path, 'rb') as f:
                return pd.read_csv(f)
        return initial_value if initial_value is not None else pd.DataFrame()

    def save_user_data(self, df, filename):
        path = f"{self.fs_root_folder}/{filename}"
        if self.fs:
            with self.fs.open(path, 'wb') as f:
                df.to_csv(f, index=False)

    # DIESE METHODEN BRAUCHT DER LOGIN-MANAGER
    def load_app_data(self, filename, initial_value=None):
        """Lädt App-Daten (wie Passwörter) direkt."""
        import json
        path = f"{self.fs_root_folder}/{filename}"
        if self.fs and self.fs.exists(path):
            with self.fs.open(path, 'r') as f:
                return json.load(f)
        return initial_value

    def save_app_data(self, data, filename):
        """Speichert App-Daten direkt."""
        import json
        path = f"{self.fs_root_folder}/{filename}"
        if self.fs:
            with self.fs.open(path, 'w') as f:
                json.dump(data, f)