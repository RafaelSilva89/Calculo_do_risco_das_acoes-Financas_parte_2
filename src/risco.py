"""Medidas de risco de ações e de carteiras.

Convenções:
- `retornos` são retornos SIMPLES diários (0,01 = +1% no dia), um ativo por coluna;
- VaR e CVaR são devolvidos como PERDA positiva (0,05 = perder 5% num dia);
- tudo o que é "anual" usa PREGOES_POR_ANO pregões (raiz do tempo para desvios).
"""
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize

from src.config import JANELA_VAR, JANELA_VOLATILIDADE, LAMBDA_EWMA, NIVEL_VAR, PREGOES_POR_ANO


# ---------------------------------------------------------------------------------------------
# Risco de cada ativo
# ---------------------------------------------------------------------------------------------
def retornos_diarios(precos):
    """Retorno simples de cada pregão: preço de hoje / preço de ontem - 1 (o 1º dia sai)."""
    return precos.pct_change().dropna(how='all')


def semivolatilidade(retornos):
    """Volatilidade só dos dias de QUEDA (desvio abaixo de zero), anualizada: o risco que dói no investidor."""
    quedas = np.minimum(retornos, 0)
    return np.sqrt((quedas ** 2).mean()) * np.sqrt(PREGOES_POR_ANO)


def var_historico(retornos, nivel=NIVEL_VAR):
    """VaR histórico: a perda diária que só foi superada em (1 - nivel) dos pregões."""
    return -retornos.quantile(1 - nivel)


def var_parametrico(retornos, nivel=NIVEL_VAR):
    """VaR pela curva normal (média e desvio dos retornos). Subestima a perda quando há caudas gordas."""
    return -(retornos.mean() + stats.norm.ppf(1 - nivel) * retornos.std())


def cvar(retornos, nivel=NIVEL_VAR):
    """CVaR (Expected Shortfall): a perda MÉDIA nos dias piores que o VaR, ou seja, "quando dá errado, quanto dói"."""
    limite = retornos.quantile(1 - nivel)
    if isinstance(retornos, pd.DataFrame):
        return -retornos.where(retornos.le(limite, axis=1)).mean()
    return -retornos[retornos <= limite].mean()


def beta(retornos, mercado):
    """Beta: quanto o ativo costuma variar quando o mercado varia 1% (1 = acompanha o mercado)."""
    return retornos.apply(lambda coluna: coluna.cov(mercado) / mercado.var()) if isinstance(retornos, pd.DataFrame) \
        else retornos.cov(mercado) / mercado.var()


def volatilidade_movel(retornos, janela=JANELA_VOLATILIDADE):
    """Volatilidade anualizada numa janela móvel de `janela` pregões."""
    return retornos.rolling(janela).std() * np.sqrt(PREGOES_POR_ANO)


# ---------------------------------------------------------------------------------------------
# Risco de carteira (pesos fixos)
# ---------------------------------------------------------------------------------------------
def _vetor_pesos(pesos, colunas):
    """Converte {ativo: peso} num vetor alinhado às colunas, normalizado para somar 1."""
    vetor = pd.Series(pesos, dtype=float).reindex(colunas).fillna(0.0)
    return vetor / vetor.sum()


def covariancia_anual(retornos):
    """Matriz de covariância dos retornos diários, anualizada."""
    return retornos.cov() * PREGOES_POR_ANO


def volatilidade_carteira(pesos, cov_anual):
    """Volatilidade anual de uma carteira com pesos fixos: raiz de w' Σ w."""
    w = _vetor_pesos(pesos, cov_anual.columns)
    return float(np.sqrt(w @ cov_anual @ w))


def contribuicao_risco(pesos, cov_anual):
    """Fração do risco (variância) da carteira que vem de cada ativo; soma 1.

    Contribuição = w_i × (Σw)_i / (w' Σ w). Um ativo pode pesar 20% no dinheiro e 35% no risco.
    """
    w = _vetor_pesos(pesos, cov_anual.columns)
    marginal = cov_anual @ w
    return (w * marginal / (w @ marginal)).rename('Contribuição para o risco')


def razao_diversificacao(pesos, cov_anual):
    """Média ponderada das volatilidades / volatilidade da carteira. 1 = nenhum ganho de diversificação."""
    w = _vetor_pesos(pesos, cov_anual.columns)
    volatilidades = np.sqrt(np.diag(cov_anual))
    return float(w @ volatilidades / volatilidade_carteira(pesos, cov_anual))


def indice_sharpe_retornos(retornos, retornos_cdi):
    """Índice de Sharpe calculado só com retornos diários (útil no bootstrap, que embaralha as datas).

    Crescimento anual = produto de (1 + r) elevado a (252 / pregões) − 1, para o ativo e para o CDI.
    """
    crescimento = lambda r: np.prod(1 + r, axis=0) ** (PREGOES_POR_ANO / len(r)) - 1
    volatilidade_anual = retornos.std() * np.sqrt(PREGOES_POR_ANO)
    return (crescimento(retornos) - crescimento(retornos_cdi)) / volatilidade_anual


def retorno_carteira_pesos_fixos(retornos, pesos):
    """Retorno diário de uma carteira que volta aos pesos-alvo todo dia (premissa da fórmula w' Σ w)."""
    w = _vetor_pesos(pesos, retornos.columns)
    w = w[w > 0]   # ativos sem peso ficam de fora (e um ativo sem dados no período, como a GOL depois de 2022, não vira NaN)
    return retornos[w.index] @ w


def valor_carteira_pesos_fixos(precos, pesos, valor_inicial=1.0):
    """Valor, dia a dia, de uma carteira com pesos fixos que começa com `valor_inicial` no 1º pregão."""
    retorno = retorno_carteira_pesos_fixos(retornos_diarios(precos), pesos)
    valor = (1 + retorno).cumprod() * valor_inicial
    return pd.concat([pd.Series([valor_inicial], index=precos.index[:1]), valor]).rename('CARTEIRA')


# ---------------------------------------------------------------------------------------------
# VaR móvel e backtest
# ---------------------------------------------------------------------------------------------
def var_movel(retornos, janela=JANELA_VAR, nivel=NIVEL_VAR):
    """VaR histórico de cada dia estimado SÓ com os `janela` pregões anteriores (shift(1): sem olhar o dia)."""
    return -retornos.rolling(janela).quantile(1 - nivel).shift(1)


def volatilidade_ewma(retornos, lambda_=LAMBDA_EWMA):
    """Desvio diário previsto para cada dia pela média móvel exponencial (RiskMetrics), só com o passado.

    σ²(hoje) = λ·σ²(ontem) + (1 − λ)·r²(ontem). Reage a um choque já no dia seguinte, ao contrário da
    janela de 252 pregões, em que um dia novo pesa só 1/252. É um GARCH(1,1) sem reversão à média.
    """
    variancia = (retornos ** 2).ewm(alpha=1 - lambda_, adjust=False).mean()
    return np.sqrt(variancia).shift(1)


def var_ewma(retornos, nivel=NIVEL_VAR, lambda_=LAMBDA_EWMA, janela=JANELA_VAR):
    """VaR por simulação histórica filtrada: volatilidade EWMA de hoje x quantil dos retornos padronizados.

    Os retornos passados são divididos pela volatilidade EWMA da época (ficam "sem crise"); o quantil
    desses retornos padronizados, nos últimos `janela` pregões, é reescalado pela volatilidade prevista
    para o dia. Assim, o VaR mantém as caudas gordas do histórico e reage rápido a mudanças de regime.
    """
    sigma = volatilidade_ewma(retornos, lambda_)
    padronizados = retornos / sigma
    quantil = padronizados.rolling(janela).quantile(1 - nivel).shift(1)
    return -quantil * sigma


def violacoes_var(retornos, var):
    """Dias em que a perda superou o VaR previsto (True = violação). Dias sem previsão ficam de fora."""
    validos = var.notna()
    return (retornos[validos] < -var[validos])


def teste_kupiec(violacoes, nivel=NIVEL_VAR):
    """Teste de Kupiec (POF): a taxa de violações do VaR é compatível com a esperada (1 - nivel)?

    p-valor baixo = VaR mal calibrado (viola demais ou de menos).
    """
    n, x = int(len(violacoes)), int(np.sum(violacoes))
    p_esperado = 1 - nivel
    p_observado = x / n
    log_h0 = (n - x) * np.log(1 - p_esperado) + x * np.log(p_esperado)
    log_h1 = ((n - x) * np.log(1 - p_observado) if x < n else 0) + (x * np.log(p_observado) if x > 0 else 0)
    estatistica = -2 * (log_h0 - log_h1)
    return {'teste': 'Kupiec (POF)', 'pregões': n, 'violações': x, 'taxa observada': p_observado,
            'taxa esperada': p_esperado, 'estatística': estatistica, 'p-valor': float(stats.chi2.sf(estatistica, 1))}


def teste_christoffersen(violacoes, nivel=NIVEL_VAR):
    """Teste de Christoffersen: as violações do VaR chegam ISOLADAS (independência) e na taxa certa?

    Um VaR bem feito erra em dias espalhados; violações em sequência indicam que ele demora a reagir a
    uma crise. Devolve o p da independência e o da cobertura condicional (Kupiec + independência).
    """
    v = np.asarray(violacoes, dtype=int)
    anterior, atual = v[:-1], v[1:]
    n00 = int(np.sum((anterior == 0) & (atual == 0)))
    n01 = int(np.sum((anterior == 0) & (atual == 1)))
    n10 = int(np.sum((anterior == 1) & (atual == 0)))
    n11 = int(np.sum((anterior == 1) & (atual == 1)))

    def log_verossimilhanca(p, falhas, acertos):
        """Log-verossimilhança de uma binomial; com p = 0 ou 1 (sem falhas ou sem acertos), vale 0."""
        if not 0 < p < 1:
            return 0.0
        return acertos * np.log(1 - p) + falhas * np.log(p)

    p01 = n01 / (n00 + n01) if n00 + n01 else 0
    p11 = n11 / (n10 + n11) if n10 + n11 else 0
    p_geral = (n01 + n11) / (n00 + n01 + n10 + n11)
    estatistica_ind = -2 * (log_verossimilhanca(p_geral, n01 + n11, n00 + n10)
                            - log_verossimilhanca(p01, n01, n00) - log_verossimilhanca(p11, n11, n10))
    kupiec = teste_kupiec(violacoes, nivel)
    estatistica_cc = kupiec['estatística'] + estatistica_ind
    return {'teste': 'Christoffersen', 'violação depois de violação': p11, 'violação depois de dia normal': p01,
            'estatística (independência)': estatistica_ind, 'p-valor (independência)': float(stats.chi2.sf(estatistica_ind, 1)),
            'p-valor (cobertura condicional)': float(stats.chi2.sf(estatistica_cc, 2))}


# ---------------------------------------------------------------------------------------------
# Horizonte maior, estresse e pesos de mínima variância
# ---------------------------------------------------------------------------------------------
def retornos_acumulados(retornos, dias):
    """Retorno acumulado de cada janela de `dias` pregões seguidos (janelas sobrepostas)."""
    return np.expm1(np.log1p(retornos).rolling(dias).sum()).dropna(how='all')


def var_horizonte(retornos, dias, nivel=NIVEL_VAR):
    """VaR de `dias` pregões de duas formas: regra da raiz do tempo (VaR de 1 dia x raiz de dias) e o
    quantil das perdas acumuladas que realmente aconteceram em janelas de `dias` pregões."""
    return pd.DataFrame({'Raiz do tempo': var_historico(retornos, nivel) * np.sqrt(dias),
                         'Observado': var_historico(retornos_acumulados(retornos, dias), nivel)})


def choques_cenario(precos, inicio, fim):
    """Variação de cada ativo num cenário histórico: do preço em `inicio` ao preço em `fim`."""
    return precos.loc[fim] / precos.loc[inicio] - 1


def perda_cenario(pesos, choques, valor=1.0):
    """Resultado de uma carteira (pesos normalizados) se cada ativo repetir o choque do cenário."""
    return float(_vetor_pesos(pesos, choques.index) @ choques * valor)


def pesos_minima_variancia(cov_anual):
    """Pesos (sem venda a descoberto, somando 1) que minimizam a volatilidade w' Σ w da carteira."""
    n = len(cov_anual)
    resultado = minimize(lambda w: w @ cov_anual.to_numpy() @ w, np.full(n, 1 / n), method='SLSQP',
                         bounds=[(0, 1)] * n, constraints={'type': 'eq', 'fun': lambda w: w.sum() - 1})
    pesos = np.clip(resultado.x, 0, None)
    return pd.Series(pesos / pesos.sum(), index=cov_anual.columns)
