import streamlit as st
import hashlib
import json
import os

# Arquivo para armazenar credenciais
USERS_FILE = "data/users.json"

def ensure_users_file_exists():
    """
    Garante que o arquivo de usuários existe
    """
    if not os.path.exists("data"):
        os.makedirs("data")
    
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({
                "Nickolas Silva": {
                    "password": hash_password("Nick230420"),
                    "role": "admin",
                    "full_name": "Nickolas Silva"
                },
                "Ivan Bonilla": {
                    "password": hash_password("ivan123"),
                    "role": "gestor",
                    "full_name": "Ivan Bonilla"
                },
                "Diego Gonçalves": {
                    "password": hash_password("diego123"),
                    "role": "admin",
                    "full_name": "Diego Gonçalves"
                },
                "Luan Mendonça": {
                    "password": hash_password("luan123"),
                    "role": "gestor",
                    "full_name": "Luan Mendonça"
                },
                "Luca Giaffone": {
                    "password": hash_password("palmeiras"),
                    "role": "gestor",
                    "full_name": "Luca Giaffone"
                },
                "Igor Nakaoka": {
                    "password": hash_password("igor123"),
                    "role": "configuracao",
                    "full_name": "Igor Nakaoka"
                }
            }, f)

def hash_password(password):
    """
    Cria um hash da senha fornecida
    """
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(username, password):
    """
    Verifica se o nome de usuário e senha correspondem
    """
    ensure_users_file_exists()
    
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    
    if username not in users:
        return False
    
    user_data = users[username]
    stored_password = user_data["password"]
    return stored_password == hash_password(password)

def get_user_role(username):
    """
    Retorna o papel (role) do usuário
    """
    ensure_users_file_exists()
    
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    
    if username not in users:
        return None
    
    return users[username].get("role", "user")

def get_user_fullname(username):
    """
    Retorna o nome completo do usuário
    """
    ensure_users_file_exists()
    
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
    
    if username not in users:
        return username
    
    return users[username].get("full_name", username)

def login_required():
    """
    Implementa a tela de login e redireciona se o usuário não estiver logado
    """
    # Inicializa estado da sessão
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.user_role = ""
        st.session_state.full_name = ""
        
    # Carrega o CSS personalizado
    try:
        with open('assets/style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except:
        pass
    
    # Se não estiver logado, mostra tela de login
    if not st.session_state.logged_in:
        # Centralizar o layout da tela de login
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Usar a imagem do logo da OakBerry
            from assets.logo_header import render_logo
            render_logo(width=250)
            
            st.markdown('<h1 class="login-title">Sistema de Gerenciamento de Faturas</h1>', unsafe_allow_html=True)
            
            # Criar uma caixa visualmente agradável para o formulário de login
            st.markdown('<div class="login-box">', unsafe_allow_html=True)
            
            with st.form("login_form"):
                st.markdown('#### Acesso ao Sistema', unsafe_allow_html=True)
                username = st.text_input("Nome de Usuário")
                password = st.text_input("Senha", type="password")
                
                submitted = st.form_submit_button("Entrar", use_container_width=True)
                
                if submitted:
                    if check_password(username, password):
                        # Armazena informações do usuário na sessão
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_role = get_user_role(username)
                        st.session_state.full_name = get_user_fullname(username)
                        st.success(f"Login bem-sucedido! Bem-vindo, {st.session_state.full_name}.")
                        st.rerun()
                    else:
                        st.error("Nome de usuário ou senha incorretos.")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Instruções de acesso mais elegantes
            with st.expander("Informações de Acesso"):
                st.markdown("""
                ##### Usuários disponíveis:
                - **Nickolas Silva** (Administrador)
                - **Diego Gonçalves** (Administrador)
                - **Ivan Bonilla** (Gestor)
                - **Luan Mendonça** (Gestor)
                - **Luca Giaffone** (Gestor)
                - **Igor Nakaoka** (Configuração)
                
                *Para suporte, contate o administrador do sistema.*
                """)
        
        # Impede a execução do restante da página
        st.stop()
    
    return st.session_state.username

def logout():
    """
    Realiza o logout do usuário
    """
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()