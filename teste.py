"""
Dashboard Corporativo – Contexto Brasileiro (Streamlit)

Requisitos:
    pip install streamlit pandas numpy pyarrow plotly faker

Execução:
    streamlit run app.py

Notas desta versão:
- Removida a dependência do `streamlit-authenticator` (causava erro no Cloud com `Hasher`).
- Implementada autenticação simples via formulário (admin/12345 e guest/guest123) para protótipo.
- Fácil migrar depois para SSO/OAuth ou `streamlit-authenticator` (deixo comentários ao final).
"""

from __future__ import annotations
import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from faker import Faker
from datetime import datetime, timedelta

# =============================
# Configuração inicial
# =============================
st.set_page_config(page_title="Dashboard Corporativo", layout="wide")
st.title("📊 Dashboard Corporativo – Brasil")

fake = Faker('pt_BR')
np.random.seed(42)

# =============================
# Autenticação simples (protótipo sem libs externas)
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
                st.success(f"Bem-vindo, {creds['name']}!")
            else:
                st.error("Usuário ou senha inválidos.")
        st.stop()
    else:
        user = st.session_state.auth["user"]
        st.write(f"Usuário logado: **{user['name']}** ({user['role']})")
        if st.button("Sair"):
            st.session_state.auth = {"logged": False, "user": None}
            st.experimental_rerun()

user = st.session_state.auth["user"]

# =============================
# Dados e constantes
# =============================
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
ESTADOS_POR_REGIAO = {
    "Norte": ["AM", "PA", "RO", "RR", "AP", "AC", "TO"],
    "Nordeste": ["BA", "PE", "CE", "MA", "PB", "SE", "RN", "AL", "PI"],
    "Centro-Oeste": ["GO", "MT", "MS", "DF"],
    "Sudeste": ["SP", "RJ", "MG", "ES"],
    "Sul": ["PR", "SC", "RS"],
}
PRODUTOS = ["Produto A", "Produto B", "Produto C", "Produto D", "Produto E"]
CATEGORIAS = ["Linha Casa", "Linha Escritório", "Linha Premium"]
CARGOS = ["Analista", "Senior", "Coordenador", "Gerente", "Estagiário"]
DEPARTAMENTOS = ["Comercial", "Financeiro", "RH", "TI", "Operações", "Logística"]

# =============================
# Geração de dados sintéticos (sem Parquet para simplificar no Cloud)
# =============================

def gen_colaboradores(n=300):
    rng = np.random.default_rng(42)
    dados = []
    for i in range(n):
        nome = fake.name()
        dep = rng.choice(DEPARTAMENTOS)
        cargo = rng.choice(CARGOS)
        salario = float(max(1800, round(rng.normal(7000, 2500), 2)))
        idade = int(rng.integers(19, 62))
        tempo_casa_meses = int(rng.integers(1, 120))
        regiao = rng.choice(REGIOES)
        estado = rng.choice(ESTADOS_POR_REGIAO[regiao])
        dados.append({
            "id_colab": i + 1,
            "nome": nome,
            "departamento": dep,
            "cargo": cargo,
            "salario": salario,
            "idade": idade,
            "tempo_casa_meses": tempo_casa_meses,
            "regiao": regiao,
            "estado": estado,
        })
    return pd.DataFrame(dados)


def gen_vendedores(df_colab: pd.DataFrame, n=50):
    cand = df_colab[df_colab["departamento"].isin(["Comercial", "Operações"])]["nome"].unique()
    vendedores = list(cand)[:n] if len(cand) >= n else list(cand) + [fake.name() for _ in range(n - len(cand))]
    return pd.DataFrame({"vendedor": vendedores[:n]})


def gen_vendas(n=15000, inicio="2024-01-01", fim="2025-10-01", df_vendedores=None):
    dates = pd.date_range(inicio, fim, freq="D")
    dias = np.random.choice(dates, size=n)
    regioes = np.random.choice(REGIOES, n)
    estados = [np.random.choice(ESTADOS_POR_REGIAO[r]) for r in regioes]
    produtos = np.random.choice(PRODUTOS, n)
    categorias = [np.random.choice(CATEGORIAS) for _ in range(n)]
    quantidade = np.random.randint(1, 20, n)
    preco_base = {"Produto A":80, "Produto B":120, "Produto C":200, "Produto D":300, "Produto E":500}
    valor_unit = np.array([preco_base[p]*np.random.uniform(0.9,1.2) for p in produtos]).round(2)
    desconto = np.random.choice([0, 0.05, 0.1, 0.15], size=n, p=[0.6,0.2,0.15,0.05])
    valor_total = (quantidade*valor_unit*(1-desconto)).round(2)
    margem_pct = np.random.uniform(0.15, 0.45, n)
    lucro = (valor_total*margem_pct).round(2)
    vendedores = np.random.choice(df_vendedores["vendedor"].values, n) if df_vendedores is not None else [fake.name() for _ in range(n)]
    clientes = [fake.company() for _ in range(n)]
    df = pd.DataFrame({
        "data": pd.to_datetime(dias),
        "ano": pd.to_datetime(dias).year,
        "mes": pd.to_datetime(dias).month,
        "regiao": regioes,
        "estado": estados,
        "produto": produtos,
        "categoria": categorias,
        "quantidade": quantidade,
        "valor_unit": valor_unit,
        "desconto": desconto,
        "valor_total": valor_total,
        "margem_pct": margem_pct,
        "lucro": lucro,
        "vendedor": vendedores,
        "cliente": clientes,
    }).sort_values("data").reset_index(drop=True)
    return df


def gen_estoque(df_vendas: pd.DataFrame):
    base = df_vendas.groupby(["produto", "estado"], as_index=False)["quantidade"].sum()
    base["estoque_atual"] = (base["quantidade"]*np.random.uniform(0.5,2.0,len(base))).astype(int)
    base["ponto_pedido"] = (base["quantidade"]*0.3).astype(int).clip(lower=20)
    base["giro_mensal"] = np.random.uniform(0.5,4.0,len(base)).round(2)
    return base.drop(columns=["quantidade"]) 


def gen_jornada(df_colab: pd.DataFrame, semanas=60):
    registros = []
    start_date = datetime(2024, 1, 1)
    for _, row in df_colab.iterrows():
        h_base = np.random.randint(36, 44)
        for w in range(semanas):
            dt = start_date + timedelta(weeks=w)
            extras = max(0, int(np.random.normal(4, 3))) if row["departamento"] in ["Comercial", "Operações", "Logística"] else max(0, int(np.random.normal(2, 2)))
            faltas = max(0, int(np.random.normal(0.2, 0.6)))
            registros.append({
                "id_colab": row["id_colab"],
                "nome": row["nome"],
                "departamento": row["departamento"],
                "semana": w + 1,
                "data_ref": dt,
                "horas_semanais": h_base,
                "horas_extras": extras,
                "faltas": faltas,
            })
    return pd.DataFrame(registros)


def gen_financeiro(df_vendas: pd.DataFrame):
    vendas_m = df_vendas.groupby(pd.Grouper(key="data", freq="MS"))["valor_total"].sum().reset_index()
    vendas_m["tipo"] = "Receita"
    periodos = vendas_m["data"].tolist()
    despesas = []
    for dt in periodos:
        despesas += [
            {"data": dt, "conta": "Operacional", "valor": float(np.random.uniform(120_000, 220_000)), "tipo": "Despesa"},
            {"data": dt, "conta": "Pessoal", "valor": float(np.random.uniform(200_000, 350_000)), "tipo": "Despesa"},
            {"data": dt, "conta": "Logística", "valor": float(np.random.uniform(60_000, 140_000)), "tipo": "Despesa"},
            {"data": dt, "conta": "Marketing", "valor": float(np.random.uniform(40_000, 100_000)), "tipo": "Despesa"},
        ]
    df_rec = vendas_m.rename(columns={"valor_total": "valor"})[["data", "valor", "tipo"]]
    df_desp = pd.DataFrame(despesas)
    return df_rec, df_desp


def gen_operacoes(df_vendas: pd.DataFrame):
    base = df_vendas.copy(); base["mes_ref"] = base["data"].dt.to_period("M").dt.to_timestamp()
    prod = base.groupby(["mes_ref", "estado"], as_index=False).agg(
        qtd_produzida=("quantidade", "sum"),
        defeitos=("produto", lambda s: int(np.random.uniform(0.5, 3.5) * len(s)))
    )
    prod["eficiencia_pct"] = (100 - prod["defeitos"] / (prod["qtd_produzida"].clip(lower=1)) * 100).clip(50, 99.5).round(2)
    log = base.groupby(["mes_ref", "estado"], as_index=False).agg(
        pedidos=("cliente", "count"),
        custo_frete=("valor_total", lambda s: float(np.random.uniform(0.03, 0.08) * s.sum())),
    )
    log["tempo_medio_entrega_dias"] = np.random.uniform(2.0, 8.0, len(log)).round(2)
    return prod, log

# Cache para não regenerar a cada interação
@st.cache_data(show_spinner=False)
def get_data():
    df_colab = gen_colaboradores(300)
    df_vendedores = gen_vendedores(df_colab, 50)
    df_vendas = gen_vendas(15000, df_vendedores=df_vendedores)
    df_estoque = gen_estoque(df_vendas)
    df_jornada = gen_jornada(df_colab, 60)
    df_rec, df_desp = gen_financeiro(df_vendas)
    df_prod, df_log = gen_operacoes(df_vendas)
    return {
        "colab": df_colab,
        "vend": df_vendedores,
        "vendas": df_vendas,
        "estoque": df_estoque,
        "jornada": df_jornada,
        "rec": df_rec,
        "desp": df_desp,
        "prod": df_prod,
        "log": df_log,
    }

dfs = get_data()

# =============================
# Filtros globais
# =============================
min_date = dfs["vendas"]["data"].min().date(); max_date = dfs["vendas"]["data"].max().date()
with st.sidebar:
    st.header("🔎 Filtros Globais")
    periodo = st.date_input("Período", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    regiao_sel = st.multiselect("Regiões", REGIOES, default=REGIOES)
    produtos_sel = st.multiselect("Produtos", PRODUTOS, default=PRODUTOS)
    categoria_sel = st.multiselect("Categorias", CATEGORIAS, default=CATEGORIAS)


def filtrar_vendas(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(periodo, (list, tuple)) and len(periodo) == 2:
        ini, fim = pd.to_datetime(periodo[0]), pd.to_datetime(periodo[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df = df[(df["data"] >= ini) & (df["data"] <= fim)]
    return df[df["regiao"].isin(regiao_sel) & df["produto"].isin(produtos_sel) & df["categoria"].isin(categoria_sel)]

# =============================
# KPIs topo
# =============================
df_vendas_f = filtrar_vendas(dfs["vendas"]) 
receita_total = df_vendas_f["valor_total"].sum(); lucro_total = df_vendas_f["lucro"].sum(); pedidos = len(df_vendas_f)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Receita (R$)", f"{receita_total:,.2f}".replace(',', '@').replace('.', ',').replace('@', '.'))
col2.metric("Lucro (R$)", f"{lucro_total:,.2f}".replace(',', '@').replace('.', ',').replace('@', '.'))
col3.metric("Pedidos", f"{pedidos:,}".replace(',', '.'))
col4.metric("Ticket médio (R$)", f"{(receita_total/max(pedidos,1)):,.2f}".replace(',', '@').replace('.', ',').replace('@', '.'))

# =============================
# Abas
# =============================
role = user["role"]
abas = ["Comercial", "Gestão de Pessoas"] + (["Financeiro", "Operações"] if role == "admin" else [])
main_tabs = st.tabs(abas)

# -------- Comercial --------
with main_tabs[abas.index("Comercial")]:
    sub = st.tabs(["Vendas", "Estoque"])
    with sub[0]:
        st.subheader("📈 Vendas")
        df = df_vendas_f
        c1, c2 = st.columns(2)
        with c1:
            serie = df.groupby(pd.Grouper(key="data", freq="MS"))["valor_total"].sum().reset_index()
            fig = px.line(serie, x="data", y="valor_total", title="Receita Mensal (R$)")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            lucro_prod = df.groupby("produto")["lucro"].sum().reset_index().sort_values("lucro", ascending=False)
            fig = px.bar(lucro_prod, x="produto", y="lucro", title="Lucro por Produto (R$)")
            st.plotly_chart(fig, use_container_width=True)
        st.expander("📄 Vendas filtradas", expanded=False).dataframe(df)
    with sub[1]:
        st.subheader("📦 Estoque")
        df_e = dfs["estoque"].copy()
        prod_f = st.multiselect("Filtrar produtos", PRODUTOS, default=PRODUTOS)
        df_e = df_e[df_e["produto"].isin(prod_f)]
        c1, c2 = st.columns(2)
        with c1:
            fig = px.bar(df_e.groupby("produto", as_index=False)["estoque_atual"].sum(), x="produto", y="estoque_atual", title="Estoque Atual por Produto")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            baixo = df_e[df_e["estoque_atual"] < df_e["ponto_pedido"]]
            pct_baixo = (len(baixo)/max(len(df_e),1))*100
            st.metric("SKUs em risco (%)", f"{pct_baixo:.1f}%")
            st.dataframe(baixo.sort_values(["produto","estado"]))

# -------- Gestão de Pessoas --------
with main_tabs[abas.index("Gestão de Pessoas")]:
    sub = st.tabs(["Jornada Laboral", "Colaboradores"])
    with sub[0]:
        st.subheader("🕒 Jornada Laboral")
        df_j = dfs["jornada"].copy()
        deps = sorted(dfs["colab"]["departamento"].unique())
        dep_sel = st.multiselect("Departamentos", deps, default=deps)
        df_j = df_j[df_j["departamento"].isin(dep_sel)]
        c1, c2 = st.columns(2)
        with c1:
            horas = df_j.groupby(pd.Grouper(key="data_ref", freq="MS"))["horas_extras"].mean().reset_index()
            fig = px.line(horas, x="data_ref", y="horas_extras", title="Horas Extras – Média Mensal")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            faltas = df_j.groupby("departamento")["faltas"].sum().reset_index()
            fig = px.bar(faltas, x="departamento", y="faltas", title="Faltas acumuladas por Departamento")
            st.plotly_chart(fig, use_container_width=True)
        st.expander("📄 Lançamentos de Jornada", expanded=False).dataframe(df_j)
    with sub[1]:
        st.subheader("👥 Colaboradores")
        df_c = dfs["colab"].copy()
        dep = st.multiselect("Departamento", sorted(df_c["departamento"].unique()))
        if dep:
            df_c = df_c[df_c["departamento"].isin(dep)]
        c1, c2 = st.columns(2)
        with c1:
            fig = px.histogram(df_c, x="salario", nbins=30, title="Distribuição Salarial")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.box(df_c, x="departamento", y="salario", title="Salário por Departamento")
            st.plotly_chart(fig, use_container_width=True)
        st.expander("📄 Base de Colaboradores", expanded=False).dataframe(df_c)

# -------- Financeiro (admin) --------
if "Financeiro" in abas:
    with main_tabs[abas.index("Financeiro")]:
        sub = st.tabs(["Receitas e Despesas", "Indicadores"])
        with sub[0]:
            st.subheader("💰 Receitas e Despesas")
            df_rec = dfs["rec"].copy(); df_desp = dfs["desp"].copy()
            if isinstance(periodo, (list, tuple)) and len(periodo) == 2:
                ini, fim = pd.to_datetime(periodo[0]), pd.to_datetime(periodo[1])
                df_rec = df_rec[(df_rec["data"] >= ini) & (df_rec["data"] <= fim)]
                df_desp = df_desp[(df_desp["data"] >= ini) & (df_desp["data"] <= fim)]
            rec_m = df_rec.groupby("data")["valor"].sum().reset_index()
            desp_m = df_desp.groupby("data")["valor"].sum().reset_index()
            fluxo = rec_m.merge(desp_m, on="data", how="outer", suffixes=("_rec","_desp")).fillna(0)
            fluxo["saldo"] = fluxo["valor_rec"] - fluxo["valor_desp"]
            fluxo["saldo_acumulado"] = fluxo["saldo"].cumsum()
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(px.line(fluxo, x="data", y=["valor_rec","valor_desp"], title="Receitas vs Despesas"), use_container_width=True)
            with c2:
                st.plotly_chart(px.area(fluxo, x="data", y="saldo_acumulado", title="Saldo Acumulado"), use_container_width=True)
            st.expander("📄 Tabela de Fluxo", expanded=False).dataframe(fluxo)
        with sub[1]:
            st.subheader("📌 Indicadores")
            df_rec = dfs["rec"]; df_desp = dfs["desp"]
            rec_total = df_rec["valor"].sum(); desp_total = df_desp["valor"].sum()
            margem = (rec_total - desp_total) / max(rec_total, 1)
            c1, c2, c3 = st.columns(3)
            c1.metric("Receita (R$)", f"{rec_total:,.2f}".replace(',', '@').replace('.', ',').replace('@', '.'))
            c2.metric("Despesa (R$)", f"{desp_total:,.2f}".replace(',', '@').replace('.', ',').replace('@', '.'))
            c3.metric("Margem líquida", f"{margem*100:,.1f}%")

# -------- Operações (admin) --------
if "Operações" in abas:
    with main_tabs[abas.index("Operações")]:
        sub = st.tabs(["Produção", "Logística"])
        with sub[0]:
            st.subheader("🏭 Produção")
            df_p = dfs["prod"].copy()
            estados = sorted(df_p["estado"].unique())
            est_sel = st.multiselect("Estados", estados, default=estados[:8])
            df_p = df_p[df_p["estado"].isin(est_sel)]
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(px.line(df_p, x="mes_ref", y="qtd_produzida", color="estado", title="Produção Mensal por Estado"), use_container_width=True)
            with c2:
                st.plotly_chart(px.bar(df_p, x="estado", y="eficiencia_pct", title="Eficiência (%) por Estado"), use_container_width=True)
            st.expander("📄 Tabela de Produção", expanded=False).dataframe(df_p)
        with sub[1]:
            st.subheader("🚚 Logística")
            df_l = dfs["log"].copy()
            estados = sorted(df_l["estado"].unique())
            est_sel = st.multiselect("Estados", estados, default=estados[:8], key="log_est")
            df_l = df_l[df_l["estado"].isin(est_sel)]
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(px.bar(df_l, x="estado", y="pedidos", title="Pedidos Entregues por Estado"), use_container_width=True)
            with c2:
                st.plotly_chart(px.line(df_l, x="mes_ref", y="tempo_medio_entrega_dias", color="estado", title="Tempo Médio de Entrega (dias)"), use_container_width=True)
            st.expander("📄 Tabela de Logística", expanded=False).dataframe(df_l)

# =============================
# (Opcional) Próximos passos para auth segura
# =============================
"""
Para produção: usar SSO (Google/Azure AD/Okta) ou `streamlit-authenticator` com hashes em YAML.
- Se optar por `streamlit-authenticator`, gere hashes localmente e carregue de um arquivo `config.yaml`.
- No Streamlit Cloud, armazene segredos em `.streamlit/secrets.toml`.
"""

# =============================
# Testes simples (sanidade)
# =============================
if __name__ == "__main__":
    d = get_data()
    assert len(d["vendas"]) >= 10000
    assert {"valor_total", "lucro"}.issubset(d["vendas"].columns)
    assert d["rec"]["valor"].sum() > 0 and d["desp"]["valor"].sum() > 0
    print("✓ Sanidade OK. Rode: streamlit run app.py")
