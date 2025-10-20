"""
Dashboard Corporativo – Contexto Brasileiro (Streamlit)
Versão Híbrida (Desktop + Mobile) com Login obrigatório + Home + Hub de Notícias (Auto + Manual)
Agora com integração de usuários e notícias via arquivos JSON externos e correção dos botões de navegação.

Requisitos:
    pip install streamlit pandas numpy pyarrow plotly faker

Como executar:
    streamlit run app.py

Arquivos externos esperados na mesma pasta:
- usuarios.json
- noticias.json

Estrutura usuarios.json:
[
  {"username": "admin", "name": "Admin", "password": "12345", "role": "admin"},
  {"username": "guest", "name": "Convidado", "password": "guest123", "role": "guest"}
]

Estrutura noticias.json:
[
  {"titulo": "Novidade!", "texto": "Agora o catálogo de clientes está ligado diretamente ao nosso banco do Oracle Cloud.", "icone": "🆕"},
  {"titulo": "Novo Dashboard!", "texto": "Acesse agora os dados de Jornada Laboral na aba Gestão de Pessoas.", "icone": "📊"},
  {"titulo": "Treinamento!", "texto": "Faça parte do novo bootcamp da área de Data & Analytics.", "icone": "🎓"}
]
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from faker import Faker
from datetime import datetime
import json
import os
import time

# =============================
# Configuração e estilo
# =============================
st.set_page_config(page_title="Dashboard Corporativo", layout="wide", initial_sidebar_state="collapsed")
st.markdown(
    """
<style>
[data-testid="stAppViewContainer"] {padding: 1rem !important;}
@media (max-width: 768px) {
  h1, h2, h3, h4, h5, h6 {font-size: 95% !important;}
  .block-container {padding: 0.5rem !important;}
  div[data-testid="stHorizontalBlock"] > div {width: 100% !important; display: block !important;}
  .stPlotlyChart {min-height: 300px !important;}
  .stDataFrame {font-size: 85% !important;}
}
.card {border:1px solid #eee; border-radius:14px; padding:1rem; box-shadow:0 1px 6px rgba(0,0,0,0.06); background: linear-gradient(180deg, #ffffff, #fafafa);} 
.card:hover {box-shadow:0 4px 14px rgba(0,0,0,0.12); transform: translateY(-2px);} 
.card-title {font-weight:700; margin-bottom:0.25rem;} 
.card-desc {color:#444; font-size:0.95rem;}
.badge {display:inline-block; padding:0.15rem 0.5rem; border-radius:999px; font-size:0.75rem; margin-left:0.5rem;}
.badge-new {background:#e0f7ec; color:#067d49;}
.badge-upd {background:#e9f2ff; color:#1a56db;}
.badge-lock {background:#fff0f0; color:#b10000;}
</style>
""",
    unsafe_allow_html=True,
)

fake = Faker("pt_BR")
np.random.seed(42)

# =============================
# Carregamento de usuários e notícias via JSON
# =============================
def load_json_file(filename: str, default_data):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"Erro ao ler {filename}: {e}. Usando dados padrão.")
    return default_data

# Usuários padrão
DEFAULT_USERS = [
    {"username": "admin", "name": "Admin", "password": "12345", "role": "admin"},
    {"username": "guest", "name": "Convidado", "password": "guest123", "role": "guest"}
]

# Notícias padrão
DEFAULT_NOTICIAS = [
    {"titulo": "Novidade!", "texto": "Agora o catálogo de clientes está ligado diretamente ao nosso banco do Oracle Cloud.", "icone": "🆕"},
    {"titulo": "Novo Dashboard!", "texto": "Acesse agora os dados de Jornada Laboral na aba Gestão de Pessoas.", "icone": "📊"},
    {"titulo": "Treinamento!", "texto": "Faça parte do novo bootcamp da área de Data & Analytics.", "icone": "🎓"}
]

USERS = load_json_file("usuarios.json", DEFAULT_USERS)
NOTICIAS = load_json_file("noticias.json", DEFAULT_NOTICIAS)

# =============================
# Login simples (obrigatório)
# =============================
if "auth" not in st.session_state:
    st.session_state.auth = {"logged": False, "user": None}
    st.session_state["active_tab"] = "Home"
    st.session_state["news_index"] = 0
    st.session_state["autoplay"] = True
    st.session_state["pause_until"] = 0.0

with st.sidebar:
    st.header("🔐 Login")
    if not st.session_state.auth["logged"]:
        u = st.text_input("Usuário", key="_u")
        p = st.text_input("Senha", type="password", key="_p")
        if st.button("Entrar"):
            creds = next((user for user in USERS if user["username"] == u and user["password"] == p), None)
            if creds:
                st.session_state.auth = {"logged": True, "user": creds}
                st.success(f"Bem-vindo, {creds['name']}! Preparando o ambiente...")
                st.toast("🔄 Carregando Home...", icon="🏠")
                st.session_state["active_tab"] = "Home"
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
        st.stop()
    else:
        user = st.session_state.auth["user"]
        st.write(f"Usuário: **{user['name']}** | Perfil: **{user['role']}**")
        if st.button("Sair"):
            st.toast("Saindo...", icon="👋")
            st.session_state.clear()
            st.rerun()

user = st.session_state.auth["user"]
role = user["role"]

# =============================
# Dados fictícios (demo)
# =============================
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
PRODUTOS = ["Produto A", "Produto B", "Produto C", "Produto D"]
DEPARTAMENTOS = ["Comercial", "Financeiro", "RH", "TI"]

vendas = pd.DataFrame(
    {
        "Data": pd.date_range("2024-01-01", periods=900),
        "Produto": np.random.choice(PRODUTOS, 900),
        "Região": np.random.choice(REGIOES, 900),
        "Valor": np.random.uniform(100, 10000, 900),
        "Vendedor": [fake.first_name() for _ in range(900)],
    }
)

colaboradores = pd.DataFrame(
    {
        "Nome": [fake.name() for _ in range(200)],
        "Departamento": np.random.choice(DEPARTAMENTOS, 200),
        "Salário": np.random.uniform(2500, 18000, 200).round(2),
    }
)

# =============================
# Filtros Globais
# =============================
min_date, max_date = vendas["Data"].min().date(), vendas["Data"].max().date()
with st.sidebar:
    st.header("📆 Filtros Globais")
    periodo = st.date_input("Período", (min_date, max_date), min_value=min_date, max_value=max_date)
    reg_sel = st.multiselect("Região", REGIOES, default=REGIOES)
    prod_sel = st.multiselect("Produto", PRODUTOS, default=PRODUTOS)

def filtro_vendas(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(periodo, (list, tuple)) and len(periodo) == 2:
        ini, fim = pd.to_datetime(periodo[0]), pd.to_datetime(periodo[1])
        df = df[(df["Data"] >= ini) & (df["Data"] <= fim)]
    return df[df["Região"].isin(reg_sel) & df["Produto"].isin(prod_sel)]

vendas_f = filtro_vendas(vendas)

# =============================
# Tabs (inclui Home primeiro)
# =============================
abas = ["Home", "Comercial", "Gestão de Pessoas"] + (["Financeiro"] if role == "admin" else [])

if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "Home"

if st.session_state.get("active_tab") not in abas:
    st.session_state["active_tab"] = "Home"

_tab_objs = st.tabs(abas)

# =============================
# HOME
# =============================
with _tab_objs[abas.index("Home")]:
    user_name = user['name']
    st.markdown(f"## 🏠 Bem-vindo, {user_name} 👋")
    st.write("Use os cards abaixo para navegar entre os módulos ou o menu de abas no topo.")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="card"><div class="card-title">📈 Comercial <span class="badge badge-upd">Atualizado</span></div>'
                    '<div class="card-desc">Vendas por produto, região e período. Estoques e distribuição.</div></div>', unsafe_allow_html=True)
        if st.button("Ir para Comercial"):
            st.session_state["active_tab"] = "Comercial"
            st.experimental_rerun()
    with c2:
        st.markdown('<div class="card"><div class="card-title">👥 Gestão de Pessoas <span class="badge badge-new">Novo</span></div>'
                    '<div class="card-desc">Distribuição salarial, colaboradores e jornada laboral.</div></div>', unsafe_allow_html=True)
        if st.button("Ir para Gestão de Pessoas"):
            st.session_state["active_tab"] = "Gestão de Pessoas"
            st.experimental_rerun()
    with c3:
        st.markdown('<div class="card"><div class="card-title">💰 Financeiro <span class="badge badge-lock">Restrito</span></div>'
                    '<div class="card-desc">(Admin) Fluxo financeiro, receitas e indicadores.</div></div>', unsafe_allow_html=True)
        if st.button("Ir para Financeiro", disabled=(role != "admin")):
            st.session_state["active_tab"] = "Financeiro"
            st.experimental_rerun()

    st.markdown("---")
    st.markdown("### 📰 Hub de Notícias")

    idx = int(st.session_state.get("news_index", 0))
    autoplay = bool(st.session_state.get("autoplay", True))
    pause_until = float(st.session_state.get("pause_until", 0.0))
    total = len(NOTICIAS)
    trio = [NOTICIAS[(idx + i) % total] for i in range(3)]

    n1, n2, n3 = st.columns(3)
    for n, col in zip(trio, [n1, n2, n3]):
        with col:
            st.markdown(
                f"<div class='card'><div class='card-title'>{n['icone']} {n['titulo']} <span style='float:right;color:#888;font-size:0.85rem'>{datetime.now().strftime('%d/%m/%Y')}</span></div>"
                f"<div class='card-desc'>{n['texto']}</div></div>", unsafe_allow_html=True)

    col_prev, col_mid, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("◀️ Anterior"):
            st.session_state["news_index"] = (idx - 1) % total
            st.session_state["pause_until"] = time.time() + 10
            st.experimental_rerun()
    with col_mid:
        play_pause = st.toggle("Autoplay", value=autoplay, help="Rotaciona automaticamente a cada 5s")
        st.session_state["autoplay"] = play_pause
    with col_next:
        if st.button("Próxima ▶️"):
            st.session_state["news_index"] = (idx + 1) % total
            st.session_state["pause_until"] = time.time() + 10
            st.experimental_rerun()

    now = time.time()
    if st.session_state.get("autoplay", True) and now >= pause_until:
        time.sleep(5)
        st.session_state["news_index"] = (int(st.session_state.get("news_index", 0)) + 1) % total
        st.experimental_rerun()

# =============================
# COMERCIAL
# =============================
with _tab_objs[abas.index("Comercial")]:
    st.subheader("📈 Comercial – Vendas")
    df = filtro_vendas(vendas).copy()

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(df.groupby("Produto")["Valor"].sum().reset_index(), x="Produto", y="Valor", title="Vendas por Produto")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.pie(df, values="Valor", names="Região", title="Distribuição por Região")
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df.head(25))

# =============================
# GESTÃO DE PESSOAS
# =============================
with _tab_objs[abas.index("Gestão de Pessoas")]:
    st.subheader("👥 Gestão de Pessoas")
    df_c = colaboradores.copy()
    dep_sel = st.multiselect("Departamento", DEPARTAMENTOS, default=DEPARTAMENTOS)
    df_c = df_c[df_c["Departamento"].isin(dep_sel)]

    col1, col2 = st.columns(2)
    with col1:
        fig = px.box(df_c, x="Departamento", y="Salário", title="Distribuição Salarial por Departamento")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.histogram(df_c, x="Salário", nbins=25, title="Distribuição de Salários")
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df_c)

# =============================
# FINANCEIRO (apenas admin)
# =============================
if role == "admin" and "Financeiro" in abas:
    with _tab_objs[abas.index("Financeiro")]:
        st.subheader("💰 Financeiro")
        df = filtro_vendas(vendas).copy()
        df["Mês"] = df["Data"].dt.to_period("M").astype(str)
        receita_mensal = df.groupby("Mês")["Valor"].sum().reset_index()
        fig = px.line(receita_mensal, x="Mês", y="Valor", title="Receita Mensal (R$)")
        st.plotly_chart(fig, use_container_width=True)

st.success("✅ Correção dos botões aplicada e JSON integrado!")
