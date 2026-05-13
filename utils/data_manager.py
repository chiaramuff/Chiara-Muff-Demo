import pandas as pd
import streamlit as st

class DataManager:
    def __init__(self, fs_protocol='webdav', fs_root_folder="Allergie-Tracker"):
        self.fs_protocol = fs_protocol
        self.fs_root_folder = fs_root_folder
        try:
            from fsspec import filesystem
            self.fs = filesystem(
                self.fs_protocol,
                host=st.secrets["webdav"]["hostname"],
                username=st.secrets["webdav"]["username"],
                password=st.secrets["webdav"]["password"]
            )
        except:
            self.fs = None

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

    def load_app_data(self, filename, initial_value=None):
        import json
        path = f"{self.fs_root_folder}/{filename}"
        if self.fs and self.fs.exists(path):
            with self.fs.open(path, 'r') as f:
                return json.load(f)
        return initial_value

    def save_app_data(self, data, filename):
        import json
        path = f"{self.fs_root_folder}/{filename}"
        if self.fs:
            with self.fs.open(path, 'w') as f:
                json.dump(data, f)