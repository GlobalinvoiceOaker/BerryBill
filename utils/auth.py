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
                "admin": hash_password("admin123"),  # senha inicial
                "operador": hash_password("operador123")  # senha inicial
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
    
    stored_password = users[username]
    return stored_password == hash_password(password)

def login_required():
    """
    Implementa a tela de login e redireciona se o usuário não estiver logado
    """
    # Inicializa estado da sessão
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        
    # Carrega o CSS personalizado
    try:
        with open('assets/style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except:
        pass
        st.session_state.username = ""
    
    # Se não estiver logado, mostra tela de login
    if not st.session_state.logged_in:
        # Usar a imagem do logo da OakBerry em vez de procurar um arquivo .png
        from assets.logo_header import render_logo
        render_logo(width=250)
        
        st.title("Sistema de Gerenciamento de Faturas")
        
        with st.form("login_form"):
            username = st.text_input("Nome de Usuário")
            password = st.text_input("Senha", type="password")
            
            submitted = st.form_submit_button("Entrar")
            
            if submitted:
                if check_password(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Login bem-sucedido!")
                    st.rerun()
                else:
                    st.error("Nome de usuário ou senha incorretos.")
        
        # Mostra nota de uso
        st.markdown("""
        ### Acesso ao Sistema
        
        Para acesso inicial, use as seguintes credenciais:
        - Usuário: `admin` / Senha: `admin123`
        - Usuário: `operador` / Senha: `operador123`
        
        Nota: Por motivos de segurança, altere as senhas iniciais após o primeiro acesso.
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