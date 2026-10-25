# -*- coding: utf-8 -*-
"""Fixtures compartilhadas dos testes do Cockpit Manager."""
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import simulacao as sim  # noqa: E402


@pytest.fixture()
def db_f1():
    """A DB F1 2026 (11 equipes, 24 etapas)."""
    return sim._db_legado_f1()


@pytest.fixture()
def game(db_f1):
    """Jogo novo com a primeira equipe da DB F1 2026."""
    g = sim.criar_novo_jogo(db_f1["equipes"][0]["id"], semente=2026, db_dados=db_f1)
    g["gerente"] = "Teste"
    return g


@pytest.fixture()
def etapa(game):
    return game["calendario"][0]


@pytest.fixture()
def etapa_seca(etapa):
    """Etapa com desgaste/ultrapassagem previsíveis para testes de estratégia."""
    e = dict(etapa)
    e["chuva"] = 0.0
    e["desgaste"] = 1.8
    e["ultrap"] = 0.5
    return e
