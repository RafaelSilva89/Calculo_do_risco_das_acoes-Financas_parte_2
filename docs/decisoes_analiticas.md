# Registro de decisões analíticas

Este documento registra as principais decisões do projeto, no formato
**Contexto → Decisão → Alternativas consideradas → Consequência → Onde está**.
Cada decisão tem um código (DA-XX) para ser citada em commits e pull requests.

Os números vêm das saídas do notebook [`Notebooks/Cálculo do risco das ações - Finanças parte 2 - v2.ipynb`](../Notebooks/).

| Código | Decisão |
|---|---|
| [DA-01](#da-01--variação-real-e-cagr-em-vez-do-retorno-logarítmico-lido-como-percentual) | Variação real e CAGR em vez do retorno logarítmico lido como percentual |
| [DA-02](#da-02--volatilidade-dos-retornos-diários-com-raiz-de-252) | Volatilidade dos retornos diários, com raiz de 252 |
| [DA-03](#da-03--coeficiente-de-variação-removido-índice-de-sharpe-no-lugar) | Coeficiente de variação removido; Índice de Sharpe no lugar |
| [DA-04](#da-04--dias-extremos-mantidos) | Dias extremos mantidos |
| [DA-05](#da-05--var-histórico-com-backtest-fora-da-amostra) | VaR histórico, com backtest fora da amostra |
| [DA-06](#da-06--pesos-fixos-comparados-com-comprar-e-manter) | Pesos fixos, comparados com comprar e manter |
| [DA-07](#da-07--remoção-do-stockscsv) | Remoção do `stocks.csv` |
| [DA-08](#da-08--cdi-como-taxa-livre-de-risco) | CDI como taxa livre de risco |
| [DA-09](#da-09--var-ewma-filtrado-como-estimativa-de-perda-para-amanhã) | VaR EWMA filtrado como estimativa de perda para amanhã |
| [DA-10](#da-10--intervalos-por-bootstrap-em-blocos) | Intervalos por bootstrap em blocos |
| [DA-11](#da-11--testes-de-estresse-com-crises-reais-e-var-de-10-dias-observado) | Testes de estresse com crises reais e VaR de 10 dias observado |
| [DA-12](#da-12--mínima-variância-só-com-dados-até-2019) | Mínima variância só com dados até 2019 |
| [DA-13](#da-13--extensão-até-2025-em-uma-seção-própria-com-4-ações) | Extensão até 2025 em uma seção própria, com 4 ações |
| [DA-14](#da-14--três-fases-da-covid) | Três fases da Covid |

---

## DA-01 — Variação real e CAGR em vez do retorno logarítmico lido como percentual

- **Contexto:** a versão original mostrava o retorno logarítmico do período como se fosse a variação do preço. A CVC aparecia com "−121,94%", uma perda impossível; a variação real foi de −70,5%. Na MGLU, o log (+246,55%) escondia uma alta de +1.076,9%.
- **Decisão:** apresentar a **variação real do preço** e o **CAGR**, com o retorno logarítmico só onde ele é útil (somar retornos no tempo).
- **Alternativas consideradas:** manter o log, explicando a escala; ele continua sem leitura direta para o investidor.
- **Consequência:** "quanto R$ 1 virou" passa a bater com a tabela; a MGLU caiu 70,4% em 2015, e não "121%".
- **Onde está:** item 4 da Fase 02 (Feature Engineering); `retorno_total` e `cagr` em `src/financas.py`.

## DA-02 — Volatilidade dos retornos diários, com raiz de 252

- **Contexto:** a versão original media o risco pelo desvio de **8 retornos anuais** (instável: o da MGLU vai de 127,1% a 237,6% só mudando a forma de calcular o retorno anual), pelo desvio do **preço** e pelo desvio diário × 246 (errado). Também leu o desvio diário de 4,86% como "4 reais e 85 centavos".
- **Decisão:** medir o risco pela **volatilidade dos retornos diários × √252** (convenção de mercado, igual à parte 1), com semivolatilidade, maior queda, VaR e CVaR como complementos.
- **Alternativas consideradas:** √246 (correto no método, mas fora da convenção; a diferença é de 1,2%) e o desvio dos retornos anuais (mantido só como complemento).
- **Consequência:** GOL com 77,1% ao ano, BOVA11 com 26,0%; o BOVA11 é o menos volátil em 8 de 8 anos.
- **Onde está:** itens 3 e 5 da Fase 03; `volatilidade` em `src/financas.py`, `PREGOES_POR_ANO` em `src/config.py`.

## DA-03 — Coeficiente de variação removido; Índice de Sharpe no lugar

- **Contexto:** a versão original calculava o coeficiente de variação (desvio ÷ média dos retornos anuais). Com média negativa, ele dá −1.087,4% (GOL) e −433,9% (CVC), números sem interpretação. A versão original também comparava o risco da carteira com o do BOVA11 sem olhar o retorno.
- **Decisão:** remover o coeficiente de variação e medir a relação risco × retorno pelo **Índice de Sharpe** contra o CDI.
- **Alternativas consideradas:** retorno ÷ volatilidade sem descontar a renda fixa (ignora que o CDI rendeu 8,6% ao ano sem risco).
- **Consequência:** a carteira é mais arriscada que o BOVA11 (39,6% x 26,0%), mas tem Sharpe de 0,24 contra 0,08; a WEGE tem o melhor Sharpe (0,51), e GOL e CVC têm Sharpe negativo.
- **Onde está:** H6 e item 6 da Fase 03; `indice_sharpe` em `src/financas.py`.

## DA-04 — Dias extremos mantidos

- **Contexto:** pela regra do IQR, de 3,2% a 6,0% dos pregões são outliers, e os retornos têm curtose em excesso de 5,2 a 14,2 (caudas gordas).
- **Decisão:** manter todos os dias.
- **Alternativas consideradas:** remover ou suavizar os dias extremos, o que esconderia exatamente o risco que o projeto mede (como março de 2020).
- **Consequência:** as medidas refletem as caudas gordas; por isso o VaR é histórico (DA-05).
- **Onde está:** item 2.6 da Fase 02 e H3.

## DA-05 — VaR histórico, com backtest fora da amostra

- **Contexto:** a curva normal erra o tamanho das perdas extremas (no VaR 99%, subestima em 5 dos 6 ativos), e um VaR calculado com o período inteiro acerta "exatamente" 5% das violações porque conhece o futuro.
- **Decisão:** usar o **VaR histórico de 95%**; para previsão, o **VaR móvel** (252 pregões anteriores, com `shift(1)`), testado em 2020–2022 com o teste de Kupiec.
- **Alternativas consideradas:** VaR pela normal; VaR fixo estimado com 2015–2019 (superado em 12,5% dos pregões da carteira na pandemia).
- **Consequência:** o VaR móvel viola em 6,6% dos pregões da carteira (p de Kupiec = 0,059), e o Kupiec não o rejeita em 5 dos 7 ativos/carteira. Mas ele erra em sequência (ver DA-09).
- **Onde está:** itens 4.1, 8 e 9 da Fase 03; `var_historico`, `var_movel`, `violacoes_var` e `teste_kupiec` em `src/risco.py`.

## DA-06 — Pesos fixos, comparados com comprar e manter

- **Contexto:** a fórmula w'Σw da versão original supõe, sem dizer, que a carteira volta aos 20% todo dia. Comprando e mantendo, a MGLU chegou a 91% da carteira.
- **Decisão:** manter a carteira de pesos fixos como "modelo final" (comparável com a versão original) e mostrar lado a lado "comprar e manter" e "rebalancear todo ano".
- **Alternativas consideradas:** otimizar os pesos (Markowitz), que exigiria validação fora da amostra e fica para a parte 3.
- **Consequência:** pesos fixos com 39,6% de volatilidade; comprar e manter com 45,5% e maior queda de −87,2%; rebalanceando todo ano, 37,6% e Sharpe de 0,46.
- **Onde está:** item 7 da Fase 03; `volatilidade_carteira`, `valor_carteira_pesos_fixos` em `src/risco.py` e `simular_carteira` em `src/financas.py`.

## DA-07 — Remoção do `stocks.csv`

- **Contexto:** o repositório tinha um `Datasets/stocks.csv` que nenhuma célula lia. Ele tem 416 sábados, domingos e feriados, valores de −50 a +62 e passos diários com desvio de ~1,00 em todas as colunas, sem correlação com os preços reais: é um passeio aleatório simulado com nomes de ações.
- **Decisão:** remover o arquivo.
- **Alternativas consideradas:** mantê-lo documentado; o risco de alguém tomá-lo por dado real é maior que o benefício.
- **Consequência:** a pasta `Datasets/` só tem dados reais; o arquivo continua no histórico do git (commit `bb5bf01`).
- **Onde está:** item 1.2 da Fase 02.

## DA-08 — CDI como taxa livre de risco

- **Contexto:** para saber se o risco valeu a pena, é preciso comparar com o que se ganharia sem risco.
- **Decisão:** usar o **CDI** (série 12 do Banco Central), o mesmo arquivo da parte 1.
- **Alternativas consideradas:** Selic ou poupança; o CDI é a referência usual dos fundos de renda fixa.
- **Consequência:** o CDI rendeu 8,6% ao ano com volatilidade de 0,3%, e o Sharpe do BOVA11 fica em só 0,08.
- **Onde está:** item 1.2 da Fase 02 e H6; `carregar_cdi` em `src/financas.py`.

## DA-09 — VaR EWMA filtrado como estimativa de perda para amanhã

- **Contexto:** o VaR móvel de 252 pregões demora a reagir a uma crise, porque cada dia novo pesa só 1/252. No teste de Christoffersen, suas violações vêm em sequência em CVC, WEGE e TOTS (p < 0,05), e 12 das 49 violações da carteira aconteceram em fevereiro e março de 2020.
- **Decisão:** usar o **VaR por simulação histórica filtrada**: volatilidade de hoje por média móvel exponencial (λ = 0,94, RiskMetrics) x quantil dos retornos padronizados do último ano, só com o passado (`shift(1)`).
- **Alternativas consideradas:** VaR pela normal com volatilidade EWMA (perde as caudas gordas, H3); GARCH(1,1) (exige uma biblioteca a mais; o EWMA é um GARCH sem reversão à média e fica como próximo passo).
- **Consequência:** violações de 5,5% a 6,2% em todos os ativos em 2020–2022; o Kupiec não rejeita nenhum caso (menor p = 0,155), e o Christoffersen só rejeita a TOTS (p = 0,008). Na carteira, 6,2% (p de independência = 0,922).
- **Onde está:** item 8 da Fase 03; `volatilidade_ewma`, `var_ewma` e `teste_christoffersen` em `src/risco.py`.

## DA-10 — Intervalos por bootstrap em blocos

- **Contexto:** com 8 anos de dados, Sharpe e volatilidade são estimativas com incerteza, e os retornos têm ondas de volatilidade (dias agitados vêm juntos).
- **Decisão:** **bootstrap em blocos móveis** de 21 pregões (~1 mês), 1.000 reamostras, semente 42.
- **Alternativas consideradas:** bootstrap dia a dia (separaria os dias agitados e estreitaria os intervalos de forma artificial); fórmulas analíticas do erro do Sharpe (supõem retornos normais e independentes).
- **Consequência:** a diferença de volatilidade carteira x BOVA11 é sólida (intervalos de 33,1%–48,2% e 21,9%–31,6%), mas a de Sharpe não (+0,16, de −0,27 a +0,79). A H6 passa a "⚠️ em parte".
- **Onde está:** H6; `bootstrap_blocos` em `src/estatistica.py` e `indice_sharpe_retornos` em `src/risco.py`.

## DA-11 — Testes de estresse com crises reais e VaR de 10 dias observado

- **Contexto:** o VaR de 1 dia a 95% descreve um dia ruim "comum". Ele não diz quanto se perde numa crise nem em vários dias seguidos.
- **Decisão:** aplicar à carteira os choques de 4 crises do período (Joesley Day, greve dos caminhoneiros, pior dia e queda da pandemia) e comparar o VaR de 10 dias pela regra da raiz do tempo com as perdas acumuladas reais em janelas de 10 pregões.
- **Alternativas consideradas:** só a raiz do tempo (subestima a carteira em 4% a 95% e 3% a 99%); cenários hipotéticos (ficam como próximo passo).
- **Consequência:** na queda da pandemia, a carteira perderia R$ 5.602 de R$ 10.000 (16 vezes o VaR de 1 dia), contra R$ 4.545 no BOVA11. VaR de 10 dias da carteira de R$ 1.132 (95%) e R$ 1.991 (99%).
- **Onde está:** item 5 da Fase 03 e item 1.1 da Fase 04; `var_horizonte`, `choques_cenario` e `perda_cenario` em `src/risco.py`; `CENARIOS_ESTRESSE` em `src/config.py`; tabela no app.

## DA-12 — Mínima variância só com dados até 2019

- **Contexto:** otimizar os pesos com 2015–2022 e medir no mesmo período é usar o futuro.
- **Decisão:** estimar a carteira de **mínima variância** (sem venda a descoberto) e a de inverso da volatilidade **só com 2015–2019** e medir o resultado em 2020–2022.
- **Alternativas consideradas:** fronteira eficiente completa (exige prever retornos, que são muito incertos, DA-10); reotimização anual (próximo passo, parte 3).
- **Consequência:** a mínima variância (WEGE 45%, TOTS 30%, CVC 23%, MGLU 2%, GOL 0%) teve o menor risco entre as carteiras de ações em 2020–2022 (43,4%) e transformou R$ 10.000 em R$ 10.951, mas oscilou o dobro dos 21,8% previstos.
- **Onde está:** item 2 da Fase 05; `pesos_minima_variancia` em `src/risco.py`.

## DA-13 — Extensão até 2025 em uma seção própria, com 4 ações

- **Contexto:** o usuário pediu a análise até 2025. A GOL não tem dados públicos gratuitos depois de 29/12/2022: depois da recuperação judicial, a ação virou GOLL54, passou a valer menos de R$ 0,01 e está saindo da bolsa (o Yahoo Finance não tem o ticker).
- **Decisão:** manter a análise principal (2015–2022, 5 ações) comparável com a versão original e acrescentar a extensão no item 1.2 da Fase 04, com uma **carteira de 4 ações** (25% em cada, pesos mantidos), numa base nova (`acoes_2015_2025.csv`). As bases antigas não mudam, para que a versão original continue reproduzível.
- **Alternativas consideradas:** manter a GOL até 2022 e redistribuir o peso dela depois (mistura duas carteiras); obter os dados da GOL em fonte paga.
- **Consequência:** 2023–2025 viram um teste fora do tempo do VaR EWMA (5,2% de violações na carteira, Kupiec não rejeita em nenhum ativo). O download novo ajusta o preço da CVC pelos aumentos de capital de 2020 a 2022, então os números da CVC até 2022 diferem um pouco dos da análise principal.
- **Onde está:** item 1.2 da Fase 04; `ativos_com_dados` em `src/financas.py`; `retorno_carteira_pesos_fixos` ignora ativos sem peso (a GOL vazia não contamina a carteira); no app, a GOL fica desativada em períodos que terminam depois de 2022.

## DA-14 — Três fases da Covid

- **Contexto:** para comparar o risco antes e depois da Covid, é preciso definir datas objetivas.
- **Decisão:** **pré-pandemia** até 19/02/2020 (véspera da queda da bolsa), **pandemia** de 20/02/2020 a 05/05/2023 (fim da emergência de saúde declarado pela OMS) e **pós-pandemia** até 30/12/2025.
- **Alternativas consideradas:** pandemia só em 2020–2021 (fase mais aguda).
- **Consequência:** volatilidade da carteira de 26,6% → 48,1% → 34,1%; do BOVA11, de 22,4% → 30,5% → 14,8%; correlação média entre as ações de 0,20 → 0,45 → 0,26.
- **Onde está:** `PERIODOS_COVID` em `src/config.py` e `classificar_periodo` em `src/financas.py`; item 1.2 da Fase 04; tabela por fase no app.
