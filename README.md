# 🛡️ Cálculo do Risco das Ações e da Carteira (2015–2022)

**Quanto risco cada ação carrega? Juntar as ações numa carteira é mais arriscado do que comprar o índice? E quanto se perde num dia ruim?**

<div align="center">
<img src="Imagens/Capa.png" width="300px">
</div>

**Python · Pandas · SciPy · Risco Financeiro (volatilidade, VaR, CVaR) · Streamlit · CRISP-DM**

| 📊 Destaques | |
|---|---|
| Período analisado | **8 anos** (jan/2015 a dez/2022), **1.988 pregões**, 5 ações + BOVA11 |
| Risco de cada ativo | Volatilidade de **26,0%** ao ano no BOVA11 (o menor em 8 de 8 anos) a **77,1%** na GOL. CVC, GOL e MGLU chegaram a cair **mais de 92%** |
| A carteira (20% em cada) | Mais arriscada que o BOVA11 (**39,6%** x 26,0%, diferença sólida). Rendeu mais (**18,1%** ao ano x 10,6%; Sharpe **0,24** x 0,08), mas o bootstrap mostra que 8 anos não bastam para garantir que o risco foi pago |
| Num dia ruim / numa crise | Com R$ 10.000 na carteira, perda de **mais de R$ 343** em 1 de cada 20 pregões. Se a queda da pandemia se repetisse: **−R$ 5.602** (16 vezes isso) |
| VaR que funciona | O **VaR EWMA filtrado** errou em **6,2%** dos pregões da pandemia (esperado: 5%) e passou nos testes de Kupiec e Christoffersen; o VaR fixo de 2019 errou em **12,5%** |
| Principal descoberta | Nos piores dias do mercado, a correlação entre as ações **dobra** (0,25 → 0,51): a diversificação protege menos quando mais se precisa dela |
| Entrega | Relatório + tabela de indicadores + **app Streamlit** que calcula o risco de qualquer carteira + **34 testes automatizados** (com CI) |

---

## 📑 Sumário

1. [Contexto do problema](#1-contexto-do-problema)
2. [Objetivo](#2-objetivo)
3. [Base de dados](#3-base-de-dados)
4. [Estrutura do projeto](#4-estrutura-do-projeto)
5. [Como executar](#5-como-executar)
6. [Etapas do projeto (CRISP-DM)](#6-etapas-do-projeto-crisp-dm)
7. [Principais descobertas](#7-principais-descobertas)
8. [Construção da solução](#8-construção-da-solução)
9. [Resultado: o risco da carteira](#9-resultado-o-risco-da-carteira)
10. [O VaR funcionou na pandemia?](#10-o-var-funcionou-na-pandemia)
11. [App interativo (Streamlit)](#11-app-interativo-streamlit)
12. [O que mudou da v1 para a v2](#12-o-que-mudou-da-v1-para-a-v2)
13. [Insights](#13-insights)
14. [Limites](#14-limites)
15. [Próximos passos](#15-próximos-passos)

---

## 1. Contexto do problema

Retorno é só metade da história de um investimento. A outra metade é o **risco**: quanto o valor oscila no caminho, quanto pode cair e quanto se perde num dia ruim. Duas ações com o mesmo retorno podem ser investimentos muito diferentes se uma delas cair 90% no meio do caminho.

Esta é a **parte 2** do estudo. A [parte 1](https://github.com/RafaelSilva89/Analise_do_Comportamento_da_Carteira_de_Acoes-Financas_parte_1) mediu o **retorno** da carteira; aqui medimos o **risco** das mesmas ações, no mesmo período (com a recessão de 2015–2016 e a pandemia de 2020):

| Ação | Empresa (setor) |
|---|---|
| **GOL** | Gol Linhas Aéreas (aviação) |
| **CVC** | CVC Brasil (turismo) |
| **WEGE** | WEG (máquinas e equipamentos elétricos) |
| **MGLU** | Magazine Luiza (varejo) |
| **TOTS** | Totvs (software) |
| **BOVA** | BOVA11: fundo que replica o Ibovespa (**referência**) |

## 2. Objetivo

> **Pergunta de negócio:** *Quanto risco cada ação carrega? Uma carteira com as 5 ações, com o mesmo peso em cada, é mais arriscada do que investir no BOVA11? Esse risco extra foi recompensado, e quanto se pode perder num dia ruim?*

## 3. Base de dados

| Arquivo | Fonte | Conteúdo |
|---|---|---|
| `Datasets/acoes.csv` | Yahoo Finance (`yfinance`) | Preço de **fechamento diário** (R$) de `GOLL4.SA`, `CVCB3.SA`, `WEGE3.SA`, `MGLU3.SA`, `TOTS3.SA` e `BOVA11.SA`, de 02/01/2015 a 29/12/2022. É a mesma base da parte 1 |
| `Datasets/cdi.csv` | Banco Central (série 12 do SGS) | Taxa diária do **CDI**, a referência de "investimento sem risco" para o Índice de Sharpe |

> ⚠️ A versão original também tinha um `stocks.csv`, que nenhuma análise usava. Conferindo, ele é um **passeio aleatório simulado** (tem fins de semana, valores negativos e passos de desvio ~1,00 em todas as colunas), sem relação com os preços reais. Foi removido na v2 para não ser confundido com dados reais (continua no histórico do git).

## 4. Estrutura do projeto

```
Calculo_do_risco_das_acoes-Financas_parte_2/
├── .github/workflows/testes.yml           # roda os testes a cada push (GitHub Actions)
├── Datasets/
│   ├── acoes.csv                          # preços de fechamento diários (Yahoo Finance)
│   └── cdi.csv                            # taxa diária do CDI (Banco Central)
├── Imagens/                               # gráficos gerados pelos notebooks
├── Notebooks/
│   ├── Cálculo do risco das ações - Finanças parte 2.ipynb       # versão original
│   └── Cálculo do risco das ações - Finanças parte 2 - v2.ipynb  # versão reorganizada (CRISP-DM)
├── docs/
│   └── decisoes_analiticas.md             # registro das decisões do projeto (DA-01 a DA-08)
├── reports/
│   ├── indicadores_risco.csv              # painel de risco de cada ativo e da carteira
│   └── ficha_indicadores.json             # período, convenções, backtest e avisos de uso
├── src/
│   ├── config.py                          # caminhos e convenções (252 pregões, VaR de 95%, janelas)
│   ├── financas.py                        # retornos, CAGR, volatilidade, maior queda, Sharpe, simulação
│   ├── risco.py                           # VaR (histórico, móvel, EWMA, 10 dias), CVaR, beta, carteira, estresse, backtest
│   ├── estatistica.py                     # testes das hipóteses (com tamanho de efeito), regra do IQR e bootstrap
│   └── graficos.py                        # funções de gráficos
├── tests/
│   ├── test_financas.py                   # testes das funções de src/financas.py
│   ├── test_risco.py                      # testes das medidas de risco e dos testes estatísticos
│   └── test_app.py                        # abre o app Streamlit e confere os indicadores
├── app.py                                 # app Streamlit (calculadora de risco de carteira)
├── pytest.ini
├── requirements.txt
└── README.md
```

## 5. Como executar

```bash
# 1. Clonar o repositório
git clone https://github.com/RafaelSilva89/Calculo_do_risco_das_acoes-Financas_parte_2.git
cd Calculo_do_risco_das_acoes-Financas_parte_2

# 2. Instalar as dependências
pip install -r requirements.txt

# 3. Abrir o notebook
jupyter notebook "Notebooks/Cálculo do risco das ações - Finanças parte 2 - v2.ipynb"

# 4. Abrir a calculadora de risco
streamlit run app.py

# 5. Rodar os testes
pytest
```

## 6. Etapas do projeto (CRISP-DM)

| Fase | O que foi feito |
|---|---|
| **01. Entendimento do negócio** | Definição da pergunta e das medidas de risco |
| **02. Preparação dos dados** | Conferência da base, dias extremos pela regra do IQR, análise exploratória com **7 hipóteses** (com testes estatísticos e tamanho de efeito) e criação dos retornos |
| **03. Indicadores de risco** | Volatilidade, semivolatilidade, maior queda, VaR (1 e 10 dias, 95% e 99%), CVaR, beta e Sharpe com **intervalo por bootstrap**; risco da carteira; **backtest do VaR** móvel e EWMA (Kupiec e Christoffersen) e teste anti-vazamento |
| **04. Avaliação** | Risco em reais, **testes de estresse** com 4 crises reais, risco previsto x observado na pandemia e contribuição de cada ação para o risco |
| **05. Implantação** | Tabela de indicadores, ficha em JSON, carteiras de **mínima variância** e inverso da volatilidade testadas com dados novos e app Streamlit |

> ℹ️ Não há modelo de Machine Learning. A fase de "Modelagem" do CRISP-DM foi adaptada para o **cálculo dos indicadores de risco**. Onde o roteiro de modelos tem um equivalente real, ele foi usado: a separação treino/teste vira o **backtest do VaR**, e o teste anti-vazamento mostra o que acontece quando o VaR "olha o futuro".

## 7. Principais descobertas

**O BOVA11 é o ativo menos volátil, e todas as ações oscilam mais**

<div align="center">
<img src="Imagens/Volatilidade%20por%20ativo.png" width="650px">
</div>

- A GOL oscila **2,96 vezes** mais que o BOVA11; a WEGE, a ação mais calma, **1,35 vez**. O BOVA11 foi o menos volátil em **8 de 8 anos**.

**O risco disparou na pandemia, e para CVC e GOL não voltou**

<div align="center">
<img src="Imagens/Volatilidade%20movel.png" width="850px">
</div>

- Em 2020, o movimento médio diário do BOVA11 foi de **0,87%** para **1,77%**; o da CVC, de **1,71%** para **4,38%**. Em 2022, a CVC ainda se movia o dobro de 2019.

**Os dias extremos são muito mais comuns do que a curva normal prevê**

<div align="center">
<img src="Imagens/Caudas%20gordas.png" width="850px">
</div>

- Dias com movimento maior que 3 desvios padrão aconteceram **3,9 a 5,8 vezes** mais do que numa curva normal. Por isso o VaR é calculado pelo **histórico**, e não pela fórmula da normal.

**Nos piores dias, as ações caem juntas**

<div align="center">
<img src="Imagens/Correlacao%20normal%20x%20estresse.png" width="850px">
</div>

- A correlação média entre as 5 ações vai de **0,25** nos dias normais para **0,51** nos 10% piores dias do BOVA11, e sobe em **10 de 10 pares**.

> 🧪 **Testes estatísticos** (o que importa é o tamanho do efeito, não o p):
> - **H1:** Brown-Forsythe com p < 0,001; razão de desvios de 1,35 (WEGE) a 2,96 (GOL).
> - **H2:** Kruskal-Wallis entre os anos com ε² = 0,025 (efeito pequeno); Mann-Whitney 2020 x 2015–19 com correlação de postos de 0,20.
> - **H3:** Jarque-Bera com curtose em excesso de 5,2 a 14,2 (0 na normal); teste binomial dos dias além de 3 desvios com p < 0,001.
> - **H4:** Wilcoxon pareado nos 10 pares com p = 0,002 e aumento mediano de +0,26 na correlação. Parte do efeito é mecânica: pela volatilidade do mercado, o aumento é menor (0,32 → 0,39).
> - **H5:** Wilcoxon pareado nos 8 anos com p = 0,008; a diversificação reduziu o risco em todos os anos.
> - **H6:** bootstrap em blocos (1.000 reamostras): volatilidade da carteira de 33,1% a 48,2% e do BOVA11 de 21,9% a 31,6% (sem sobreposição); diferença de Sharpe de −0,27 a +0,79 (inclui o zero).
> - **H7:** Spearman de −0,14 entre risco e retorno (p = 0,79; com 6 ativos, o teste tem pouca força).

## 8. Construção da solução

**1️⃣ Retornos, não preços:** o risco é medido pela variação percentual de um dia para o outro, que é comparável entre ações de qualquer preço. O desvio do **preço** (usado na versão original) depende do nível do preço: por ele, o BOVA11 pareceria o mais arriscado.

**2️⃣ Do dia para o ano:** o desvio cresce com a **raiz** do tempo, então a volatilidade anual é o desvio diário × **√252** pregões.

**3️⃣ Medidas de risco**, cada uma respondendo a uma pergunta:

| Medida | Pergunta |
|---|---|
| **Volatilidade** | Quanto o preço oscila num ano típico? |
| **Semivolatilidade** | E contando só as quedas? |
| **Maior queda** | Qual foi o pior momento, do pico ao fundo? |
| **VaR 95%** | Num dia ruim (1 em 20), quanto se perde? |
| **CVaR 95%** | E quando passa do VaR, quanto se perde em média? |
| **Beta** | Quanto a ação amplifica os movimentos do mercado? |
| **Índice de Sharpe** | O risco foi pago com retorno acima do CDI? |

**4️⃣ Risco da carteira:** a volatilidade de uma carteira não é a média das volatilidades, porque as ações não andam 100% juntas. Ela vem da **matriz de covariância** (fórmula w'Σw), e a **contribuição de cada ação** mostra de onde vem o risco.

**5️⃣ Backtest do VaR:** o VaR estimado só com o passado é comparado com as perdas de 2020–2022. O **teste de Kupiec** verifica se ele foi superado em ~5% dos dias, como deveria, e o de **Christoffersen**, se os erros chegam isolados (e não em sequência). Três formas de estimar:
- **fixo de 2019:** um único número, com 2015–2019;
- **móvel:** recalculado todo dia com o último ano;
- **EWMA filtrado:** a volatilidade de hoje por média móvel exponencial (o dia de ontem pesa 6%) x os retornos padronizados do último ano. Reage a um choque já no dia seguinte.

**6️⃣ Incerteza e crises:** o **bootstrap em blocos** (sorteio de meses inteiros, 1.000 vezes) mede o quanto os números mudariam com outros 8 anos parecidos. Os **testes de estresse** aplicam à carteira os choques de 4 crises reais. O **VaR de 10 dias** é comparado com a regra da raiz do tempo.

## 9. Resultado: o risco da carteira

| | Carteira (20% em cada) | BOVA11 | CDI |
|---|---|---|---|
| **Volatilidade anual** | 39,6% | **26,0%** | 0,3% |
| **Maior queda** | −65,8% | **−46,9%** | 0% |
| **Crescimento anual (CAGR)** | **18,1%** | 10,6% | 8,6% |
| **Índice de Sharpe** | **0,24** | 0,08 | – |
| **Perda num dia ruim (VaR 95%), em R$ 10 mil** | R$ 343 | **R$ 235** | – |
| **Perda média nos piores dias (CVaR 95%)** | R$ 552 | **R$ 367** | – |

- ✅ **A carteira é mais arriscada que o BOVA11:** pelo bootstrap, os intervalos de 95% da volatilidade (33,1% a 48,2% x 21,9% a 31,6%) nem se encostam.
- ⚠️ **O risco extra parece ter sido pago, mas sem certeza:** Sharpe de 0,24 contra 0,08, porém o intervalo de 95% da diferença vai de −0,27 a +0,79 e inclui o zero. E o ganho veio quase todo da MGLU, como mostra a parte 1.
- ✅ **Diversificar funcionou:** a média das volatilidades das 5 ações é 55,6%, mas a carteira oscila 39,6% (**29% menos risco**).

**Cada ação tem 20% do dinheiro, mas não 20% do risco**

<div align="center">
<img src="Imagens/Contribuicao%20para%20o%20risco.png" width="650px">
</div>

- A **GOL** responde por **31%** do risco. GOL, MGLU e CVC têm 60% do dinheiro e **77%** do risco; WEGE e TOTS, 40% do dinheiro e só 23% do risco.

**E se as crises do período se repetissem?** (R$ 10.000 investidos)

| Cenário | Carteira | BOVA11 |
|---|---|---|
| Joesley Day (18/05/2017) | −R$ 1.056 | −R$ 866 |
| Greve dos caminhoneiros (mai/2018) | **−R$ 35** | −R$ 697 |
| Pior dia da pandemia (12/03/2020) | −R$ 2.300 | −R$ 1.457 |
| Queda da pandemia (19/02 a 23/03/2020) | **−R$ 5.602** | −R$ 4.545 |

- Nas crises que atingem o mercado todo, a carteira perde mais que o BOVA11. Na greve dos caminhoneiros, um choque que não atingiu todas as empresas igualmente, MGLU e CVC subiram e a carteira quase não perdeu.
- Em 10 pregões, a perda que só foi superada em 1 de cada 20 janelas é de **R$ 1.132**; a regra da raiz do tempo (VaR de 1 dia × √10) dá um valor 4% menor.

**Pesos fixos x comprar e manter:** a fórmula da versão original supõe que a carteira volta aos 20% todo dia. Comprando e mantendo, a MGLU chegou a **91%** da carteira, e a volatilidade sobe para **45,5%** (maior queda de **−87,2%**). Rebalanceando uma vez por ano: **37,6%** de volatilidade e Sharpe de **0,46**.

## 10. O VaR funcionou na pandemia?

<div align="center">
<img src="Imagens/Backtest%20VaR%20carteira.png" width="850px">
</div>

| VaR da carteira | Como é estimado | Dias em que a perda passou do VaR (2020–2022) |
|---|---|---|
| Fixo de 2019 | Um único número, com 2015–2019 | **12,5%** ❌ (Kupiec rejeita) |
| Móvel | Recalculado todo dia com o último ano | 6,6% ⚠️ (passa no Kupiec, mas erra em sequência em CVC, WEGE e TOTS) |
| **EWMA filtrado** | Volatilidade exponencial x retornos padronizados | **6,2%** ✅ (passa em Kupiec e Christoffersen; de 5,5% a 6,2% em todos os ativos) |
| "Que vê o futuro" | Com 2015–2022 inteiro | 5,0% (perfeito por construção: **vazamento**) |

- ❌ O VaR de 2019 subestimou a perda de **todos** os ativos na pandemia: na CVC, foi superado em **20%** dos dias, porque ela parecia calma até 2019.
- ⚠️ O **VaR móvel** demora a reagir: 12 das 49 violações da carteira aconteceram em fevereiro e março de 2020, porque cada dia novo pesa só 1/252 na janela.
- ✅ O **VaR EWMA** reage já no dia seguinte a um choque (no gráfico, a linha azul despenca em março de 2020) e é a estimativa recomendada de "perda para amanhã".
- 💡 O VaR calculado com o período inteiro acerta "exatamente" 5% porque **já conhece** as perdas. É o equivalente, em risco, a avaliar um modelo nos próprios dados de treino.

## 11. App interativo (Streamlit)

A **calculadora de risco** permite montar qualquer carteira com as 5 ações e o BOVA11 e ver:

1. **Volatilidade**, **perda num dia ruim (VaR e CVaR) em reais**, **maior queda** e **Índice de Sharpe**, lado a lado com o BOVA11;
2. **Peso no dinheiro x peso no risco** de cada ativo e a razão de diversificação;
3. Quanto a carteira perderia se as **4 crises do período** se repetissem (testes de estresse);
4. **Volatilidade ao longo do tempo** e a **correlação** entre os ativos escolhidos.

O usuário escolhe o valor investido, o período e o peso de cada ativo.

```bash
streamlit run app.py
```

## 12. O que mudou da v1 para a v2

| Tema | v1 (original) | v2 |
|---|---|---|
| Estrutura | Seções soltas | Roteiro **CRISP-DM** completo, funções em `src/`, testes e CI |
| Retorno do período | Log lido como percentual (CVC "−121,94%") | **Variação real** (−70,5%) e CAGR |
| Retorno por ano | Do 1º ao último pregão do mesmo ano | Do fim do ano anterior ao fim do ano |
| Medida de risco | Desvio de **8 retornos anuais** e desvio do preço | **Volatilidade dos retornos diários** (√252), com semivolatilidade, maior queda, VaR, CVaR e beta |
| Leitura do desvio diário | "A GOL varia 4 reais e 85 centavos" | **4,86% ao dia** (é percentual, não reais) |
| Anualização | × 246 (errado) e √246 | √252 (convenção de mercado) |
| Coeficiente de variação | −1.087% para a GOL (média negativa) | Removido; **Índice de Sharpe** no lugar |
| Correlação | "Menor entre MGLU e TOTS" | Menor entre **CVC e WEGE (0,296)**; e a correlação **dobra** nos dias de estresse |
| Risco da carteira | 0,39 x 0,25, sem retorno | 39,6% x 26,0% **com** retorno, Sharpe, maior queda e contribuição de cada ação |
| Premissa dos pesos | Implícita (pesos fixos todo dia) | Explícita, comparada com comprar e manter e com rebalancear todo ano |
| Previsão de perda | Não havia | **VaR testado fora da amostra** (fixo, móvel e EWMA; Kupiec e Christoffersen), VaR de 10 dias e 99% e teste anti-vazamento |
| Crises | Não havia | **Testes de estresse** com 4 crises reais, em reais |
| Incerteza | Não havia | **Intervalos de confiança por bootstrap** em blocos (volatilidade, VaR e Sharpe) |
| Pesos | Só pesos iguais | Mínima variância e inverso da volatilidade, estimados em 2015–2019 e **testados em 2020–2022** |
| Testes estatísticos | Não havia | 7 hipóteses, cada uma com teste e **tamanho de efeito** |
| Dados | Incluía `stocks.csv` (simulado, não usado) | Removido; CDI acrescentado |
| Entrega | Notebook | Notebook + `reports/` + ficha JSON + **app Streamlit** + 34 testes automatizados (com CI) |

## 13. Insights

1. **O BOVA11 é o investimento menos arriscado** em todas as medidas e em todos os 8 anos.
2. **Volatilidade sozinha não conta a história:** CVC, GOL e MGLU chegaram a perder mais de 92% do pico ao fundo.
3. **Diversificar funciona, mas falha nas crises:** a carteira cortou 29% do risco, mas nos piores dias a correlação entre as ações dobra. Na queda da pandemia, a carteira perderia R$ 5.602 de R$ 10.000, mais que o BOVA11.
4. **O risco se concentra:** com 20% do dinheiro, a GOL responde por 31% do risco da carteira.
5. **"O risco foi recompensado" é uma estimativa, não uma certeza:** Sharpe de 0,24 x 0,08, mas o intervalo da diferença inclui o zero. A WEGE teve o 2º menor risco e o melhor Sharpe (0,51); GOL e CVC renderam menos que o CDI.
6. **O VaR precisa reagir rápido:** o VaR de 2019 foi superado em 12,5% dos pregões da carteira na pandemia, e o de janela móvel errou em sequência. O VaR EWMA ficou em 6,2% e passou nos dois testes.
7. **Otimizar pelo passado ajuda, mas não blinda:** a mínima variância de 2019 teve o menor risco entre as carteiras de ações em 2020–2022 (e transformou R$ 10.000 em R$ 10.951), mas oscilou o dobro do previsto.
8. **A conta da versão original estava certa; as interpretações, não:** log lido como percentual, desvio de retorno lido em reais, coeficiente de variação com média negativa e risco analisado sem o retorno.

## 14. Limites

- **Um único período (2015–2022)** e **5 ações escolhidas depois de conhecer o resultado**: o risco do passado não garante o do futuro.
- **Poucos ativos e poucos anos:** com 6 ativos, 10 pares e 8 anos, vários testes têm pouca força estatística, e o Sharpe de 8 anos é muito incerto.
- **VaR de 1 dia a 95%:** não cobre crises como a de março de 2020 (16 vezes o VaR); o VaR de 10 dias usa janelas sobrepostas.
- **Uma única janela de teste (2020–2022)** para o backtest e para a mínima variância, dominada pela pandemia.
- **Correlação nos dias de estresse:** parte do aumento é mecânica, pela forma de escolher os dias.
- **Sem dividendos, corretagem e impostos**, e sem o custo de rebalancear a carteira.

## 15. Próximos passos

1. **Otimização de pesos (parte 3):** fronteira eficiente de Markowitz e os algoritmos citados na versão original (subida da encosta, têmpera simulada e algoritmo genético), com **reotimização anual** e avaliação em várias janelas (*walk-forward*).
2. **Covariância mais estável** (encolhimento de Ledoit-Wolf ou EWMA), para que a mínima variância dependa menos de um passado calmo.
3. **GARCH com reversão à média** e distribuição t de Student, comparado ao EWMA no backtest.
4. **Cenários hipotéticos** (alta de juros ou do dólar), com o choque de cada setor.
5. **Atualizar os dados** até hoje (`ATUALIZAR_DADOS = True`), substituindo o ticker da GOL, e repetir o backtest com mais anos de teste.
6. **Publicar o app** no Streamlit Community Cloud.

---

**Autor:** Rafael R. Silva · [GitHub](https://github.com/RafaelSilva89)
