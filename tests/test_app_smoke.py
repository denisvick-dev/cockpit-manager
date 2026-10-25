# -*- coding: utf-8 -*-
"""Smoke test da interface Streamlit (AppTest): todas as telas e a corrida."""

import os
import re
import time

import pytest

from streamlit.testing.v1 import AppTest

import simulacao as sim

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


MENUS = [
    "🏠 Escritório",
    "🏁 Corrida",
    "🔧 Carro & Investimentos",
    "👨‍✈️ Pilotos & Contratos",
    "⚙️ Motores",
    "💰 Patrocinadores & Finanças",
    "📊 Campeonato",
    "🏆 Hall da Fama & Conquistas",
    "💾 Salvar / Carregar",
    "❓ Como Jogar",
]


@pytest.fixture()
def app():
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    assert not at.exception, f"tela inicial quebrou: {at.exception}"
    return at


@pytest.fixture()
def app_com_jogo(app, game):
    app.session_state["game"] = game
    app.session_state["fds"] = None
    app.run()
    return app


def test_tela_inicial(app):
    assert any(b.label == "🚥 Iniciar carreira" for b in app.button)
    assert any("Base de dados" in sb.label for sb in app.selectbox)


def test_botao_novo_jogo_confirma_antes_de_abandonar(app_com_jogo):
    app = app_com_jogo
    jogo_atual = app.session_state["game"]

    next(b for b in app.button if b.label == "🆕 Novo jogo").click().run()

    assert not app.exception
    assert app.session_state["game"] is jogo_atual
    assert app.button(key="cancelar_novo_jogo")
    assert app.button(key="confirmar_novo_jogo")

    app.button(key="cancelar_novo_jogo").click().run()

    assert app.session_state["game"] is jogo_atual
    assert not any(b.key == "confirmar_novo_jogo" for b in app.button)

    next(b for b in app.button if b.label == "🆕 Novo jogo").click().run()
    app.button(key="confirmar_novo_jogo").click().run()

    assert not app.exception
    assert app.session_state["game"] is None
    assert app.session_state["fds"] is None


@pytest.mark.parametrize("menu", MENUS)
def test_todas_as_telas_abrem(app_com_jogo, menu):
    app_com_jogo.session_state["menu"] = menu
    app_com_jogo.run()
    assert not app_com_jogo.exception, f"{menu}: {app_com_jogo.exception}"


def _largo(app, game, fds):
    etapa = game["calendario"][game["rodada"]]
    fds["molhado"] = False
    fds["grid"] = sim.simular_classificacao(game, etapa, False)
    fds["treino"] = sim.sessao_treino(game, etapa, False, fds["grid"])
    fds["treino"]["t0"] = 0.0
    fds["treino"]["concluido"] = True
    fds["treino_ok"] = True
    fds["paddock_ok"] = True
    app.run()
    app.button(key="dar_largada").click().run()
    return fds["replay"]


def test_corrida_janela_de_pit_pausa_e_volta(app_com_jogo, game):
    app = app_com_jogo
    app.session_state["menu"] = "🏁 Corrida"
    app.run()
    fds = app.session_state["fds"]
    stt = _largo(app, game, fds)
    assert stt and not app.exception

    chave = fds["chave"]
    plano = stt["rep"]["info"]
    # avança até a primeira parada planejada de um piloto do jogador
    meus = set(stt["pit_perguntar"])
    alvo = min((p, v) for p, d in plano.items() if p in meus and stt["pit_perguntar"][p] for v in d["pits_plano"])
    pid, volta = alvo
    s_por_volta = max(0.2, min(0.55, 24.0 / stt["rep"]["voltas"]))
    stt["t0"] = time.time() - s_por_volta * (volta + 0.5)
    app.run()
    pedido = stt.get("pit_aberto")
    assert pedido and pedido["pid"] == pid, "a janela do Pit Stop não abriu"
    assert pedido["volta"] == volta, "a janela não manteve a volta planejada"
    assert stt["lap"] >= volta, "a prova retrocedeu antes da parada"

    # confirma a troca de pneu + ritmo
    app.selectbox(key=f"dlg_pneu_{pid}_{chave}").set_value("Duro")
    app.radio(key=f"dlg_ritmo_{pid}_{chave}").set_value("Atacar")
    next(b for b in app.button if b.label.startswith("Trocar pneu")).click().run()

    assert volta in stt["pits"][pid]
    assert stt["pneus_manual"][pid][1] == "Duro"
    assert stt["ritmos"][pid] == "Atacar"
    assert stt.get("pit_aberto") is None
    assert not app.exception


def test_corrida_abre_pit_automatico_quando_pneu_esgota(app_com_jogo, game):
    app = app_com_jogo
    app.session_state["menu"] = "🏁 Corrida"
    app.run()
    fds = app.session_state["fds"]
    stt = _largo(app, game, fds)

    pid = next(iter(stt["pit_perguntar"]))
    stt["pit_perguntar"] = {piloto_id: False for piloto_id in stt["pit_perguntar"]}
    stt["rep"]["info"][pid]["pneus"] = ["Macio"]
    stt["rep"]["info"][pid]["pits_plano"] = []
    stt["rep"]["info"][pid]["paradas"] = 0
    for outro_pid, dados in stt["rep"]["info"].items():
        if outro_pid != pid:
            dados["pneus"] = ["Duro"]
    lap = 15
    s_por_volta = max(0.2, min(0.55, 24.0 / stt["rep"]["voltas"]))
    stt["t0"] = time.time() - s_por_volta * (lap + 0.5)
    etapa = game["calendario"][game["rodada"]]
    etapa["desgaste"] = 3.0

    app.run()

    assert stt.get("pit_aberto") == {
        "pid": pid,
        "volta": stt["lap"],
        "planejada": False,
        "esgotado": True,
    }
    assert stt["lap"] >= lap
    assert not app.exception


def test_pausa_e_velocidade_congelam_a_prova(app_com_jogo, game):
    app = app_com_jogo
    app.session_state["menu"] = "🏁 Corrida"
    app.run()
    fds = app.session_state["fds"]
    stt = _largo(app, game, fds)

    stt["pausado"] = True
    app.run()
    time.sleep(0.6)
    app.run()
    assert stt["lap"] <= 2, "a prova andou mesmo pausada"

    app.button(key="pausar_corrida").click().run()
    assert stt["pausado"] is False

    app.button(key="vel_4").click().run()
    assert stt["velocidade"] == 4
    assert not app.exception


def test_proxima_parada_avanca_a_transmissao(app_com_jogo, game):
    app = app_com_jogo
    app.session_state["menu"] = "🏁 Corrida"
    app.run()
    stt = _largo(app, game, app.session_state["fds"])
    # desliga as janelas automáticas para a corrida andar sozinha
    stt["pit_perguntar"] = {pid: False for pid in stt["pit_perguntar"]}
    app.run()

    botao = app.button(key="proxima_parada")
    if botao.disabled:
        pytest.skip("sem paradas planejadas à frente nesta etapa")

    alvo = int(re.search(r"volta (\d+)", botao.label).group(1))
    antes = stt["lap"]
    botao.click().run()

    assert stt["lap"] > antes
    assert stt["lap"] >= alvo - 1, f"deveria saltar para a volta {alvo}, parou na {stt['lap']}"
    assert not app.exception


def test_alerta_de_undercut_e_resposta_imediata(app_com_jogo, game):
    app = app_com_jogo
    app.session_state["menu"] = "🏁 Corrida"
    app.run()
    stt = _largo(app, game, app.session_state["fds"])
    stt["pit_perguntar"] = {pid: False for pid in stt["pit_perguntar"]}
    app.run()

    meus = set(stt["pit_perguntar"])
    pid = next(iter(meus))
    # procura, de forma determinística, uma volta com um rival logo atrás de mim
    voltas_rep = int(stt["rep"]["voltas"])
    spv = max(0.2, min(0.55, 24.0 / max(1, voltas_rep)))
    achado = None
    for lap in range(4, 25):
        stt["t0"] = time.time() - spv * lap
        app.run()
        lap_atual = int(stt["lap"])
        if lap_atual < 3:
            continue
        pits_antes = {k: [x for x in (v or []) if x < lap_atual] for k, v in stt["pits"].items()}
        linhas = sim.linhas_replay(stt["rep"], max(1, lap_atual - 1), pits_antes)
        pos = {ln["pid"]: ln["pos"] for ln in linhas if not ln.get("fora")}
        rival = next((r for r in pos if r not in meus and 0 < pos[r] - pos[pid] <= 3), None)
        if rival:
            achado = (lap_atual, rival)
            break
    assert achado, "nenhuma volta com rival a até 3 posições atrás"
    lap, rival = achado

    # simula o rival indo ao box nesta volta
    stt["pits"].setdefault(rival, []).append(lap)
    app.run()

    assert stt["undercut_ativo"].get(pid), "o alerta de undercut não foi registrado"
    assert any("undercut" in f for f in stt["feed"])
    botao = [b for b in app.button if b.label == "⚡ Responder agora"]
    assert botao, "o botão de resposta imediata não apareceu"

    botao[0].click().run()
    aberto = stt.get("pit_aberto")
    assert aberto and aberto["pid"] == pid and not aberto["planejada"]
    assert not app.exception


def test_overcut_na_transmissao_avisa_e_permite_atacar(app_com_jogo, game):
    app = app_com_jogo
    app.session_state["menu"] = "🏁 Corrida"
    app.run()
    stt = _largo(app, game, app.session_state["fds"])
    stt["pit_perguntar"] = {pid: False for pid in stt["pit_perguntar"]}
    app.run()

    meus = set(stt["pit_perguntar"])
    pid = next(iter(meus))
    spv = max(0.2, min(0.55, 24.0 / max(1, int(stt["rep"]["voltas"]))))
    achado = None
    for lap in range(4, 25):
        stt["t0"] = time.time() - spv * lap
        app.run()
        lap_atual = int(stt["lap"])
        pits_antes = {k: [x for x in (v or []) if x < lap_atual] for k, v in stt["pits"].items()}
        linhas = sim.linhas_replay(stt["rep"], max(1, lap_atual - 1), pits_antes)
        pos = {ln["pid"]: ln["pos"] for ln in linhas if not ln.get("fora")}
        rival = next((r for r in pos if r not in meus and 0 < pos[pid] - pos[r] <= 3), None)
        if rival:
            achado = (lap_atual, rival)
            break
    assert achado, "nenhuma volta com rival à frente a até 3 posições"
    lap, rival = achado

    stt["pits"].setdefault(rival, []).append(lap)
    app.run()

    assert stt["overcut_ativo"].get(pid), "o alerta de overcut não foi registrado"
    assert any("overcut" in f for f in stt["feed"])

    botao = [b for b in app.button if b.label == "🔥 Ficar e atacar"]
    assert botao, "o botão de overcut não apareceu"
    botao[0].click().run()

    assert stt["ritmos"][pid] == "Atacar"
    assert not app.exception
