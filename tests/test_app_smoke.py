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


def _salva_e_corre(app, game, n=1):
    """Roda n corridas completas pelo motor (sem passar pela transmissão)."""
    for _ in range(n):
        etapa = game["calendario"][game["rodada"]]
        grid = sim.simular_classificacao(game, etapa, False)
        res, ev = sim.simular_corrida(game, etapa, grid, {}, False, clima=sim.plano_clima(game, etapa, False))
        sim.aplicar_resultado(game, etapa, grid, res, False, eventos=ev)
        game["rodada"] += 1
    app.session_state["game"] = game


def test_campeonato_mostra_gap_e_ultimas_corridas(app_com_jogo, game):
    app = app_com_jogo
    _salva_e_corre(app, game, 2)
    app.session_state["menu"] = "📊 Campeonato"
    app.run()
    assert not app.exception

    tabelas = [df.value for df in app.dataframe]
    pilotos = next(t for t in tabelas if "Piloto" in t.columns and "Pontos" in t.columns)
    assert "Gap" in pilotos.columns and "Últimas 5" in pilotos.columns
    assert pilotos["Gap"].isna().sum() == 1, "só o líder deve ficar sem gap"
    assert pilotos["Gap"].dropna().max() > 0

    # a aba de evolução deixa escolher quantos pilotos desenhar
    app.slider(key="evolucao_top").set_value(5).run()
    assert not app.exception
    assert app.slider(key="evolucao_top").value == 5


def test_financas_filtra_extrato_por_temporada(app_com_jogo, game):
    app = app_com_jogo
    _salva_e_corre(app, game, 1)
    # lançamento de uma temporada anterior para o filtro ter o que separar
    game["extrato"].append({"temporada": game["ano"] - 1, "etapa": 0, "descricao": "Prêmio antigo", "valor": 1200.0})
    app.session_state["game"] = game
    app.session_state["menu"] = "💰 Patrocinadores & Finanças"
    app.run()
    assert not app.exception

    opcoes = [str(o) for o in app.selectbox(key="extrato_ano").options]
    assert "Todas" in opcoes
    assert {str(game["ano"]), str(game["ano"] - 1)} <= set(opcoes)
    assert len(app.metric) >= 3

    # filtrando pela temporada atual o prêmio antigo sai do extrato e do saldo
    app.selectbox(key="extrato_ano").set_value(game["ano"]).run()
    assert not app.exception
    extrato = next(df.value for df in app.dataframe if "Descrição" in df.value.columns)
    assert "Prêmio antigo" not in set(extrato["Descrição"])
    assert set(extrato["Ano"]) == {game["ano"]}


def test_sidebar_mostra_stats_e_atalho_para_a_corrida(app_com_jogo, game):
    app = app_com_jogo
    app.session_state["menu"] = "🏠 Escritório"
    app.run()
    assert not app.exception

    # cartão do próximo GP com o circuito da etapa atual
    prox = game["calendario"][game["rodada"]]
    html = "\n".join(m.value for m in app.markdown if "side-" in str(m.value))
    assert "side-stats" in html and "side-next" in html
    assert prox["gp"] in html and f"{prox['voltas']} voltas" in html
    for lab in ("Caixa", "Construtores", "Melhor piloto", "Etapa"):
        assert lab in html, f"stat {lab} sumiu da barra lateral"

    # o atalho leva para a tela de corrida
    app.button(key="side_ir_corrida").click().run()
    assert not app.exception
    assert app.session_state["menu"] == "🏁 Corrida"


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


def test_corrida_pergunta_quando_pneu_esgota_e_o_box_automatico_esta_desligado(app_com_jogo, game):
    app = app_com_jogo
    app.session_state["menu"] = "🏁 Corrida"
    app.run()
    fds = app.session_state["fds"]
    stt = _largo(app, game, fds)

    pid = next(iter(stt["pit_perguntar"]))
    stt["pit_perguntar"] = {piloto_id: False for piloto_id in stt["pit_perguntar"]}
    # com o box automático desligado, o chefe decide na janela
    stt["pit_auto_esgotado"] = {piloto_id: False for piloto_id in stt["pit_perguntar"]}
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


def _posicoes_antes(app, stt):
    """Mesma conta da tela: posições na volta anterior, com os ajustes de pneu/ritmo."""
    lap = int(stt["lap"])
    pits_antes = {k: [x for x in (v or []) if x < lap] for k, v in stt["pits"].items()}
    linhas = sim.linhas_replay(
        stt["rep"],
        max(1, lap - 1),
        pits_antes,
        stt.get("pneus_manual") or {},
        stt.get("ritmos") or {},
        stt.get("overcut_ativo"),
    )
    return {ln["pid"]: ln["pos"] for ln in linhas if not ln.get("fora")}


def _avanca_ate_rival_proximo(app, stt, atras=True):
    """Roda a transmissão até achar uma volta com rival a até 3 posições."""
    meus = set(stt["pit_perguntar"])
    spv = max(0.2, min(0.55, 24.0 / max(1, int(stt["rep"]["voltas"]))))
    for lap in range(4, 30):
        stt["t0"] = time.time() - spv * lap
        app.run()
        if int(stt["lap"]) < 3:
            continue
        pos = _posicoes_antes(app, stt)
        pid = next(iter(meus))
        if pid not in pos:
            continue
        rival = next(
            (r for r in pos if r not in meus and (0 < pos[r] - pos[pid] <= 3 if atras else 0 < pos[pid] - pos[r] <= 3)),
            None,
        )
        if rival:
            # congela a prova para o pit injetado cair exatamente nesta volta
            stt["pausado"] = True
            app.run()
            return rival
    return None


def test_alerta_de_undercut_e_resposta_imediata(app_com_jogo, game):
    app = app_com_jogo
    app.session_state["menu"] = "🏁 Corrida"
    app.run()
    stt = _largo(app, game, app.session_state["fds"])
    stt["pit_perguntar"] = {pid: False for pid in stt["pit_perguntar"]}
    app.run()

    rival = _avanca_ate_rival_proximo(app, stt, atras=True)
    assert rival, "nenhuma volta com rival a até 3 posições atrás"

    # simula o rival indo ao box nesta volta
    stt["pits"].setdefault(rival, []).append(int(stt["lap"]))
    app.run()

    assert stt["undercut_ativo"], "o alerta de undercut não foi registrado"
    assert any("undercut" in f and "foi ao box" in f for f in stt["feed"])
    botao = [b for b in app.button if b.label == "⚡ Responder agora"]
    assert botao, "o botão de resposta imediata não apareceu"

    pid = next(iter(stt["undercut_ativo"]))
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

    rival = _avanca_ate_rival_proximo(app, stt, atras=False)
    assert rival, "nenhuma volta com rival à frente a até 3 posições"

    stt["pits"].setdefault(rival, []).append(int(stt["lap"]))
    app.run()

    assert stt["overcut_ativo"], "o alerta de overcut não foi registrado"
    assert any("overcut" in f and "parou na volta" in f for f in stt["feed"])

    botao = [b for b in app.button if b.label == "🔥 Ficar e atacar"]
    assert botao, "o botão de overcut não apareceu"
    botao[0].click().run()

    assert any(r == "Atacar" for r in stt["ritmos"].values())
    assert not app.exception


def test_escritorio_tem_timeline_do_calendario(app_com_jogo, game):
    app = app_com_jogo
    app.session_state["menu"] = "🏠 Escritório"
    app.run()
    assert not app.exception
    html = "\n".join(str(m.value) for m in app.markdown)
    assert "timeline" in html and "tl-item" in html
    # uma etapa marcada como atual e as futuras em aberto
    assert html.count('class="tl-item agora"') == 1
    assert "tl-item done" not in html  # temporada recém-começada


def test_escritorio_simula_etapas_em_lote(app_com_jogo, game):
    app = app_com_jogo
    app.session_state["menu"] = "🏠 Escritório"
    app.run()
    rodada = game["rodada"]
    app.slider(key="lote_n").set_value(2).run()
    app.button(key="lote_simular").click().run()
    assert not app.exception
    assert app.session_state["game"]["rodada"] == rodada + 2
    assert len(app.session_state["game"]["resultados"]) >= 2
    assert app.dataframe  # a tabela do resumo do lote aparece


def test_pagina_save_grava_e_lista_slot(app_com_jogo, game, tmp_path, monkeypatch):
    import armazenamento

    monkeypatch.setattr(armazenamento, "PASTA_SAVES", str(tmp_path))
    app = app_com_jogo
    app.session_state["menu"] = "💾 Salvar / Carregar"
    app.run()
    assert not app.exception

    app.text_input(key="slot_nome").set_value("carreira_teste").run()
    app.button(key="slot_salvar").click().run()

    assert not app.exception
    assert (tmp_path / "carreira_teste.json").exists()
    slots = armazenamento.listar_saves()
    assert [s["nome"] for s in slots] == ["carreira_teste"]
    assert any(df.value["Slot"].eq("carreira_teste").any() for df in app.dataframe if "Slot" in df.value.columns)


def test_tema_claro_alterna_sem_quebrar(app_com_jogo):
    app = app_com_jogo
    app.session_state["tema_claro"] = True
    app.run()
    assert not app.exception
    css = "\n".join(str(m.value) for m in app.markdown)
    assert "--cm-bg:#F4F6FA" in css  # bloco do tema claro injetado


def test_pilotos_mostra_contraproposta_e_fecha_acordo(app_com_jogo, game):
    app = app_com_jogo
    app.session_state["menu"] = "👨‍✈️ Pilotos & Contratos"
    eqj = game["equipe_jogador"]
    # o seletor da página lista os pilotos por overall: usamos o primeiro da lista
    alvo = sorted([p for p in game["pilotos"] if not p["aposentado"]], key=lambda p: -sim.overall(p))[0]
    assert alvo["equipe_id"] != eqj
    game["negociacoes"] = {
        alvo["id"]: {
            "papel": "P2",
            "salario": 100,
            "anos": 1,
            "pedido": {"salario": 400, "anos": 2},
            "rodada": 1,
        }
    }
    app.run()
    assert not app.exception

    assert any("Contraproposta" in str(w.value) for w in app.warning)

    app.button(key="nego_aceitar").click().run()
    assert not app.exception
    assert alvo["id"] in game["contratos_proxima"]
    assert alvo["id"] not in game["negociacoes"]


def test_pagina_save_carrega_e_apaga_slot(app_com_jogo, game, tmp_path):
    import armazenamento

    armazenamento.salvar(game, "slot_para_carregar")
    app = app_com_jogo
    app.session_state["menu"] = "💾 Salvar / Carregar"
    app.run()
    assert not app.exception

    app.button(key="slot_apagar").click().run()
    assert not app.exception
    assert armazenamento.listar_saves() == []


def test_pos_corrida_mostra_volta_rapida_e_stints(app_com_jogo, game):
    """Depois da bandeirada: ⚡ volta rápida, gráfico de stints e CSV do resultado."""
    app = app_com_jogo
    app.session_state["menu"] = "🏁 Corrida"
    app.run()
    etapa = game["calendario"][game["rodada"]]
    fds = app.session_state["fds"]
    fds["molhado"] = False
    fds["grid"] = sim.simular_classificacao(game, etapa, False)
    res, ev = sim.simular_corrida(game, etapa, fds["grid"], {}, False, clima=fds.get("clima"))
    fds["resultado"], fds["eventos"] = res, ev
    fds["resumo"] = sim.aplicar_resultado(game, etapa, fds["grid"], res, False, eventos=ev)
    fds["replay"] = {
        "rep": sim.montar_replay(game, etapa, fds["grid"], res, False, eventos=ev),
        "t0": 0.0,
        "pits": {},
        "feed": [],
        "feed_dnf": [],
        "sc_ok": True,
        "lap": etapa["voltas"],
        "pulou": True,
        "concluido": True,
        "venceu": False,
        "balloons_ok": True,
        "ritmos": {},
        "pneus_manual": {},
        "pit_perguntar": {},
        "pit_aberto": None,
        "pits_recusados": {},
        "clima": fds.get("clima"),
        "clima_visto": None,
        "pausado": False,
        "velocidade": 1,
        "red_ok": True,
    }
    fds["treino"] = sim.sessao_treino(game, etapa, False, fds["grid"])
    fds["treino"]["t0"] = 1.0  # cronômetro já rodou (0.0 é tratado como "não iniciado")
    fds["treino"]["concluido"] = True
    fds["treino_ok"] = True
    fds["paddock_ok"] = True
    app.run()

    assert not app.exception
    html = "\n".join(str(m.value) for m in app.markdown)
    assert "Volta mais rápida" in html
    assert any("Stints e degradação" in str(e.label) for e in app.expander)
    # botão de CSV do resultado (download_button não entra em app.button)
    assert any("Exportar CSV" in str(d.label) for d in app.get("download_button"))


# ------------------------------------------------- fluxo guiado da corrida
def _treino_pronto(app, game, fds):
    """Deixa o treino concluído sem esperar o cronômetro."""
    etapa = game["calendario"][game["rodada"]]
    fds["molhado"] = False
    fds["grid"] = sim.simular_classificacao(game, etapa, False)
    fds["treino"] = sim.sessao_treino(game, etapa, False, fds["grid"])
    fds["treino"]["t0"] = 1.0  # cronômetro já rodou (0.0 é tratado como "não iniciado")
    fds["treino"]["concluido"] = True
    app.run()


def test_fluxo_da_corrida_mostra_um_passo_por_vez(app_com_jogo, game):
    app = app_com_jogo
    app.session_state["menu"] = "🏁 Corrida"
    app.run()
    fds = app.session_state["fds"]

    # passo 1: só treino (nenhum seletor de pneu do Paddock na tela)
    html = "\n".join(str(m.value) for m in app.markdown)
    assert 'class="wizard"' in html and "wz-step agora" in html
    assert not any(s.key and str(s.key).startswith("pad_pneu") for s in app.selectbox)
    assert any(b.key == "iniciar_treino" for b in app.button)

    # passo 2: paddock, sem a tabela do treino
    _treino_pronto(app, game, fds)
    app.button(key="ir_corrida").click().run()
    assert not app.exception
    html = "\n".join(str(m.value) for m in app.markdown)
    assert "Paddock" in html and "wz-step done" in html
    assert any(s.key and str(s.key).startswith("pad_pneu") for s in app.selectbox)
    assert any(e.label == "📋 Grid de largada" for e in app.expander)
    assert not any(b.key == "iniciar_treino" for b in app.button)

    # passo 3: transmissão — os blocos de preparação saem da tela
    app.button(key="paddock_confirmar").click().run()
    app.button(key="dar_largada").click().run()
    assert not app.exception
    assert any(b.key == "concluir_corrida" for b in app.button)
    assert not any(s.key and str(s.key).startswith("pad_pneu") for s in app.selectbox)
    assert not any(b.key in ("iniciar_treino", "paddock_confirmar", "dar_largada") for b in app.button)


def test_paddock_permite_rever_o_treino_sem_perder_a_grade(app_com_jogo, game):
    app = app_com_jogo
    app.session_state["menu"] = "🏁 Corrida"
    app.run()
    fds = app.session_state["fds"]
    _treino_pronto(app, game, fds)
    grade = [g["piloto_id"] for g in fds["grid"]]

    app.button(key="ir_corrida").click().run()
    app.button(key="voltar_treino").click().run()
    assert not app.exception
    assert any(b.key == "ir_corrida" for b in app.button)
    assert [g["piloto_id"] for g in fds["grid"]] == grade

    # e volta para o paddock com a mesma grade
    app.button(key="ir_corrida").click().run()
    assert any(s.key and str(s.key).startswith("pad_pneu") for s in app.selectbox)
    assert [g["piloto_id"] for g in fds["grid"]] == grade


# ------------------------------------------ box automático no fim do pneu
def _corrida_com_pneu_vencido(app, game, auto=True):
    """Larga a prova e deixa o 1º piloto do jogador com o pneu no fim da vida."""
    app.session_state["menu"] = "🏁 Corrida"
    app.run()
    fds = app.session_state["fds"]
    etapa = game["calendario"][game["rodada"]]
    fds["molhado"] = False
    fds["grid"] = sim.simular_classificacao(game, etapa, False)
    fds["treino"] = sim.sessao_treino(game, etapa, False, fds["grid"])
    fds["treino"]["t0"] = 1.0
    fds["treino"]["concluido"] = True
    fds["treino_ok"] = True
    fds["paddock_ok"] = True
    app.session_state[f"pad_autoesg_{sim.titulares(game, game['equipe_jogador'])[0]['id']}_{fds['chave']}"] = auto
    app.run()
    app.button(key="dar_largada").click().run()

    stt = fds["replay"]
    pid = sim.titulares(game, game["equipe_jogador"])[0]["id"]
    voltas = int(stt["rep"]["voltas"])
    stt["rep"]["info"][pid]["pits_plano"] = []  # sem janela de pit planejada no caminho
    stt["pit_perguntar"][pid] = False
    stt["pneus_manual"] = {pid: {0: "Macio"}}
    stt["ritmos"][pid] = "Normal"
    alvo = next(v for v in range(2, voltas) if sim.vida_pneu(etapa, "Macio", v, "Normal") == 0)
    spv = max(0.2, min(0.55, 24.0 / max(1, voltas)))
    stt["t0"] = time.time() - spv * (alvo + 0.3)
    stt["velocidade"] = 1
    app.run()
    return fds, stt, pid, alvo


def test_pneu_no_limite_para_no_box_automaticamente(app_com_jogo, game):
    app = app_com_jogo
    fds, stt, pid, alvo = _corrida_com_pneu_vencido(app, game, auto=True)

    assert not app.exception
    assert alvo in stt["pits"].get(pid, []), "o carro tinha de entrar no box sozinho"
    assert stt["pneus_manual"][pid][1] == "Duro"  # próximo composto depois do macio
    assert stt.get("pit_aberto") is None, "no modo automático a prova não para"
    assert any("box automático" in f for f in stt["feed"])


def test_pneu_no_limite_ainda_pergunta_quando_o_automatico_esta_desligado(app_com_jogo, game):
    app = app_com_jogo
    fds, stt, pid, alvo = _corrida_com_pneu_vencido(app, game, auto=False)

    assert not app.exception
    assert stt.get("pit_aberto"), "deveria abrir a janela do Pit Stop"
    assert stt["pit_aberto"]["pid"] == pid and stt["pit_aberto"].get("esgotado") is True
    assert alvo not in stt["pits"].get(pid, [])


def test_paddock_tem_a_opcao_de_box_automatico(app_com_jogo, game):
    app = app_com_jogo
    app.session_state["menu"] = "🏁 Corrida"
    app.run()
    fds = app.session_state["fds"]
    etapa = game["calendario"][game["rodada"]]
    fds["molhado"] = False
    fds["grid"] = sim.simular_classificacao(game, etapa, False)
    fds["treino"] = sim.sessao_treino(game, etapa, False, fds["grid"])
    fds["treino"]["t0"] = 1.0
    fds["treino"]["concluido"] = True
    app.run()
    app.button(key="ir_corrida").click().run()

    opcoes = [c for c in app.checkbox if c.key and str(c.key).startswith("pad_autoesg_")]
    assert opcoes, "o Paddock precisa da opção de box automático"
    assert all(c.value is True for c in opcoes)  # ligado por padrão
