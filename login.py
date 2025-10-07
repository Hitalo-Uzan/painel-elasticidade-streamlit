# login.py
import streamlit as st
from auth import verify_login

st.set_page_config(layout="centered", page_title="Login")

# --- GERENCIAMENTO DE ESTADO DA SESSÃO ---
# Inicializa as variáveis da sessão se elas não existirem
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ""
if 'force_reset' not in st.session_state:
    st.session_state['force_reset'] = False

# --- LÓGICA DE REDIRECIONAMENTO ---
# Se o usuário já está logado e não precisa resetar, vai para o painel
if st.session_state['authenticated'] and not st.session_state['force_reset']:
    st.switch_page("pages/1_Painel.py")
# Se o usuário precisa resetar a senha, vai para a página de reset
elif st.session_state.get('force_reset', False):
    st.switch_page("pages/2_Reset_Password.py") # Criaremos esta página no próximo passo

# --- PÁGINA DE LOGIN ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("logo.png", width=300)
st.title("Login do Painel de Elasticidade")
st.write("---")

username_input = st.text_input("Usuário")
password_input = st.text_input("Senha", type="password")

if st.button("Entrar"):
    if username_input and password_input:
        # Chama a função de verificação que consulta o BigQuery
        status = verify_login(username_input, password_input)

        if status == "SUCCESS":
            st.session_state['authenticated'] = True
            st.session_state['username'] = username_input
            st.session_state['force_reset'] = False
            st.switch_page("pages/1_Painel.py")

        elif status in ["FORCE_RESET_INITIAL", "FORCE_RESET_EXPIRED"]:
            st.session_state['username'] = username_input
            st.session_state['force_reset'] = True
            st.switch_page("pages/2_Reset_Password.py")

        else: # Status "INVALID"
            st.error("Usuário ou senha inválidos.")
            st.session_state['authenticated'] = False
    else:
        st.warning("Por favor, preencha o usuário e a senha.")