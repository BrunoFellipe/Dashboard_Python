"""
Space Dashboard v4.3.1 — Streamlit
- Login via usuarios.json (raiz) + roles (admin/guest)
- Notícias via noticias.json (raiz)
- Barra 'Space' fixa (sempre no topo), profundidade, tema adaptativo
- Logout como texto clicável (estilizado)
- Páginas com múltiplos gráficos (Comercial, RH, Financeiro)

Requisitos:
    pip install streamlit pandas numpy pyarrow plotly faker
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from faker import Faker
from datetime import datetime
import json, os

# =============================
# CONFIG GERAL + TEMA
# =============================
st.set_page_config(page_title="Space Dashboard", layout="wide")

base_theme = (st.get_option("theme.base") or "light").lower()
is_dark = base_theme == "dark"

BG       = "#1e293b" if is_dark else "#ffffff"
TEXT     = "#f8fafc" if is_dark else "#0f172a"
PRIMARY  = "#ffffff" if is_dark else "#1a56db"   # 'Space' em branco no escuro, azul no claro
BORDER   = "#334155" if is_dark else "#e5e7eb"
HOVER    = "#475569" if is_dark else "#f1f5f9"
SHADOW   = "0 3px 12px rgba(0,0,0,0.25)" if is_dark else "0 3px 12px rgba(0,0,0,0.08)"

# =============================
# CSS GLOBAL
# =============================
st.markdown(f"""
<style>
:root {{
  --bg:{BG}; --text:{TEXT}; --primary:{PRIMARY}; --border:{BORDER}; --hover:{HOVER};
}}

html, body [data-testid="stAppViewContainer"] {{
  background: var(--bg); color: var(--text);
}}

.navbar {{
  position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
  background: linear-gradient(to bottom, var(--bg), var(--bg));
  border-bottom: 1px solid var(--border);
  box-shadow: {SHADOW};
  padding: .6rem 1.2rem;
}}
.navbar-inner {{
  display: flex; align-items: center; justify-content: space-between;
}}
.nav-left {{
  font-weight: 800; font-size: 1.2rem; color: var(--primary);
}}
.nav-center {{
  display: flex; gap: .5rem; justify-content: center;
}}
.nav-right {{
  display: flex; align-items: center; gap: .6rem; color: var(--text); font-weight: 500;
}}
.link-like > button {{
  background: transparent; border: none; color: var(--text);
  padding: 0; margin: 0; font-weight: 600; cursor: pointer;
}}
.link-like > button:hover {{ color: var(--primary); text-decoration: underline; }}
.separator {{ color: #9ca3af; }}
.spacer {{ height: 64px; }} /* espaço para a navbar fixa */

.stButton > button {{
  background: transparent; color: var(--text);
  border: 1px solid var(--border); border-radius: 8px;
  padding: .35rem .75rem; font-weight: 600; transition: all .2s;
}}
.stButton > button:hover {{ background: var(--hover); color: var(--primary); border-color: var(--primary); }}

.card {{
  border: 1px solid var(--border); border-radius: 10px; padding: 1rem; margin-bottom: 1rem;
  box-shadow: 0 2px 6px rgba(0,0,0,0.05); background: var(--bg);
}}
.card-title {{ font-weight: 700; font-size: 1rem; color: var(--text); }}
.card-desc  {{ color: #94a3b8; font-size: .9rem; }}
</style>
""", unsafe_allow_html=True)

# =============================
# HELPERS JSON
# =============================
def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.warning(f"Erro ao ler {path}: {e}. Usando dados padrão.")
    return default

# =============================
# CARREGA USUÁRIOS E NOTÍCIAS (ARQUIVOS NA RAIZ)
# =============================
DEFAULT_USERS = [
    {"username": "admin", "password": "12345", "name": "Admin", "role": "admin"},
    {"username": "guest", "password": "guest123", "name": "Convidado", "role": "guest"}
]
USERS = load_json("usuarios.json", DEFAULT_USERS)

DEFAULT_NEWS = [
    {"titulo":"Novidade!","texto":"Agora o catálogo de clientes está ligado diretamente ao Oracle Cloud.","icone":"🆕","data":datetime.now().strftime("%d/%m/%Y")},
    {"titulo":"Novo Dashboard!","texto":"Acesse os dados de Jornada Laboral na aba Gestão de Pessoas.","icone":"📊","data":datetime.now().strftime("%d/%m/%Y")},
    {"titulo":"Treinamento!","texto":"Participe do novo bootcamp de Data & Analytics.","icone":"🎓","data":datetime.now().strftime("%d/%m/%Y")}
]
NEWS = load_json("noticias.json", DEFAULT_NEWS)

# =============================
# ESTADO
# =============================
if "auth" not in st.session_state:
    st.session_state.auth = {"logged": False, "user": None}
if "page" not in st.session_state:
    st.session_state.page = "Home"

# =============================
# LOGIN
# =============================
def login_view():
    # mostra só o título Space no topo (sem navegação)
    st.markdown(f"""
    <div class="navbar"><div class="navbar-inner">
      <div class="nav-left">Space</div>
      <div class="nav-right"></div>
    </div></div>
    <div class="spacer"></div>
    """, unsafe_allow_html=True)

    st.markdown("### 🔐 Acesso ao Space")
    u = st.text_input("Usuário")
    p = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        user = next((x for x in USERS if x["username"]==u and x["password"]==p), None)
        if user:
            st.session_state.auth = {"logged": True, "user": user}
            st.session_state.page = "Home"
            st.success(f"Bem-vindo(a), {user['name']}!")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos.")

if not st.session_state.auth["logged"]:
    login_view()
    st.stop()

user = st.session_state.auth["user"]
is_admin = (user.get("role") == "admin")

# =============================
# NAVBAR FIXA (com logout texto clicável)
# =============================
def navbar():
    st.markdown('<div class="navbar"><div class="navbar-inner">', unsafe_allow_html=True)
    col_left, col_center, col_right = st.columns([2, 7, 3])
    with col_left:
        st.markdown('<div class="nav-left">Space</div>', unsafe_allow_html=True)

    with col_center:
        cols = st.columns([1, 1.4, 1.8, 1.4])
        pages = [("🏠 Home", "Home"), ("📈 Comercial", "Comercial"), ("👥 Gestão de Pessoas", "Gestão de Pessoas")]
        if is_admin:
            pages.append(("💰 Financeiro", "Financeiro"))
        for i, (label, page) in enumerate(pages):
            with cols[i]:
                # botão normal (aplica estilo global)
                if st.button(label, key=f"btn_{page}"):
                    st.session_state.page = page
                    st.rerun()

    with col_right:
        c_a, c_sep, c_user = st.columns([1.2, 0.3, 1.5])
        with c_a:
            # botão estilizado como link (texto clicável)
            st.markdown('<div class="link-like">', unsafe_allow_html=True)
            if st.button("🚪 Sair", key="btn_logout"):
                st.session_state.clear()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c_sep:
            st.markdown('<div class="nav-right"><span class="separator">|</span></div>', unsafe_allow_html=True)
        with c_user:
            st.markdown(f'<div class="nav-right">👤 {user["name"]}</div>', unsafe_allow_html=True)

    st.markdown('</div></div><div class="spacer"></div>', unsafe_allow_html=True)

navbar()

# =============================
# MOCK DE DADOS
# =============================
fake = Faker("pt_BR")
np.random.seed(42)

vendas = pd.DataFrame({
    "Data": pd.date_range("2024-01-01", periods=500),
    "Produto": np.random.choice(["Produto A","Produto B","Produto C","Produto D"], 500),
    "Região": np.random.choice(["Norte","Nordeste","Centro-Oeste","Sudeste","Sul"], 500),
    "Valor": np.random.uniform(500, 10000, 500),
})
colaboradores = pd.DataFrame({
    "Nome": [fake.name() for _ in range(300)],
    "Departamento": np.random.choice(["Comercial","Financeiro","RH","TI"], 300),
    "Salário": np.random.uniform(2500, 18000, 300).round(2),
})

# =============================
# PÁGINAS
# =============================
def page_home():
    st.markdown("## Bem-vindo ao Space 👋")
    st.write("Explore os dashboards e acompanhe os indicadores estratégicos da organização.")
    st.markdown("---")

    c1, c2, c3 = st.columns(3)
    for col, titulo, desc in zip(
        [c1, c2, c3],
        ["📈 Comercial", "👥 Gestão de Pessoas", "💰 Financeiro"],
        ["Monitoramento de vendas e performance.", "Métricas de pessoas e salários.", "Receitas, despesas e margens (Admin)."]
    ):
        with col:
            st.markdown(
                f"<div class='card'><div class='card-title'>{titulo}</div>"
                f"<div class='card-desc'>{desc}</div></div>",
                unsafe_allow_html=True
            )

    st.markdown("---")
    st.subheader("📰 Hub de Notícias")
    ncols = st.columns(3)
    for n, col in zip(NEWS[:3], ncols):
        with col:
            data_txt = n.get("data", datetime.now().strftime("%d/%m/%Y"))
            st.markdown(
                f"<div class='card'><div class='card-title'>{n.get('icone','📰')} {n.get('titulo','Sem título')}"
                f"<span style='float:right;font-size:0.85rem;color:#94a3b8'>{data_txt}</span></div>"
                f"<div class='card-desc'>{n.get('texto','')}</div></div>",
                unsafe_allow_html=True
            )

def page_comercial():
    st.markdown("## 📈 Comercial")
    st.caption("Análise de vendas por produto, região e tempo.")
    df = vendas.copy()
    df["Mês"] = df["Data"].dt.to_period("M").astype(str)

    # KPIs
    k1, k2, k3 = st.columns(3)
    k1.metric("Receita Total", f"R$ {df['Valor'].sum():,.2f}".replace(",", "@").replace(".", ",").replace("@", "."))
    k2.metric("Pedidos", f"{len(df):,}".replace(",", "."))
    k3.metric("Ticket Médio", f"R$ {df['Valor'].mean():,.2f}".replace(",", "@").replace(".", ",").replace("@", "."))

    # Gráficos
    st.plotly_chart(px.bar(df, x="Produto", y="Valor", color="Região", title="Vendas por Produto e Região"), use_container_width=True)
    st.plotly_chart(px.pie(df, values="Valor", names="Região", title="Participação por Região"), use_container_width=True)
    st.plotly_chart(px.line(df.groupby("Mês")["Valor"].sum().reset_index(), x="Mês", y="Valor", title="Tendência Mensal de Vendas"), use_container_width=True)

    pivot = df.pivot_table(values="Valor", index="Região", columns="Produto", aggfunc="sum").fillna(0)
    st.plotly_chart(px.imshow(pivot, title="Heatmap - Valor por Região e Produto", color_continuous_scale="Blues"), use_container_width=True)

def page_rh():
    st.markdown("## 👥 Gestão de Pessoas")
    st.caption("Distribuição salarial e perfil de colaboradores.")
    df = colaboradores.copy()
    st.plotly_chart(px.box(df, x="Departamento", y="Salário", title="Distribuição Salarial por Departamento"), use_container_width=True)
    st.plotly_chart(px.histogram(df, x="Salário", nbins=28, title="Histograma de Salários"), use_container_width=True)
    media_dep = df.groupby("Departamento")["Salário"].mean().reset_index()
    st.plotly_chart(px.bar(media_dep, x="Departamento", y="Salário", title="Média Salarial por Departamento"), use_container_width=True)

def page_fin():
    if not is_admin:
        st.warning("Acesso restrito a administradores.")
        return
    st.markdown("## 💰 Financeiro")
    st.caption("Receita, despesa e margem por mês.")

    df = vendas.copy()
    df["Mês"] = df["Data"].dt.to_period("M").astype(str)
    receita = df.groupby("Mês")["Valor"].sum().reset_index()
    despesa = receita.copy()
    despesa["Valor"] = receita["Valor"] * np.random.uniform(0.6, 0.95, len(receita))

    st.plotly_chart(px.line(receita, x="Mês", y="Valor", title="Receita Mensal (R$)"), use_container_width=True)

    comp = pd.DataFrame({"Mês": receita["Mês"], "Receita": receita["Valor"], "Despesa": despesa["Valor"]})
    st.plotly_chart(px.bar(comp, x="Mês", y=["Receita", "Despesa"], barmode="group", title="Receita vs Despesa"), use_container_width=True)

    comp["Margem %"] = ((comp["Receita"] - comp["Despesa"]) / comp["Despesa"]) * 100
    st.plotly_chart(px.area(comp, x="Mês", y="Margem %", title="Margem (%)"), use_container_width=True)

# =============================
# ROTEAMENTO
# =============================
page = st.session_state.page
if page == "Home":
    page_home()
elif page == "Comercial":
    page_comercial()
elif page == "Gestão de Pessoas":
    page_rh()
elif page == "Financeiro":
    page_fin()
else:
    st.session_state.page = "Home"
    st.rerun()
