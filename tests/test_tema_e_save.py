# -*- coding: utf-8 -*-
"""Testes do tema/interface estática (ui/tema.py) e do save em JSON."""
import json
import re

from ui import tema

import simulacao as sim


def test_css_bem_formado_e_com_tokens():
    css = tema.CSS
    assert css.strip().startswith("<style>") and css.strip().endswith("</style>")
    # chaves balanceadas (um CSS quebrado derruba o layout inteiro)
    assert css.count("{") == css.count("}")
    # tokens de fonte usados por todo o app
    for token in ("--cm-font-brand", "--cm-font-ui", "--cm-font-text", "--cm-font-mono"):
        assert token in css
    # fontes declaradas precisam existir no tema (config.toml)
    assert '"Formula1"' in css and '"Manrope"' in css and '"Inter"' in css


def test_css_tem_componentes_do_jogo():
    css = tema.CSS
    for classe in (
        ".office-meta",
        ".previsao-tempo",
        ".tbl-viva",
        ".tyre",
        ".gap-bar",
        ".box-piloto",
        ".undercut-card",
        ".overcut-card",
        ".pit-titulo",
        ".side-next",
        ".pausa-chip",
    ):
        assert classe in css, f"componente {classe} sumiu do tema"


def test_css_respeita_acessibilidade_e_mobile():
    css = tema.CSS
    assert "prefers-reduced-motion" in css
    assert ":focus-visible" in css
    assert "@media (max-width:900px)" in css and "@media (max-width:760px)" in css


def test_fontes_registradas_no_tema_batem_com_os_arquivos():
    """Toda família declarada no CSS deve estar registrada em .streamlit/config.toml."""
    css_familias = set(re.findall(r'font-family:\s*"([A-Za-z0-9 ]+)"', tema.CSS))
    config = open(".streamlit/config.toml", encoding="utf-8").read()
    registradas = set(re.findall(r'family = "([^"]+)"', config))
    faltando = {f for f in css_familias if f not in registradas and f != "Material Symbols Rounded"}
    assert not faltando, f"fontes usadas no CSS mas não registradas: {sorted(faltando)}"


def test_save_json_ida_e_volta(game, etapa):
    """Salvar (.json) e carregar de volta preserva o estado essencial."""
    grid = sim.simular_classificacao(game, etapa, False)
    res, ev = sim.simular_corrida(game, etapa, grid, {}, False,
                                  clima=sim.plano_clima(game, etapa, False))
    sim.aplicar_resultado(game, etapa, grid, res, False, eventos=ev)

    texto = json.dumps(game, ensure_ascii=False)
    carregado = json.loads(texto)

    assert carregado["ano"] == game["ano"]
    assert carregado["rodada"] == game["rodada"]
    assert carregado["equipe_jogador"] == game["equipe_jogador"]
    assert len(carregado["equipes"]) == len(game["equipes"])
    assert len(carregado["pilotos"]) == len(game["pilotos"])
    assert len(carregado["resultados"]) == len(game["resultados"])
    # o jogo recarregado continua consultável pelas mesmas funções
    eqj = sim.equipe(carregado, carregado["equipe_jogador"])
    assert eqj["id"] == game["equipe_jogador"]
    assert sim.tabela_pilotos(carregado)[0]["pontos"] >= 0
    assert sim.posicao_equipe(carregado, eqj["id"]) >= 1


def test_ultimas_corridas_e_forma_texto(game):
    assert sim.ultimas_corridas(game, "ninguem") == []
    assert sim.forma_texto([]) == "—"

    for _ in range(3):
        etapa = game["calendario"][game["rodada"]]
        grid = sim.simular_classificacao(game, etapa, False)
        res, ev = sim.simular_corrida(game, etapa, grid, {}, False,
                                      clima=sim.plano_clima(game, etapa, False))
        sim.aplicar_resultado(game, etapa, grid, res, False, eventos=ev)
        game["rodada"] += 1

    pid = game["pilotos"][0]["id"]
    hist = sim.ultimas_corridas(game, pid, 5)
    assert len(hist) == 3
    assert [h["rodada"] for h in hist] == sorted(h["rodada"] for h in hist)
    marcas = sim.forma_texto(hist).split("·")
    assert len(marcas) == 3 and all(m == "D" or m.isdigit() for m in marcas)
