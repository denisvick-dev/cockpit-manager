# -*- coding: utf-8 -*-
"""A F1 não tem mais corrida sprint; as outras DBs mantêm suas duas corridas."""

import json

import armazenamento
import dbs
import simulacao as sim


def test_db_f1_2026_tem_corrida_unica():
    db = dbs.db_f1_2026()
    assert db["meta"]["rotulo_corrida2"] is None
    assert not any(e.get("sprint") for e in db["calendario"])
    # o calendário continua completo (24 etapas)
    assert len(db["calendario"]) == 24


def test_jogo_novo_da_f1_nao_tem_sprint():
    game = sim.criar_novo_jogo("mclaren", semente=2026, db_dados=dbs.db_f1_2026())
    assert not any(e.get("sprint") for e in game["calendario"])
    etapa = game["calendario"][0]
    res, eventos = [], []
    grid = sim.simular_classificacao(game, etapa, False)
    res, eventos = sim.simular_corrida(game, etapa, grid, {}, False)
    # uma corrida só: nada de "sprint" no registro do fim de semana
    sim.aplicar_resultado(game, etapa, grid, res, False, eventos=eventos)
    assert game["resultados"][-1]["sprint"] is False
    assert len([r for r in game["resultados"] if r["rodada"] == 1]) == 1


def test_simular_etapas_na_f1_nao_cria_sprint(game):
    resumos = sim.simular_etapas(game, 2)
    assert all(r["sprint"] is None for r in resumos)
    assert all(r["resultado"] for r in resumos)


def test_outras_dbs_continuam_com_duas_corridas():
    stock = dbs.db_stock_2026()
    assert stock["meta"]["rotulo_corrida2"] == "Corrida sprint"
    assert all(e.get("sprint") for e in stock["calendario"])

    dtm = dbs.db_dtm_2026()
    assert dtm["meta"]["rotulo_corrida2"] == "Corrida 1"
    assert all(e.get("sprint") for e in dtm["calendario"])

    academy = dbs.db_f1_academy_2026()
    assert academy["meta"]["rotulo_corrida2"] == "Corrida 2"
    assert all(e.get("sprint") for e in academy["calendario"])


def test_migracao_remove_sprint_de_save_antigo_da_f1(game):
    antigo = json.loads(json.dumps(game))
    antigo["versao"] = 3
    antigo["meta"]["rotulo_corrida2"] = "Sprint"
    # volta duas etapas com sprint, como nos saves da versão anterior
    antigo["calendario"][0]["sprint"] = True
    antigo["calendario"][3]["sprint"] = True

    migrado, avisos = armazenamento.migrar_save(antigo)
    assert not any(e.get("sprint") for e in migrado["calendario"])
    assert migrado["versao"] == armazenamento.VERSAO_SAVE
    assert any("sprint" in a.lower() for a in avisos)


def test_migracao_preserva_as_duas_corridas_do_stock_car():
    stock = sim.criar_novo_jogo("eurofarma_rc", semente=7, db_dados=dbs.db_stock_2026())
    antigo = json.loads(json.dumps(stock))
    antigo["versao"] = 3
    migrado, _ = armazenamento.migrar_save(antigo)
    assert all(e.get("sprint") for e in migrado["calendario"])
