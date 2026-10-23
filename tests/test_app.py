"""Teste do app Streamlit: abre sem erro, mostra os 5 indicadores e reage a pesos zerados."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


def test_app_abre_e_mostra_os_indicadores():
    app = AppTest.from_file(APP, default_timeout=60).run()
    assert not app.exception
    assert len(app.metric) == 5
    assert app.metric[0].label == 'Volatilidade anual'
    assert len(app.table) == 1 and len(app.table[0].value) == 4   # os 4 cenários de estresse


def test_app_avisa_quando_todos_os_pesos_sao_zero():
    app = AppTest.from_file(APP, default_timeout=60).run()
    for controle in app.sidebar.slider:
        if controle.label != 'Período':
            controle.set_value(0)
    app.run()
    assert not app.exception
    assert any('pelo menos um ativo' in aviso.value for aviso in app.warning)
