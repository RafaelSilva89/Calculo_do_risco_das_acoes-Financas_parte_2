import pandas as pd
import streamlit as st

from src.config import ACOES, CENARIOS_ESTRESSE, NIVEL_VAR, PASTA_DADOS, PERIODOS_COVID, REFERENCIA
from src.financas import (EMPRESAS, ativos_com_dados, carregar_cdi, carregar_precos, cagr, indice_sharpe, maior_queda,
                          volatilidade)
from src.risco import (choques_cenario, contribuicao_risco, covariancia_anual, cvar, perda_cenario,
                       razao_diversificacao, retornos_diarios, valor_carteira_pesos_fixos, var_historico,
                       volatilidade_movel)

st.set_page_config(page_title="Risco da Carteira 🛡️", page_icon="🛡️", layout="wide")
st.title("🛡️ Calculadora de Risco de Carteira")
st.markdown("Escolha os pesos e veja **quanto a carteira oscila**, **quanto pode perder num dia ruim** e "
            "**de onde vem o risco**, comparando com o **BOVA11** (Ibovespa), de **2015 a 2025**.")


### Carregamento dos dados
@st.cache_data
def carregar():
    precos = carregar_precos(PASTA_DADOS / "acoes_2015_2025.csv")
    return precos, carregar_cdi(PASTA_DADOS / "cdi_2015_2025.csv", precos.index)


def reais(valor):
    return f"R$ {valor:,.0f}".replace(",", ".")


def percentual(valor):
    return f"{valor:.1%}".replace(".", ",")


precos, cdi = carregar()

### Parâmetros
with st.sidebar:
    st.header("⚙️ Parâmetros")
    valor_inicial = st.number_input("Valor investido (R$)", 1_000, 1_000_000, 10_000, step=1_000)
    primeira, ultima = precos.index[0].date(), precos.index[-1].date()

    st.header("📅 Período")
    inicio = st.date_input("Data de início", value=primeira, min_value=primeira, max_value=ultima, format="DD/MM/YYYY")
    fim = st.date_input("Data de término", value=ultima, min_value=primeira, max_value=ultima, format="DD/MM/YYYY")
    st.caption("Pré-pandemia: até 19/02/2020 · Pandemia: 20/02/2020 a 05/05/2023 · Pós-pandemia: depois disso")

    periodo = precos.loc[pd.Timestamp(inicio):pd.Timestamp(fim)]
    disponiveis = ativos_com_dados(periodo)
    peso_padrao = 100 // max(len([a for a in ACOES if a in disponiveis]), 1) // 5 * 5

    st.header("⚖️ Pesos da carteira (%)")
    pesos = {}
    for acao in ACOES:
        tem_dados = acao in disponiveis
        peso = st.slider(f"{acao} – {EMPRESAS[acao].split(' (')[0]}", 0, 100, peso_padrao if tem_dados else 0,
                         step=5, disabled=not tem_dados)
        pesos[acao] = peso if tem_dados else 0
    pesos[REFERENCIA] = st.slider("BOVA – BOVA11 (índice)", 0, 100, 0, step=5)
    if len(disponiveis) < len(precos.columns):
        st.caption("A GOL não tem dados públicos depois de 29/12/2022 (recuperação judicial e saída da bolsa). "
                   "Para incluí-la, termine o período até essa data.")
    st.caption("Os pesos são normalizados para somar 100% e mantidos fixos todos os dias.")

if inicio >= fim:
    st.warning("A data de término precisa ser depois da data de início.")
    st.stop()
if sum(pesos.values()) == 0:
    st.warning("Defina o peso de pelo menos um ativo.")
    st.stop()
if len(periodo) < 2 * 63:
    st.warning("Escolha um período de pelo menos 6 meses.")
    st.stop()

### Cálculos
pesos = {ativo: peso for ativo, peso in pesos.items() if peso > 0}
retornos = retornos_diarios(periodo)
cdi_periodo = cdi.loc[periodo.index]
carteira = valor_carteira_pesos_fixos(periodo, pesos)
bova = valor_carteira_pesos_fixos(periodo, {REFERENCIA: 1})
retorno_carteira, retorno_bova = carteira.pct_change().dropna(), bova.pct_change().dropna()

### Indicadores principais
st.subheader("📊 Carteira x BOVA11")
colunas = st.columns(5)
indicadores = [
    ("Volatilidade anual", volatilidade(carteira), volatilidade(bova), percentual),
    (f"Perda num dia ruim (VaR {NIVEL_VAR:.0%})", var_historico(retorno_carteira) * valor_inicial,
     var_historico(retorno_bova) * valor_inicial, reais),
    ("Perda média nos piores dias (CVaR)", cvar(retorno_carteira) * valor_inicial,
     cvar(retorno_bova) * valor_inicial, reais),
    ("Maior queda", maior_queda(carteira), maior_queda(bova), percentual),
    ("Índice de Sharpe", indice_sharpe(carteira, cdi_periodo), indice_sharpe(bova, cdi_periodo),
     lambda v: f"{v:.2f}".replace(".", ",")),
]
for coluna, (nome, valor_carteira, valor_bova, formatar) in zip(colunas, indicadores):
    coluna.metric(nome, formatar(valor_carteira), f"BOVA11: {formatar(valor_bova)}", delta_color="off")

st.caption(f"Crescimento anual (CAGR): carteira {percentual(cagr(carteira))} | BOVA11 {percentual(cagr(bova))} | "
           f"CDI {percentual(cagr(cdi_periodo))}. {reais(valor_inicial)} na carteira viraram "
           f"{reais(carteira.iloc[-1] * valor_inicial)}.")

### De onde vem o risco
cov = covariancia_anual(retornos[list(pesos)])
esquerda, direita = st.columns(2)
with esquerda:
    st.subheader("🧩 Peso no dinheiro x peso no risco")
    peso_dinheiro = pd.Series(pesos, dtype=float) / sum(pesos.values())
    st.bar_chart(pd.DataFrame({"Peso no dinheiro": peso_dinheiro, "Peso no risco": contribuicao_risco(pesos, cov)}),
                 stack=False)
    if len(pesos) > 1:
        st.caption(f"Razão de diversificação: {razao_diversificacao(pesos, cov):.2f} "
                   "(1 = nenhum ganho; quanto maior, mais a diversificação reduziu o risco).")
with direita:
    st.subheader("📈 Volatilidade de 3 meses ao longo do tempo")
    st.line_chart(pd.DataFrame({"Carteira": volatilidade_movel(retorno_carteira),
                                "BOVA11": volatilidade_movel(retorno_bova)}).dropna())

### Antes, durante e depois da Covid
fases = {}
for nome, (inicio_fase, fim_fase) in PERIODOS_COVID.items():
    trecho = retornos.loc[inicio_fase:fim_fase]
    if len(trecho) < 63:  # fase fora do período escolhido (ou curta demais para medir o risco)
        continue
    carteira_fase = (1 + trecho[list(pesos)] @ (pd.Series(pesos) / sum(pesos.values()))).cumprod()
    bova_fase = (1 + trecho[REFERENCIA]).cumprod()
    fases[nome] = {"Início": f"{trecho.index[0]:%d/%m/%Y}", "Fim": f"{trecho.index[-1]:%d/%m/%Y}",
                   "Volatilidade da carteira": percentual(volatilidade(carteira_fase)),
                   "Volatilidade do BOVA11": percentual(volatilidade(bova_fase)),
                   "VaR da carteira (1 dia)": reais(var_historico(carteira_fase.pct_change().dropna()) * valor_inicial),
                   "Maior queda da carteira": percentual(maior_queda(carteira_fase)),
                   "Maior queda do BOVA11": percentual(maior_queda(bova_fase))}
if fases:
    st.subheader("🦠 Antes, durante e depois da Covid")
    st.caption("Risco da carteira escolhida em cada fase que cabe no período (pesos mantidos todo dia).")
    st.table(pd.DataFrame(fases).T)

st.subheader("🌪️ E se as crises do período se repetissem?")
st.caption("Cada ativo repete a variação que teve na crise; a carteira usa os pesos escolhidos.")
estresse = pd.DataFrame({
    nome: {"Carteira": reais(perda_cenario(pesos, choques_cenario(precos, inicio, fim), valor_inicial)),
           "BOVA11": reais(choques_cenario(precos, inicio, fim)[REFERENCIA] * valor_inicial)}
    for nome, (inicio, fim) in CENARIOS_ESTRESSE.items()
}).T
st.table(estresse)

st.subheader("🔗 Correlação dos retornos diários")
st.dataframe(retornos[list(pesos)].corr().style.format("{:.2f}").background_gradient(cmap="RdBu_r", vmin=-1, vmax=1))

st.info("ℹ️ Risco histórico não garante o risco futuro. O VaR é a perda de um dia que só foi superada em 1 de "
        "cada 20 pregões do período; em crises, ela é superada com mais frequência. Valores sem custos e impostos.")
