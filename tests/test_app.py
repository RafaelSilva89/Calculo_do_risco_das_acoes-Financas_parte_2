"""Teste do app Streamlit: abre sem erro, mostra os indicadores, respeita as datas e desativa a GOL depois de 2022."""
from datetime import date
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


def abrir():
    return AppTest.from_file(APP, default_timeout=60).run()


def gol(app):
    return next(s for s in app.sidebar.slider if s.label.startswith('GOL'))


def test_app_abre_com_2015_a_2025_e_mostra_os_indicadores():
    app = abrir()
    assert not app.exception
    assert len(app.metric) == 5
    assert app.metric[0].label == 'Volatilidade anual'
    assert gol(app).disabled and gol(app).value == 0
    assert len(app.table) == 2                       # fases da Covid + cenários de estresse
    assert len(app.table[0].value) == 3 and len(app.table[1].value) == 4


def test_app_libera_a_gol_quando_o_periodo_termina_ate_2022():
    app = abrir()
    app.sidebar.date_input[1].set_value(date(2022, 12, 29)).run()
    assert not app.exception
    assert not gol(app).disabled and gol(app).value == 20


def test_app_avisa_quando_as_datas_estao_invertidas():
    app = abrir()
    app.sidebar.date_input[0].set_value(date(2024, 1, 2))
    app.sidebar.date_input[1].set_value(date(2023, 1, 2)).run()
    assert any('depois da data de início' in aviso.value for aviso in app.warning)


def test_app_avisa_quando_todos_os_pesos_sao_zero():
    app = abrir()
    for controle in app.sidebar.slider:
        if not controle.disabled:
            controle.set_value(0)
    app.run()
    assert not app.exception
    assert any('pelo menos um ativo' in aviso.value for aviso in app.warning)
