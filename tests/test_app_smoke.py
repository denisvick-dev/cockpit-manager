# -*- coding: utf-8 -*-
"""Smoke test da interface Streamlit (AppTest): todas as telas e a corrida."""

import os
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
    stt["t0"] = time.time() - 0.41 * (volta + 0.6)
    app.run()
    pedido = stt.get("pit_aberto")
    assert pedido and pedido["pid"] == pid, "a janela do Pit Stop não abriu"
    assert stt["lap"] == volta, "a prova não congelou na volta da parada"

    # confirma a troca de pneu + ritmo
    app.selectbox(key=f"dlg_pneu_{pid}_{chave}").set_value("Duro")
    app.radio(key=f"dlg_ritmo_{pid}_{chave}").set_value("Atacar")
    next(b for b in app.button if b.label.startswith("Trocar pneu")).click().run()

    assert volta in stt["pits"][pid]
    assert stt["pneus_manual"][pid][1] == "Duro"
    assert stt["ritmos"][pid] == "Atacar"
    assert stt.get("pit_aberto") is None
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

    antes = stt["lap"]
    app.button(key="proxima_parada").click().run()

    assert stt["lap"] > antes + 2, "o atalho deveria pular para a próxima parada planejada"
    assert not app.exception


def test_alerta_de_undercut_e_resposta_imediata(app_com_jogo, game):
    app = app_com_jogo
    app.session_state["menu"] = "🏁 Corrida"
    app.run()
    stt = _largo(app, game, app.session_state["fds"])
    stt["pit_perguntar"] = {pid: False for pid in stt["pit_perguntar"]}
    app.run()

    lap = max(5, int(stt["lap"]))
    stt["t0"] = time.time() - 0.41 * lap
    app.run()
    lap = int(stt["lap"])
    pits_antes = {k: [x for x in (v or []) if x < lap] for k, v in stt["pits"].items()}
    linhas = sim.linhas_replay(stt["rep"], max(1, lap - 1), pits_antes)
    pos = {ln["pid"]: ln["pos"] for ln in linhas if not ln.get("fora")}
    meus = set(stt["pit_perguntar"])
    pid = next(iter(meus))
    rival = next(
        (r for r in pos if r not in meus and 0 < pos[r] - pos[pid] <= 3),
        None,
    )
    assert rival, "a corrida precisa de um rival próximo para o teste"

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
