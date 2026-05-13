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
            self.auth_cookie_key = secrets.token_urlsafe(32)
            self.initialized = True

    def _load_credentials(self):
        """Erzwingt das Laden der frischen Daten vom Drive."""
        # Wir löschen den Cache, falls vorhanden
        if 'auth_credentials' in st.session_state:
            del st.session_state['auth_credentials']
            
        data = self.dm.load_json_data(self.auth_credentials_file)
        if not data or 'usernames' not in data:
            return {'usernames': {}}
        return data

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
            self.authenticator.login(location='main')

            if st.session_state.get("authentication_status"):
                st.session_state.logged_in = True
                # Den Usernamen für die restliche App global verfügbar machen
                if "username" not in st.session_state:
                    st.session_state.username = st.session_state.get("username")
            elif st.session_state.get("authentication_status") is False:
                st.error('Benutzername/Passwort ist falsch')
            elif st.session_state.get("authentication_status") is None:
                st.warning('Bitte gib deinen Benutzernamen und dein Passwort ein')

        with register_tab:
            try:
                # pre_authorized=None erlaubt jedem die Registrierung
                res = self.authenticator.register_user(location='main', pre_authorized=None)
                
                if res:
                    # Der Authenticator hat self.auth_credentials im Hintergrund aktualisiert
                    self._save_credentials()
                    st.success('Benutzer erfolgreich registriert! Du kannst dich jetzt im Tab "Anmelden" einloggen.')
            except Exception as e:
                # Verhindert den Absturz, falls Felder noch leer sind
                st.info("Fülle die Felder oben aus, um ein neues Konto zu erstellen.")

    def logout(self):
        """Logout-Logik: Löscht die Session und erzwingt Neustart."""
        if self.authenticator:
            self.authenticator.logout('Logout', 'sidebar')
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
