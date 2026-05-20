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
        
        # Falls die Datei komplett leer oder ungültig ist, Grundgerüst bauen
        if not data or 'usernames' not in data:
            data = {'usernames': {}}
            
        # WICHTIG: Moderne Versionen der Library verlangen diese Keys zwingend!
        if 'cookie' not in data:
            data['cookie'] = {
                'expiry_days': 30,
                'key': self.auth_cookie_key,
                'name': self.auth_cookie_name
            }
        if 'preauthorized' not in data:
            data['preauthorized'] = {'emails': []}
            
        return data

    def login_register(self):
        self.auth_credentials = self._load_credentials()
        
        # Initialisierung des Authenticators mit dem vollständigen Daten-Gerüst
        self.authenticator = stauth.Authenticate(
            self.auth_credentials,
            self.auth_cookie_name,
            self.auth_cookie_key,
            cookie_expiry_days=30
        )

        login_tab, register_tab = st.tabs(["Anmelden", "Konto erstellen"])

        with login_tab:
            # Zeigt die Felder für Username & Passwort an
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
                    if 'usernames' not in self.auth_credentials:
                        self.auth_credentials['usernames'] = {}
                    
                    # Passwort direkt im Klartext abspeichern um Hasher-Inkompatibilitäten zu umgehen
                    self.auth_credentials['usernames'][new_username] = {
                        "email": new_email,
                        "name": new_name,
                        "password": new_pw
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
