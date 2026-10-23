"""Cálculos financeiros usados no notebook e no app Streamlit."""
import json
from datetime import datetime

import numpy as np
import pandas as pd

from src.config import PREGOES_POR_ANO

# Ticker na B3 (Yahoo Finance) -> nome curto usado nas análises
TICKERS = {
    'GOLL4.SA': 'GOL',
    'CVCB3.SA': 'CVC',
    'WEGE3.SA': 'WEGE',
    'MGLU3.SA': 'MGLU',
    'TOTS3.SA': 'TOTS',
    'BOVA11.SA': 'BOVA',
}

EMPRESAS = {
    'GOL': 'Gol Linhas Aéreas (aviação)',
    'CVC': 'CVC Brasil (turismo)',
    'WEGE': 'WEG (máquinas e equipamentos elétricos)',
    'MGLU': 'Magazine Luiza (varejo)',
    'TOTS': 'Totvs (software)',
    'BOVA': 'BOVA11: fundo que replica o Ibovespa (referência do mercado)',
}

# Série 12 do Banco Central: taxa do CDI ao dia (em %)
URL_CDI = ('https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json'
           '&dataInicial={inicio}&dataFinal={fim}')


# ---------------------------------------------------------------------------------------------
# Coleta e leitura dos dados
# ---------------------------------------------------------------------------------------------
def baixar_precos(tickers=TICKERS, inicio='2015-01-01', fim='2022-12-31', coluna='Close'):
    """Baixa os preços do Yahoo Finance (precisa de internet e da biblioteca yfinance).

    coluna='Close' -> preço de fechamento | coluna='Adj Close' -> fechamento ajustado por dividendos.
    """
    import yfinance as yf
    precos = yf.download(list(tickers), start=inicio, end=fim, auto_adjust=False, progress=False)[coluna]
    return precos[list(tickers)]


def baixar_cdi(inicio='2015-01-01', fim='2022-12-31'):
    """Baixa a taxa diária do CDI (em %) da API do Banco Central."""
    url = URL_CDI.format(inicio=pd.Timestamp(inicio).strftime('%d/%m/%Y'), fim=pd.Timestamp(fim).strftime('%d/%m/%Y'))
    cdi = pd.read_json(url)
    cdi['data'] = pd.to_datetime(cdi['data'], format='%d/%m/%Y')
    return cdi.set_index('data')['valor'].rename('CDI')


def carregar_precos(caminho):
    """Lê o CSV de preços, usa a data como índice e troca os tickers por nomes curtos."""
    precos = pd.read_csv(caminho, parse_dates=['Date'], index_col='Date')
    return precos.rename(columns=TICKERS)


def carregar_cdi(caminho, datas):
    """Lê a taxa diária do CDI e devolve o valor acumulado de R$ 1 nas mesmas datas dos preços."""
    taxa = pd.read_csv(caminho, parse_dates=['data'], index_col='data')['CDI']
    acumulado = (1 + taxa / 100).cumprod()
    acumulado = acumulado / acumulado.iloc[0]
    return acumulado.reindex(datas, method='ffill').rename('CDI')


# ---------------------------------------------------------------------------------------------
# Indicadores de desempenho
# ---------------------------------------------------------------------------------------------
def anos_no_periodo(precos):
    """Duração do período em anos de calendário."""
    return (precos.index[-1] - precos.index[0]).days / 365.25


def retorno_total(precos):
    """Quanto o preço variou do primeiro ao último dia (0,5 = +50%)."""
    return precos.iloc[-1] / precos.iloc[0] - 1


def cagr(precos):
    """Crescimento anual composto: a taxa constante por ano que leva do preço inicial ao final."""
    return (precos.iloc[-1] / precos.iloc[0]) ** (1 / anos_no_periodo(precos)) - 1


def retorno_por_ano(precos):
    """Retorno simples de cada ano: último preço do ano / último preço do ano anterior - 1."""
    fechamento = precos.groupby(precos.index.year).last()
    anterior = fechamento.shift(1)
    anterior.iloc[0] = precos.iloc[0]  # no 1º ano, a base é o primeiro preço da série
    return fechamento / anterior - 1


def volatilidade(precos):
    """Quanto o preço oscila por ano: desvio padrão dos retornos diários x raiz de 252 pregões."""
    return precos.pct_change().std() * np.sqrt(PREGOES_POR_ANO)


def maior_queda(precos):
    """Maior queda a partir de um pico anterior (drawdown máximo)."""
    return (precos / precos.cummax() - 1).min()


def indice_sharpe(precos, cdi):
    """Retorno acima do CDI por unidade de risco: (CAGR - CAGR do CDI) / volatilidade."""
    return (cagr(precos) - cagr(cdi)) / volatilidade(precos)


# ---------------------------------------------------------------------------------------------
# Simulação de carteira
# ---------------------------------------------------------------------------------------------
def simular_carteira(precos, pesos, valor_inicial=10_000, rebalancear=False):
    """Evolução do valor de uma carteira comprada no 1º dia do período.

    `pesos` é um dicionário {ação: peso}; os pesos são normalizados para somar 1.
    rebalancear=False -> compra e mantém até o fim.
    rebalancear=True  -> no fim de cada ano, redistribui o valor para voltar aos pesos iniciais.
    """
    pesos = pd.Series(pesos, dtype=float)
    pesos = pesos[pesos > 0] / pesos[pesos > 0].sum()
    precos = precos[pesos.index]

    if not rebalancear:
        return (precos / precos.iloc[0] * pesos * valor_inicial).sum(axis=1)

    valores, valor_atual, base = [], valor_inicial, precos.iloc[0]
    for _, precos_ano in precos.groupby(precos.index.year):
        valor_ano = (precos_ano / base * pesos * valor_atual).sum(axis=1)  # variação desde o último rebalanceamento
        valores.append(valor_ano)
        valor_atual, base = valor_ano.iloc[-1], precos_ano.iloc[-1]       # fim do ano: volta aos pesos-alvo
    return pd.concat(valores)


# ---------------------------------------------------------------------------------------------
# Saída
# ---------------------------------------------------------------------------------------------
def salvar_ficha(caminho, **campos):
    """Grava a ficha dos indicadores (JSON): período, convenções e avisos para usá-los corretamente."""
    ficha = {'data_calculo': datetime.now().strftime('%Y-%m-%d %H:%M'), **campos}
    with open(caminho, 'w', encoding='utf-8') as arquivo:
        json.dump(ficha, arquivo, ensure_ascii=False, indent=2, default=float)
    return ficha
