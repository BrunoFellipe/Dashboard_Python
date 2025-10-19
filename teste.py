"""
Dashboard Corporativo – Contexto Brasileiro (Streamlit) com Autenticação

Requisitos:
    pip install streamlit pandas numpy pyarrow plotly faker streamlit-authenticator

Execução:
    streamlit run app.py
"""

import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import streamlit_authenticator as stauth
from faker import Faker
from datetime import datetime, timedelta

# =============================
# Autenticação de Usuários
# =============================

users = ['Admin', 'Convidado']
usernames = ['admin', 'guest']
passwords = ['12345', 'guest123']  # Senhas simples para teste
hashed_pw = stauth.Hasher(passwords).generate()

authenticator = stauth.Authenticate(
    users, usernames, hashed_pw,
    'cookie_app_dashboard', 'chave_cookie', cookie_expiry_days=1
)

name, auth_status, username = authenticator.login('Login', 'main')

if not auth_status:
    if auth_status == False:
        st.error('Usuário ou senha incorretos.')
    else:
        st.warning('Por favor, entre com suas credenciais.')
    st.stop()

# =============================
# Interface após login
# =============================
authenticator.logout('Sair', 'sidebar')
st.sidebar.write(f'Usuário logado: **{name}**')

# =============================
# Configuração inicial
# =============================
st.set_page_config(page_title="Dashboard Corporativo", layout="wide")
st.title(f"📊 Dashboard Corporativo – Bem-vindo, {name}!")

fake = Faker('pt_BR')
np.random.seed(42)

# =============================
# Geração de dados fictícios
# =============================

REGIOES = ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul']
PRODUTOS = ['Produto A', 'Produto B', 'Produto C']
DEPARTAMENTOS = ['Comercial', 'Financeiro', 'RH', 'TI']

# Simula vendas
vendas = pd.DataFrame({
    'Data': pd.date_range('2024-01-01', periods=500),
    'Produto': np.random.choice(PRODUTOS, 500),
    'Região': np.random.choice(REGIOES, 500),
    'Valor': np.random.uniform(100, 10000, 500),
    'Vendedor': [fake.first_name() for _ in range(500)]
})

# Simula colaboradores
colaboradores = pd.DataFrame({
    'Nome': [fake.name() for _ in range(100)],
    'Departamento': np.random.choice(DEPARTAMENTOS, 100),
    'Salário': np.random.uniform(2500, 15000, 100).round(2)
})

# =============================
# Controle de acesso por perfil
# =============================

if username == 'guest':
    permissoes = {
        'Comercial': True,
        'Gestão de Pessoas': True,
        'Financeiro': False,
        'Operações': False,
    }
else:
    permissoes = {aba: True for aba in ['Comercial', 'Gestão de Pessoas', 'Financeiro', 'Operações']}

# =============================
# Abas principais
# =============================
tabs = [aba for aba, permitido in permissoes.items() if permitido]
abas = st.tabs(tabs)

# =============================
# Comercial
# =============================
if 'Comercial' in permissoes and permissoes['Comercial']:
    with abas[tabs.index('Comercial')]:
        st.subheader('📈 Vendas')
        regioes_sel = st.multiselect('Regiões', REGIOES, default=REGIOES)
        df = vendas[vendas['Região'].isin(regioes_sel)]

        col1, col2 = st.columns(2)
        with col1:
            st.metric('Total de Vendas (R$)', f"{df['Valor'].sum():,.2f}".replace(',', '@').replace('.', ',').replace('@', '.'))
        with col2:
            st.metric('Média por Venda (R$)', f"{df['Valor'].mean():,.2f}".replace(',', '@').replace('.', ',').replace('@', '.'))

        fig = px.bar(df.groupby('Produto')['Valor'].sum().reset_index(), x='Produto', y='Valor', title='Vendas por Produto')
        st.plotly_chart(fig, use_container_width=True)

# =============================
# Gestão de Pessoas
# =============================
if 'Gestão de Pessoas' in permissoes and permissoes['Gestão de Pessoas']:
    with abas[tabs.index('Gestão de Pessoas')]:
        st.subheader('👥 Colaboradores')
        dep_sel = st.multiselect('Departamento', DEPARTAMENTOS, default=DEPARTAMENTOS)
        df_c = colaboradores[colaboradores['Departamento'].isin(dep_sel)]

        col1, col2 = st.columns(2)
        with col1:
            st.metric('Total de Colaboradores', len(df_c))
        with col2:
            st.metric('Salário Médio (R$)', f"{df_c['Salário'].mean():,.2f}".replace(',', '@').replace('.', ',').replace('@', '.'))

        fig = px.box(df_c, x='Departamento', y='Salário', title='Distribuição Salarial por Departamento')
        st.plotly_chart(fig, use_container_width=True)

# =============================
# Financeiro
# =============================
if 'Financeiro' in permissoes and permissoes['Financeiro']:
    with abas[tabs.index('Financeiro')]:
        st.subheader('💰 Financeiro')
        st.info('Acesso restrito ao perfil **Admin**.')
        receita = vendas['Valor'].sum()
        despesa = receita * np.random.uniform(0.6, 0.9)
        st.metric('Lucro (R$)', f"{receita - despesa:,.2f}".replace(',', '@').replace('.', ',').replace('@', '.'))

# =============================
# Operações
# =============================
if 'Operações' in permissoes and permissoes['Operações']:
    with abas[tabs.index('Operações')]:
        st.subheader('⚙️ Operações')
        st.info('Acesso restrito ao perfil **Admin**.')
        dados_op = pd.DataFrame({
            'Mês': pd.date_range('2024-01-01', periods=12, freq='M'),
            'Eficiência (%)': np.random.uniform(70, 98, 12)
        })
        fig = px.line(dados_op, x='Mês', y='Eficiência (%)', title='Eficiência Operacional Mensal')
        st.plotly_chart(fig, use_container_width=True)

st.success('✅ Login e controle de acesso ativos!')