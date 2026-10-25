# -*- coding: utf-8 -*-
"""Testes do motor: determinismo, pontuação, abandonos e tabelas."""

import copy

import pytest

import dados2026 as db
import simulacao as sim


ORDEM_PAPEIS = ("P1", "P2", "P3", "P4")


def _estrategias(game, etapa, pneu="Médio", paradas=1, ritmo="Normal"):
    return {
        p["id"]: {"pneu": pneu, "paradas": paradas, "ritmo": ritmo} for p in sim.titulares(game, game["equipe_jogador"])
    }


def test_criar_jogo_estrutura_basica(game):
    assert game["rodada"] == 0
    assert game["equipe_jogador"]
    assert len(game["calendario"]) >= 20
    assert all(e["motor_id"] for e in game["equipes"])
    ids = {p["id"] for p in game["pilotos"]}
    assert len(ids) == len(game["pilotos"]), "ids de piloto duplicados"
    assert sim.equipe(game, game["equipe_jogador"])["id"] == game["equipe_jogador"]


def test_classificacao_ordenada_e_unica(game, etapa):
    grid = sim.simular_classificacao(game, etapa, molhado=False)
    assert [g["pos"] for g in grid] == list(range(1, len(grid) + 1))
    assert len({g["piloto_id"] for g in grid}) == len(grid)
    tempos = [g["tempo"] for g in grid]
    assert tempos == sorted(tempos), "tempos do grid fora de ordem"
    assert grid[0]["gap"] == 0


def test_corrida_resultado_coerente(game, etapa):
    grid = sim.simular_classificacao(game, etapa, molhado=False)
    res, eventos = sim.simular_corrida(game, etapa, grid, _estrategias(game, etapa), molhado=False)

    assert len(res) == len(grid)
    assert [l["pos"] for l in res] == list(range(1, len(res) + 1))
    assert len({l["piloto_id"] for l in res}) == len(res)

    # quem abandonou fica atrás de quem terminou e não pontua
    terminaram = [l for l in res if not l["dnf"]]
    abandonaram = [l for l in res if l["dnf"]]
    if terminaram and abandonaram:
        assert max(l["pos"] for l in terminaram) < min(l["pos"] for l in abandonaram)
    assert all(l["pontos"] == 0 for l in abandonaram)
    assert all(l["gap_seg"] is None for l in abandonaram)

    # pontos = tabela oficial da categoria, atribuídos em ordem
    tabela = (game.get("meta") or {}).get("pontos_corrida") or db.PONTOS_CORRIDA
    for l in res[: len(tabela)]:
        if not l["dnf"]:
            assert l["pontos"] == tabela[l["pos"] - 1]
    assert isinstance(eventos, list) and eventos
    for m in ("dnf", "motivo", "status", "volta_dnf", "pontos"):
        assert m in res[0]
    assert any(l.get("volta_rapida") for l in res) == bool(terminaram)
    assert any("Volta mais rápida" in e for e in eventos) or not terminaram


def test_corrida_e_deterministica_por_semente(db_f1, game, etapa):
    grid = sim.simular_classificacao(game, etapa, molhado=False)

    jogo_a = copy.deepcopy(game)
    jogo_b = copy.deepcopy(game)
    res_a, ev_a = sim.simular_corrida(jogo_a, etapa, grid, _estrategias(jogo_a, etapa), False)
    res_b, ev_b = sim.simular_corrida(jogo_b, etapa, grid, _estrategias(jogo_b, etapa), False)

    simples = lambda res: [(l["piloto_id"], l["pos"], l["dnf"], l["pontos"]) for l in res]
    assert simples(res_a) == simples(res_b)
    assert ev_a == ev_b


def test_aplicar_resultado_soma_pontos_e_historico(game, etapa):
    grid = sim.simular_classificacao(game, etapa, molhado=False)
    res, eventos = sim.simular_corrida(game, etapa, grid, _estrategias(game, etapa), False)
    antes = sum(e["pontos"] for e in game["equipes"])
    sim.aplicar_resultado(game, etapa, grid, res, molhado=False, eventos=eventos)

    pontos_resultado = sum(l["pontos"] for l in res)
    assert sum(e["pontos"] for e in game["equipes"]) == antes + pontos_resultado
    # a rodada avança na tela da corrida (botão Continuar), não no aplicar_resultado
    assert len(game["resultados"]) == 1
    assert game["historico_pontos"]

    tabela = sim.tabela_pilotos(game)
    assert tabela[0]["pontos"] >= tabela[-1]["pontos"]
    construtores = sim.tabela_construtores(game)
    assert construtores[0]["pontos"] >= construtores[-1]["pontos"]


def test_titulares_batem_com_as_vagas(game):
    for eq in game["equipes"]:
        tits = sim.titulares(game, eq["id"])
        assert tits, f"{eq['nome']} sem titulares"
        assert all(p["equipe_id"] == eq["id"] for p in tits)
        assert len({p["id"] for p in tits}) == len(tits)


@pytest.mark.parametrize(
    "desgaste,ultrap,esperado",
    [
        (1.2, 0.5, 1),
        (1.8, 0.2, 1),
        (1.8, 0.6, 2),
        (2.8, 0.6, 2),
    ],
)
def test_paradas_ideais(desgaste, ultrap, esperado):
    etapa = {"desgaste": desgaste, "ultrap": ultrap}
    assert sim.paradas_ideais(etapa) == esperado
