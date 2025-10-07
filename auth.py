# auth.py
import streamlit as st
import bcrypt
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account

# --- CONSTANTES DO BIGQUERY ---
GCP_PROJECT_ID = "vaulted-zodiac-294702"
BQ_DATASET = "RBBR_DATA_SCIENCE"
BQ_USERS_TABLE = "PAINEL_USERS"
TABLE_ID = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_USERS_TABLE}"

# --- FUNÇÕES DE CONEXÃO E AUTENTICAÇÃO ---

@st.cache_resource
def get_bq_client():
    """Inicializa e retorna um cliente BigQuery usando as credenciais do Streamlit."""
    credentials_info = dict(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    return bigquery.Client(project=GCP_PROJECT_ID, credentials=credentials)

def hash_password(password):
    """Gera o hash de uma senha."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed_password):
    """Verifica se a senha corresponde ao hash."""
    # O hash do BigQuery vem como bytes, então decodificamos
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_user_data(username):
    """Busca os dados de um usuário na tabela do BigQuery."""
    client = get_bq_client()
    query = f"""
        SELECT PASSWORD_HASH, LAST_RESET_DATE, FIRST_LOGIN
        FROM `{TABLE_ID}`
        WHERE USERNAME = @username
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("username", "STRING", username),
        ]
    )
    query_job = client.query(query, job_config=job_config)
    
    # Pega a primeira linha do resultado, se houver
    results = list(query_job)
    if results:
        return results[0]
    return None

def update_password(username, new_password):
    """Atualiza a senha do usuário e a data de reset no BigQuery."""
    client = get_bq_client()
    new_hash = hash_password(new_password).decode('utf-8') # Decodifica para salvar como string
    
    query = f"""
        UPDATE `{TABLE_ID}`
        SET 
            PASSWORD_HASH = @new_hash,
            LAST_RESET_DATE = CURRENT_TIMESTAMP(),
            FIRST_LOGIN = FALSE
        WHERE USERNAME = @username
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("new_hash", "STRING", new_hash),
            bigquery.ScalarQueryParameter("username", "STRING", username),
        ]
    )
    client.query(query, job_config=job_config).result() # .result() espera a query terminar

def verify_login(username, password):
    """Verifica o login do usuário consultando o BigQuery."""
    user_data = get_user_data(username)
    if not user_data:
        return "INVALID"

    password_hash, last_reset_date, first_login = user_data

    if not check_password(password, password_hash):
        return "INVALID"

    if first_login is True:
        return "FORCE_RESET_INITIAL"
        
    # Adiciona 15 dias à data de reset e compara com a data atual
    if datetime.now(last_reset_date.tzinfo) > last_reset_date + timedelta(days=15):
        return "FORCE_RESET_EXPIRED"
        
    return "SUCCESS"