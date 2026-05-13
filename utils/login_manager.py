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
            self.auth_cookie_key = 'some_fixed_key_123'
            self.initialized = True

    def _load_credentials(self):
        data = self.dm.load_json_data(self.auth_credentials_file)
        if not data or 'usernames' not in data:
            return {'usernames': {}}
        return data

    def _save_credentials(self):
        self.dm.save_json_data(self.auth_credentials, self.auth_credentials_file)

    def login_register(self):
        self.auth_credentials = self._load_credentials()
        self.authenticator = stauth.Authenticate(
            self.auth_credentials,
            self.auth_cookie_name,
            self.auth_cookie_key,
            cookie_expiry_days=30
        )

        login_tab, register_tab = st.tabs(["Anmelden", "Konto erstellen"])

        with login_tab:
            # Der Authenticator erledigt den Login intern
            self.authenticator.login(location='main')
            
            # WICHTIG: Hier setzen wir die Variable, die app.py abfragt
            if st.session_state.get("authentication_status"):
                st.session_state['logged_in'] = True
                st.session_state['username'] = st.session_state['username']
            elif st.session_state.get("authentication_status") is False:
                st.error('Username/Passwort falsch')

        with register_tab:
            try:
                res = self.authenticator.register_user(location='main', captcha=False)
                if res:
                    self._save_credentials()
                    st.success('Registriert! Bitte oben auf "Anmelden" klicken.')
            except Exception as e:
                st.info("Bitte fülle die Felder zur Registrierung aus.")

    def logout(self):
        if hasattr(self, 'authenticator'):
            self.authenticator.logout('Logout', 'sidebar')
        # Alles zurücksetzen
        st.session_state['logged_in'] = False
        st.session_state['authentication_status'] = None
        st.rerun()
