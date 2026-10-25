# -*- coding: utf-8 -*-
"""Testes das novidades: neutralizações, volta rápida, stints, lote, negociação e slots."""

import json
import os

import pytest

import armazenamento
import simulacao as sim


# --------------------------------------------------------------- helpers
def _rep(voltas=20, sc=None, vsc=None, red=None):
    """Replay mínimo com um piloto só (bom para checar as janelas de neutralização)."""
    info = {
        "a": {
            "equipe_id": "e1",
            "grid": 1,
            "final_pos": 1,
            "dnf": False,
            "volta_dnf": voltas,
            "motivo": "",
            "gap_final": 0.0,
            "pneus": ["Médio", "Duro"],
            "paradas": 1,
            "pits_plano": [10],
            "ruido": [0.0] * (voltas + 2),
            "tempos": [80.0] * (voltas + 2),
        },
        "b": {
            "equipe_id": "e2",
            "grid": 2,
            "final_pos": 2,
            "dnf": False,
            "volta_dnf": voltas,
            "motivo": "",
            "gap_final": 8.0,
            "pneus": ["Macio", "Duro"],
            "paradas": 1,
            "pits_plano": [12],
            "ruido": [0.0] * (voltas + 2),
            "tempos": [80.4] * (voltas + 2),
        },
    }
    return {
        "voltas": voltas,
        "info": info,
        "sc_lap": sc,
        "sc_dur": 3 if sc else 0,
        "vsc_lap": vsc,
        "vsc_dur": 2 if vsc else 0,
        "red_lap": red,
    }


# --------------------------------------------------- neutralizações (1 e 2)
def test_safety_car_comprime_o_pelotao_e_libera_depois():
    rep = _rep(sc=10)
    antes = sim.linhas_replay(rep, 9, {})
    durante = sim.linhas_replay(rep, 11, {})
    depois = sim.linhas_replay(rep, 20, {})
    gap_antes = antes[1]["dif1"]
    gap_durante = durante[1]["dif1"]
    assert gap_durante < gap_antes, "o safety car tem de grudar o pelotão"
    assert depois[1]["dif1"] >= gap_durante
    # volta atrás do safety car é bem mais lenta
    assert durante[1]["tempo"] > antes[1]["tempo"] + 20


def test_vsc_comprime_menos_que_safety_car():
    vsc = sim.linhas_replay(_rep(vsc=10), 11, {})
    sc = sim.linhas_replay(_rep(sc=10), 11, {})
    assert vsc[1]["dif1"] > sc[1]["dif1"] > 0


def test_bandeira_vermelha_zera_o_pelotao_na_relargada():
    rep = _rep(red=12)
    normal = sim.linhas_replay(rep, 11, {})
    relargada = sim.linhas_replay(rep, 13, {})
    assert relargada[1]["dif1"] < normal[1]["dif1"] / 3
    # volta de relargada também é lenta
    assert relargada[1]["tempo"] > normal[1]["tempo"] + 20


def test_montar_replay_marca_as_janelas_dos_eventos(game, etapa):
    grid = sim.simular_classificacao(game, etapa, False)
    res, _ = sim.simular_corrida(game, etapa, grid, {}, False)
    rep = sim.montar_replay(game, etapa, grid, res, False, eventos=["🟨 Safety Car no meio da prova agrupou o pelotão"])
    assert rep["sc_lap"] and rep["sc_dur"] >= 1
    assert rep["vsc_lap"] is None and rep["red_lap"] is None
    rep2 = sim.montar_replay(game, etapa, grid, res, False, eventos=["🟥 Bandeira vermelha: prova interrompida"])
    assert rep2["red_lap"]


# --------------------------------------------------- volta mais rápida (+1)
def test_volta_mais_rapida_da_um_ponto_extra(game, etapa):
    grid = sim.simular_classificacao(game, etapa, False)
    res, eventos = sim.simular_corrida(game, etapa, grid, {}, False)
    vr = sim.volta_mais_rapida(res)
    assert vr is not None and vr["ponto_volta_rapida"] is True
    assert any("+1 ponto" in e for e in eventos)
    antes = sim.piloto(game, vr["piloto_id"])["pontos"]
    sim.aplicar_resultado(game, etapa, grid, res, False, eventos=eventos)
    depois = sim.piloto(game, vr["piloto_id"])["pontos"]
    assert depois == antes + vr["pontos"]
    # o save guarda a estatística de voltas rápidas
    assert sim.piloto(game, vr["piloto_id"])["voltas_rapidas"] >= 1


# --------------------------------------------------------- stints (item 5)
def test_stints_corrida_cobre_a_prova_e_usa_os_compostos():
    rep = _rep(voltas=20)
    stints = sim.stints_corrida(rep, "a")
    assert len(stints) == 2
    assert stints[0]["inicio"] == 1 and stints[0]["fim"] == 10
    assert stints[1]["inicio"] == 11 and stints[1]["fim"] == 20
    assert [s["pneu"] for s in stints] == ["Médio", "Duro"]
    assert all(s["voltas"] > 0 and s["tempo_medio"] == 80.0 for s in stints)


def test_stints_respeitam_paradas_manuais():
    rep = _rep(voltas=20)
    stints = sim.stints_corrida(rep, "a", pits_feitas={"a": [15]}, pneus_manual={"a": {1: "Macio"}})
    assert stints[1]["inicio"] == 16
    assert stints[1]["pneu"] == "Macio"


# ------------------------------------------------ temporada rápida (item 16)
def test_simular_etapas_em_lote_avanca_a_temporada(game):
    rodada_ini = game["rodada"]
    resumos = sim.simular_etapas(game, 3)
    assert len(resumos) == 3
    assert game["rodada"] == rodada_ini + 3
    assert len(game["resultados"]) >= 3
    for r in resumos:
        assert r["vencedor"] != "—"
        assert {"rodada", "gp", "clima" if False else "molhado", "minha_melhor_pos"} <= set(r)


def test_simular_etapas_para_no_fim_do_calendario(game):
    game["rodada"] = len(game["calendario"]) - 1
    resumos = sim.simular_etapas(game, 5)
    assert len(resumos) == 1
    assert game["rodada"] == len(game["calendario"])
    assert sim.simular_etapas(game, 2) == []


# ------------------------------------------------ negociação em rodadas (7)
def test_negociacao_contraproposta_ate_o_acordo(game):
    eqj = sim.equipe(game, game["equipe_jogador"])
    alvo = next(p for p in game["pilotos"] if p["equipe_id"] != eqj["id"] and not p["aposentado"])
    esperado = sim.salario_esperado(game, alvo, "P2")
    # oferta baixa: o estafe responde com um pedido, não com um "não" seco
    r = sim.negociar_piloto_detalhado(game, alvo["id"], "P2", max(10, esperado // 4), 1)
    assert r["status"] in ("contra", "aceita")
    if r["status"] == "contra":
        assert r["pedido"]["salario"] > esperado // 4
        assert game["negociacoes"][alvo["id"]]["rodada"] == 1
        # aceitar o pedido fecha o acordo
        r2 = sim.negociar_piloto_detalhado(game, alvo["id"], "P2", r["pedido"]["salario"], r["pedido"]["anos"])
        assert r2["status"] == "aceita"
        assert alvo["id"] in game["contratos_proxima"]
        assert alvo["id"] not in game["negociacoes"]


def test_negociacao_termina_depois_de_tres_recusas(game):
    alvo = next(p for p in game["pilotos"] if p["equipe_id"] != game["equipe_jogador"] and not p["aposentado"])
    sim.negociar_piloto_detalhado(game, alvo["id"], "P2", 10, 1)
    sim.negociar_piloto_detalhado(game, alvo["id"], "P2", 10, 1)
    r3 = sim.negociar_piloto_detalhado(game, alvo["id"], "P2", 10, 1)
    assert r3["status"] in ("recusa", "aceita")
    if r3["status"] == "recusa":
        assert alvo["id"] not in game["negociacoes"]
    # negociar_piloto continua compatível (bool, msg)
    ok, msg = sim.negociar_piloto(game, alvo["id"], "P2", 10, 1)
    assert isinstance(ok, bool) and isinstance(msg, str)


# ------------------------------------------------------- slots e migração
def test_slot_ida_e_volta(game, tmp_path, monkeypatch):
    monkeypatch.setattr(armazenamento, "PASTA_SAVES", str(tmp_path))
    caminho = armazenamento.salvar(game, "minha carreira/2026!")
    assert os.path.exists(caminho)
    assert os.path.basename(caminho) == "minha_carreira2026.json"

    slots = armazenamento.listar_saves()
    assert len(slots) == 1
    assert slots[0]["equipe"] and slots[0]["ano"] == game["ano"]

    carregado, avisos = armazenamento.carregar("minha carreira/2026!")
    assert carregado["equipe_jogador"] == game["equipe_jogador"]
    assert carregado["versao"] == armazenamento.VERSAO_SAVE
    assert avisos == []

    assert armazenamento.apagar("minha carreira/2026!")
    assert armazenamento.listar_saves() == []


def test_auto_save_grava_e_lista(game, tmp_path, monkeypatch):
    monkeypatch.setattr(armazenamento, "PASTA_SAVES", str(tmp_path))
    assert armazenamento.auto_save_info() is None
    caminho = armazenamento.auto_salvar(game)
    assert caminho.endswith("_autosave.json")
    info = armazenamento.auto_save_info()
    assert info and info["auto"] and info["rodada"] == game["rodada"] + 1


def test_migracao_de_save_antigo_preenche_campos(game):
    antigo = json.loads(json.dumps(game))
    antigo["versao"] = 1
    for chave in ("negociacoes", "historico_temporadas", "conquistas", "extrato"):
        antigo.pop(chave, None)
    antigo["meta"].pop("fator_pontos_bonus", None)
    for p in antigo["pilotos"]:
        p.pop("voltas_rapidas", None)

    migrado, avisos = armazenamento.migrar_save(antigo)
    assert migrado["versao"] == armazenamento.VERSAO_SAVE
    assert migrado["negociacoes"] == {}
    assert migrado["meta"]["fator_pontos_bonus"] == 1.0
    assert all("voltas_rapidas" in p for p in migrado["pilotos"])
    assert avisos and any("migrado" in a for a in avisos)
    # o save migrado continua consultável pelas mesmas funções
    assert sim.tabela_pilotos(migrado)
    assert sim.equipe(migrado, migrado["equipe_jogador"])["id"] == migrado["equipe_jogador"]


def test_save_incompleto_e_rejeitado():
    with pytest.raises(ValueError):
        armazenamento.migrar_save({"ano": 2026})
    with pytest.raises(ValueError):
        armazenamento.migrar_save("não é um save")


def test_csv_bytes_tem_bom_e_separador(game):
    tabela = sim.tabela_pilotos(game)
    df = __import__("pandas").DataFrame([{"Piloto": p["nome"], "Pontos": p["pontos"]} for p in tabela])
    dados = armazenamento.csv_bytes(df)
    assert dados.startswith(b"\xef\xbb\xbf")  # BOM para o Excel
    texto = dados.decode("utf-8-sig")
    assert ";" in texto.splitlines()[0]


# ------------------------------------------- temporada inteira + virada (20/21)
def test_temporada_completa_e_virada(game):
    """Joga todas as etapas em lote e fecha o ano: histórico, títulos e mercado."""
    total = len(game["calendario"])
    resumos = sim.simular_etapas(game, total)
    assert len(resumos) == total
    assert game["rodada"] == total

    ano = game["ano"]
    campeao = sim.tabela_pilotos(game)[0]["nome"]
    sim.virar_temporada(game)

    assert game["ano"] == ano + 1
    assert game["rodada"] == 0
    assert game["temporadas_completas"] == 1
    hist = game["historico_temporadas"][-1]
    assert hist["ano"] == ano and hist["campeao_pilotos"] == campeao
    assert hist["sua_posicao"] >= 1
    assert game["contratos_proxima"] == {}
    # todo titular do grid tem equipe e contrato coerentes depois do mercado
    for p in sim.titulares(game):
        assert p["equipe_id"] and p["contrato_anos"] >= 0


# ------------------------------------------------ radar e timeline (13 e 14)
def test_radar_svg_plota_os_seis_eixos(game):
    from paginas.carro import EIXOS_RADAR, radar_svg

    eq = sim.equipe(game, game["equipe_jogador"])
    eixos = sim.eixos_carro(eq)
    assert {k for k, _ in EIXOS_RADAR} <= set(eixos), "todo eixo do radar precisa existir no motor"
    outros = next(e for e in game["equipes"] if e["id"] != eq["id"])
    svg = radar_svg([(eq["nome"], "#E02444", eixos), (outros["nome"], "#38BDF8", sim.eixos_carro(outros))])
    assert svg.count("<polygon") >= 6  # grade + 2 séries
    assert "#E02444" in svg and "#38BDF8" in svg
    assert "Confiab." in svg and "Aero" in svg


def test_timeline_marca_concluidas_atual_e_futuras(game):
    from paginas.escritorio import linha_tempo

    game["rodada"] = 3
    html = linha_tempo(game)
    assert html.count("tl-item done") == 3
    assert html.count("tl-item agora") == 1
    assert html.count("tl-item futuro") == len(game["calendario"]) - 4


# ------------------------------------------- pit automático por pneu gasto
def test_composto_de_troca_nao_repete_o_pneu_que_acabou():
    assert sim.composto_de_troca("Macio", False) == "Duro"
    assert sim.composto_de_troca("Duro", False) == "Médio"
    assert sim.composto_de_troca("Médio", False) == "Macio"
    # composto desconhecido (ex.: pneu de chuva no seco) cai no médio
    assert sim.composto_de_troca("Chuva extrema", False) == "Médio"
    # na chuva o box calça intermediário
    assert sim.composto_de_troca("Macio", True) == "Intermediário"


def _rep_uma_volta(voltas=30, pneu="Macio"):
    info = {
        "a": {
            "equipe_id": "e1",
            "grid": 1,
            "final_pos": 1,
            "dnf": False,
            "volta_dnf": voltas,
            "motivo": "",
            "gap_final": 0.0,
            "pneus": [pneu, "Duro"],
            "paradas": 1,
            "pits_plano": [],
            "ruido": [0.0] * (voltas + 2),
            "tempos": [80.0] * (voltas + 2),
        }
    }
    return {"voltas": voltas, "info": info, "sc_lap": None, "red_lap": None}


def test_pit_automatico_quando_o_pneu_acaba(etapa_seca):
    rep = _rep_uma_volta()
    volta_morta = next(v for v in range(1, 30) if sim.vida_pneu(etapa_seca, "Macio", v) == 0)
    pits, manuais = {}, {}
    feitos = sim.pit_automatico_por_desgaste(etapa_seca, rep, volta_morta, pits, manuais)
    assert feitos == [("a", "Duro")]
    assert pits["a"] == [volta_morta]
    assert manuais["a"][1] == "Duro"
    # com pneu novo, ele sai da lista de esgotados
    assert "a" not in sim.pneus_esgotados(etapa_seca, rep, volta_morta, pits, manuais)
    # rodar de novo na mesma volta não duplica a parada
    assert sim.pit_automatico_por_desgaste(etapa_seca, rep, volta_morta, pits, manuais) == []


def test_pit_automatico_respeita_o_filtro_de_pilotos(etapa_seca):
    rep = _rep_uma_volta()
    volta_morta = next(v for v in range(1, 30) if sim.vida_pneu(etapa_seca, "Macio", v) == 0)
    pits, manuais = {}, {}
    assert sim.pit_automatico_por_desgaste(etapa_seca, rep, volta_morta, pits, manuais, apenas={"outro"}) == []
    assert pits == {}
    # na chuva o composto automático é o intermediário
    feitos = sim.pit_automatico_por_desgaste(etapa_seca, rep, volta_morta, pits, manuais, molhado=True)
    assert feitos == [("a", "Intermediário")]
