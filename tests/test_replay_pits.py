# -*- coding: utf-8 -*-
"""Testes do replay: pneus, pits (janela/auto/recusa), clima e vida do pneu."""

import simulacao as sim


def _replay_com_pits(plano_por_piloto, voltas=50):
    """Replay sintético: {pid: [voltas planejadas]}."""
    info = {}
    for pid, plano in plano_por_piloto.items():
        info[pid] = {
            "pits_plano": list(plano),
            "dnf": False,
            "pneus": ["Médio"] * (len(plano) + 1),
            "paradas": len(plano),
            "grid": 1,
            "final_pos": 1,
            "gap_final": 0.0,
            "volta_dnf": voltas,
            "motivo": "",
            "ruido": [0.0] * (voltas + 2),
            "tempos": [90.0] * (voltas + 2),
        }
    return {"voltas": voltas, "info": info, "sc_lap": None}


def test_sequencia_de_pneus_segue_rotacao():
    assert sim._sequencia_pneus("Macio", 0, False) == ["Macio"]
    # rota de compostos: cada parada usa o próximo composto da rotação
    seq = sim._sequencia_pneus("Macio", 2, False)
    assert seq[0] == "Macio" and len(seq) == 3
    assert set(seq) == set(sim.PNEUS_SECO)
    assert sim._sequencia_pneus("Duro", 1, False)[1] == "Médio"
    molhado = sim._sequencia_pneus("Macio", 1, True)
    assert molhado[0] == "Macio" and molhado[1] in sim.PNEUS_MOLHADO


def test_pits_pendentes_respeita_volta_recusa_e_abandono():
    rep = _replay_com_pits({"a": [10, 30], "b": [12], "c": [8]})
    rep["info"]["c"]["dnf"] = True

    assert sim.pits_pendentes(rep, 5, {}) == []
    assert sim.pits_pendentes(rep, 10, {}) == [("a", 10)]
    # pilotos que abandonaram não recebem janela
    assert all(pid != "c" for pid, _ in sim.pits_pendentes(rep, 40, {}))

    # parada recusada não volta a ser perguntada
    pend = sim.pits_pendentes(rep, 12, {}, recusadas={"a": [10]})
    assert pend == [("b", 12)]

    # `perguntar` desligado = para sozinho, sem janela
    assert sim.pits_pendentes(rep, 40, {}, perguntar={"a": False, "b": False}) == []

    # `apenas` limita a janela aos pilotos do jogador
    assert sim.pits_pendentes(rep, 40, {}, apenas={"b"}) == [("b", 12)]


def test_auto_pits_executa_plano_e_respeita_configuracao():
    rep = _replay_com_pits({"a": [10, 30], "b": [12]})
    feitas = {}
    sim.auto_pits(rep, 10, feitas, {"a": True, "b": True})
    assert feitas == {"a": [10]}

    # salto de voltas não perde paradas
    sim.auto_pits(rep, 31, feitas, {"a": True, "b": True})
    assert feitas["a"] == [10, 30] and feitas["b"] == [12]

    # desligado para um piloto = ele não para sozinho
    feitas2 = {}
    sim.auto_pits(rep, 31, feitas2, {"a": False, "b": True})
    assert "a" not in feitas2 and feitas2["b"] == [12]

    # parada recusada nunca é executada
    feitas3 = {}
    sim.auto_pits(rep, 31, feitas3, {"a": True, "b": True}, recusadas={"a": [10]})
    assert feitas3["a"] == [30]

    # sem criar listas vazias para quem não parou
    assert all(v for v in feitas3.values())


def test_vida_pneu_degrada_com_voltas_e_ritmo(etapa_seca):
    nova = sim.vida_pneu(etapa_seca, "Duro", 0, "Normal")
    usada = sim.vida_pneu(etapa_seca, "Duro", 20, "Normal")
    ataque = sim.vida_pneu(etapa_seca, "Duro", 20, "Atacar")
    conservar = sim.vida_pneu(etapa_seca, "Duro", 20, "Conservar")

    assert nova == 1.0
    assert 0.0 <= usada < nova
    assert ataque < usada < conservar
    assert sim.vida_pneu(etapa_seca, "Duro", 999, "Normal") == 0.0


def test_linhas_replay_ordenadas_e_com_box(game, etapa):
    grid = sim.simular_classificacao(game, etapa, False)
    res, eventos = sim.simular_corrida(game, etapa, grid, {}, False)
    rep = sim.montar_replay(game, etapa, grid, res, False, eventos=eventos)

    linhas = sim.linhas_replay(rep, 1, {})
    assert [l["pos"] for l in linhas] == list(range(1, len(linhas) + 1))
    assert all(l["pneu"] in sim.PNEUS_DURACAO for l in linhas)

    pid = next(p for p, d in rep["info"].items() if not d["dnf"])
    lap_pit = 5
    linhas_pit = sim.linhas_replay(rep, lap_pit, {pid: [lap_pit]})
    box = next(l for l in linhas_pit if l["pid"] == pid)
    assert box["box"] is True and box["pits"] == 1

    # pneu manual escolhido na janela aparece no replay
    linhas_manual = sim.linhas_replay(rep, lap_pit, {pid: [lap_pit]}, pneus_manual={pid: {1: "Duro"}})
    assert next(l for l in linhas_manual if l["pid"] == pid)["pneu"] == "Duro"


def test_plano_clima_e_condicao_da_pista(game, etapa):
    seco = sim.plano_clima(game, etapa, molhado=False)
    molhado = sim.plano_clima(game, etapa, molhado=True)

    assert seco["inicio"] == "seco" and molhado["inicio"] == "molhado"
    # determinístico: mesma chamada, mesmo plano
    assert sim.plano_clima(game, etapa, molhado=False) == seco

    voltas = int(etapa["voltas"])
    assert sim.condicao_pista(seco, 1) == "seco"
    if seco["virada_volta"]:
        v = seco["virada_volta"]
        assert 3 <= v < voltas
        assert sim.condicao_pista(seco, v - 1) == "seco"
        assert sim.condicao_pista(seco, v) == seco["virada_para"]
        assert sim.condicao_pista(seco, voltas) == seco["virada_para"]
    assert sim.condicao_pista(None, 10) == "seco"
    assert isinstance(sim.previsao_texto(seco), str) and sim.previsao_texto(seco)


def test_clima_muda_o_ritmo_pelo_menos_em_uma_etapa(game):
    """Em 24 etapas × 2 condições, alguma prova tem virada de tempo."""
    viradas = 0
    for i, etapa in enumerate(game["calendario"]):
        game["rodada"] = i
        for molhado in (False, True):
            if sim.plano_clima(game, etapa, molhado)["virada_volta"]:
                viradas += 1
    game["rodada"] = 0
    assert viradas > 0


def test_undercut_detecta_rival_logo_atras_que_parou():
    posicoes = {"eu": 5, "rival": 7, "longe": 12, "frente": 3}
    pits = {"rival": [20], "longe": [20], "frente": [20]}
    alertas = sim.undercut_nesta_volta(20, pits, {"eu"}, posicoes)

    assert alertas == [("eu", "rival", 7, 5)], "só o rival até 3 posições atrás deve alertar"
    # janela maior pega também quem estava mais longe
    nomes = {r for _, r, _, _ in sim.undercut_nesta_volta(20, pits, {"eu"}, posicoes, janela=8)}
    assert nomes == {"rival", "longe"}
    # quem está à frente não é undercut, e outra volta não gera alerta
    assert sim.undercut_nesta_volta(21, pits, {"eu"}, posicoes) == []
    # rivais que também são "meus" (parceiro de equipe) não entram
    assert sim.undercut_nesta_volta(20, pits, {"eu", "rival"}, posicoes) == []


def test_overcut_disponivel_pega_rival_da_frente():
    posicoes = {"eu": 8, "frente": 6, "longe_frente": 2, "atras": 10}
    pits = {"frente": [30], "longe_frente": [30], "atras": [30]}

    assert sim.overcut_disponivel(30, pits, {"eu"}, posicoes) == [("eu", "frente", 6, 8)]
    nomes = {r for _, r, _, _ in sim.overcut_disponivel(30, pits, {"eu"}, posicoes, janela=7)}
    assert nomes == {"frente", "longe_frente"}
    assert sim.overcut_disponivel(31, pits, {"eu"}, posicoes) == []
    assert sim.overcut_disponivel(30, pits, {"eu", "frente"}, posicoes) == []


def test_overcut_melhora_posicao_na_janela_e_zera_no_fim(game, etapa):
    grid = sim.simular_classificacao(game, etapa, False)
    res, eventos = sim.simular_corrida(game, etapa, grid, {}, False)
    rep = sim.montar_replay(game, etapa, grid, res, False, eventos=eventos)
    pid = next(p for p, d in rep["info"].items() if not d["dnf"])

    voltas = int(rep["voltas"])
    overcut = {pid: {"volta": 10, "laps": 3}}
    # dentro da janela o piloto aparece à frente de onde apareceria sem overcut
    pior = next(l["pos"] for l in sim.linhas_replay(rep, 11, {}) if l["pid"] == pid)
    melhor = next(l["pos"] for l in sim.linhas_replay(rep, 11, {}, overcut=overcut) if l["pid"] == pid)
    assert melhor <= pior
    # fora da janela (e na bandeirada) nada muda: o resultado do motor manda
    fim_sem = [(l["pid"], l["pos"]) for l in sim.linhas_replay(rep, voltas, {})]
    fim_com = [(l["pid"], l["pos"]) for l in sim.linhas_replay(rep, voltas, {}, overcut=overcut)]
    assert fim_sem == fim_com


def test_clima_no_motor_muda_o_resultado(game):
    import copy

    etapa = game["calendario"][1]
    grid = sim.simular_classificacao(game, etapa, False)
    ests = {p["id"]: {"pneu": "Médio", "paradas": 1, "ritmo": "Normal"}
            for p in sim.titulares(game, game["equipe_jogador"])}

    seco = {"inicio": "seco", "virada_volta": None, "virada_para": None}
    chuva = {"inicio": "seco", "virada_volta": 20, "virada_para": "molhado"}

    sem_plano, _ = sim.simular_corrida(copy.deepcopy(game), etapa, grid, ests, False)
    com_seco, _ = sim.simular_corrida(copy.deepcopy(game), etapa, grid, ests, False, clima=seco)
    com_chuva, eventos = sim.simular_corrida(copy.deepcopy(game), etapa, grid, ests, False, clima=chuva)

    ordem = lambda res: [l["piloto_id"] for l in res]  # noqa: E731
    # plano seco sem virada não altera nada (invariante de balanceamento)
    assert ordem(sem_plano) == ordem(com_seco)
    # chuva chegando no meio muda o resultado e é anunciada
    assert ordem(com_chuva) != ordem(com_seco)
    assert any("volta 20" in e for e in eventos)
    assert [l["pos"] for l in com_chuva] == list(range(1, len(com_chuva) + 1))


def test_clima_fracao_e_ajuste_por_composto():
    assert sim.clima_fracao({"inicio": "seco"}, 50) == (0.0, None)
    assert sim.clima_fracao({"inicio": "molhado"}, 50) == (1.0, None)
    frac, v = sim.clima_fracao({"inicio": "seco", "virada_volta": 40, "virada_para": "molhado"}, 50)
    assert v == 40 and 0.0 < frac < 0.3

    etapa = {"voltas": 50, "desgaste": 2.0, "ultrap": 0.5, "potencia": 0.6}
    piloto = {"atributos": {"chuva": 95, "fisico": 80}}
    molhado = {"inicio": "molhado", "virada_volta": None, "virada_para": None}
    certo = sim.ajuste_clima(molhado, etapa, {"pneu": "Intermediário", "paradas": 1}, piloto)
    errado = sim.ajuste_clima(molhado, etapa, {"pneu": "Macio", "paradas": 1}, piloto)
    assert certo > errado
    # sem plano, nenhum ajuste
    assert sim.ajuste_clima(None, etapa, {"pneu": "Macio", "paradas": 1}, piloto) == 0.0
