"""Testes das funções de src/financas.py. Rodar na raiz do projeto com: pytest"""
import numpy as np
import pandas as pd
import pytest

from src.financas import (cagr, indice_sharpe, maior_queda, retorno_por_ano, retorno_total,
                          simular_carteira, volatilidade)


def serie(valores, inicio='2020-01-01', freq='D'):
    return pd.Series(valores, index=pd.date_range(inicio, periods=len(valores), freq=freq), dtype=float)


def test_retorno_total():
    assert retorno_total(serie([100, 150])) == pytest.approx(0.5)
    assert retorno_total(serie([100, 50])) == pytest.approx(-0.5)


def test_cagr_dobrar_em_dois_anos():
    precos = pd.Series([100.0, 200.0], index=pd.to_datetime(['2019-01-01', '2021-01-01']))
    assert cagr(precos) == pytest.approx(2 ** 0.5 - 1, rel=1e-3)  # ~41,4% ao ano


def test_cagr_e_menor_que_a_media_aritmetica_quando_oscila():
    # Sobe 10% e cai 10%: média aritmética = 0%, mas o investidor perdeu 1%
    precos = pd.Series([100.0, 110.0, 99.0], index=pd.to_datetime(['2020-01-01', '2020-07-01', '2021-01-01']))
    assert precos.pct_change().mean() == pytest.approx(0)
    assert cagr(precos) < 0


def test_retorno_por_ano_usa_o_fim_do_ano_anterior_como_base():
    precos = pd.Series([100.0, 120.0, 90.0, 180.0],
                       index=pd.to_datetime(['2020-01-02', '2020-12-30', '2021-06-01', '2021-12-30']))
    resultado = retorno_por_ano(precos)
    assert resultado[2020] == pytest.approx(0.2)    # 100 -> 120
    assert resultado[2021] == pytest.approx(0.5)    # 120 -> 180


def test_maior_queda():
    assert maior_queda(serie([100, 120, 60, 90, 130])) == pytest.approx(-0.5)  # 120 -> 60


def test_volatilidade_de_preco_constante_e_zero():
    assert volatilidade(serie([10] * 30)) == pytest.approx(0)


def test_sharpe_positivo_quando_rende_mais_que_o_cdi():
    datas = pd.date_range('2020-01-01', '2022-01-01', freq='B')
    rng = np.random.default_rng(42)
    acao = pd.Series(100 * np.cumprod(1 + rng.normal(0.001, 0.01, len(datas))), index=datas)
    cdi = pd.Series(np.cumprod(np.full(len(datas), 1.0001)), index=datas)
    assert indice_sharpe(acao, cdi) > 0


def test_simular_carteira_normaliza_os_pesos():
    precos = pd.DataFrame({'A': [10, 20], 'B': [10, 10]}, index=pd.to_datetime(['2020-01-01', '2020-12-31']))
    carteira = simular_carteira(precos, {'A': 1, 'B': 1}, valor_inicial=1_000)  # pesos 1 e 1 -> 50% e 50%
    assert carteira.iloc[0] == pytest.approx(1_000)
    assert carteira.iloc[-1] == pytest.approx(1_500)                          # 500 x 2 + 500 x 1


def test_rebalanceamento_volta_aos_pesos_no_fim_do_ano():
    datas = pd.to_datetime(['2020-01-02', '2020-12-30', '2021-12-30'])
    precos = pd.DataFrame({'A': [10, 20, 10], 'B': [10, 10, 10]}, index=datas)  # A dobra em 2020 e cai à metade em 2021

    sem_rebalancear = simular_carteira(precos, {'A': 1, 'B': 1}, valor_inicial=1_000)
    com_rebalancear = simular_carteira(precos, {'A': 1, 'B': 1}, valor_inicial=1_000, rebalancear=True)

    assert sem_rebalancear.iloc[-1] == pytest.approx(1_000)   # 1.000 em A + 500 em B -> 500 + 500
    # Fim de 2020: 1.500 -> rebalanceia para 750 em cada. Em 2021, A cai à metade: 375 + 750
    assert com_rebalancear.iloc[-1] == pytest.approx(1_125)


def test_carteira_de_uma_acao_e_igual_com_e_sem_rebalanceamento():
    precos = pd.DataFrame({'A': [10, 15, 12, 30]},
                          index=pd.to_datetime(['2020-01-02', '2020-12-30', '2021-06-01', '2021-12-30']))
    pd.testing.assert_series_equal(simular_carteira(precos, {'A': 1}),
                                   simular_carteira(precos, {'A': 1}, rebalancear=True))
