"""
Dashboard Corporativo – Contexto Brasileiro (Streamlit)

Requisitos (instalar no terminal):
    pip install streamlit pandas numpy pyarrow plotly faker

Como executar:
    streamlit run app.py

Observações:
- Gera um "banco" fictício grande em Parquet na pasta ./data (primeira execução).
- Usa Plotly para gráficos interativos e filtros dinâmicos por período, região, produto, vendedor, departamento etc.
- Estrutura de abas: Comercial (Vendas/Estoque), Gestão de Pessoas (Jornada/Colaboradores), Financeiro (Receitas e Despesas/Indicadores), Operações (Produção/Logística).
- Caso deseje conectar APIs reais (ex.: BCB/IBGE), há blocos comentados de exemplo no final.
"""

from __future__ import annotations
import os
import json
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
from faker import Faker

# =============================
# Configuração Streamlit
# =============================
st.set_page_config(page_title="Dashboard Corporativo", layout="wide")
st.title("📊 Dashboard Corporativo – Brasil")

# =============================
# Constantes e utilitários
# =============================
DATA_DIR = "data"
SEED = 42
np.random.seed(SEED)
fake = Faker("pt_BR")

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
# Geração de Dados Sintéticos (Parquet)
# =============================

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _rand_choice(seq, n):
    return np.random.choice(seq, n)


def gerar_colaboradores(n=300) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    dados = []
    for i in range(n):
        nome = fake.name()
        dep = rng.choice(DEPARTAMENTOS)
        cargo = rng.choice(CARGOS)
        salario = float(rng.normal(7000, 2500))
        salario = max(1800, round(salario, 2))
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
    df = pd.DataFrame(dados)
    return df


def gerar_vendedores(df_colab: pd.DataFrame, n=40) -> pd.DataFrame:
    # Seleciona nomes do Comercial/Operações para vendedores
    candidatos = df_colab[df_colab["departamento"].isin(["Comercial", "Operações"])]["nome"].unique()
    vendedores = list(candidatos)[:n] if len(candidatos) >= n else list(candidatos)
    if len(vendedores) < n:
        # completa com nomes fake adicionais
        vendedores += [fake.name() for _ in range(n - len(vendedores))]
    return pd.DataFrame({"vendedor": vendedores[:n]})


def gerar_vendas(n=15000, inicio="2024-01-01", fim="2025-10-01", df_vendedores: pd.DataFrame | None = None) -> pd.DataFrame:
    dates = pd.date_range(inicio, fim, freq="D")
    dias = np.random.choice(dates, size=n)
    regioes = _rand_choice(REGIOES, n)
    estados = [np.random.choice(ESTADOS_POR_REGIAO[r]) for r in regioes]
    produtos = _rand_choice(PRODUTOS, n)
    categorias = [np.random.choice(CATEGORIAS) for _ in range(n)]
    quantidade = np.random.randint(1, 20, n)
    preco_base = {
        "Produto A": 80,
        "Produto B": 120,
        "Produto C": 200,
        "Produto D": 300,
        "Produto E": 500,
    }
    valor_unit = np.array([preco_base[p] * np.random.uniform(0.9, 1.2) for p in produtos]).round(2)
    desconto = np.random.choice([0, 0.05, 0.1, 0.15], size=n, p=[0.6, 0.2, 0.15, 0.05])
    valor_total = (quantidade * valor_unit * (1 - desconto)).round(2)
    margem_pct = np.random.uniform(0.15, 0.45, n)
    lucro = (valor_total * margem_pct).round(2)

    if df_vendedores is None or df_vendedores.empty:
        vendedores = [fake.name() for _ in range(n)]
    else:
        vendedores = np.random.choice(df_vendedores["vendedor"].values, n)

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
    })
    return df.sort_values("data").reset_index(drop=True)


def gerar_estoque(df_vendas: pd.DataFrame) -> pd.DataFrame:
    # Estoque por produto/estado (snapshot)
    base = df_vendas.groupby(["produto", "estado"], as_index=False)["quantidade"].sum()
    base["estoque_atual"] = (base["quantidade"] * np.random.uniform(0.5, 2.0, len(base))).astype(int)
    base["ponto_pedido"] = (base["quantidade"] * 0.3).astype(int).clip(lower=20)
    base["giro_mensal"] = np.random.uniform(0.5, 4.0, len(base)).round(2)
    base = base.drop(columns=["quantidade"]) 
    return base


def gerar_jornada(df_colab: pd.DataFrame, semanas=60) -> pd.DataFrame:
    # Lançamentos semanais por colaborador
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


def gerar_financeiro(df_vendas: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Receitas = somatório de vendas por mês; Despesas = sintético por centro de custo
    vendas_mensal = df_vendas.groupby(pd.Grouper(key="data", freq="MS"))["valor_total"].sum().reset_index()
    vendas_mensal["tipo"] = "Receita"

    # Despesas mensais sintéticas
    periodos = vendas_mensal["data"].tolist()
    despesas = []
    for dt in periodos:
        despesas.append({"data": dt, "conta": "Operacional", "valor": float(np.random.uniform(120_000, 220_000)), "tipo": "Despesa"})
        despesas.append({"data": dt, "conta": "Pessoal", "valor": float(np.random.uniform(200_000, 350_000)), "tipo": "Despesa"})
        despesas.append({"data": dt, "conta": "Logística", "valor": float(np.random.uniform(60_000, 140_000)), "tipo": "Despesa"})
        despesas.append({"data": dt, "conta": "Marketing", "valor": float(np.random.uniform(40_000, 100_000)), "tipo": "Despesa"})
    df_desp = pd.DataFrame(despesas)

    df_rec = vendas_mensal.rename(columns={"valor_total": "valor"})[["data", "valor", "tipo"]]
    return df_rec, df_desp


def gerar_operacoes(df_vendas: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    # Produção e Logística mensais por estado
    base = df_vendas.copy()
    base["mes_ref"] = base["data"].dt.to_period("M").dt.to_timestamp()

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


def salvar_parquet(nome: str, df: pd.DataFrame):
    ensure_data_dir()
    caminho = os.path.join(DATA_DIR, nome)
    df.to_parquet(caminho, index=False)


def carregar_ou_gerar_dados():
    ensure_data_dir()
    paths = {p: os.path.join(DATA_DIR, p) for p in [
        "colaboradores.parquet", "vendedores.parquet", "vendas.parquet",
        "estoque.parquet", "jornada.parquet", "financeiro_receitas.parquet",
        "financeiro_despesas.parquet", "producao.parquet", "logistica.parquet"
    ]}

    if not all(os.path.exists(p) for p in paths.values()):
        # Geração completa
        df_colab = gerar_colaboradores(n=300)
        df_vendedores = gerar_vendedores(df_colab, n=50)
        df_vendas = gerar_vendas(n=15000, df_vendedores=df_vendedores)
        df_estoque = gerar_estoque(df_vendas)
        df_jornada = gerar_jornada(df_colab, semanas=60)
        df_rec, df_desp = gerar_financeiro(df_vendas)
        df_prod, df_log = gerar_operacoes(df_vendas)

        salvar_parquet("colaboradores.parquet", df_colab)
        salvar_parquet("vendedores.parquet", df_vendedores)
        salvar_parquet("vendas.parquet", df_vendas)
        salvar_parquet("estoque.parquet", df_estoque)
        salvar_parquet("jornada.parquet", df_jornada)
        salvar_parquet("financeiro_receitas.parquet", df_rec)
        salvar_parquet("financeiro_despesas.parquet", df_desp)
        salvar_parquet("producao.parquet", df_prod)
        salvar_parquet("logistica.parquet", df_log)

    # Carregamento
    dfs = {
        "colab": pd.read_parquet(paths["colaboradores.parquet"]),
        "vend": pd.read_parquet(paths["vendedores.parquet"]),
        "vendas": pd.read_parquet(paths["vendas.parquet"]).assign(data=lambda d: pd.to_datetime(d["data"])) ,
        "estoque": pd.read_parquet(paths["estoque.parquet"]),
        "jornada": pd.read_parquet(paths["jornada.parquet"]).assign(data_ref=lambda d: pd.to_datetime(d["data_ref"])) ,
        "rec": pd.read_parquet(paths["financeiro_receitas.parquet"]).assign(data=lambda d: pd.to_datetime(d["data"])) ,
        "desp": pd.read_parquet(paths["financeiro_despesas.parquet"]).assign(data=lambda d: pd.to_datetime(d["data"])) ,
        "prod": pd.read_parquet(paths["producao.parquet"]).assign(mes_ref=lambda d: pd.to_datetime(d["mes_ref"])) ,
        "log": pd.read_parquet(paths["logistica.parquet"]).assign(mes_ref=lambda d: pd.to_datetime(d["mes_ref"])) ,
    }
    return dfs


@st.cache_data(show_spinner=False)
def get_data():
    return carregar_ou_gerar_dados()


dfs = get_data()

# =============================
# Filtros Globais (Sidebar)
# =============================
min_date = dfs["vendas"]["data"].min()
max_date = dfs["vendas"]["data"].max()

with st.sidebar:
    st.header("🔎 Filtros Globais")
    periodo = st.date_input(
        "Período",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(), max_value=max_date.date()
    )
    regiao_sel = st.multiselect("Regiões", REGIOES, default=REGIOES)
    produtos_sel = st.multiselect("Produtos", PRODUTOS, default=PRODUTOS)
    categoria_sel = st.multiselect("Categorias", CATEGORIAS, default=CATEGORIAS)


# Helper para aplicar filtros

def filtrar_vendas(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(periodo, (list, tuple)) and len(periodo) == 2:
        ini, fim = pd.to_datetime(periodo[0]), pd.to_datetime(periodo[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df = df[(df["data"] >= ini) & (df["data"] <= fim)]
    df = df[df["regiao"].isin(regiao_sel)]
    df = df[df["produto"].isin(produtos_sel)]
    df = df[df["categoria"].isin(categoria_sel)]
    return df

# =============================
# KPIs (Topo)
# =============================
df_vendas_f = filtrar_vendas(dfs["vendas"]) 
receita_total = df_vendas_f["valor_total"].sum()
lucro_total = df_vendas_f["lucro"].sum()
qtd_pedidos = len(df_vendas_f)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Receita no período (R$)", f"{receita_total:,.2f}".replace(",", "@").replace(".", ",").replace("@", "."))
col2.metric("Lucro no período (R$)", f"{lucro_total:,.2f}".replace(",", "@").replace(".", ",").replace("@", "."))
col3.metric("Pedidos", f"{qtd_pedidos:,}".replace(",", "."))
col4.metric("Ticket médio (R$)", f"{(receita_total/max(qtd_pedidos,1)):,.2f}".replace(",", "@").replace(".", ",").replace("@", "."))

# =============================
# Abas principais e sub-abas
# =============================
aba_principal = st.tabs(["Comercial", "Gestão de Pessoas", "Financeiro", "Operações"])

# -------- COMERCIAL ---------
with aba_principal[0]:
    sub = st.tabs(["Vendas", "Estoque"])

    # VENDAS
    with sub[0]:
        st.subheader("📈 Vendas")
        df = df_vendas_f.copy()

        colA, colB = st.columns(2)
        with colA:
            # Receita mensal
            serie = df.groupby(pd.Grouper(key="data", freq="MS"))["valor_total"].sum().reset_index()
            fig = px.line(serie, x="data", y="valor_total", title="Receita Mensal (R$)")
            st.plotly_chart(fig, use_container_width=True)
        with colB:
            # Lucro por produto
            lucro_prod = df.groupby("produto")["lucro"].sum().reset_index().sort_values("lucro", ascending=False)
            fig = px.bar(lucro_prod, x="produto", y="lucro", title="Lucro por Produto (R$)")
            st.plotly_chart(fig, use_container_width=True)

        colC, colD = st.columns(2)
        with colC:
            # Top vendedores por receita
            top_vend = df.groupby("vendedor")["valor_total"].sum().reset_index().sort_values("valor_total", ascending=False).head(15)
            fig = px.bar(top_vend, x="vendedor", y="valor_total", title="Top Vendedores (Receita)")
            st.plotly_chart(fig, use_container_width=True)
        with colD:
            # Receita por região
            rec_reg = df.groupby("regiao")["valor_total"].sum().reset_index()
            fig = px.pie(rec_reg, names="regiao", values="valor_total", title="Receita por Região")
            st.plotly_chart(fig, use_container_width=True)

        st.expander("📄 Tabela de Vendas Filtradas", expanded=False).dataframe(df)

    # ESTOQUE
    with sub[1]:
        st.subheader("📦 Estoque")
        df_e = dfs["estoque"].copy()
        # Filtro por produto
        filt_prod = st.multiselect("Filtrar produtos (estoque)", PRODUTOS, default=PRODUTOS)
        df_e = df_e[df_e["produto"].isin(filt_prod)]

        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(df_e.groupby("produto", as_index=False)["estoque_atual"].sum(), x="produto", y="estoque_atual", title="Estoque Atual por Produto")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            # Itens abaixo do ponto de pedido (risco de ruptura)
            baixo = df_e[df_e["estoque_atual"] < df_e["ponto_pedido"]]
            pct_baixo = (len(baixo) / max(len(df_e), 1)) * 100
            st.metric("SKUs em risco (%)", f"{pct_baixo:.1f}%")
            st.dataframe(baixo.sort_values(["produto", "estado"]))

# -------- GESTÃO DE PESSOAS ---------
with aba_principal[1]:
    sub = st.tabs(["Jornada Laboral", "Colaboradores"])

    # JORNADA
    with sub[0]:
        st.subheader("🕒 Jornada Laboral")
        df_j = dfs["jornada"].copy()
        # Filtros específicos
        deps = sorted(dfs["colab"]["departamento"].unique())
        dep_sel = st.multiselect("Departamentos", deps, default=deps)
        df_j = df_j[df_j["departamento"].isin(dep_sel)]

        col1, col2 = st.columns(2)
        with col1:
            horas = df_j.groupby(pd.Grouper(key="data_ref", freq="MS"))["horas_extras"].mean().reset_index()
            fig = px.line(horas, x="data_ref", y="horas_extras", title="Horas Extras – Média Mensal")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            faltas = df_j.groupby("departamento")["faltas"].sum().reset_index()
            fig = px.bar(faltas, x="departamento", y="faltas", title="Faltas acumuladas por Departamento")
            st.plotly_chart(fig, use_container_width=True)

        st.expander("📄 Lançamentos de Jornada", expanded=False).dataframe(df_j)

    # COLABORADORES
    with sub[1]:
        st.subheader("👥 Colaboradores")
        df_c = dfs["colab"].copy()
        dep = st.multiselect("Departamento", sorted(df_c["departamento"].unique()), default=None)
        if dep:
            df_c = df_c[df_c["departamento"].isin(dep)]
        col1, col2 = st.columns(2)
        with col1:
            fig = px.histogram(df_c, x="salario", nbins=30, title="Distribuição Salarial")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.box(df_c, x="departamento", y="salario", title="Salário por Departamento")
            st.plotly_chart(fig, use_container_width=True)
        st.expander("📄 Base de Colaboradores", expanded=False).dataframe(df_c)

# -------- FINANCEIRO ---------
with aba_principal[2]:
    sub = st.tabs(["Receitas e Despesas", "Indicadores Financeiros"])

    with sub[0]:
        st.subheader("💰 Receitas e Despesas")
        df_rec = dfs["rec"].copy()
        df_desp = dfs["desp"].copy()

        # Aplica filtro de período
        if isinstance(periodo, (list, tuple)) and len(periodo) == 2:
            ini, fim = pd.to_datetime(periodo[0]), pd.to_datetime(periodo[1])
            df_rec = df_rec[(df_rec["data"] >= ini) & (df_rec["data"] <= fim)]
            df_desp = df_desp[(df_desp["data"] >= ini) & (df_desp["data"] <= fim)]

        # Séries mensais
        rec_m = df_rec.groupby("data")["valor"].sum().reset_index()
        desp_m = df_desp.groupby("data")["valor"].sum().reset_index()
        fluxo = rec_m.merge(desp_m, on="data", how="outer", suffixes=("_rec", "_desp")).fillna(0)
        fluxo["saldo"] = fluxo["valor_rec"] - fluxo["valor_desp"]
        fluxo["saldo_acumulado"] = fluxo["saldo"].cumsum()

        col1, col2 = st.columns(2)
        with col1:
            fig = px.line(fluxo, x="data", y=["valor_rec", "valor_desp"], title="Receitas vs Despesas (Mensal)")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.area(fluxo, x="data", y="saldo_acumulado", title="Saldo Acumulado")
            st.plotly_chart(fig, use_container_width=True)

        st.expander("📄 Tabela de Fluxo", expanded=False).dataframe(fluxo)

    with sub[1]:
        st.subheader("📌 Indicadores Financeiros")
        df_rec = dfs["rec"].copy(); df_desp = dfs["desp"].copy()
        rec_total = df_rec["valor"].sum()
        desp_total = df_desp["valor"].sum()
        margem = (rec_total - desp_total) / max(rec_total, 1)

        c1, c2, c3 = st.columns(3)
        c1.metric("Receita total (R$)", f"{rec_total:,.2f}".replace(",", "@").replace(".", ",").replace("@", "."))
        c2.metric("Despesa total (R$)", f"{desp_total:,.2f}".replace(",", "@").replace(".", ",").replace("@", "."))
        c3.metric("Margem líquida", f"{margem*100:,.1f}%")

# -------- OPERAÇÕES ---------
with aba_principal[3]:
    sub = st.tabs(["Produção", "Logística"])

    with sub[0]:
        st.subheader("🏭 Produção")
        df_p = dfs["prod"].copy()
        estados = sorted(df_p["estado"].unique())
        est_sel = st.multiselect("Estados", estados, default=estados[:8])
        df_p = df_p[df_p["estado"].isin(est_sel)]

        col1, col2 = st.columns(2)
        with col1:
            fig = px.line(df_p, x="mes_ref", y="qtd_produzida", color="estado", title="Produção Mensal por Estado")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(df_p, x="estado", y="eficiencia_pct", title="Eficiência (%) por Estado", barmode="group")
            st.plotly_chart(fig, use_container_width=True)
        st.expander("📄 Tabela de Produção", expanded=False).dataframe(df_p)

    with sub[1]:
        st.subheader("🚚 Logística")
        df_l = dfs["log"].copy()
        estados = sorted(df_l["estado"].unique())
        est_sel = st.multiselect("Estados", estados, default=estados[:8], key="log_est")
        df_l = df_l[df_l["estado"].isin(est_sel)]

        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(df_l, x="estado", y="pedidos", title="Pedidos Entregues por Estado")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.line(df_l, x="mes_ref", y="tempo_medio_entrega_dias", color="estado", title="Tempo Médio de Entrega (dias)")
            st.plotly_chart(fig, use_container_width=True)
        st.expander("📄 Tabela de Logística", expanded=False).dataframe(df_l)

# =============================
# (Opcional) Exemplos de integração com APIs públicas – Comentado
# =============================
"""
# Exemplo Banco Central do Brasil (SGS) – requer internet
# SELIC meta (codigo 432): https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados?formato=json
import requests
try:
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados?formato=json"
    selic = requests.get(url, timeout=5).json()
    # Converter para DataFrame e exibir…
except Exception as e:
    pass
"""

# =============================
# Testes simples (sanidade dos dados)
# Execute com: python app.py (não via streamlit) para ver asserts no terminal
# =============================
if __name__ == "__main__":
    d = carregar_ou_gerar_dados()
    assert len(d["vendas"]) >= 10000, "Base de vendas menor que o esperado"
    assert set(["valor_total", "lucro"]).issubset(d["vendas"].columns), "Colunas de vendas ausentes"
    assert d["rec"]["valor"].sum() > 0 and d["desp"]["valor"].sum() > 0, "Financeiro inválido"
    print("✓ Testes de sanidade passaram. Rode: streamlit run app.py")
