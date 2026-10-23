"""Testes das funções de src/risco.py e dos testes estatísticos acrescentados em src/estatistica.py."""
import numpy as np
import pandas as pd
import pytest

from src.config import PREGOES_POR_ANO
from src.estatistica import bootstrap_blocos, teste_binomial, teste_levene, teste_normalidade
from src.risco import (beta, contribuicao_risco, covariancia_anual, cvar, razao_diversificacao,
                       retorno_carteira_pesos_fixos, semivolatilidade, valor_carteira_pesos_fixos, var_historico,
                       var_movel, var_parametrico, violacoes_var, teste_kupiec, volatilidade_carteira,
                       choques_cenario, indice_sharpe_retornos, perda_cenario, pesos_minima_variancia,
                       retornos_acumulados, teste_christoffersen, var_ewma, var_horizonte, volatilidade_ewma)


@pytest.fixture
def retornos_independentes():
    """Dois ativos sem correlação e com a mesma volatilidade (1% ao dia)."""
    rng = np.random.default_rng(42)
    datas = pd.bdate_range('2020-01-01', periods=50_000)
    return pd.DataFrame(rng.normal(0, 0.01, (len(datas), 2)), index=datas, columns=['A', 'B'])


def test_var_e_cvar_sao_perdas_positivas_e_o_cvar_e_maior():
    retornos = pd.Series(np.linspace(-0.10, 0.10, 201))   # de -10% a +10%, passo de 0,1%
    assert var_historico(retornos, 0.95) == pytest.approx(0.09)
    assert cvar(retornos, 0.95) > var_historico(retornos, 0.95)
    assert cvar(retornos, 0.95) == pytest.approx(0.095)    # média de -10% a -9%


def test_cvar_funciona_por_coluna():
    retornos = pd.DataFrame({'A': np.linspace(-0.10, 0.10, 201), 'B': np.linspace(-0.20, 0.20, 201)})
    resultado = cvar(retornos, 0.95)
    assert resultado['A'] == pytest.approx(0.095)
    assert resultado['B'] == pytest.approx(0.19)


def test_var_parametrico_na_normal_padrao(retornos_independentes):
    # Normal com desvio de 1%: VaR 95% = 1,645 desvio
    assert var_parametrico(retornos_independentes['A'], 0.95) == pytest.approx(0.01645, rel=0.02)


def test_semivolatilidade_ignora_os_dias_de_alta():
    so_altas = pd.Series([0.01, 0.02, 0.03])
    assert semivolatilidade(so_altas) == 0
    quedas = pd.Series([-0.01, 0.01] * 50)
    assert semivolatilidade(quedas) == pytest.approx(np.sqrt(0.0001 / 2) * np.sqrt(PREGOES_POR_ANO))


def test_beta_de_um_ativo_que_dobra_o_mercado():
    mercado = pd.Series([0.01, -0.02, 0.015, -0.005, 0.03])
    assert beta(2 * mercado, mercado) == pytest.approx(2)


def test_diversificacao_com_ativos_independentes(retornos_independentes):
    cov = covariancia_anual(retornos_independentes)
    risco_de_um = np.sqrt(cov.loc['A', 'A'])
    # Metade em cada: o risco cai para 1/raiz(2) (~71%) do risco de um ativo
    assert volatilidade_carteira({'A': 1, 'B': 1}, cov) == pytest.approx(risco_de_um / np.sqrt(2), rel=0.02)
    assert razao_diversificacao({'A': 1, 'B': 1}, cov) == pytest.approx(np.sqrt(2), rel=0.02)


def test_contribuicao_risco_soma_1_e_pesa_mais_no_ativo_mais_volatil():
    cov = pd.DataFrame([[0.04, 0.0], [0.0, 0.01]], index=['A', 'B'], columns=['A', 'B'])  # A: 20% | B: 10%
    contribuicao = contribuicao_risco({'A': 0.5, 'B': 0.5}, cov)
    assert contribuicao.sum() == pytest.approx(1)
    assert contribuicao['A'] == pytest.approx(0.8)   # 0,25 x 0,04 / (0,25 x 0,04 + 0,25 x 0,01)


def test_carteira_com_pesos_fixos():
    precos = pd.DataFrame({'A': [10.0, 11.0, 12.1], 'B': [10.0, 9.0, 8.1]}, index=pd.bdate_range('2020-01-01', periods=3))
    retorno = retorno_carteira_pesos_fixos(precos.pct_change().dropna(), {'A': 1, 'B': 1})
    assert retorno.tolist() == pytest.approx([0.0, 0.0])   # +10% e -10% todo dia, com 50% em cada
    valor = valor_carteira_pesos_fixos(precos, {'A': 1, 'B': 1}, valor_inicial=100)
    assert valor.tolist() == pytest.approx([100, 100, 100])


def test_var_movel_nao_usa_o_proprio_dia():
    retornos = pd.Series([0.0] * 10 + [-0.5])        # uma queda enorme no último dia
    previsto = var_movel(retornos, janela=10, nivel=0.95)
    assert previsto.iloc[-1] == pytest.approx(0.0)   # a previsão do último dia não "sabe" da queda
    assert violacoes_var(retornos, previsto).sum() == 1


def test_kupiec_aceita_taxa_certa_e_rejeita_taxa_errada():
    certo = np.array([True] * 50 + [False] * 950)      # 5% de violações
    errado = np.array([True] * 150 + [False] * 850)    # 15% de violações
    assert teste_kupiec(certo, 0.95)['p-valor'] > 0.9
    assert teste_kupiec(errado, 0.95)['p-valor'] < 0.001


def test_kupiec_sem_violacoes():
    assert teste_kupiec(np.zeros(500, dtype=bool), 0.95)['violações'] == 0


def test_levene_efeito_e_a_razao_dos_desvios(retornos_independentes):
    resultado = teste_levene(3 * retornos_independentes['A'], retornos_independentes['B'])
    assert resultado['tamanho do efeito'] == pytest.approx(3, rel=0.02)
    assert resultado['p-valor'] < 0.001


def test_normalidade_curtose_proxima_de_zero_na_normal(retornos_independentes):
    assert abs(teste_normalidade(retornos_independentes['A'])['tamanho do efeito']) < 0.1


def test_binomial_razao_observada_esperada():
    assert teste_binomial(27, 1000, 0.0027)['tamanho do efeito'] == pytest.approx(10)


def test_volatilidade_ewma_reage_no_dia_seguinte_e_nao_usa_o_proprio_dia():
    retornos = pd.Series([0.01, -0.01] * 50 + [-0.20, 0.0])
    sigma = volatilidade_ewma(retornos, lambda_=0.94)
    assert sigma.iloc[-2] == pytest.approx(sigma.iloc[-3], rel=0.05)   # no dia da queda, ainda não sabe dela
    assert sigma.iloc[-1] > 2 * sigma.iloc[-2]                          # no dia seguinte, já reagiu


def test_var_ewma_e_positivo_e_cresce_depois_de_um_choque():
    rng = np.random.default_rng(1)
    retornos = pd.Series(np.r_[rng.normal(0, 0.01, 400), rng.normal(0, 0.04, 30)])
    var = var_ewma(retornos, janela=252)
    assert (var.dropna() > 0).all()
    assert var.iloc[-1] > 2 * var.iloc[399]


def test_christoffersen_detecta_violacoes_em_sequencia():
    espalhadas = np.random.default_rng(0).random(1000) < 0.05   # ~5%, em dias sorteados ao acaso
    agrupadas = np.zeros(1000, dtype=bool)
    agrupadas[100:150] = True                     # os mesmos 5%, todos seguidos
    assert teste_christoffersen(espalhadas)['p-valor (independência)'] > 0.05
    assert teste_christoffersen(agrupadas)['p-valor (independência)'] < 0.001


def test_retornos_acumulados_e_var_horizonte():
    retornos = pd.Series([0.10, 0.10, -0.50])
    assert retornos_acumulados(retornos, 2).tolist() == pytest.approx([0.21, -0.45])
    tabela = var_horizonte(pd.DataFrame({'A': np.linspace(-0.05, 0.05, 500)}), dias=4)
    assert tabela.loc['A', 'Raiz do tempo'] == pytest.approx(2 * var_historico(pd.Series(np.linspace(-0.05, 0.05, 500))))


def test_perda_cenario_com_os_choques_de_um_periodo():
    datas = pd.to_datetime(['2020-01-01', '2020-01-02'])
    precos = pd.DataFrame({'A': [10.0, 5.0], 'B': [10.0, 11.0]}, index=datas)
    choques = choques_cenario(precos, '2020-01-01', '2020-01-02')
    assert choques.tolist() == pytest.approx([-0.5, 0.1])
    assert perda_cenario({'A': 1, 'B': 1}, choques, valor=1_000) == pytest.approx(-200)   # 500 x -50% + 500 x +10%


def test_minima_variancia_prefere_o_ativo_mais_calmo_e_respeita_os_limites():
    cov = pd.DataFrame([[0.04, 0.0], [0.0, 0.01]], index=['A', 'B'], columns=['A', 'B'])
    pesos = pesos_minima_variancia(cov)
    assert pesos.sum() == pytest.approx(1)
    assert (pesos >= 0).all()
    assert pesos['B'] == pytest.approx(0.8, abs=1e-3)   # sem correlação: peso proporcional a 1 / variância


def test_sharpe_retornos_e_zero_quando_rende_igual_ao_cdi():
    rng = np.random.default_rng(3)
    retornos = pd.Series(rng.normal(0.0005, 0.01, 500))
    assert indice_sharpe_retornos(retornos, retornos) == pytest.approx(0)


def test_bootstrap_blocos_e_reprodutivel_e_contem_a_estimativa(retornos_independentes):
    estatistica = lambda amostra: {'desvio': amostra['A'].std()}
    a = bootstrap_blocos(retornos_independentes.iloc[:2000], estatistica, n=200, semente=7)
    b = bootstrap_blocos(retornos_independentes.iloc[:2000], estatistica, n=200, semente=7)
    pd.testing.assert_frame_equal(a, b)
    assert a.loc['desvio', 'IC inferior'] < a.loc['desvio', 'estimativa'] < a.loc['desvio', 'IC superior']
