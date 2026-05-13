import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

class LoginManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if 'login_manager' not in st.session_state:
            instance = super(LoginManager, cls).__new__(cls)
            st.session_state.login_manager = instance
            return instance
        return st.session_state.login_manager

    def __init__(self, data_manager=None):
        # Initialisierung nur beim ersten Mal
        if not hasattr(self, 'initialized'):
            self.dm = data_manager
            self.auth_credentials_file = 'credentials.json'
            self.auth_cookie_name = 'allergy_tracker_cookie'
            self.auth_cookie_key = 'some_signature_key'
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
            name, authentication_status, username = self.authenticator.login('main')

            if st.session_state["authentication_status"]:
                st.session_state.logged_in = True
                st.session_state.username = username
            elif st.session_state["authentication_status"] is False:
                st.error('Benutzername/Passwort ist falsch')
            elif st.session_state["authentication_status"] is None:
                st.warning('Bitte gib deinen Benutzernamen und dein Passwort ein')

        with register_tab:
            try:
                # Registrierungsformular
                email_of_registered_user, username_of_registered_user, name_of_registered_user = self.authenticator.register_user(pre_authorized=['admin@test.ch'])
                if email_of_registered_user:
                    # Speichern, wenn Registrierung erfolgreich
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
