"""Funções de gráficos usadas no notebook. Cada gráfico é salvo na pasta Imagens/ do projeto."""
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns

PASTA_IMAGENS = Path(__file__).resolve().parents[1] / 'Imagens'

CORES = {'GOL': '#E07A1F', 'CVC': '#2E86AB', 'WEGE': '#3B8B5A', 'MGLU': '#C0392B', 'TOTS': '#7D5BA6',
         'BOVA': '#555555', 'CARTEIRA': '#111111', 'REBALANCEADA': '#E0A800', 'CDI': '#1F9BD1'}
COR_POSITIVO = '#3B8B5A'
COR_NEGATIVO = '#C0392B'


def salvar(nome_arquivo):
    plt.savefig(PASTA_IMAGENS / f'{nome_arquivo}.png', bbox_inches='tight', dpi=110)


def titulo(texto, subtitulo=None):
    plt.suptitle(texto, fontsize=16, x=0.01, ha='left', y=1.02)
    if subtitulo:
        plt.figtext(0.01, 0.955, subtitulo, ha='left', fontsize=11, color='#656565', style='italic')


def plot_linhas(dados, titulo_grafico, nome_arquivo, ylabel='', subtitulo=None, log=False, percentual=False):
    """Uma linha por coluna.

    percentual=False -> a legenda mostra o valor final de cada linha (ordenada do maior para o menor).
    percentual=True  -> eixo y em % e linha de referência no zero.
    """
    plt.figure(figsize=(14, 6))
    ordem = dados.columns if percentual else dados.iloc[-1].sort_values(ascending=False).index
    for coluna in ordem:
        estilo = {'lw': 3} if coluna == 'CARTEIRA' else {'lw': 1.6}
        rotulo = coluna if percentual else f'{coluna}: {dados[coluna].iloc[-1]:.2f}'.replace('.', ',')
        plt.plot(dados.index, dados[coluna], color=CORES.get(coluna), label=rotulo, **estilo)
    if log:
        plt.yscale('log')
    if percentual:
        plt.axhline(0, color='black', lw=0.8)
        plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    plt.ylabel(ylabel)
    plt.legend(title=None if percentual else 'Valor no fim do período', loc='upper left', frameon=False)
    sns.despine()
    titulo(titulo_grafico, subtitulo)
    salvar(nome_arquivo)
    plt.show()


def plot_barras_retorno(serie, titulo_grafico, nome_arquivo, ylabel='Retorno', subtitulo=None):
    """Barras verdes (positivo) e vermelhas (negativo), com o valor em % em cada barra."""
    plt.figure(figsize=(10, 5))
    cores = [COR_POSITIVO if v >= 0 else COR_NEGATIVO for v in serie.values]
    ax = plt.bar(serie.index.astype(str), serie.values, color=cores)
    plt.bar_label(ax, labels=[f'{v:+.1%}'.replace('.', ',') for v in serie.values], padding=3)
    plt.axhline(0, color='black', lw=0.8)
    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    plt.ylabel(ylabel)
    sns.despine()
    titulo(titulo_grafico, subtitulo)
    salvar(nome_arquivo)
    plt.show()


def plot_retorno_anual_grade(retornos, titulo_grafico, nome_arquivo):
    """Um gráfico de barras por ação, com o retorno de cada ano."""
    fig, axs = plt.subplots(2, 3, figsize=(16, 8), sharey=True)
    for ax, coluna in zip(axs.ravel(), retornos.columns):
        valores = retornos[coluna]
        ax.bar(valores.index.astype(str), valores.values,
               color=[COR_POSITIVO if v >= 0 else COR_NEGATIVO for v in valores.values])
        ax.axhline(0, color='black', lw=0.8)
        ax.set_title(coluna, fontsize=13)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.tick_params(axis='x', rotation=45)
        sns.despine(ax=ax)
    titulo(titulo_grafico)
    plt.tight_layout()
    salvar(nome_arquivo)
    plt.show()


def plot_barras(serie, titulo_grafico, nome_arquivo, ylabel='', subtitulo=None, formato='{:.1%}', referencia=None):
    """Barras na cor de cada ativo, com o valor escrito em cada barra.

    referencia -> valor de uma linha tracejada horizontal (ex.: o risco do BOVA11).
    """
    plt.figure(figsize=(10, 5))
    barras = plt.bar(serie.index.astype(str), serie.values, color=[CORES.get(i, '#7A7A7A') for i in serie.index])
    plt.bar_label(barras, labels=[formato.format(v).replace('.', ',') for v in serie.values], padding=3)
    if referencia is not None:
        plt.axhline(referencia, color='black', ls='--', lw=1)
    if '%' in formato:
        plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    plt.ylabel(ylabel)
    sns.despine()
    titulo(titulo_grafico, subtitulo)
    salvar(nome_arquivo)
    plt.show()


def plot_heatmap(matriz, titulo_grafico, nome_arquivo, ax=None):
    """Mapa de calor de uma matriz de correlação (vermelho = andam juntos, azul = em sentidos opostos)."""
    if ax is None:
        plt.figure(figsize=(8, 6))
        ax = plt.gca()
    sns.heatmap(matriz, annot=True, fmt='.2f', cmap='RdBu_r', center=0, vmin=-1, vmax=1, ax=ax)
    ax.set_title(titulo_grafico, fontsize=13, loc='left')
    if nome_arquivo:
        salvar(nome_arquivo)
        plt.show()
