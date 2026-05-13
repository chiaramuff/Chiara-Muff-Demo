import streamlit as st
from fsspec import filesystem

class DataManager:
    def __init__(self, fs_protocol='webdav', fs_root_folder="Allergie-Tracker"):
        self.fs_protocol = fs_protocol
        self.fs_root_folder = fs_root_folder.strip("/")
        self.fs = None

        try:
            conf = st.secrets["webdav"]
            # Sicherstellen, dass kein https:// im Hostnamen steht
            host = conf['hostname'].replace("https://", "").replace("http://", "").strip("/")
            
            # Die sicherste URL-Struktur für SwitchDrive ZHAW
            url = f"https://{host}/remote.php/dav/files/{conf['username']}/"
            
            self.fs = filesystem(
                self.fs_protocol,
                base_url=url,
                username=conf['username'],
                password=conf['password'],
                requests_kwargs={'verify': False}  # Umgeht SSL-Probleme in der Cloud
            )

            # Prüfen, ob der Hauptordner existiert
            if not self.fs.exists(self.fs_root_folder):
                self.fs.mkdir(self.fs_root_folder)
                
            st.sidebar.success("✅ SwitchDrive aktiv")

        except Exception as e:
            # Zeigt den exakten Fehler in der Sidebar an
            st.sidebar.error(f"❌ Verbindung fehlgeschlagen: {e}")
            self.fs = None

    def load_app_data(self, self_filename, initial_value=None):
        path = f"{self.fs_root_folder}/{self_filename}"
        try:
            if self.fs and self.fs.exists(path):
                with self.fs.open(path, 'r', encoding='utf-8') as f:
                    import json
                    return json.load(f)
        except:
            pass
        return initial_value if initial_value is not None else {}

    def save_app_data(self, data, filename):
        path = f"{self.fs_root_folder}/{filename}"
        if self.fs:
            try:
                with self.fs.open(path, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(data, f, indent=4)
                return True
            except:
                pass
        return False
