import streamlit as st
import streamlit_authenticator as stauth
import secrets
import json

class LoginManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if 'login_manager' not in st.session_state:
            instance = super(LoginManager, cls).__new__(cls)
            st.session_state.login_manager = instance
            return instance
        return st.session_state.login_manager

    def __init__(self, data_manager=None):
        if not hasattr(self, 'initialized'):
            self.dm = data_manager
            self.auth_credentials_file = 'credentials.json'
            self.auth_cookie_name = 'allergy_tracker_cookie'
            # Wir nutzen secrets für einen sicheren Schlüssel
            self.auth_cookie_key = secrets.token_urlsafe(32)
            self.initialized = True

    def _load_credentials(self):
        """Lädt die Benutzerdaten via DataManager als Dictionary (JSON)."""
        return self.dm.load_json_data(
            self.auth_credentials_file, 
            initial_value={'usernames': {}}
        )

    def _save_credentials(self):
        """Speichert die aktuellen Benutzerdaten via DataManager."""
        self.dm.save_json_data(self.auth_credentials, self.auth_credentials_file)

    def login_register(self):
        """Hauptmethode für Login und Registrierung."""
        # 1. Credentials laden
        self.auth_credentials = self._load_credentials()

        # 2. Authenticator konfigurieren
        self.authenticator = stauth.Authenticate(
            self.auth_credentials,
            self.auth_cookie_name,
            self.auth_cookie_key,
            cookie_expiry_days=30
        )

        # 3. Login/Register Interface in Tabs
        login_tab, register_tab = st.tabs(["Anmelden", "Konto erstellen"])

        with login_tab:
            # FIX: In der neuen Version von stauth wird der Login so aufgerufen:
            self.authenticator.login(location='main')

            # Die Status-Werte ziehen wir uns jetzt direkt aus dem session_state
            if st.session_state["authentication_status"]:
                st.session_state.logged_in = True
                # Nutzername für die App setzen
                if 'username' not in st.session_state:
                    st.session_state.username = st.session_state["username"]
            elif st.session_state["authentication_status"] is False:
                st.error('Benutzername/Passwort ist falsch')
            elif st.session_state["authentication_status"] is None:
                st.warning('Bitte gib deinen Benutzernamen und dein Passwort ein')

        with register_tab:
            try:
                # Registrierungsformular
                res = self.authenticator.register_user(pre_authorized=None])
                # res[0] ist die E-Mail des registrierten Users
                if res and res[0]:
                    self._save_credentials()
                    st.success('Benutzer erfolgreich registriert! Du kannst dich jetzt anmelden.')
            except Exception as e:
                st.error(f"Fehler bei der Registrierung: {e}")

    def logout(self):
        """Logout-Logik."""
        self.authenticator.logout('Logout', 'sidebar')
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
