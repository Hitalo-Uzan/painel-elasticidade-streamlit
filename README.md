# 📊 Painel de Análise de Elasticidade de Preço

Um painel interativo desenvolvido em Streamlit para análise de elasticidade de preço e previsão de vendas usando Machine Learning.

## 🎯 Visão Geral

Este projeto implementa um sistema completo de análise de elasticidade de preço que permite:

- **Simulação de cenários** de mudança de preço em tempo real
- **Previsão de vendas** usando modelos de Machine Learning
- **Análise de impacto** na receita e demanda
- **Visualizações interativas** com gráficos dinâmicos
- **Comparativo entre produtos** e análise histórica

## 🚀 Funcionalidades Principais

### 📈 Indicadores Principais
- **Preço Atual vs Novo**: Comparação visual dos preços
- **Vendas Atuais vs Previstas**: Impacto na demanda
- **Receita Atual vs Prevista**: Impacto financeiro
- **Mudanças Percentuais**: Deltas em tempo real

### 📊 Análise de Impacto
- **Gráficos de Barras**: Comparação visual entre cenários
- **Impacto na Receita**: Análise financeira detalhada
- **Impacto na Demanda**: Análise de volume de vendas

### 📈 Curva de Sensibilidade de Preço
- **Simulação Automática**: Testa preços de -20% a +20%
- **Curva de Demanda**: Relação preço vs vendas
- **Curva de Receita**: Otimização de preços
- **Ponto Atual Destacado**: Situação atual do produto

### 📊 Visão Histórica e Tendências
- **Evolução de Preços**: Tendência temporal
- **Evolução de Vendas**: Análise histórica
- **Linhas de Tendência**: Regressão linear automática
- **Dados de 30 dias**: Histórico completo

### 🔍 Comparativo de Produtos
- **Ranking de Vendas**: Por volume total
- **Scatter Plot**: Preço vs Vendas
- **Análise Cross-Product**: Comparação entre produtos
- **Métricas Agregadas**: Preço médio, vendas totais, receita

### 📋 Tabela de Resumo
- **Métricas Detalhadas**: Resumo completo da análise
- **Mudanças Percentuais**: Impactos quantificados
- **Dados Formatados**: Fácil leitura e interpretação

## 🛠️ Tecnologias Utilizadas

### Backend
- **Python 3.8+**
- **Streamlit**: Framework web para dashboards
- **Pandas**: Manipulação de dados
- **NumPy**: Computação numérica
- **Scikit-learn**: Machine Learning

### Visualização
- **Plotly**: Gráficos interativos
- **Plotly Express**: Gráficos simplificados
- **Plotly Graph Objects**: Gráficos customizados

### Cloud & Storage
- **Google Cloud Storage**: Armazenamento do modelo ML
- **Google BigQuery**: Banco de dados analítico
- **Google Cloud IAM**: Autenticação e autorização

### Machine Learning
- **Joblib**: Serialização do modelo
- **Random Forest**: Algoritmo de ML (exemplo)
- **Feature Engineering**: Criação de features temporais

## 📁 Estrutura do Projeto

```
painel_elasticidade/
├── app.py                          # Aplicação principal
├── .streamlit/
│   └── secrets.toml               # Configurações do GCP
├── logo.png                       # Logo da empresa
└── README.md                      # Documentação
```

## ⚙️ Configuração e Instalação

### 1. Pré-requisitos
```bash
# Python 3.8 ou superior
python --version

# Instalar dependências
pip install streamlit pandas numpy plotly scikit-learn google-cloud-storage google-cloud-bigquery joblib
```

### 2. Configuração do Google Cloud

#### 2.1 Criar Service Account
1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Vá para **IAM & Admin** → **Service Accounts**
3. Clique em **Create Service Account**
4. Nome: `data-scientist`
5. Adicione as seguintes roles:
   - `Storage Object Viewer`
   - `BigQuery Data Viewer`
   - `BigQuery Job User`

#### 2.2 Baixar Credenciais
1. Clique na service account criada
2. Vá para **Keys** → **Add Key** → **Create New Key**
3. Escolha **JSON** e baixe o arquivo

#### 2.3 Configurar Streamlit Secrets
Crie o arquivo `.streamlit/secrets.toml`:

```toml
[gcp_service_account]
type = "service_account"
project_id = "seu-projeto-id"
private_key_id = "sua-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nsua-chave-privada\n-----END PRIVATE KEY-----\n"
client_email = "data-scientist@seu-projeto.iam.gserviceaccount.com"
client_id = "seu-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/data-scientist%40seu-projeto.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
```

### 3. Configuração do BigQuery

#### 3.1 Criar Dataset
```sql
CREATE SCHEMA `seu-projeto.RBBR_DATA_SCIENCE`
OPTIONS (
  description = "Dataset para análise de elasticidade de preço",
  location = "US"
);
```

#### 3.2 Criar Tabela
```sql
CREATE TABLE `seu-projeto.RBBR_DATA_SCIENCE.DM_ELASTICITY` (
  NM_ITEM STRING,
  PRECO_ATUAL FLOAT64,
  PRECO_SIMULADO FLOAT64,
  VARIACAO_PERCENTUAL FLOAT64,
  VENDAS_PREVISTAS INT64,
  UPDATED_DT TIMESTAMP
);
```

### 4. Configuração do Google Cloud Storage

#### 4.1 Criar Bucket
```bash
gsutil mb gs://rbbr-artifacts
```

#### 4.2 Fazer Upload do Modelo
```bash
gsutil cp modelo_final_elasticidade.joblib gs://rbbr-artifacts/models/elasticity/
```

### 5. Executar a Aplicação

```bash
# Executar o Streamlit
streamlit run app.py

# Ou com porta específica
streamlit run app.py --server.port 8501
```

## 🔧 Configurações do Projeto

### Variáveis de Configuração
No arquivo `app.py`, ajuste as seguintes variáveis:

```python
# Configurações do GCP
GCP_PROJECT_ID = "seu-projeto-id"
MODEL_BUCKET = "rbbr-artifacts"
MODEL_BLOB = "models/elasticity/modelo_final_elasticidade.joblib"
BQ_DATASET = "RBBR_DATA_SCIENCE"
BQ_BASE_TABLE = "DM_ELASTICITY"
```

## 📊 Estrutura de Dados

### Tabela BigQuery: DM_ELASTICITY
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `NM_ITEM` | STRING | Nome do produto |
| `PRECO_ATUAL` | FLOAT64 | Preço atual do produto |
| `PRECO_SIMULADO` | FLOAT64 | Preço simulado |
| `VARIACAO_PERCENTUAL` | FLOAT64 | Variação percentual do preço |
| `VENDAS_PREVISTAS` | INT64 | Quantidade de vendas previstas |
| `UPDATED_DT` | TIMESTAMP | Data de atualização |

### Modelo de Machine Learning
- **Formato**: Joblib (.joblib)
- **Localização**: Google Cloud Storage
- **Features**: Preço, data, feriados, sazonalidade
- **Target**: Vendas (transformação logarítmica)

## 🎨 Interface do Usuário

### Sidebar
- **📅 Período de Previsão**: 15 dias fixo
- **📦 Seleção de Produto**: Dropdown com todos os produtos
- **💰 Ajuste de Preço**: Slider de -10% a +10%
- **💵 Preços**: Métricas de preço atual vs novo

### Área Principal
- **📈 Indicadores Principais**: 4 KPIs em destaque
- **📊 Análise de Impacto**: Gráficos de comparação
- **📈 Curva de Sensibilidade**: Simulação de cenários
- **📊 Visão Histórica**: Tendências temporais
- **🔍 Comparativo de Produtos**: Análise cross-product
- **📋 Tabela de Resumo**: Métricas detalhadas

## 🔄 Fluxo de Dados

1. **Carregamento**: Dados do BigQuery + Modelo do GCS
2. **Seleção**: Usuário escolhe produto e variação de preço
3. **Processamento**: Engenharia de features + Predição ML
4. **Visualização**: Gráficos e métricas atualizadas
5. **Interação**: Atualização em tempo real

## 🚀 Funcionalidades Avançadas

### Engenharia de Features
- **Features Temporais**: Ano, mês, dia
- **Feriados**: Dia da Mulher, Dia das Mães, Dia dos Namorados
- **Sazonalidade**: Black Friday, Natal
- **One-Hot Encoding**: Produtos categóricos

### Simulação de Cenários
- **Range de Preços**: -20% a +20%
- **20 Pontos**: Simulação granular
- **Curvas Suaves**: Interpolação automática
- **Otimização**: Encontrar preço ótimo

### Análise de Tendências
- **Regressão Linear**: Linhas de tendência
- **Métricas Temporais**: Evolução histórica
- **Padrões Sazonais**: Identificação automática
- **Projeções**: Extrapolação de tendências

## 🔒 Segurança

### Autenticação
- **Service Account**: Autenticação segura
- **IAM Roles**: Permissões mínimas necessárias
- **Secrets Management**: Credenciais protegidas

### Dados
- **Conexão Segura**: HTTPS/TLS
- **Credenciais Criptografadas**: Armazenamento seguro
- **Acesso Controlado**: Baseado em roles

## 📈 Performance

### Otimizações
- **Cache de Dados**: `@st.cache_data`
- **Cache de Modelo**: `@st.cache_resource`
- **Lazy Loading**: Carregamento sob demanda
- **Batch Processing**: Processamento em lotes

### Escalabilidade
- **BigQuery**: Processamento distribuído
- **Cloud Storage**: Armazenamento escalável
- **Streamlit**: Interface responsiva
- **Plotly**: Visualizações otimizadas

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. Erro de Autenticação
```
Erro: This library only supports credentials from google-auth-library-python
```
**Solução**: Verificar se as credenciais estão no formato correto no `secrets.toml`

#### 2. Erro de Permissões
```
Erro: Permission 'storage.objects.get' denied
```
**Solução**: Adicionar role `Storage Object Viewer` à service account

#### 3. Erro de Conexão BigQuery
```
Erro: 403 Forbidden
```
**Solução**: Verificar se a service account tem acesso ao dataset

#### 4. Modelo Não Encontrado
```
Erro: 404 Not Found
```
**Solução**: Verificar se o arquivo existe no bucket e o caminho está correto

### Logs e Debug
```python
# Habilitar logs detalhados
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔄 Atualizações e Manutenção

### Atualização do Modelo
1. Treinar novo modelo
2. Fazer upload para o GCS
3. Atualizar versão no código
4. Testar em ambiente de desenvolvimento

### Atualização de Dados
1. Executar pipeline de dados
2. Atualizar tabela BigQuery
3. Verificar qualidade dos dados
4. Monitorar performance

### Monitoramento
- **Logs de Erro**: Streamlit logs
- **Performance**: Tempo de resposta
- **Uso de Recursos**: CPU/Memória
- **Qualidade dos Dados**: Validações automáticas

## 📚 Referências

### Documentação
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Google Cloud Storage](https://cloud.google.com/storage/docs)
- [Google BigQuery](https://cloud.google.com/bigquery/docs)
- [Plotly Python](https://plotly.com/python/)

### Tutoriais
- [Streamlit Tutorial](https://docs.streamlit.io/getting-started)
- [Google Cloud Setup](https://cloud.google.com/docs/authentication)
- [Machine Learning with Scikit-learn](https://scikit-learn.org/stable/)

## 👥 Contribuição

### Como Contribuir
1. Fork do repositório
2. Criar branch para feature
3. Implementar mudanças
4. Testar localmente
5. Criar Pull Request

### Padrões de Código
- **PEP 8**: Formatação Python
- **Docstrings**: Documentação de funções
- **Type Hints**: Tipagem de variáveis
- **Error Handling**: Tratamento de erros

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para suporte técnico ou dúvidas:
- **Email**: suporte@empresa.com
- **Issues**: Use o sistema de issues do repositório
- **Documentação**: Consulte este README

---

**Desenvolvido com ❤️ para análise de elasticidade de preço e otimização de vendas.**
