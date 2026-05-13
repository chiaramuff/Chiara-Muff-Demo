import streamlit as st
import streamlit_authenticator as stauth
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
            self.auth_cookie_key = 'fixed_key_123'
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
        
        # Initialisierung des Authenticators
        self.authenticator = stauth.Authenticate(
            self.auth_credentials,
            self.auth_cookie_name,
            self.auth_cookie_key,
            cookie_expiry_days=30
        )

        login_tab, register_tab = st.tabs(["Anmelden", "Konto erstellen"])

        with login_tab:
            # Login-Feld anzeigen
            self.authenticator.login(location='main')
            
            if st.session_state.get("authentication_status"):
                st.session_state['logged_in'] = True
            elif st.session_state.get("authentication_status") is False:
                st.error('Username/Passwort falsch')

        with register_tab:
            st.subheader("Neues Konto anlegen")
            new_email = st.text_input("E-Mail", key="reg_email")
            new_username = st.text_input("Username", key="reg_user")
            new_name = st.text_input("Name", key="reg_name")
            new_pw = st.text_input("Passwort", type="password", key="reg_pw")
            
            if st.button("Registrieren"):
                if new_email and new_username and new_pw:
                    # Wir speichern das Passwort für diesen Test einfach direkt
                    # Um den 'Hasher'-Fehler komplett zu umgehen
                    if 'usernames' not in self.auth_credentials:
                        self.auth_credentials['usernames'] = {}
                    
                    self.auth_credentials['usernames'][new_username] = {
                        "email": new_email,
                        "name": new_name,
                        "password": new_pw  # Passwort direkt speichern
                    }
                    
                    self.dm.save_json_data(self.auth_credentials, self.auth_credentials_file)
                    st.success("Registriert! Bitte Seite neu laden (F5) und einloggen.")
                else:
                    st.warning("Bitte alle Felder ausfüllen.")

    def logout(self):
        if hasattr(self, 'authenticator'):
            self.authenticator.logout('Logout', 'sidebar')
        st.session_state.clear()
        st.rerun()
