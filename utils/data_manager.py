import streamlit as st
from fsspec import filesystem
import pandas as pd
import json

class DataManager:
    def __init__(self, fs_protocol='webdav', fs_root_folder="Allergie-Tracker"):
        self.fs_protocol = fs_protocol
        self.fs_root_folder = fs_root_folder.strip("/")
        self.fs = None

        try:
            conf = st.secrets["webdav"]
            host = conf['hostname'].replace("https://", "").replace("http://", "").strip("/")
            url = f"https://{host}/remote.php/dav/files/{conf['username']}/"
            
            self.fs = filesystem(
                self.fs_protocol,
                base_url=url,
                username=conf['user'],
                password=conf['password'],
                requests_kwargs={'verify': False}
            )

            if not self.fs.exists(self.fs_root_folder):
                self.fs.mkdir(self.fs_root_folder)
                
            st.sidebar.success("✅ SwitchDrive aktiv")
        except Exception as e:
            st.sidebar.error(f"❌ Verbindung fehlgeschlagen: {e}")
            self.fs = None

    # NEU: Speziell für Tabellen (Allergie-Daten)
    def load_app_data(self, filename, initial_value=None):
        path = f"{self.fs_root_folder}/{filename}"
        try:
            if self.fs and self.fs.exists(path):
                with self.fs.open(path, 'rb') as f:
                    return pd.read_csv(f)
        except:
            pass
        return pd.DataFrame()

    def save_app_data(self, df, filename):
        path = f"{self.fs_root_folder}/{filename}"
        if self.fs:
            try:
                with self.fs.open(path, 'wb') as f:
                    df.to_csv(f, index=False)
                return True
            except:
                pass
        return False

    # NEU: Speziell für Login-Daten (Credentials)
    def load_json_data(self, filename, initial_value=None):
        path = f"{self.fs_root_folder}/{filename}"
        try:
            if self.fs and self.fs.exists(path):
                with self.fs.open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return initial_value if initial_value is not None else {"usernames": {}}

    def save_json_data(self, data, filename):
        path = f"{self.fs_root_folder}/{filename}"
        if self.fs:
            try:
                with self.fs.open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                return True
            except:
                pass
        return False
