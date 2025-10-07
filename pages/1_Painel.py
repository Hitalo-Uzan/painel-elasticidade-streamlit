import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google.cloud import storage
from google.cloud import bigquery
from io import BytesIO
from datetime import datetime, timedelta

# =============================================================================
# SEÇÃO DE AUTENTICAÇÃO E SEGURANÇA
# =============================================================================
# Verifica se o usuário está autenticado. Se não, bloqueia o acesso.
if not st.session_state.get('authenticated', False):
    st.error("🔒 Acesso negado. Por favor, faça o login para continuar.")
    st.stop()

# Botão de Logout será movido para o final da sidebar
# =============================================================================

# --- CONFIGURAÇÕES DO PAINEL E DO PROJETO ---
GCP_PROJECT_ID = "vaulted-zodiac-294702"                
MODEL_BUCKET = "rbbr-artifacts"                 
MODEL_BLOB = "models/elasticity/modelo_final_elasticidade.joblib"    
BQ_DATASET = "RBBR_DATA_SCIENCE"                 
BQ_BASE_TABLE = "DM_ELASTICITY"         


@st.cache_resource
def load_model(project_id, bucket_name, blob_name):
    """Carrega o modelo do GCS usando os segredos do Streamlit."""
    try:
        from google.oauth2 import service_account
        import json
        
        # Converter o dicionário de credenciais para o formato correto
        credentials_info = dict(st.secrets["gcp_service_account"])
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        
        storage_client = storage.Client(project=project_id, credentials=credentials)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        model_file = BytesIO(blob.download_as_bytes())
        model, model_columns = joblib.load(model_file)
        return model, model_columns
    except Exception as e:
        st.error(f"Erro ao carregar o modelo: {e}")
        return None, None

@st.cache_data
def load_data(project_id, dataset, table):
    """Carrega os dados base do BigQuery."""
    try:
        from google.oauth2 import service_account
        
        # Converter o dicionário de credenciais para o formato correto
        credentials_info = dict(st.secrets["gcp_service_account"])
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        
        query = f"""
            SELECT 
                NM_ITEM,
                PRECO_ATUAL,
                PRECO_SIMULADO,
                VARIACAO_PERCENTUAL,
                VENDAS_PREVISTAS,
                UPDATED_DT
            FROM `{project_id}.{dataset}.{table}`
            ORDER BY UPDATED_DT DESC
        """
        bq_client = bigquery.Client(project=project_id, credentials=credentials)
        df = bq_client.query(query).to_dataframe()
        if df.empty:
            st.warning("A consulta ao BigQuery não retornou dados. Verifique a tabela e a query.")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()

def engenharia_features(df, data_predicao):
    """Cria as features de data e feriados para a predição."""
    df['DT_EMISSAO'] = pd.to_datetime(data_predicao)
    df['ANO'] = df['DT_EMISSAO'].dt.year
    df['MES'] = df['DT_EMISSAO'].dt.month
    
    mes, dia = data_predicao.month, data_predicao.day
    df['eh_dia_mulher'] = 1 if mes == 3 and dia <= 15 else 0
    df['eh_dia_maes'] = 1 if (mes == 4 and dia > 15) or (mes == 5 and dia <= 15) else 0
    df['eh_dia_namorados'] = 1 if (mes == 5 and dia > 15) or (mes == 6 and dia <= 15) else 0
    df['eh_black_friday'] = 1 if mes == 11 and dia > 15 else 0
    df['eh_natal'] = 1 if mes == 12 and dia <= 15 else 0
    return df

def generate_price_sensitivity_curve(df, selected_product, model, model_columns, num_points=20):
    """Gera dados para a curva de sensibilidade de preço."""
    try:
        # Filtrar dados do produto selecionado
        product_data = df[df['NM_ITEM'] == selected_product].copy()
        if product_data.empty:
            return None
        
        # Obter preço atual
        current_price = product_data['PRECO_ATUAL'].iloc[0]
        
        # Gerar range de preços (-20% a +20%)
        price_range = np.linspace(current_price * 0.8, current_price * 1.2, num_points)
        
        sensitivity_data = []
        
        for price in price_range:
            # Criar dados para predição
            df_sim = product_data.copy()
            df_sim['PRECO_SIMULADO'] = price
            df_sim['PRECO_MEDIO'] = price
            
            # Engenharia de features
            df_sim = engenharia_features(df_sim, datetime.now())
            
            # One-hot encoding
            df_encoded = pd.get_dummies(df_sim, columns=['NM_ITEM'], prefix='ITEM')
            df_modelo_pronto = df_encoded.reindex(columns=model_columns, fill_value=0)
            
            # Predição
            pred_log = model.predict(df_modelo_pronto)
            pred_real = np.expm1(pred_log).round().astype(int)
            pred_real[pred_real < 0] = 0
            
            # Calcular receita
            receita = price * pred_real[0]
            
            sensitivity_data.append({
                'preco': price,
                'vendas': pred_real[0],
                'receita': receita
            })
        
        return pd.DataFrame(sensitivity_data)
    except Exception as e:
        st.error(f"Erro ao gerar curva de sensibilidade: {e}")
        return None

def predict_sales_with_price_change(df, selected_product, price_change_percent, model, model_columns):
    """Prediz vendas com mudança de preço."""
    try:
        # Filtrar dados do produto selecionado
        product_data = df[df['NM_ITEM'] == selected_product].copy()
        if product_data.empty:
            return None
        
        # Obter dados atuais
        current_price = product_data['PRECO_ATUAL'].iloc[0]
        current_sales = product_data['VENDAS_PREVISTAS'].iloc[0]
        current_revenue = current_price * current_sales
        
        # Calcular novo preço
        new_price = current_price * (1 + price_change_percent / 100)
        
        # Criar dados para predição
        df_sim = product_data.copy()
        df_sim['PRECO_SIMULADO'] = new_price
        df_sim['PRECO_MEDIO'] = new_price
        
        # Engenharia de features
        df_sim = engenharia_features(df_sim, datetime.now())
        
        # One-hot encoding
        df_encoded = pd.get_dummies(df_sim, columns=['NM_ITEM'], prefix='ITEM')
        df_modelo_pronto = df_encoded.reindex(columns=model_columns, fill_value=0)
        
        # Predição
        pred_log = model.predict(df_modelo_pronto)
        pred_real = np.expm1(pred_log).round().astype(int)
        pred_real[pred_real < 0] = 0
        
        # Calcular métricas
        predicted_sales = pred_real[0]
        predicted_revenue = new_price * predicted_sales
        
        sales_change = predicted_sales - current_sales
        sales_change_percent = (sales_change / current_sales * 100) if current_sales > 0 else 0
        
        revenue_change = predicted_revenue - current_revenue
        revenue_change_percent = (revenue_change / current_revenue * 100) if current_revenue > 0 else 0
        
        return {
            'preco_atual': current_price,
            'preco_novo': new_price,
            'vendas_atuais': current_sales,
            'vendas_preditas': predicted_sales,
            'mudanca_vendas': sales_change,
            'mudanca_vendas_percent': sales_change_percent,
            'receita_atual': current_revenue,
            'receita_predita': predicted_revenue,
            'mudanca_receita': revenue_change,
            'mudanca_receita_percent': revenue_change_percent
        }
    except Exception as e:
        st.error(f"Erro na predição: {e}")
        return None

# --- APLICAÇÃO STREAMLIT ---

# Configuração da página
st.set_page_config(
    page_title="Análise de Elasticidade de Preço - SR Fantástico",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para sidebar
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    /* Background da sidebar */
    .css-1d391kg, .css-1cypcdb {
        background-color: #1a1a1a !important;
    }
    
    /* Seções da sidebar */
    .sidebar-section {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    
    /* Títulos de seção */
    .section-title {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 500;
        color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
    }
    
    .section-icon {
        font-size: 14px;
    }
    
    /* Header de filtros */
    .filters-header {
        padding: 5px;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .filters-title {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 600;
        color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .filters-separator {
        height: 2px;
        background-color: #404040;
    }
    
    /* Card do período */
    .period-card {
        background: #2C3E50;
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
        padding: 2px;
        margin-bottom: 10px;
        text-align: center;
        width: 100%;
    }
    
    .period-label {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 700;
        color: #ffffff;
    }
    
    .period-value {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 400;
        color: #ffffff;
    }
    
    /* Container para centralizar inputs */
    .input-container {
        display: flex;
        justify-content: center;
        width: 100%;
    }
    
    /* Cards de resumo */
    .summary-card {
        background: #2C3E50;
        border-radius: 8px;
        padding: 6px;
        margin-bottom: 5px;
        text-align: center;
        border-left: 3px solid;
        width: 100%;
    }
    
    .summary-card.current {
        border-left-color: #3b82f6;
    }
    
    .summary-card.new {
        border-left-color: #f97316;
    }
    
    .summary-card.variation {
        border-left-color: #ffffff;
    }
    
    .summary-card.variation.positive {
        border-left-color: #22c55e;
    }
    
    .summary-card.variation.positive .summary-value {
        color: #22c55e !important;
    }
    
    .summary-card.variation.negative {
        border-left-color: #ef4444;
    }
    
    .summary-card.variation.negative .summary-value {
        color: #ef4444 !important;
    }
    
    .summary-label {
        font-family: 'Inter', sans-serif;
        font-size: 10px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 2px;
        letter-spacing: 0.5px;
    }
    
    .summary-value {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 600;
        color: #ffffff;
    }
</style>

""", unsafe_allow_html=True)

# Título principal
st.title("📊 Análise de Elasticidade de Preço")

# Carrega o modelo e os dados base
model, model_columns = load_model(GCP_PROJECT_ID, MODEL_BUCKET, MODEL_BLOB)
df = load_data(GCP_PROJECT_ID, BQ_DATASET, BQ_BASE_TABLE)

# A aplicação só continua se o modelo e os dados foram carregados com sucesso
if model is not None and not df.empty:
    
    # Logo centralizado
    try:
        col1, col2, col3 = st.sidebar.columns([1, 2, 1])
        with col2:
            st.image("logo.png", width=200)
    except:
        col1, col2, col3 = st.sidebar.columns([1, 2, 1])
        with col2:
            st.markdown("### TANGLE TEEZER")
    
    # Header de Filtros
    st.sidebar.markdown("""
    <div class="filters-header">
        <div class="filters-title">
            <span class="icon">🔍</span>
            Filtros
        </div>
    </div>
    <div class="filters-separator"></div>
    """, unsafe_allow_html=True)
    
    # Período de previsão
    st.sidebar.markdown("""
    <div class="sidebar-section">
        <div class="section-title">
            Período Atual
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Calcular período de 15 dias automaticamente
    from datetime import datetime, timedelta
    today = datetime.now()
    start_date = today
    end_date = today + timedelta(days=14)  # 15 dias incluindo hoje
    
    st.markdown("---")

    st.sidebar.markdown(f"""
    <div class="period-card">
        <div class="period-label">Quinzena</div>
        <div class="period-value">{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Linha separadora
    st.sidebar.markdown("""
    <div class="filters-separator"></div>
    """, unsafe_allow_html=True)
    
    # Seleção de produto
    st.sidebar.markdown("""
    <div class="sidebar-section">
        <div class="section-title">
            Produto
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Container para centralizar o dropdown
    st.sidebar.markdown('<div class="input-container">', unsafe_allow_html=True)
    selected_product = st.sidebar.selectbox(
        "Escolha o produto:",
        options=df['NM_ITEM'].unique(),
        index=0,
        label_visibility="collapsed"
    )
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # Linha separadora
    st.sidebar.markdown("""
    <div class="filters-separator"></div>
    """, unsafe_allow_html=True)
    
    # Input de preço com design melhorado
    st.sidebar.markdown("""
    <div class="sidebar-section">
        <div class="section-title">
            Preço
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if selected_product:
        # Obter preço atual do produto selecionado
        product_data = df[df['NM_ITEM'] == selected_product]
        if not product_data.empty:
            current_price = product_data['PRECO_ATUAL'].iloc[0]
            
            # Input de preço no padrão Streamlit
            st.sidebar.markdown("""
            <div style="margin-bottom: 2px; font-family: 'Inter', sans-serif; font-size: 12px; color: #ffffff; font-weight: 500; text-align: left;">
                Novo preço (R$) <span style="background: #555555; color: #ffffff; border-radius: 50%; width: 16px; height: 16px; display: inline-flex; align-items: center; justify-content: center; font-size: 10px; margin-left: 6px;">?</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Container para centralizar o input
            st.sidebar.markdown('<div class="input-container">', unsafe_allow_html=True)
            # Calcular limites de ±10% do preço atual
            min_price = current_price * 0.9  # -10%
            max_price = current_price * 1.1  # +10%
            new_price = st.sidebar.number_input(
                "Preço (R$)",
                min_value=min_price,
                max_value=max_price,
                value=float(current_price),
                step=0.01,
                format="%.2f",
                label_visibility="collapsed",
                key="price_input"
            )
            st.sidebar.markdown('</div>', unsafe_allow_html=True)
            
            # Calcular variação percentual
            price_change_percent = ((new_price - current_price) / current_price) * 100
            
            
            # Card do preço atual (azul)
            st.sidebar.markdown(f"""
            <div class="summary-card current">
                <div class="summary-label">Atual</div>
                <div class="summary-value">R$ {current_price:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Card do novo preço (laranja)
            st.sidebar.markdown(f"""
            <div class="summary-card new">
                <div class="summary-label">Novo</div>
                <div class="summary-value">R$ {new_price:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Card de variação com cores dinâmicas
            if price_change_percent > 0:
                # Positiva - verde
                variation_icon = "↗"
                variation_text = f"{variation_icon} +{price_change_percent:.1f}%"
                variation_class = "summary-card variation positive"
            elif price_change_percent < 0:
                # Negativa - vermelho
                variation_icon = "↘"
                variation_text = f"{variation_icon} {price_change_percent:.1f}%"
                variation_class = "summary-card variation negative"
            else:
                # Zero - branco
                variation_icon = "→"
                variation_text = f"{variation_icon} +0.0%"
                variation_class = "summary-card variation"
            
            st.sidebar.markdown(f"""
            <div class="{variation_class}">
                <div class="summary-label">Variação</div>
                <div class="summary-value">{variation_text}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Converter para percentual para usar nas funções existentes
            price_change = price_change_percent
    
    # Linha separadora
    st.sidebar.markdown("---")
    
    # Botão de Logout no final da sidebar
    if st.sidebar.button("Logout"):
        # Limpa todo o estado da sessão para deslogar o usuário
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun() # Reinicia a aplicação para voltar à tela de login
    
    # Calcular previsão com mudança de preço
    prediction = predict_sales_with_price_change(df, selected_product, price_change, model, model_columns)
    
    if prediction:
        # Gerar dados da curva de sensibilidade para o gráfico principal
        sensitivity_curve_data = generate_price_sensitivity_curve(df, selected_product, model, model_columns, 20)
        
        if sensitivity_curve_data is not None:
            # Gráfico principal: Preço (X) vs Vendas Previstas (Y)
            fig_main = px.line(
                sensitivity_curve_data,
                x='preco',
                y='vendas',
                title=f"Curva de Elasticidade - {selected_product}",
                markers=True
            )
            
            # Destacar ponto atual
            current_sales = prediction['vendas_atuais']
            current_price = prediction['preco_atual']
            
            fig_main.add_trace(go.Scatter(
                x=[current_price],
                y=[current_sales],
                mode='markers',
                marker=dict(size=15, color='red', symbol='star'),
                name='Situação Atual'
            ))
            
            # Destacar ponto com novo preço se houver mudança
            if price_change != 0:
                new_price = prediction['preco_novo']
                new_sales = prediction['vendas_preditas']
                
                fig_main.add_trace(go.Scatter(
                    x=[new_price],
                    y=[new_sales],
                    mode='markers',
                    marker=dict(size=15, color='green', symbol='star'),
                    name='Cenário Simulado'
                ))
            
            fig_main.update_layout(
                xaxis_title="Preço (R$)",
                yaxis_title="Vendas Previstas",
                showlegend=True,
                height=500
            )
            
            st.plotly_chart(fig_main, use_container_width=True)
        
        st.markdown("---")
        
        # KPIs Principais
        st.header("📈 Indicadores Principais")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💰 Preço Atual",
                value=f"R$ {prediction['preco_atual']:.2f}",
                delta=f"R$ {prediction['preco_novo'] - prediction['preco_atual']:.2f}" if price_change != 0 else None
            )
        
        with col2:
            st.metric(
                label="📦 Vendas Atuais",
                value=f"{prediction['vendas_atuais']:,.0f}",
                delta=f"{prediction['mudanca_vendas']:,.0f}" if price_change != 0 else None
            )
        
        with col3:
            st.metric(
                label="💵 Receita Atual",
                value=f"R$ {prediction['receita_atual']:,.2f}",
                delta=f"R$ {prediction['mudanca_receita']:,.2f}" if price_change != 0 else None
            )
        
        with col4:
            st.metric(
                label="🎯 Previsão",
                value=f"{prediction['vendas_preditas']:,.0f}",
                delta=f"{prediction['mudanca_vendas_percent']:.1f}%" if price_change != 0 else None,
            )
        
        
        # Rodapé
        st.markdown("---")
        st.markdown(
            """
            <div style='text-align: center; color: #666;'>
                <p>Previsão de Vendas com Machine Learning - SR Fantástico | Desenvolvido com Streamlit</p>
            </div>
            """,
            unsafe_allow_html=True
    )

else:
    st.error("🔴 Falha ao carregar modelo ou dados do BigQuery. Verifique as configurações e os logs.")