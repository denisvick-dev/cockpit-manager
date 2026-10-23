# -*- coding: utf-8 -*-
"""
Sistema de DBs (bases de dados) do Cockpit Manager — Edição Streamlit.

Uma DB é um dicionário (serializável em JSON) com:
  meta         -> nome, categoria, ano, pontuação, rótulos
  equipes      -> equipes jogáveis
  pilotos      -> titulares (P1..P4), testes e livres
  motores      -> fornecedores (motores, montadoras, carros GT3...)
  calendario   -> etapas da temporada
  hall_da_fama -> lendas da categoria

DBs embutidas: F1 2026, Fórmula Indy 2026, Stock Car 2026 e DTM 2026.
Você também pode criar a sua no editor (aba "Criar / editar DB"),
baixá-la em .json e compartilhá-la — igualzinho à comunidade do CM14!
"""
import copy
import json
import re
import unicodedata
from pathlib import Path

import dados2026 as _f1

PAPEIS_TITULARES = ("P1", "P2", "P3", "P4")

# --------------------------------------------------------------- pontuações
PONTOS_INDY = [50, 40, 35, 32, 30, 28, 26, 24, 22, 20, 19, 18, 17, 16, 15,
               14, 13, 12, 11, 10, 9, 8, 7, 6] + [5] * 16
PONTOS_STOCK_PRINCIPAL = [80, 74, 69, 64, 59, 55, 51, 47, 43, 40, 37, 34, 31, 28, 25,
                          22, 19, 17, 15, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3]
PONTOS_STOCK_SPRINT = [55, 50, 46, 42, 38, 36, 34, 32, 30, 28, 26, 24, 22, 20, 18,
                       16, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
PONTOS_DTM = [25, 20, 16, 13, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]

PRESETS_PONTUACAO = {
    "F1 (25-18-15… + sprint)": (_f1.PONTOS_CORRIDA, _f1.PONTOS_SPRINT),
    "Indy (50-40-35…, todos pontuam)": (PONTOS_INDY, PONTOS_INDY),
    "Stock Car (80 principal / 55 sprint)": (PONTOS_STOCK_PRINCIPAL, PONTOS_STOCK_SPRINT),
    "DTM (25-20-16… top 15, 2 corridas iguais)": (PONTOS_DTM, PONTOS_DTM),
}


def slugificar(texto, padrao="item"):
    t = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "_", t.lower()).strip("_")
    return t or padrao


def _unicos(ids):
    vistos, saida = {}, []
    for i in ids:
        vistos[i] = vistos.get(i, 0) + 1
        saida.append(i if vistos[i] == 1 else f"{i}{vistos[i]}")
    return saida


# ------------------------------------------------------------ construtores
def _attrs(ovr, **ajustes):
    a = {"velocidade": ovr + 1, "chuva": ovr - 1, "concentracao": ovr, "largada": ovr - 1,
         "ultrapassagem": ovr, "acerto": ovr - 1, "fisico": ovr}
    a.update(ajustes)
    return {k: int(max(35, min(99, v))) for k, v in a.items()}


def _piloto(nome, sigla, numero, pais, bandeira, idade, equipe_id, papel, salario, ovr,
            potencial=None, auge=(25, 32), contrato=2, **ajustes):
    return {"id": slugificar(nome), "nome": nome, "sigla": sigla, "numero": numero,
            "pais": pais, "bandeira": bandeira, "idade": idade, "equipe_id": equipe_id,
            "papel": papel, "salario_corrida": salario, "contrato_anos": contrato,
            "auge_inicio": auge[0],
            "auge_fim": max(auge[1], idade + 2) if idade > auge[1] else auge[1],
            "potencial": potencial if potencial is not None else min(99, ovr + (6 if idade < auge[0] else 0)),
            "atributos": _attrs(ovr, **ajustes)}


def _equipe(nome, pais, bandeira, cor, fornecedor_id, nivel, caixa, prestigio, investimento,
            patrocinador="Seguros Prisma", nome_completo=None, conf=88, titulos=0, proprio=False):
    return {"id": slugificar(nome), "nome": nome, "nome_completo": nome_completo or nome,
            "pais": pais, "bandeira": bandeira, "cor": cor, "motor_id": fornecedor_id,
            "motor_proprio": proprio, "nivel_carro": nivel, "confiabilidade": conf,
            "caixa": float(caixa), "prestigio": prestigio, "investimento_corrida": investimento,
            "titulos_construtores": titulos, "patrocinador": patrocinador}


def _fornecedor(nome, potencia, conf, preco, desc, proprio_de=None):
    return {"id": slugificar(nome), "nome": nome, "potencia": potencia,
            "confiabilidade": conf, "preco": float(preco), "proprio_de": proprio_de, "desc": desc}


def _etapa(gp, circuito, pais, bandeira, voltas, data, pot, ultrap, desgaste, chuva, sprint=False):
    return {"gp": gp, "circuito": circuito, "pais": pais, "bandeira": bandeira, "voltas": voltas,
            "data": data, "sprint": sprint, "potencia": pot, "ultrap": ultrap,
            "desgaste": desgaste, "chuva": chuva}


def _fallback(nome="Fornecedor da organização (compulsório)"):
    return {"id": "fia", "nome": nome, "potencia": 50, "confiabilidade": 95, "preco": 0.0,
            "proprio_de": None,
            "desc": "Sem caixa para pagar um fornecedor decente? A organização empresta um com 50% de desempenho."}


# =====================================================================
#  DB F1 2026 (a partir de dados2026.py)
# =====================================================================
def db_f1_2026():
    return {
        "meta": {"id": "f1_2026", "nome": "F1 2026", "categoria": "Fórmula 1", "ano": 2026,
                 "descricao": "A DB clássica: 11 equipes, novo regulamento, Audi e Cadillac estreando, Bortoleto no grid.",
                 "rotulo_fornecedor": "Motor", "rotulo_corrida2": "Sprint",
                 "pontos_corrida": list(_f1.PONTOS_CORRIDA), "pontos_corrida2": list(_f1.PONTOS_SPRINT),
                 "importancia_carro_sugerida": 0.60, "fator_pontos_bonus": 1.0, "pontua_abandono": False},
        "equipes": copy.deepcopy(_f1.EQUIPES), "pilotos": copy.deepcopy(_f1.PILOTOS),
        "motores": copy.deepcopy(_f1.MOTORES), "calendario": copy.deepcopy(_f1.CALENDARIO_2026),
        "hall_da_fama": copy.deepcopy(_f1.HALL_DA_FAMA_INICIAL),
        "patrocinadores": copy.deepcopy(_f1.PATROCINADORES),
    }


# =====================================================================
#  DB FÓRMULA Indy 2026 (NTT IndyCar Series)
# =====================================================================
def db_indy_2026():
    equipes = [
        _equipe("Chip Ganassi", "Estados Unidos", "🇺🇸", "#E4002B", "honda_indy", 95, 120, 96, 1500, "TechNova", "Chip Ganassi Racing", titulos=17),
        _equipe("Team Penske", "Estados Unidos", "🇺🇸", "#F5C400", "chevrolet_indy", 94, 125, 95, 1500, "PetroMax", titulos=17),
        _equipe("Andretti Global", "Estados Unidos", "🇺🇸", "#00A9E0", "honda_indy", 92, 110, 90, 1400, "Banco Vetor", titulos=4),
        _equipe("Arrow McLaren", "Estados Unidos", "🇺🇸", "#FF8000", "chevrolet_indy", 91, 105, 88, 1350, "TechNova"),
        _equipe("Meyer Shank", "Estados Unidos", "🇺🇸", "#E31837", "honda_indy", 87, 80, 78, 1000, "AeroLine", "Meyer Shank Racing"),
        _equipe("Rahal Letterman", "Estados Unidos", "🇺🇸", "#003DA5", "honda_indy", 85, 85, 80, 1050, "Banco Vetor", "Rahal Letterman Lanigan Racing", titulos=1),
        _equipe("Ed Carpenter", "Estados Unidos", "🇺🇸", "#7A7D84", "chevrolet_indy", 84, 72, 72, 900, "Seguros Prisma", "Ed Carpenter Racing"),
        _equipe("A.J. Foyt", "Estados Unidos", "🇺🇸", "#FF6712", "chevrolet_indy", 83, 70, 74, 850, "Seguros Prisma", "A.J. Foyt Enterprises", titulos=2),
        _equipe("Dale Coyne", "Estados Unidos", "🇺🇸", "#F2A900", "honda_indy", 81, 60, 66, 700, "Lanchonetes BigBurguer", "Dale Coyne Racing"),
        _equipe("Juncos Hollinger", "Estados Unidos", "🇺🇸", "#00B140", "chevrolet_indy", 80, 62, 64, 750, "Energia Volts"),
    ]
    P = lambda *a, **k: _piloto(*a, **k)
    pilotos = [
        P("Álex Palou", "PAL", 10, "Espanha", "🇪🇸", 29, "chip_ganassi", "P1", 800, 97, concentracao=98, auge=(26, 34)),
        P("Scott Dixon", "DIX", 9, "Nova Zelândia", "🇳🇿", 45, "chip_ganassi", "P2", 700, 91, concentracao=98, acerto=96, auge=(25, 38)),
        P("Kyffin Simpson", "SIM", 8, "Ilhas Cayman", "🇰🇾", 21, "chip_ganassi", "P3", 150, 80, potencial=87, auge=(24, 31)),
        P("Josef Newgarden", "NEW", 2, "Estados Unidos", "🇺🇸", 35, "team_penske", "P1", 650, 91, auge=(25, 34)),
        P("Scott McLaughlin", "MCL", 3, "Nova Zelândia", "🇳🇿", 33, "team_penske", "P2", 550, 92, velocidade=95),
        P("David Malukas", "MAL", 12, "Estados Unidos", "🇺🇸", 24, "team_penske", "P3", 220, 87, potencial=92, concentracao=82),
        P("Kyle Kirkwood", "KIR", 27, "Estados Unidos", "🇺🇸", 27, "andretti_global", "P1", 500, 92),
        P("Will Power", "POW", 26, "Austrália", "🇦🇺", 45, "andretti_global", "P2", 600, 90, velocidade=96, concentracao=86, auge=(26, 38)),
        P("Marcus Ericsson", "ERI", 28, "Suécia", "🇸🇪", 35, "andretti_global", "P3", 350, 86, concentracao=92),
        P("Pato O'Ward", "OWA", 5, "México", "🇲🇽", 26, "arrow_mclaren", "P1", 550, 94, ultrapassagem=97, concentracao=87),
        P("Christian Lundgaard", "LUN", 7, "Dinamarca", "🇩🇰", 24, "arrow_mclaren", "P2", 280, 90, potencial=94),
        P("Nolan Siegel", "SIE", 6, "Estados Unidos", "🇺🇸", 21, "arrow_mclaren", "P3", 140, 83, potencial=90, concentracao=79),
        P("Felix Rosenqvist", "ROS", 60, "Suécia", "🇸🇪", 34, "meyer_shank", "P1", 320, 90, velocidade=94),
        P("Marcus Armstrong", "ARM", 66, "Nova Zelândia", "🇳🇿", 25, "meyer_shank", "P2", 180, 87, potencial=91),
        P("Graham Rahal", "RAH", 15, "Estados Unidos", "🇺🇸", 37, "rahal_letterman", "P1", 300, 84, acerto=90),
        P("Louis Foster", "FOS", 45, "Reino Unido", "🇬🇧", 22, "rahal_letterman", "P2", 140, 84, potencial=90, auge=(24, 31)),
        P("Mick Schumacher", "MSC", 47, "Alemanha", "🇩🇪", 27, "rahal_letterman", "P3", 250, 83, potencial=89, chuva=87),
        P("Alexander Rossi", "ROS2", 20, "Estados Unidos", "🇺🇸", 34, "ed_carpenter", "P1", 300, 88),
        P("Christian Rasmussen", "RAS", 21, "Dinamarca", "🇩🇰", 25, "ed_carpenter", "P2", 150, 86, concentracao=80, ultrapassagem=91),
        P("Santino Ferrucci", "FER", 14, "Estados Unidos", "🇺🇸", 27, "a_j_foyt", "P1", 180, 85, largada=92),
        P("Caio Collet", "COL", 4, "Brasil", "🇧🇷", 24, "a_j_foyt", "P2", 120, 84, potencial=91, auge=(24, 31)),
        P("Romain Grosjean", "GRO", 18, "França", "🇫🇷", 40, "dale_coyne", "P1", 280, 85, concentracao=78, velocidade=90),
        P("Dennis Hauger", "HAU", 19, "Noruega", "🇳🇴", 23, "dale_coyne", "P2", 130, 85, potencial=92, auge=(24, 31)),
        P("Rinus VeeKay", "VEE", 76, "Países Baixos", "🇳🇱", 25, "juncos_hollinger", "P1", 170, 86, chuva=90),
        P("Sting Ray Robb", "ROB", 77, "Estados Unidos", "🇺🇸", 24, "juncos_hollinger", "P2", 100, 78, potencial=84),
        # reservas/500 milhas e mercado
        P("Hélio Castroneves", "CAS", 6, "Brasil", "🇧🇷", 50, "meyer_shank", "teste", 200, 84, concentracao=94, auge=(25, 38)),
        P("Ryan Hunter-Reay", "HUN", 31, "Estados Unidos", "🇺🇸", 45, "arrow_mclaren", "teste", 120, 83),
        P("Takuma Sato", "SATI", 75, "Japão", "🇯🇵", 49, "rahal_letterman", "teste", 120, 83, concentracao=80),
        P("Ed Carpenter", "CAR", 33, "Estados Unidos", "🇺🇸", 45, "ed_carpenter", "teste", 100, 82, acerto=92),
        P("Conor Daly", "DALI", 23, "Estados Unidos", "🇺🇸", 34, "juncos_hollinger", "teste", 90, 82),
        P("Katherine Legge", "LEG", 11, "Reino Unido", "🇬🇧", 45, "a_j_foyt", "teste", 80, 80),
        P("Jacob Abel", "ABE", 51, "Estados Unidos", "🇺🇸", 25, None, "livre", 70, 79, potencial=86),
        P("Robert Shwartzman", "SHW", 83, "Israel", "🇮🇱", 26, None, "livre", 120, 84, potencial=89),
        P("Callum Ilott", "ILO", 90, "Reino Unido", "🇬🇧", 27, None, "livre", 130, 85, potencial=90),
        P("Linus Lundqvist", "LUND", 8, "Suécia", "🇸🇪", 27, "team_penske", "teste", 80, 81),
        P("Jack Harvey", "HAR", 24, "Reino Unido", "🇬🇧", 33, "dale_coyne", "teste", 70, 80),
        P("Toby Sowery", "SOW", 51, "Reino Unido", "🇬🇧", 30, None, "livre", 50, 79),
    ]
    motores = [
        _fornecedor("Honda Indy", 96, 92, 16.0, "V6 biturbo híbrido da Honda — atual campeã de construtores da IndyCar."),
        _fornecedor("Chevrolet Indy", 95, 91, 15.0, "V6 biturbo da Ilmor/Chevrolet — fortíssimo nos ovais curtos."),
        _fallback("Motor emprestado da IndyCar (compulsório)"),
    ]
    motores[0]["id"], motores[1]["id"] = "honda_indy", "chevrolet_indy"
    calendario = [
        _etapa("GP de St. Petersburg", "Ruas de St. Petersburg", "Estados Unidos", "🇺🇸", 100, "1 mar", .45, .35, 1.8, .12),
        _etapa("Phoenix 250", "Phoenix Raceway (oval)", "Estados Unidos", "🇺🇸", 250, "7 mar", .90, .75, 1.6, .02),
        _etapa("GP de Arlington", "Ruas de Arlington", "Estados Unidos", "🇺🇸", 70, "15 mar", .5, .4, 1.7, .18),
        _etapa("GP do Alabama", "Barber Motorsports Park", "Estados Unidos", "🇺🇸", 90, "29 mar", .45, .45, 2.0, .25),
        _etapa("GP de Long Beach", "Ruas de Long Beach", "Estados Unidos", "🇺🇸", 90, "19 abr", .5, .35, 1.7, .08),
        _etapa("GP de Indianápolis (misto)", "IMS Road Course", "Estados Unidos", "🇺🇸", 85, "9 mai", .55, .6, 1.9, .25),
        _etapa("500 Milhas de Indianápolis", "Indianapolis Motor Speedway (oval)", "Estados Unidos", "🇺🇸", 200, "24 mai", .95, .85, 1.5, .05),
        _etapa("GP de Detroit", "Ruas de Detroit", "Estados Unidos", "🇺🇸", 100, "31 mai", .45, .3, 1.8, .2),
        _etapa("Bommarito 500", "WWTR Gateway (oval)", "Estados Unidos", "🇺🇸", 260, "7 jun", .9, .7, 1.7, .08),
        _etapa("GP de Road America", "Road America", "Estados Unidos", "🇺🇸", 55, "21 jun", .55, .65, 2.1, .25),
        _etapa("Indy 200 Mid-Ohio", "Mid-Ohio", "Estados Unidos", "🇺🇸", 90, "5 jul", .45, .4, 2.0, .25),
        _etapa("Music City GP", "Nashville Superspeedway (oval)", "Estados Unidos", "🇺🇸", 206, "20 jul", .9, .75, 1.6, .05),
        _etapa("GP de Portland", "Portland International", "Estados Unidos", "🇺🇸", 110, "9 ago", .5, .55, 1.9, .15),
        _etapa("Indy Markham", "Ruas de Markham", "Canadá", "🇨🇦", 85, "16 ago", .5, .35, 1.7, .2),
        _etapa("GP de Washington", "Ruas de Washington, D.C.", "Estados Unidos", "🇺🇸", 85, "23 ago", .5, .4, 1.7, .2),
        _etapa("Milwaukee 250 — Corrida 1", "Milwaukee Mile (oval)", "Estados Unidos", "🇺🇸", 250, "29 ago", .9, .7, 1.8, .05),
        _etapa("Milwaukee 250 — Corrida 2", "Milwaukee Mile (oval)", "Estados Unidos", "🇺🇸", 250, "30 ago", .9, .7, 1.8, .05),
        _etapa("GP de Monterey", "Laguna Seca", "Estados Unidos", "🇺🇸", 95, "6 set", .45, .4, 2.2, .1),
    ]
    hall = [
        {"nome": "A.J. Foyt", "pais": "Estados Unidos", "bandeira": "🇺🇸", "titulos": 7, "vitorias": 67, "anos": "1957-1993"},
        {"nome": "Mario Andretti", "pais": "Estados Unidos", "bandeira": "🇺🇸", "titulos": 4, "vitorias": 52, "anos": "1964-1994"},
        {"nome": "Scott Dixon* (em atividade)", "pais": "Nova Zelândia", "bandeira": "🇳🇿", "titulos": 6, "vitorias": 58, "anos": "2001-"},
        {"nome": "Dário Franchitti", "pais": "Reino Unido", "bandeira": "🇬🇧", "titulos": 4, "vitorias": 31, "anos": "1997-2013"},
        {"nome": "Al Unser", "pais": "Estados Unidos", "bandeira": "🇺🇸", "titulos": 3, "vitorias": 39, "anos": "1965-1994"},
        {"nome": "Rick Mears", "pais": "Estados Unidos", "bandeira": "🇺🇸", "titulos": 3, "vitorias": 29, "anos": "1976-1992"},
        {"nome": "Emerson Fittipaldi", "pais": "Brasil", "bandeira": "🇧🇷", "titulos": 1, "vitorias": 22, "anos": "1984-1996"},
        {"nome": "Hélio Castroneves", "pais": "Brasil", "bandeira": "🇧🇷", "titulos": 0, "vitorias": 31, "anos": "1998-"},
    ]
    return {"meta": {"id": "indy_2026", "nome": "Fórmula Indy 2026", "categoria": "IndyCar Series", "ano": 2026,
                     "descricao": "Monopostos americanos: ovais a 370 km/h, ruas e mistos — e as lendárias 500 Milhas de Indianápolis. Grid cheio com 25 carros e todo mundo pontuando.",
                     "rotulo_fornecedor": "Motor", "rotulo_corrida2": None,
                     "pontos_corrida": list(PONTOS_INDY), "pontos_corrida2": list(PONTOS_INDY),
                     "importancia_carro_sugerida": 0.45, "fator_pontos_bonus": 0.5, "pontua_abandono": True},
            "equipes": equipes, "pilotos": pilotos, "motores": motores, "calendario": calendario,
            "hall_da_fama": hall, "patrocinadores": copy.deepcopy(_f1.PATROCINADORES)}


# =====================================================================
#  DB STOCK CAR PRO SERIES 2026
# =====================================================================
def db_stock_2026():
    def E(nome, mot, nivel, caixa, prest, inv, cor="#888888", completo=None, titulos=0):
        return _equipe(nome, "Brasil", "🇧🇷", cor, mot, nivel, caixa, prest, inv,
                       nome_completo=completo or nome, titulos=titulos)
    equipes = [
        E("Eurofarma RC", "mitsubishi_stock", 93, 70, 95, 950, "#F6C90E"),
        E("A.Mattheis Vogel", "chevrolet_stock", 91, 65, 92, 900, "#D22630"),
        E("Full Time Gazoo", "toyota_stock", 89, 66, 90, 880, "#EB0A1E", "Full Time Toyota Gazoo Racing"),
        E("Blau Motorsport", "mitsubishi_stock", 88, 58, 86, 800, "#0057B8"),
        E("Mercado Livre Racing", "toyota_stock", 88, 68, 88, 900, "#FFE600"),
        E("Time Lubrax TMG", "chevrolet_stock", 88, 60, 87, 820, "#00A859"),
        E("Cavaleiro Sports", "chevrolet_stock", 87, 55, 84, 780, "#111111"),
        E("Scuderia Bandeiras", "mitsubishi_stock", 86, 56, 85, 800, "#8A1538"),
        E("Crown Racing", "toyota_stock", 84, 52, 80, 720, "#F26522"),
        E("CAR Racing", "toyota_stock", 83, 50, 78, 700, "#5B2D90"),
        E("A.Mattheis TMG", "toyota_stock", 83, 54, 82, 740, "#0072CE"),
        E("Scuderia Chiarelli", "chevrolet_stock", 82, 50, 80, 700, "#B58500"),
        E("RC Team", "mitsubishi_stock", 82, 48, 76, 680, "#666666"),
        E("Car Racing Sports", "mitsubishi_stock", 81, 46, 74, 650, "#2E7D6B"),
        E("Scuderia Bandeiras Sports", "chevrolet_stock", 84, 54, 83, 760, "#34495E"),
        E("SG28 Racing", "mitsubishi_stock", 78, 44, 68, 600, "#D6336C"),
    ]
    P = lambda n, s, num, idade, eq, papel, sal, ovr, **k: _piloto(n, s, num, "Brasil", "🇧🇷", idade, eq, papel, sal, ovr, **k)
    pilotos = [
        P("Felipe Fraga", "FRA", 1, 30, "eurofarma_rc", "P1", 220, 94, velocidade=97),
        P("Gaetano di Mauro", "MAU", 11, 28, "eurofarma_rc", "P2", 180, 91, concentracao=94),
        P("Gabriel Casagrande", "CAS", 83, 31, "a_mattheis_vogel", "P1", 210, 93),
        P("Lucas Foresti", "FOR", 12, 33, "a_mattheis_vogel", "P2", 120, 86),
        P("Ricardo Zonta", "ZON", 10, 50, "full_time_gazoo", "P1", 150, 88, acerto=95, auge=(25, 38)),
        P("Alfredo Ibiapina", "IBI", 80, 17, "full_time_gazoo", "P2", 40, 79, potencial=91, auge=(23, 31)),
        P("Daniel Serra", "SERI", 29, 42, "blau_motorsport", "P1", 190, 92, chuva=95, concentracao=95),
        P("Allam Khodair", "KHO", 18, 45, "blau_motorsport", "P2", 130, 87, auge=(25, 38)),
        P("Thiago Camilo", "CAM", 21, 41, "mercado_livre_racing", "P1", 180, 90),
        P("César Ramos", "RAM", 30, 38, "mercado_livre_racing", "P2", 140, 88),
        P("Hélio Castroneves", "HEL", 6, 51, "mercado_livre_racing", "P3", 160, 85, concentracao=93, auge=(25, 38)),
        P("Felipe Massa", "MAS", 19, 45, "time_lubrax_tmg", "P1", 200, 88, chuva=91, auge=(25, 37)),
        P("Júlio Campos", "JUL", 4, 44, "time_lubrax_tmg", "P2", 130, 87, auge=(25, 37)),
        P("Guilherme Salas", "SAL", 85, 31, "cavaleiro_sports", "P1", 130, 89),
        P("Ricardo Maurício", "RIC", 90, 47, "cavaleiro_sports", "P2", 150, 89, concentracao=94, auge=(25, 38)),
        P("Nelson Piquet Jr.", "PIQ", 33, 41, "scuderia_bandeiras", "P1", 150, 87),
        P("Rafael Suzuki", "SUZ", 8, 39, "scuderia_bandeiras", "P2", 120, 87, concentracao=92),
        P("Arthur Leist", "LEI", 81, 24, "crown_racing", "P1", 90, 85, potencial=91),
        P("Lucas Kohl", "KOH", 95, 28, "crown_racing", "P2", 70, 82),
        P("Rafael Reis", "RAFI", 301, 24, "car_racing", "P1", 80, 84, potencial=90),
        P("Leonardo Reis", "LEO", 293, 22, "car_racing", "P2", 50, 81, potencial=89, auge=(24, 31)),
        P("Enzo Elias", "ELI", 73, 24, "a_mattheis_tmg", "P1", 90, 86, potencial=92),
        P("Renan Guerra", "REN", 99, 36, "a_mattheis_tmg", "P2", 60, 80),
        P("Cacá Bueno", "CAC", 0, 51, "scuderia_chiarelli", "P1", 170, 86, concentracao=95, acerto=94, auge=(25, 38)),
        P("André Moraes Jr.", "AND", 22, 26, "scuderia_chiarelli", "P2", 50, 79, potencial=86),
        P("Sérgio Sette Câmara", "SET", 7, 27, "rc_team", "P1", 110, 86, potencial=91, chuva=90),
        P("Zezinho Mugiatti", "MUG", 38, 22, "rc_team", "P2", 60, 83, potencial=90, auge=(24, 31)),
        P("Felipe Baptista", "BAP", 121, 26, "car_racing_sports", "P1", 90, 86),
        P("Vicente Orige", "ORI", 444, 39, "car_racing_sports", "P2", 80, 83),
        P("Rubens Barrichello", "RUBI", 111, 53, "scuderia_bandeiras_sports", "P1", 190, 87, chuva=96, acerto=96, auge=(25, 38)),
        P("Átila Abreu", "ATI", 51, 39, "scuderia_bandeiras_sports", "P2", 120, 85, ultrapassagem=90),
        P("Tatiana Calderón", "TATI", 25, 33, "sg28_racing", "P1", 80, 82, pais_ignora=None) if False else
        _piloto("Tatiana Calderón", "TATI", 25, "Colômbia", "🇨🇴", 33, "sg28_racing", "P1", 80, 82),
        P("Bruna Tomaselli", "BRU", 97, 28, "sg28_racing", "P2", 50, 79, potencial=87),
        P("Felipe Barrichello Bartz", "BART", 24, 20, "sg28_racing", "P3", 45, 81, potencial=90, auge=(23, 31)),
        # mercado / Stock Light
        P("Dudu Barrichello", "DUDU", 91, 24, None, "livre", 70, 84, potencial=89),
        P("Vitor Baptista", "VIT", 120, 28, None, "livre", 60, 82),
        P("Diego Nunes", "DI", 70, 39, None, "livre", 70, 83),
        P("Bia Figueiredo", "BIA", 100, 41, None, "livre", 60, 81),
        P("Pedro Cardoso", "PED", 143, 26, None, "livre", 40, 79, potencial=87),
        P("Matheus Leist", "MAT", 81, 28, None, "livre", 50, 80),
    ]
    motores = [
        _fornecedor("Toyota Corolla Cross", 94, 90, 9.0, "SUV da Toyota com o retorno do V8 aspirado em 2026."),
        _fornecedor("Mitsubishi Eclipse Cross", 94, 89, 9.0, "O SUV da Mitsubishi, campeão de 2025 com Felipe Fraga."),
        _fornecedor("Chevrolet Tracker", 93, 90, 8.5, "O Tracker V8 — a maior torcida do Brasil empurrando junto."),
        _fallback("Carro da organização (compulsório)"),
    ]
    for m, mid in zip(motores, ["toyota_stock", "mitsubishi_stock", "chevrolet_stock", "fia"]):
        m["id"] = mid
    calendario = [
        _etapa("Etapa de Curvelo", "Circuito dos Cristais, Curvelo-MG", "Brasil", "🇧🇷", 20, "8 mar", .5, .5, 2.0, .25, True),
        _etapa("Etapa de Cascavel", "Autódromo de Cascavel-PR", "Brasil", "🇧🇷", 32, "29 mar", .65, .55, 2.2, .3, True),
        _etapa("Etapa de Interlagos", "Interlagos, São Paulo-SP", "Brasil", "🇧🇷", 28, "26 abr", .55, .7, 2.0, .35, True),
        _etapa("Etapa de Goiânia", "Autódromo Ayrton Senna, Goiânia-GO", "Brasil", "🇧🇷", 30, "17 mai", .6, .6, 2.1, .15, True),
        _etapa("Etapa de Cuiabá (noturna)", "Autódromo de Cuiabá-MT", "Brasil", "🇧🇷", 26, "20 jun", .55, .5, 1.9, .05, True),
        _etapa("Etapa do Velocitta", "Velocitta, Mogi Guaçu-SP", "Brasil", "🇧🇷", 24, "26 jul", .4, .35, 2.3, .2, True),
        _etapa("Etapa de Santa Cruz do Sul", "Autódromo de Santa Cruz do Sul-RS", "Brasil", "🇧🇷", 26, "9 ago", .5, .45, 2.0, .35, True),
        _etapa("Etapa de Curvelo II", "Circuito dos Cristais, Curvelo-MG", "Brasil", "🇧🇷", 20, "6 set", .5, .5, 2.0, .2, True),
        _etapa("Corrida de Duplas — Brasília", "Autódromo de Brasília-DF", "Brasil", "🇧🇷", 24, "27 set", .55, .55, 1.9, .15, True),
        _etapa("Corrida Endurance — Cascavel", "Autódromo de Cascavel-PR", "Brasil", "🇧🇷", 75, "18 out", .6, .55, 2.6, .3, True),
        _etapa("Corrida do Milhão — Velopark", "Velopark, Nova Santa Rita-RS", "Brasil", "🇧🇷", 34, "15 nov", .45, .4, 2.0, .3, True),
        _etapa("Super Final — Interlagos", "Interlagos, São Paulo-SP", "Brasil", "🇧🇷", 28, "13 dez", .55, .7, 2.0, .4, True),
    ]
    hall = [
        {"nome": "Ingo Hoffmann", "pais": "Brasil", "bandeira": "🇧🇷", "titulos": 12, "vitorias": 77, "anos": "1979-2008"},
        {"nome": "Cacá Bueno* (em atividade)", "pais": "Brasil", "bandeira": "🇧🇷", "titulos": 5, "vitorias": 37, "anos": "2002-"},
        {"nome": "Paulo Gomes", "pais": "Brasil", "bandeira": "🇧🇷", "titulos": 4, "vitorias": 27, "anos": "1979-2003"},
        {"nome": "Chico Serra", "pais": "Brasil", "bandeira": "🇧🇷", "titulos": 3, "vitorias": 33, "anos": "1981-2007"},
        {"nome": "Daniel Serra* (em atividade)", "pais": "Brasil", "bandeira": "🇧🇷", "titulos": 3, "vitorias": 27, "anos": "2013-"},
        {"nome": "Gabriel Casagrande* (em atividade)", "pais": "Brasil", "bandeira": "🇧🇷", "titulos": 3, "vitorias": 17, "anos": "2013-"},
        {"nome": "Ricardo Maurício* (em atividade)", "pais": "Brasil", "bandeira": "🇧🇷", "titulos": 3, "vitorias": 34, "anos": "2004-"},
        {"nome": "Marcos Gomes", "pais": "Brasil", "bandeira": "🇧🇷", "titulos": 1, "vitorias": 17, "anos": "2005-2023"},
    ]
    return {"meta": {"id": "stock_2026", "nome": "Stock Car 2026", "categoria": "Stock Car Pro Series", "ano": 2026,
                     "descricao": "A maior categoria do Brasil: SUVs V8, 34 carros, sprint no sábado e principal no domingo, Corrida do Milhão e até prova Endurance.",
                     "rotulo_fornecedor": "Montadora", "rotulo_corrida2": "Corrida sprint",
                     "pontos_corrida": list(PONTOS_STOCK_PRINCIPAL), "pontos_corrida2": list(PONTOS_STOCK_SPRINT),
                     "importancia_carro_sugerida": 0.40, "fator_pontos_bonus": 0.35, "pontua_abandono": False},
            "equipes": equipes, "pilotos": pilotos, "motores": motores, "calendario": calendario,
            "hall_da_fama": hall, "patrocinadores": copy.deepcopy(_f1.PATROCINADORES)}


# =====================================================================
#  DB DTM 2026
# =====================================================================
def db_dtm_2026():
    equipes = [
        _equipe("Manthey Racing", "Alemanha", "🇩🇪", "#F5D90A", "porsche_gt3", 93, 85, 94, 1100, "PetroMax", titulos=3),
        _equipe("Winward Racing", "Estados Unidos", "🇺🇸", "#C0C0C0", "mercedes_gt3", 91, 82, 90, 1050, "PetroMax"),
        _equipe("Schubert Motorsport", "Alemanha", "🇩🇪", "#1C69D4", "bmw_gt3", 90, 80, 90, 1050, "Banco Vetor", titulos=2),
        _equipe("Landgraf Motorsport", "Alemanha", "🇩🇪", "#00A19B", "mercedes_gt3", 88, 72, 84, 950, "TechNova"),
        _equipe("Grasser Racing", "Áustria", "🇦🇹", "#E87722", "lamborghini_gt3", 88, 70, 84, 920, "Energia Volts", "Grasser Racing Team"),
        _equipe("Emil Frey Racing", "Suíça", "🇨🇭", "#D22630", "ferrari_gt3", 87, 74, 85, 960, "AeroLine"),
        _equipe("Abt Sportsline", "Alemanha", "🇩🇪", "#888888", "lamborghini_gt3", 86, 78, 88, 980, "Banco Vetor", titulos=5),
        _equipe("Land-Motorsport", "Alemanha", "🇩🇪", "#F5D90A", "porsche_gt3", 85, 60, 78, 800, "Seguros Prisma"),
        _equipe("HRT Ford Performance", "Alemanha", "🇩🇪", "#2E96FF", "ford_gt3", 85, 76, 84, 940, "TechNova"),
        _equipe("Comtoyou Racing", "Bélgica", "🇧🇪", "#00565F", "aston_gt3", 84, 64, 78, 850, "Seguros Prisma"),
        _equipe("Dörr Motorsport", "Alemanha", "🇩🇪", "#FF8000", "mclaren_gt3", 83, 62, 76, 820, "Energia Volts"),
    ]
    P = lambda *a, **k: _piloto(*a, **k)
    pilotos = [
        P("Thomas Preining", "PRE", 91, "Áustria", "🇦🇹", 27, "manthey_racing", "P1", 320, 94, auge=(25, 34)),
        P("Ricardo Feller", "FEL", 90, "Suíça", "🇨🇭", 28, "manthey_racing", "P2", 240, 91),
        P("Maro Engel", "ENG", 80, "Alemanha", "🇩🇪", 40, "winward_racing", "P1", 300, 93, concentracao=96),
        P("Jules Gounon", "GOU", 48, "França", "🇫🇷", 31, "winward_racing", "P2", 220, 89),
        P("Kelvin van der Linde", "VDL", 3, "África do Sul", "🇿🇦", 30, "schubert_motorsport", "P1", 260, 90, chuva=94),
        P("Marco Wittmann", "WIT", 11, "Alemanha", "🇩🇪", 36, "schubert_motorsport", "P2", 260, 89, concentracao=94),
        P("Lucas Auer", "AUE", 22, "Áustria", "🇦🇹", 31, "landgraf_motorsport", "P1", 240, 90),
        P("Tom Kalender", "KAL", 84, "Alemanha", "🇩🇪", 18, "landgraf_motorsport", "P2", 80, 82, potencial=92, auge=(23, 31)),
        P("Mirko Bortolotti", "BOR", 63, "Itália", "🇮🇹", 36, "grasser_racing", "P1", 280, 92),
        P("Maximilian Paul", "PAU", 19, "Alemanha", "🇩🇪", 26, "grasser_racing", "P2", 130, 84),
        P("Matteo Cairoli", "Matteo Cairoli", 14, "Itália", "🇮🇹", 29, "emil_frey_racing", "P1", 200, 87),
        P("Thierry Vermeulen", "VER", 69, "Países Baixos", "🇳🇱", 23, "emil_frey_racing", "P2", 140, 86, potencial=91),
        P("Marco Mapelli", "Marco Mapelli", 10, "Itália", "🇮🇹", 38, "abt_sportsline", "P1", 190, 86, acerto=93),
        P("Luca Engstler", "ENR", 130, "Alemanha", "🇩🇪", 26, "abt_sportsline", "P2", 140, 85),
        P("Bastian Buus", "BUU", 29, "Dinamarca", "🇩🇰", 22, "land_motorsport", "P1", 150, 85, potencial=92, auge=(24, 31)),
        P("Arjun Maini", "Arjun Maini", 36, "Índia", "🇮🇳", 28, "hrt_ford_performance", "P1", 160, 84),
        P("Finn Wiebelhaus", "Wiebelhaus", 64, "Alemanha", "🇩🇪", 19, "hrt_ford_performance", "P2", 70, 81, potencial=89, auge=(23, 31)),
        P("Nicki Thiim", "THI", 7, "Dinamarca", "🇩🇰", 37, "comtoyou_racing", "P1", 200, 88),
        P("Nicolas Baert", "BAE", 8, "Bélgica", "🇧🇪", 24, "comtoyou_racing", "P2", 90, 81, potencial=87),
        P("Timo Glock", "GLO", 16, "Alemanha", "🇩🇪", 44, "dorr_motorsport", "P1", 210, 84, chuva=92, auge=(25, 36)),
        P("Ben Dörr", "DOR", 25, "Alemanha", "🇩🇪", 21, "dorr_motorsport", "P2", 80, 82, potencial=89, auge=(24, 31)),
        # mercado GT
        P("Ayhancan Güven", "GUV", 99, "Turquia", "🇹🇷", 28, None, "livre", 220, 91),
        P("Morris Schuring", "SCH", 92, "Países Baixos", "🇳🇱", 21, None, "livre", 110, 85, potencial=91),
        P("Jordan Pepper", "PEP", 9, "África do Sul", "🇿🇦", 29, None, "livre", 120, 85),
        P("René Rast", "RAS", 33, "Alemanha", "🇩🇪", 39, None, "livre", 230, 89, auge=(25, 35)),
        P("Fabian Schiller", "SCI", 31, "Alemanha", "🇩🇪", 28, None, "livre", 90, 83),
        P("Tim Heinemann", "HEI", 30, "Alemanha", "🇩🇪", 28, None, "livre", 80, 82),
    ]
    motores = [
        _fornecedor("Porsche 911 GT3 R", 95, 91, 13.0, "O GT3 a ser batido — atual campeão com a Manthey."),
        _fornecedor("Mercedes-AMG GT3", 94, 92, 13.0, "Equilíbrio e confiabilidade de Affalterbach."),
        _fornecedor("BMW M4 GT3 Evo", 94, 90, 12.5, "O seis-em-linha biturbo da Schubert."),
        _fornecedor("Ferrari 296 GT3", 93, 89, 12.5, "Refinamento italiano da Emil Frey."),
        _fornecedor("Lamborghini Temerario GT3", 93, 88, 12.0, "O estreante Temerario substituindo o Huracán."),
        _fornecedor("Aston Martin Vantage GT3", 92, 90, 11.5, "Elegância britânica com coração V8 AMG."),
        _fornecedor("McLaren 720S GT3 Evo", 92, 88, 11.5, "Leve, ágil e temperamental — assinatura de Woking."),
        _fornecedor("Ford Mustang GT3", 91, 89, 11.0, "O V8 americano em solo alemão."),
        _fornecedor("Audi R8 LMS Evo II", 90, 89, 10.0, "O veterano V10 — barato e honesto."),
        _fallback("GT3 emprestado do ADAC (compulsório)"),
    ]
    for m, mid in zip(motores, ["porsche_gt3", "mercedes_gt3", "bmw_gt3", "ferrari_gt3", "lamborghini_gt3",
                                "aston_gt3", "mclaren_gt3", "ford_gt3", "audi_gt3", "fia"]):
        m["id"] = mid
    calendario = [
        _etapa("Red Bull Ring", "Red Bull Ring, Spielberg", "Áustria", "🇦🇹", 40, "26 abr", .65, .7, 1.8, .3, True),
        _etapa("Zandvoort", "Circuito de Zandvoort", "Países Baixos", "🇳🇱", 39, "24 mai", .45, .35, 2.0, .35, True),
        _etapa("Lausitzring", "EuroSpeedway Lausitz", "Alemanha", "🇩🇪", 40, "21 jun", .55, .55, 1.9, .25, True),
        _etapa("Norisring", "Norisring, Nuremberg (rua)", "Alemanha", "🇩🇪", 62, "5 jul", .6, .55, 1.6, .2, True),
        _etapa("Oschersleben", "Motorsport Arena Oschersleben", "Alemanha", "🇩🇪", 42, "26 jul", .45, .4, 2.0, .25, True),
        _etapa("Nürburgring", "Nürburgring (sprint)", "Alemanha", "🇩🇪", 40, "16 ago", .5, .5, 2.0, .4, True),
        _etapa("Sachsenring", "Sachsenring", "Alemanha", "🇩🇪", 45, "13 set", .45, .4, 2.1, .3, True),
        _etapa("Final — Hockenheim", "Hockenheimring", "Alemanha", "🇩🇪", 37, "11 out", .6, .6, 1.9, .3, True),
    ]
    hall = [
        {"nome": "Bernd Schneider", "pais": "Alemanha", "bandeira": "🇩🇪", "titulos": 5, "vitorias": 43, "anos": "1986-2008"},
        {"nome": "Klaus Ludwig", "pais": "Alemanha", "bandeira": "🇩🇪", "titulos": 3, "vitorias": 37, "anos": "1985-2000"},
        {"nome": "René Rast", "pais": "Alemanha", "bandeira": "🇩🇪", "titulos": 3, "vitorias": 28, "anos": "2012-2025"},
        {"nome": "Mattias Ekström", "pais": "Suécia", "bandeira": "🇸🇪", "titulos": 2, "vitorias": 25, "anos": "2001-2018"},
        {"nome": "Gary Paffett", "pais": "Reino Unido", "bandeira": "🇬🇧", "titulos": 2, "vitorias": 23, "anos": "2003-2018"},
        {"nome": "Marco Wittmann* (em atividade)", "pais": "Alemanha", "bandeira": "🇩🇪", "titulos": 2, "vitorias": 19, "anos": "2013-"},
        {"nome": "Bruno Spengler", "pais": "Canadá", "bandeira": "🇨🇦", "titulos": 1, "vitorias": 18, "anos": "2005-2019"},
        {"nome": "Thomas Preining* (em atividade)", "pais": "Áustria", "bandeira": "🇦🇹", "titulos": 1, "vitorias": 12, "anos": "2022-"},
    ]
    return {"meta": {"id": "dtm_2026", "nome": "DTM 2026", "categoria": "DTM (GT3)", "ano": 2026,
                     "descricao": "O campeonato alemão de turismo em formato GT3: 8 fins de semana, duas corridas por etapa e 8 montadoras no grid.",
                     "rotulo_fornecedor": "Carro GT3", "rotulo_corrida2": "Corrida 1",
                     "pontos_corrida": list(PONTOS_DTM), "pontos_corrida2": list(PONTOS_DTM),
                     "importancia_carro_sugerida": 0.50, "fator_pontos_bonus": 1.4, "pontua_abandono": False},
            "equipes": equipes, "pilotos": pilotos, "motores": motores, "calendario": calendario,
            "hall_da_fama": hall, "patrocinadores": copy.deepcopy(_f1.PATROCINADORES)}


def dbs_embutidas():
    return {"f1_2026": db_f1_2026(), "indy_2026": db_indy_2026(),
            "stock_2026": db_stock_2026(), "dtm_2026": db_dtm_2026()}


def grid_natural(db_dados):
    return sum(1 for p in db_dados["pilotos"] if p.get("papel") in PAPEIS_TITULARES)


def grid_maximo(db_dados):
    return min(len(db_dados["pilotos"]), len(db_dados["equipes"]) * 4)


def modelo_db_vazia():
    base = db_dtm_2026()
    base["meta"] = {"id": "minha_db", "nome": "Minha Categoria 2027", "categoria": "Categoria Personalizada",
                    "ano": 2027, "descricao": "DB criada no editor do Cockpit Manager.",
                    "rotulo_fornecedor": "Motor", "rotulo_corrida2": "Sprint",
                    "pontos_corrida": list(_f1.PONTOS_CORRIDA), "pontos_corrida2": list(_f1.PONTOS_SPRINT),
                    "importancia_carro_sugerida": 0.55, "fator_pontos_bonus": 1.0, "pontua_abandono": False}
    base["equipes"] = [_equipe(f"Equipe {i + 1}", "Brasil", "🇧🇷", "#3366FF", "motor_exemplo",
                               80, 80, 70, 900) for i in range(4)]
    base["motores"] = [_fornecedor("Motor Exemplo", 90, 90, 10.0, "Edite-me!"),
                       _fallback()]
    base["motores"][0]["id"] = "motor_exemplo"
    base["pilotos"] = []
    for i, eq in enumerate(base["equipes"]):
        for j, papel in enumerate(("P1", "P2")):
            base["pilotos"].append(_piloto(f"Piloto {i * 2 + j + 1}", f"P{i * 2 + j + 1}", i * 2 + j + 1,
                                           "Brasil", "🇧🇷", 25, eq["id"], papel, 100, 82))
    base["pilotos"].append(_piloto("Jovem Promissor", "JOV", 99, "Brasil", "🇧🇷", 19, None, "livre", 40, 78, potencial=93))
    base["calendario"] = [_etapa("Etapa 1", "Autódromo Exemplo", "Brasil", "🇧🇷", 30, "1 mar", .5, .5, 2.0, .2, False),
                          _etapa("Etapa 2", "Circuito Exemplo", "Brasil", "🇧🇷", 28, "15 mar", .6, .6, 1.8, .25, True)]
    base["hall_da_fama"] = []
    return base


# =====================================================================
#  Validação / normalização (usado pelo editor e por DBs carregadas)
# =====================================================================
def validar_e_normalizar(db_dados):
    """Retorna (db_normalizada, erros, avisos). Não levanta exceção."""
    erros, avisos = [], []
    try:
        d = copy.deepcopy(db_dados)
    except Exception:
        return None, ["Conteúdo inválido (não é um objeto de DB)."], []
    if not isinstance(d, dict):
        return None, ["A DB precisa ser um objeto JSON (dicionário)."], []

    meta = d.get("meta") or {}
    meta.setdefault("id", slugificar(meta.get("nome", "minha_db")))
    meta.setdefault("nome", "DB Personalizada")
    meta.setdefault("categoria", "Categoria Personalizada")
    try:
        meta["ano"] = int(meta.get("ano", 2026))
    except Exception:
        meta["ano"] = 2026
    meta.setdefault("descricao", "")
    meta.setdefault("rotulo_fornecedor", "Motor")
    if meta.get("rotulo_corrida2") in ("", "Nenhuma", "nenhuma"):
        meta["rotulo_corrida2"] = None
    for chave, padrao in (("pontos_corrida", _f1.PONTOS_CORRIDA), ("pontos_corrida2", _f1.PONTOS_SPRINT)):
        v = meta.get(chave) or padrao
        try:
            meta[chave] = [int(x) for x in v if str(x).strip() != ""] or list(padrao)
        except Exception:
            meta[chave] = list(padrao)
            avisos.append(f"Pontuação '{chave}' inválida — usando padrão F1.")
    meta.setdefault("importancia_carro_sugerida", 0.55)
    meta.setdefault("fator_pontos_bonus", 1.0)
    meta.setdefault("pontua_abandono", False)
    d["meta"] = meta

    # motores
    motores = d.get("motores") or []
    ids = _unicos([slugificar(m.get("id") or m.get("nome", f"motor{i}")) for i, m in enumerate(motores)])
    motores_ok = []
    for m, mid in zip(motores, ids):
        motores_ok.append({"id": mid, "nome": str(m.get("nome", mid)),
                           "potencia": int(max(30, min(99, float(m.get("potencia", 85))))),
                           "confiabilidade": int(max(30, min(99, float(m.get("confiabilidade", 85))))),
                           "preco": float(m.get("preco", 10) or 0), "proprio_de": m.get("proprio_de"),
                           "desc": str(m.get("desc", ""))})
    if not motores_ok:
        motores_ok = [_fornecedor("Motor Padrão", 88, 88, 10.0, "Fornecedor padrão criado automaticamente.")]
        motores_ok[0]["id"] = "motor_padrao"
        avisos.append("Nenhum fornecedor definido — criei um 'Motor Padrão'.")
    mapa_motor_nome = {m["nome"].lower(): m["id"] for m in motores_ok}
    ids_motores = {m["id"] for m in motores_ok}

    # equipes
    equipes = [e for e in (d.get("equipes") or []) if str(e.get("nome", "")).strip()]
    if len(equipes) < 2:
        erros.append("A DB precisa de pelo menos 2 equipes com nome.")
    ids_e = _unicos([slugificar(e.get("id") or e.get("nome")) for e in equipes])
    mapa_eq_nome = {str(e.get("nome", "")).lower(): eid for e, eid in zip(equipes, ids_e)}
    equipes_ok = []
    for e, eid in zip(equipes, ids_e):
        mid = e.get("motor_id") or mapa_motor_nome.get(str(e.get("motor", "")).lower())
        if mid not in ids_motores:
            mid = motores_ok[0]["id"]
            avisos.append(f"Equipe '{e['nome']}': fornecedor ajustado para {motores_ok[0]['nome']}.")
        equipes_ok.append({"id": eid, "nome": str(e["nome"]),
                           "nome_completo": str(e.get("nome_completo") or e["nome"]),
                           "pais": str(e.get("pais", "Brasil")), "bandeira": str(e.get("bandeira", "🏁")),
                           "cor": str(e.get("cor", "#3366FF")), "motor_id": mid,
                           "motor_proprio": bool(e.get("motor_proprio", False)),
                           "nivel_carro": float(max(30, min(99, float(e.get("nivel_carro", 80))))),
                           "confiabilidade": float(max(30, min(99, float(e.get("confiabilidade", 85))))),
                           "caixa": float(e.get("caixa", 80) or 0),
                           "prestigio": int(max(0, min(99, float(e.get("prestigio", 70))))),
                           "investimento_corrida": int(float(e.get("investimento_corrida", 900) or 0)),
                           "titulos_construtores": int(float(e.get("titulos_construtores", 0) or 0)),
                           "patrocinador": str(e.get("patrocinador") or "Seguros Prisma")})
    ids_equipes = {e["id"] for e in equipes_ok}

    # pilotos
    pilotos = [p for p in (d.get("pilotos") or []) if str(p.get("nome", "")).strip()]
    if len(pilotos) < 4:
        erros.append("A DB precisa de pelo menos 4 pilotos com nome.")
    ids_p = _unicos([slugificar(p.get("id") or p.get("nome")) for p in pilotos])
    pilotos_ok, titulares_por_equipe = [], {eid: 0 for eid in ids_equipes}
    for p, pid in zip(pilotos, ids_p):
        eq_id = p.get("equipe_id") or mapa_eq_nome.get(str(p.get("equipe", "")).lower())
        papel = str(p.get("papel") or "livre")
        if papel not in PAPEIS_TITULARES + ("teste", "livre"):
            papel = "livre"
        if eq_id not in ids_equipes:
            if papel != "livre":
                avisos.append(f"Piloto '{p['nome']}' sem equipe válida — virou agente livre.")
            eq_id, papel = None, "livre"
        if papel in PAPEIS_TITULARES and eq_id:
            titulares_por_equipe[eq_id] += 1
        at = p.get("atributos") or {}
        atributos = {k: int(max(1, min(99, float(at.get(k, 75))))) for k in _f1.ATRIBUTOS}
        try:
            idade = int(float(p.get("idade", 25)))
        except Exception:
            idade = 25
        pilotos_ok.append({"id": pid, "nome": str(p["nome"]),
                           "sigla": str(p.get("sigla") or p["nome"][:3].upper()),
                           "numero": int(float(p.get("numero", 0) or 0)),
                           "pais": str(p.get("pais", "Brasil")), "bandeira": str(p.get("bandeira", "🏁")),
                           "idade": max(14, min(70, idade)), "equipe_id": eq_id, "papel": papel,
                           "salario_corrida": int(float(p.get("salario_corrida", 100) or 0)),
                           "contrato_anos": int(float(p.get("contrato_anos", 2) or 0)),
                           "auge_inicio": int(float(p.get("auge_inicio", 25))), "auge_fim": int(float(p.get("auge_fim", 32))),
                           "potencial": int(max(1, min(99, float(p.get("potencial", 85))))),
                           "atributos": atributos})
    for eid, qtd in titulares_por_equipe.items():
        if qtd == 0:
            nome_eq = next(e["nome"] for e in equipes_ok if e["id"] == eid)
            erros.append(f"A equipe '{nome_eq}' não tem nenhum piloto titular (P1/P2/...).")
        if qtd > 4:
            avisos.append("Uma equipe tem mais de 4 titulares — o excedente pode ser ajustado pelo tamanho do grid.")

    # calendário
    calendario = [c for c in (d.get("calendario") or []) if str(c.get("gp", "")).strip()]
    if not calendario:
        erros.append("A DB precisa de pelo menos 1 etapa no calendário.")
    cal_ok = []
    for c in calendario:
        cal_ok.append({"gp": str(c["gp"]), "circuito": str(c.get("circuito", c["gp"])),
                       "pais": str(c.get("pais", "Brasil")), "bandeira": str(c.get("bandeira", "🏁")),
                       "voltas": int(max(1, float(c.get("voltas", 30) or 30))),
                       "data": str(c.get("data", "")), "sprint": bool(c.get("sprint", False)),
                       "potencia": float(max(0, min(1, float(c.get("potencia", .5))))),
                       "ultrap": float(max(0, min(1, float(c.get("ultrap", .5))))),
                       "desgaste": float(max(0.5, min(4, float(c.get("desgaste", 2))))),
                       "chuva": float(max(0, min(1, float(c.get("chuva", .2)))))})

    # motor compulsório obrigatório
    if "fia" not in {m["id"] for m in motores_ok}:
        motores_ok.append(_fallback())
    for m in motores_ok:  # próprio_de precisa apontar para equipe existente
        if m.get("proprio_de") not in ids_equipes:
            m["proprio_de"] = None if m["id"] != "fia" else None

    d.update({"equipes": equipes_ok, "pilotos": pilotos_ok, "motores": motores_ok,
              "calendario": cal_ok, "hall_da_fama": d.get("hall_da_fama") or [],
              "patrocinadores": d.get("patrocinadores") or copy.deepcopy(_f1.PATROCINADORES)})
    if erros:
        return None, erros, avisos
    return d, [], avisos


# =====================================================================
#  DBs personalizadas salvas em disco (pasta minhas_dbs/)
# =====================================================================
PASTA_DBS = Path(__file__).resolve().parent / "minhas_dbs"


def carregar_dbs_personalizadas():
    saida, problemas = {}, []
    try:
        if PASTA_DBS.exists():
            for arq in sorted(PASTA_DBS.glob("*.json")):
                try:
                    dados, erros, _ = validar_e_normalizar(json.loads(arq.read_text(encoding="utf-8")))
                    if dados:
                        saida[f"custom:{arq.stem}"] = dados
                    else:
                        problemas.append(f"{arq.name}: {'; '.join(erros)}")
                except Exception as e:
                    problemas.append(f"{arq.name}: {e}")
    except Exception:
        pass
    return saida, problemas


def salvar_db_personalizada(db_dados):
    """Salva em minhas_dbs/<id>.json. Retorna (ok, caminho_ou_erro)."""
    try:
        PASTA_DBS.mkdir(parents=True, exist_ok=True)
        caminho = PASTA_DBS / f"{slugificar(db_dados['meta'].get('id') or db_dados['meta']['nome'])}.json"
        caminho.write_text(json.dumps(db_dados, ensure_ascii=False, indent=1), encoding="utf-8")
        return True, str(caminho)
    except Exception as e:
        return False, str(e)
