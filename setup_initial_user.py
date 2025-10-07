# setup_initial_user.py (VERSÃO CORRIGIDA - USA INSERT DML)
import bcrypt
import toml
from google.cloud import bigquery
from google.oauth2 import service_account
import sys
import subprocess

# --- DADOS DO USUÁRIO INICIAL ---
INITIAL_USERNAME = "Dados"
INITIAL_PASSWORD = "changeme"

# --- CONSTANTES DO BIGQUERY ---
GCP_PROJECT_ID = "vaulted-zodiac-294702"
BQ_DATASET = "RBBR_DATA_SCIENCE"
BQ_USERS_TABLE = "PAINEL_USERS"
TABLE_ID = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_USERS_TABLE}"

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def get_bq_client_from_secrets():
    try:
        secrets_path = ".streamlit/secrets.toml"
        secrets = toml.load(secrets_path)
        credentials_info = dict(secrets["gcp_service_account"])
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        return bigquery.Client(project=GCP_PROJECT_ID, credentials=credentials)
    except Exception as e:
        print(f"ERRO: Não foi possível criar o cliente BigQuery. Verifique o seu arquivo '.streamlit/secrets.toml'.")
        print(f"Detalhe do erro: {e}")
        return None

def setup_user():
    print("Iniciando script de configuração de usuário (v3 - DML)...")
    client = get_bq_client_from_secrets()
    if client is None: return

    print(f"Verificando se o usuário '{INITIAL_USERNAME}' já existe...")
    query_check = f"SELECT USERNAME FROM `{TABLE_ID}` WHERE USERNAME = @username"
    job_config_check = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("username", "STRING", INITIAL_USERNAME)]
    )
    results = list(client.query(query_check, job_config=job_config_check))

    if results:
        print(f"-> Usuário '{INITIAL_USERNAME}' já existe. Nenhuma ação foi tomada.")
        return

    print(f"-> Usuário '{INITIAL_USERNAME}' não encontrado. Inserindo na tabela via DML...")
    password_hash = hash_password(INITIAL_PASSWORD).decode('utf-8')
    
    # --- MUDANÇA PRINCIPAL AQUI ---
    # Usando INSERT DML em vez de streaming insert (insert_rows_json)
    query_insert = f"""
        INSERT INTO `{TABLE_ID}` (USERNAME, PASSWORD_HASH, LAST_RESET_DATE, FIRST_LOGIN)
        VALUES (@username, @password_hash, @last_reset_date, @first_login)
    """
    job_config_insert = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("username", "STRING", INITIAL_USERNAME),
            bigquery.ScalarQueryParameter("password_hash", "STRING", password_hash),
            bigquery.ScalarQueryParameter("last_reset_date", "TIMESTAMP", "1970-01-01T00:00:00"),
            bigquery.ScalarQueryParameter("first_login", "BOOL", True),
        ]
    )
    
    try:
        client.query(query_insert, job_config=job_config_insert).result() # .result() espera a query terminar
        print("-> SUCESSO!")
        print(f"   Usuário '{INITIAL_USERNAME}' criado com a senha temporária '{INITIAL_PASSWORD}'.")
    except Exception as e:
        print(f"-> ERRO ao inserir usuário via DML: {e}")

if __name__ == "__main__":
    try: import toml
    except ImportError:
        print("Biblioteca 'toml' não encontrada. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "toml"])
    
    setup_user()