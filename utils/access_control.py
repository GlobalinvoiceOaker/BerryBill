import streamlit as st
from utils.auth import get_user_role

def check_access(allowed_roles):
    """
    Verifica se o usuário tem permissão para acessar determinada funcionalidade
    
    Parâmetros:
    - allowed_roles (list): Lista de papéis (roles) que têm permissão
    
    Retorna:
    - boolean: True se tem acesso, False caso contrário
    """
    if 'user_role' not in st.session_state:
        return False
    
    user_role = st.session_state.user_role
    
    # Se for admin, tem acesso a tudo
    if user_role == "admin":
        return True
    
    # Caso contrário, verifica se o papel do usuário está na lista de permitidos
    return user_role in allowed_roles

def show_access_denied():
    """
    Mostra mensagem de acesso negado
    """
    st.error("### Acesso Negado")
    st.warning("Você não tem permissão para acessar esta funcionalidade.")
    st.info("Entre em contato com o administrador do sistema para solicitar acesso.")
    
    if st.button("Voltar para o Dashboard"):
        st.switch_page("app.py")
    
    st.stop()

def require_role(allowed_roles):
    """
    Decorador para funções que requerem papéis específicos.
    Se o usuário não tiver o papel adequado, será redirecionado.
    
    Parâmetros:
    - allowed_roles (list): Lista de papéis (roles) que têm permissão
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if check_access(allowed_roles):
                return func(*args, **kwargs)
            else:
                show_access_denied()
        return wrapper
    return decorator