"""Constantes do projeto: caminhos, convenções de mercado e parâmetros das medidas de risco."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PASTA_DADOS = RAIZ / 'Datasets'
PASTA_REPORTS = RAIZ / 'reports'

ACOES = ['GOL', 'CVC', 'WEGE', 'MGLU', 'TOTS']   # ações da carteira
REFERENCIA = 'BOVA'                              # BOVA11: fundo que replica o Ibovespa

PREGOES_POR_ANO = 252     # convenção de mercado para anualizar (a v1 usava 246)
NIVEL_VAR = 0.95          # VaR de 95%: a perda que só deve ser superada em 1 de cada 20 pregões
JANELA_VAR = 252          # VaR móvel estimado com o último ano de pregões
JANELA_VOLATILIDADE = 63  # volatilidade móvel de ~3 meses
FIM_ESTIMACAO = '2019-12-31'  # backtest: estimação até 2019, teste em 2020-2022 (pandemia incluída)
LAMBDA_EWMA = 0.94        # decaimento do RiskMetrics: o dia de ontem pesa 6%, e o peso cai 6% a cada dia mais antigo
SEMENTE = 42              # reprodutibilidade do bootstrap
N_BOOTSTRAP = 1_000       # reamostragens do bootstrap
BLOCO_BOOTSTRAP = 21      # blocos de ~1 mês, para manter os períodos agitados juntos

# Cenários de estresse históricos: (último pregão antes do choque, último pregão do choque)
CENARIOS_ESTRESSE = {
    'Joesley Day (18/05/2017)': ('2017-05-17', '2017-05-18'),
    'Greve dos caminhoneiros (mai/2018)': ('2018-05-18', '2018-06-01'),
    'Pior dia da pandemia (12/03/2020)': ('2020-03-11', '2020-03-12'),
    'Queda da pandemia (19/02 a 23/03/2020)': ('2020-02-19', '2020-03-23'),
}

# Períodos da Covid: até a véspera da queda da bolsa | até o fim da emergência declarado pela OMS | depois
PERIODOS_COVID = {
    'Pré-pandemia': ('2015-01-01', '2020-02-19'),
    'Pandemia': ('2020-02-20', '2023-05-05'),
    'Pós-pandemia': ('2023-05-06', '2025-12-31'),
}
