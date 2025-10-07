# pages/2_Reset_Password.py
import streamlit as st
from auth import update_password
import re

st.set_page_config(page_title="Redefinir Senha", layout="centered")

# --- FUNÇÃO DE VALIDAÇÃO DE SENHA (A mesma de antes) ---
def validate_password_complexity(password):
    # Usaremos um dicionário para retornar o status de cada requisito
    requirements = {
        "length": len(password) >= 8,
        "lowercase": bool(re.search(r"[a-z]", password)),
        "uppercase": bool(re.search(r"[A-Z]", password)),
        "digit": bool(re.search(r"\d", password)),
        "special": bool(re.search(r"[!@#$%^&*(),.?\":{}|<>]", password))
    }
    return requirements

# --- GUARDA DE ACESSO ---
if not st.session_state.get('force_reset', False):
    st.error("Acesso não autorizado.")
    st.stop()

# --- LAYOUT DA PÁGINA ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("logo.png", width=300)

st.title("Redefinição de Senha Obrigatória")
st.info(f"Olá, **{st.session_state.get('username', '')}**. Por segurança, defina uma nova senha forte.")

# --- CAMPOS DE SENHA (FORA DO FORMULÁRIO) ---
new_password = st.text_input("Nova Senha", type="password", key="new_password")
confirm_password = st.text_input("Confirme a Nova Senha", type="password", key="confirm_password")

# --- CHECKLIST INTERATIVO DE REQUISITOS ---
# Pega o valor atual da senha digitada para a verificação em tempo real
password_value = st.session_state.get("new_password", "")
requirements_status = validate_password_complexity(password_value)

# Define o texto e o status de cada requisito
req_list = {
    "length": "Pelo menos 8 caracteres",
    "lowercase": "Pelo menos uma letra minúscula (a-z)",
    "uppercase": "Pelo menos uma letra maiúscula (A-Z)",
    "digit": "Pelo menos um número (0-9)",
    "special": "Pelo menos um caractere especial (!@#$...)"
}

st.markdown("**Sua senha precisa atender aos seguintes critérios:**")

# Monta a lista visualmente, mudando cor e ícone conforme o status
all_met = True
for key, text in req_list.items():
    is_met = requirements_status[key]
    if is_met:
        st.markdown(f"""
        <div style='display: flex; align-items: center; margin: 8px 0; font-size: 14px;'>
            <div style='width: 20px; height: 20px; border-radius: 50%; background-color: #28a745; display: flex; align-items: center; justify-content: center; margin-right: 12px;'>
                <span style='color: white; font-size: 12px; font-weight: bold;'>✓</span>
            </div>
            <span>{text}</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='display: flex; align-items: center; margin: 8px 0; font-size: 14px;'>
            <div style='width: 20px; height: 20px; border-radius: 50%; background-color: #dc3545; display: flex; align-items: center; justify-content: center; margin-right: 12px;'>
                <span style='color: white; font-size: 12px; font-weight: bold;'>✕</span>
            </div>
            <span>{text}</span>
        </div>
        """, unsafe_allow_html=True)
        all_met = False

st.write("---") # Linha separadora

# --- BOTÃO DE SUBMISSÃO ---
if st.button("Redefinir Senha"):
    if not all_met:
        st.error("Sua senha ainda não atende a todos os requisitos.")
    elif new_password != confirm_password:
        st.error("As senhas não coincidem.")
    elif not new_password:
        st.warning("Por favor, preencha a senha.")
    else:
        # Se tudo estiver correto, atualiza a senha
        try:
            update_password(st.session_state['username'], new_password)
            # Limpa os campos de senha do estado da sessão para segurança
            if "new_password" in st.session_state: del st.session_state["new_password"]
            if "confirm_password" in st.session_state: del st.session_state["confirm_password"]
            
            st.session_state['authenticated'] = True
            st.session_state['force_reset'] = False
            
            st.success("Senha redefinida com sucesso! Redirecionando...")
            st.switch_page("pages/1_Painel.py")
        except Exception as e:
            st.error(f"Ocorreu um erro ao atualizar a senha: {e}")