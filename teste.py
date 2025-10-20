"""
Dashboard Corporativo – Contexto Brasileiro (Streamlit) – Versão Híbrida (Desktop + Mobile) com correção de login/logout

Requisitos:
    pip install streamlit pandas numpy pyarrow plotly faker

Execução:
    streamlit run app.py

Notas:
- Layout responsivo adaptável automaticamente a desktop e mobile.
- Login simples (usuário/senha): admin/12345 e guest/guest123.
- Corrigido duplo clique no login e erro no logout.
- Adicionado feedback visual no login/logout.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from faker import Faker
from datetime import datetime, timedelta

# =============================
# Configuração e estilo
# =============================
st.set_page_config(page_title="Dashboard Corporativo", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {padding: 1rem !important;}
@media (max-width: 768px) {
  h1, h2, h3, h4, h5, h6 {font-size: 95% !important;}
  .block-container {padding: 0.5rem !important;}
  div[data-testid="stHorizontalBlock"] > div {width: 100% !important; display: block !important;}
  .stPlotlyChart {min-height: 300px !important;}
  .stDataFrame {font-size: 85% !important;}
}
</style>
""", unsafe_allow_html=True)

fake = Faker('pt_BR')
np.random.seed(42)

# =============================
# Login simples
# =============================
DEFAULT_USERS = {
    "admin": {"name": "Admin", "password": "12345", "role": "admin"},
    "guest": {"name": "Convidado", "password": "guest123", "role": "guest"},
}

if 'auth' not in st.session_state:
    st.session_state.auth = {"logged": False, "user": None}

with st.sidebar:
    st.header("🔐 Login")
    if not st.session_state.auth["logged"]:
        u = st.text_input("Usuário", key="_u")
        p = st.text_input("Senha", type="password", key="_p")
        if st.button("Entrar"):
            creds = DEFAULT_USERS.get(u)
            if creds and p == creds["password"]:
                st.session_state.auth = {"logged": True, "user": {"username": u, **creds}}
                st.success(f"Bem-vindo, {creds['name']}! Carregando dashboard...")
                st.toast("🔄 Redirecionando...", icon="🔁")
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
        st.stop()
    else:
        user = st.session_state.auth["user"]
        st.write(f"Usuário logado: **{user['name']}** ({user['role']})")
        if st.button("Sair"):
            st.toast("Saindo...", icon="👋")
            st.session_state.clear()
            st.rerun()

user = st.session_state.auth["user"]

# =============================
# Dados fictícios
# =============================
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
PRODUTOS = ["Produto A", "Produto B", "Produto C"]
DEPARTAMENTOS = ["Comercial", "Financeiro", "RH", "TI"]

vendas = pd.DataFrame({
    'Data': pd.date_range('2024-01-01', periods=600),
    'Produto': np.random.choice(PRODUTOS, 600),
    'Região': np.random.choice(REGIOES, 600),
    'Valor': np.random.uniform(100, 10000, 600),
    'Vendedor': [fake.first_name() for _ in range(600)]
})

colaboradores = pd.DataFrame({
    'Nome': [fake.name() for _ in range(100)],
    'Departamento': np.random.choice(DEPARTAMENTOS, 100),
    'Salário': np.random.uniform(2500, 15000, 100).round(2)
})

# =============================
# Filtros Globais
# =============================
min_date, max_date = vendas['Data'].min().date(), vendas['Data'].max().date()
with st.sidebar:
    st.header("📆 Filtros Globais")
    periodo = st.date_input("Período", (min_date, max_date), min_value=min_date, max_value=max_date)
    reg_sel = st.multiselect("Região", REGIOES, default=REGIOES)
    prod_sel = st.multiselect("Produto", PRODUTOS, default=PRODUTOS)

def filtro_vendas(df):
    if isinstance(periodo, (list, tuple)) and len(periodo) == 2:
        ini, fim = pd.to_datetime(periodo[0]), pd.to_datetime(periodo[1])
        df = df[(df['Data'] >= ini) & (df['Data'] <= fim)]
    return df[df['Região'].isin(reg_sel) & df['Produto'].isin(prod_sel)]

vendas_f = filtro_vendas(vendas)

# =============================
# KPIs principais (adaptáveis)
# =============================
receita = vendas_f['Valor'].sum()
media_venda = vendas_f['Valor'].mean()
total_vendas = len(vendas_f)

col1, col2 = st.columns(2)
col1.metric("Receita (R$)", f"{receita:,.2f}".replace(',', '@').replace('.', ',').replace('@', '.'))
col2.metric("Média por Venda (R$)", f"{media_venda:,.2f}".replace(',', '@').replace('.', ',').replace('@', '.'))

# =============================
# Abas adaptáveis
# =============================
role = user['role']
abas = ["Comercial", "Gestão de Pessoas"] + (["Financeiro"] if role == 'admin' else [])
tabs = st.tabs(abas)

# =============================
# COMERCIAL
# =============================
with tabs[0]:
    st.subheader("📈 Comercial – Vendas")
    df = vendas_f.copy()
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(df.groupby('Produto')['Valor'].sum().reset_index(), x='Produto', y='Valor', title='Vendas por Produto')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.pie(df, values='Valor', names='Região', title='Distribuição por Região')
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df.head(20))

# =============================
# GESTÃO DE PESSOAS
# =============================
with tabs[1]:
    st.subheader("👥 Gestão de Pessoas")
    df_c = colaboradores.copy()
    dep_sel = st.multiselect('Departamento', DEPARTAMENTOS, default=DEPARTAMENTOS)
    df_c = df_c[df_c['Departamento'].isin(dep_sel)]
    col1, col2 = st.columns(2)
    with col1:
        fig = px.box(df_c, x='Departamento', y='Salário', title='Distribuição Salarial por Departamento')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.histogram(df_c, x='Salário', nbins=25, title='Distribuição de Salários')
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df_c)

# =============================
# FINANCEIRO (ADMIN)
# =============================
if role == 'admin' and len(tabs) > 2:
    with tabs[2]:
        st.subheader("💰 Financeiro")
        df = vendas_f.copy()
        df['Mês'] = df['Data'].dt.to_period('M').astype(str)
        receita_mensal = df.groupby('Mês')['Valor'].sum().reset_index()
        fig = px.line(receita_mensal, x='Mês', y='Valor', title='Receita Mensal (R$)')
        st.plotly_chart(fig, use_container_width=True)

st.success('✅ Dashboard responsivo e adaptável pronto para desktop e mobile!')