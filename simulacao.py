# -*- coding: utf-8 -*-
"""
Motor de jogo do Cockpit Manager (edição Streamlit).

Filosofia do original (Cartola Games, 2014): simulação simples e viciante.
- Importância do carro = 60% (padrão das DBs da comunidade)
- Motor pesa muito dentro do desempenho do carro
- Você contrata pilotos/motores/patrocinadores para a PRÓXIMA temporada
- Sem dinheiro para motor? Motor FIA compulsório com 50% de potência

Melhorias em relação às limitações apontadas pela comunidade:
- Auge do piloto agora é um PLATÔ (auge_inicio -> auge_fim), com declínio gradual
- Velocidade (1 volta) separada de Concentração (não bater) permite o perfil
  "rápido mas destruidor de carros" sem quebrar o equilíbrio
"""

import copy
import random
from typing import cast

import dados2026 as db


# --------------------------------------------------------------------- utils
def _rng(game):
    """RNG determinística por contador (salvável em JSON)."""
    game["contador_rng"] += 1
    return random.Random(game["semente"] * 1000003 + game["contador_rng"] * 7919)


def fmt_dinheiro_k(valor_k):
    """Formata valor em US$ mil -> texto."""
    if abs(valor_k) >= 1000:
        return f"US$ {valor_k / 1000:,.1f} mi".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"US$ {valor_k:,.0f} mil".replace(",", ".")


def fmt_dinheiro_m(valor_m):
    return f"US$ {valor_m:,.1f} mi".replace(",", "X").replace(".", ",").replace("X", ".")


def equipe(game, equipe_id) -> dict:
    """Equipe pelo id. Os ids do jogo vêm validados pelas DBs (ausência = bug de
    dados), então os chamadores tratam o retorno como dict — verificado em runtime."""
    return cast(dict, next((e for e in game["equipes"] if e["id"] == equipe_id), None))


def piloto(game, piloto_id) -> dict:
    """Piloto pelo id (mesma premissa de equipe)."""
    return cast(dict, next((p for p in game["pilotos"] if p["id"] == piloto_id), None))


def motor(game, motor_id) -> dict:
    """Motor/fornecedor pelo id (mesma premissa de equipe)."""
    return cast(dict, next((m for m in game["motores"] if m["id"] == motor_id), None))


PAPEIS_TITULARES = ("P1", "P2", "P3", "P4")


def titulares(game, equipe_id=None):
    ps = [p for p in game["pilotos"] if p["papel"] in PAPEIS_TITULARES]
    if equipe_id:
        ps = [p for p in ps if p["equipe_id"] == equipe_id]
    return sorted(ps, key=lambda p: PAPEIS_TITULARES.index(p["papel"]))


def piloto_teste(game, equipe_id):
    return next((p for p in game["pilotos"] if p["equipe_id"] == equipe_id and p["papel"] == "teste"), None)


def noticia(game, texto):
    game["noticias"].insert(0, {"ano": game["ano"], "rodada": game["rodada"] + 1, "texto": texto})
    game["noticias"] = game["noticias"][:60]


def lancar_financa(game, descricao, valor_k):
    """Lança no caixa da equipe do jogador (valor em US$ mil) e registra no extrato."""
    eq = equipe(game, game["equipe_jogador"])
    eq["caixa"] += valor_k / 1000.0
    game["extrato"].insert(
        0,
        {
            "temporada": game["ano"],
            "etapa": game["rodada"] + 1,
            "descricao": descricao,
            "valor": round(valor_k, 1),
        },
    )
    game["extrato"] = game["extrato"][:200]
    # acumuladores do ano (painel Finanças do Escritório, como no original)
    fa = game.get("financas_ano") or {}
    if int(fa.get("ano", -1)) != int(game["ano"]):
        fa = {"ano": int(game["ano"]), "receitas": 0.0, "despesas": 0.0}
    if valor_k >= 0:
        fa["receitas"] = round(fa["receitas"] + float(valor_k), 1)
    else:
        fa["despesas"] = round(fa["despesas"] - float(valor_k), 1)
    game["financas_ano"] = fa


# --------------------------------------------------------------- novo jogo
def ajustar_grid(equipes, pilotos, qtd_pilotos):
    """Ajusta o nº de carros titulares: promove reservas/livres (3º/4º carros)
    ou rebaixa excedentes, mantendo ao menos 1 carro por equipe."""
    if not qtd_pilotos:
        return

    def tits(eq_id=None):
        return [x for x in pilotos if x["papel"] in PAPEIS_TITULARES and (eq_id is None or x["equipe_id"] == eq_id)]

    qtd_pilotos = max(len(equipes), min(int(qtd_pilotos), len(pilotos), len(equipes) * 4))
    while len(tits()) > qtd_pilotos:
        cands = [x for x in tits() if len(tits(x["equipe_id"])) > 1]
        if not cands:
            break
        cands.sort(key=lambda x: (-PAPEIS_TITULARES.index(x["papel"]), overall(x)))
        x = cands[0]
        if any(y["equipe_id"] == x["equipe_id"] and y["papel"] == "teste" for y in pilotos):
            x["equipe_id"], x["papel"] = None, "livre"
        else:
            x["papel"] = "teste"
    while len(tits()) < qtd_pilotos:
        pool = sorted(
            [x for x in pilotos if x["papel"] == "teste" and not x.get("aposentado")], key=lambda x: -overall(x)
        ) + sorted(
            [x for x in pilotos if x["papel"] == "livre" and not x.get("aposentado")],
            key=lambda x: -(overall(x) * 0.7 + x["potencial"] * 0.3),
        )
        if not pool:
            break
        eqs = sorted(equipes, key=lambda e: (len(tits(e["id"])), e["nivel_carro"]))
        eqs = [e for e in eqs if len(tits(e["id"])) < 4]
        if not eqs:
            break
        alvo, x = eqs[0], pool[0]
        x["equipe_id"] = alvo["id"]
        x["papel"] = f"P{len(tits(alvo['id'])) + 1}"


def _db_legado_f1():
    return {
        "meta": {
            "id": "f1_2026",
            "nome": "F1 2026",
            "categoria": "Fórmula 1",
            "ano": 2026,
            "rotulo_fornecedor": "Motor",
            "rotulo_corrida2": "Sprint",
            "pontos_corrida": list(db.PONTOS_CORRIDA),
            "pontos_corrida2": list(db.PONTOS_SPRINT),
            "importancia_carro_sugerida": 0.60,
            "fator_pontos_bonus": 1.0,
            "pontua_abandono": False,
        },
        "equipes": db.EQUIPES,
        "pilotos": db.PILOTOS,
        "motores": db.MOTORES,
        "calendario": db.CALENDARIO_2026,
        "hall_da_fama": db.HALL_DA_FAMA_INICIAL,
        "patrocinadores": db.PATROCINADORES,
    }


def criar_novo_jogo(
    equipe_jogador_id,
    semente=2026,
    incluir_canceladas=True,
    importancia_carro=0.60,
    equipe_custom=None,
    pilotos_custom=None,
    db_dados=None,
    qtd_pilotos=None,
):
    if db_dados is None:
        db_dados = _db_legado_f1()
    db_dados = copy.deepcopy(db_dados)
    equipes = db_dados["equipes"]
    pilotos = db_dados["pilotos"]

    if equipe_custom:  # modo "crie sua equipe" (12ª equipe do grid)
        equipes.append(equipe_custom)
        equipe_jogador_id = equipe_custom["id"]
        for pid, papel, salario in pilotos_custom or []:
            p = next(x for x in pilotos if x["id"] == pid)
            p["equipe_id"] = equipe_jogador_id
            p["papel"] = papel
            p["salario_corrida"] = salario
            p["contrato_anos"] = 2

    ajustar_grid(equipes, pilotos, qtd_pilotos)
    calendario_base = [dict(e) for e in db_dados["calendario"]]
    calendario = [dict(e) for e in calendario_base if incluir_canceladas or not e.get("cancelavel")]

    for e in equipes:
        e.update(
            {
                "pontos": 0,
                "vitorias": 0,
                "podios": 0,
                "poles": 0,
                "vitorias_carreira": 0,
                "usou_motor_fia": e["motor_id"] == "fia",
                "foco": "equilibrado",
            }
        )
    for p in pilotos:
        p.update(
            {
                "pontos": 0,
                "vitorias": 0,
                "podios": 0,
                "poles": 0,
                "corridas": 0,
                "abandonos": 0,
                "titulos": 0,
                "forma": 50,
                "aposentado": False,
                "equipes_historico": [p["equipe_id"]] if p["equipe_id"] else [],
            }
        )

    meta = db_dados.get("meta") or {}
    vagas = {
        e["id"]: [
            x["papel"]
            for x in sorted(
                [y for y in pilotos if y["equipe_id"] == e["id"] and y["papel"] in PAPEIS_TITULARES],
                key=lambda y: PAPEIS_TITULARES.index(y["papel"]),
            )
        ]
        or ["P1", "P2"]
        for e in equipes
    }
    game = {
        "versao": 2,
        "ano": int(meta.get("ano", 2026)),
        "rodada": 0,
        "semente": int(semente),
        "contador_rng": 0,
        "meta": meta,
        "db_id": meta.get("id", "f1_2026"),
        "vagas_por_equipe": vagas,
        "patrocinadores": db_dados.get("patrocinadores") or copy.deepcopy(db.PATROCINADORES),
        "calendario_base": calendario_base,
        "equipe_jogador": equipe_jogador_id,
        "importancia_carro": float(importancia_carro),
        "incluir_canceladas": incluir_canceladas,
        "equipes": equipes,
        "pilotos": pilotos,
        "motores": db_dados["motores"],
        "calendario": calendario,
        "resultados": [],  # um dict por etapa concluída
        "historico_pontos": [],  # snapshots p/ gráfico de evolução
        "historico_caixa": [],
        "historico_temporadas": [],
        "noticias": [],
        "extrato": [],
        "contratos_proxima": {},  # piloto_id -> {papel, salario, anos}
        "motor_proxima": None,
        "patrocinador_proxima": None,
        "hall_da_fama": db_dados.get("hall_da_fama") or [],
        "regen_nomes": db_dados.get("regen_nomes"),
        "conquistas": [],
        "temporadas_completas": 0,
        "regen_usados": 0,
    }
    eq = equipe(game, equipe_jogador_id)
    n_grid = len(titulares(game))
    noticia(
        game,
        f"🏁 Você assumiu o comando da **{eq['nome_completo']}** para a temporada {game['ano']} "
        f"da **{meta.get('categoria', meta.get('nome', 'categoria'))}** — grid com {n_grid} pilotos. "
        f"O paddock observa cada movimento...",
    )
    if eq["motor_id"] == "fia":
        noticia(
            game, "⚠️ Sem verba para um fornecedor decente, a organização emprestou o compulsório (50% de desempenho)."
        )
    return game


# ------------------------------------------------------------ desempenho
def overall(p):
    a = p["atributos"]
    return round(
        0.30 * a["velocidade"]
        + 0.15 * a["concentracao"]
        + 0.13 * a["chuva"]
        + 0.12 * a["ultrapassagem"]
        + 0.12 * a["acerto"]
        + 0.09 * a["largada"]
        + 0.09 * a["fisico"],
        1,
    )


def desempenho_carro(game, eq, etapa=None):
    """Chassi + motor. O peso do motor cresce em pistas de potência (Monza etc.)."""
    mot = motor(game, eq["motor_id"])
    peso_motor = 0.35 if etapa is None else 0.15 + 0.45 * etapa["potencia"]
    return (1 - peso_motor) * eq["nivel_carro"] + peso_motor * mot["potencia"]


def _perf_piloto_qualy(p, molhado):
    a = p["atributos"]
    velocidade = a["chuva"] * 0.65 + a["velocidade"] * 0.35 if molhado else a["velocidade"]
    return velocidade * 0.55 + a["acerto"] * 0.20 + a["concentracao"] * 0.15 + a["fisico"] * 0.10


def _perf_piloto_corrida(p, molhado, etapa):
    a = p["atributos"]
    velocidade = a["chuva"] * 0.60 + a["velocidade"] * 0.40 if molhado else a["velocidade"]
    peso_ultrap = 0.08 + 0.14 * etapa["ultrap"]
    return (
        velocidade * 0.36
        + a["concentracao"] * 0.18
        + a["ultrapassagem"] * peso_ultrap
        + a["acerto"] * 0.12
        + a["fisico"] * 0.10
        + a["largada"] * 0.07
    )


def sortear_clima(game, etapa):
    rng = _rng(game)
    return rng.random() < etapa["chuva"]  # True = molhado


# ------------------------------------------------------- clima ao vivo
def plano_clima(game, etapa, molhado):
    """Previsão do fim de semana: condição de largada + eventual virada no meio
    da prova. Determinística por etapa (semente própria — não consome o
    contador do save) e usada só pela tela: não altera o resultado do motor."""
    rng = random.Random(
        int(game.get("semente", 0)) * 7919 + int(game.get("ano", 0)) * 131 + int(game.get("rodada", 0)) * 17
    )
    plano = {"inicio": "molhado" if molhado else "seco", "virada_volta": None, "virada_para": None}
    chance = 0.38 if molhado else 0.26
    chance *= 0.55 + float(etapa.get("chuva", 0.2))
    if rng.random() < chance:
        voltas = max(8, int(etapa["voltas"]))
        plano["virada_volta"] = max(3, int(voltas * rng.uniform(0.22, 0.82)))
        plano["virada_para"] = "seco" if molhado else "molhado"
    return plano


def condicao_pista(plano, lap):
    """Condição da pista ("seco"/"molhado") na volta `lap`, dado o plano."""
    if not plano:
        return "seco"
    v = plano.get("virada_volta")
    if v and int(lap) >= int(v):
        return plano.get("virada_para") or plano.get("inicio", "seco")
    return plano.get("inicio", "seco")


def clima_fracao(plano, voltas):
    """Quanto da prova é molhada, dado o plano de clima. Devolve
    (fração molhada, volta da virada ou None)."""
    voltas = max(1, int(voltas))
    if not plano:
        return 0.0, None
    inicio_molhado = plano.get("inicio") == "molhado"
    virada = plano.get("virada_volta")
    if not virada:
        return (1.0 if inicio_molhado else 0.0), None
    v = max(1, min(int(virada), voltas))
    fim_molhado = plano.get("virada_para") == "molhado"
    molhadas = (v - 1) * (1.0 if inicio_molhado else 0.0) + (voltas - v + 1) * (1.0 if fim_molhado else 0.0)
    return max(0.0, min(1.0, molhadas / voltas)), v


def ajuste_clima(plano, etapa, est, p):
    """Efeito do clima REAL da prova no resultado: talento de chuva pesa
    conforme a fração molhada, o composto de largada certo para a condição
    inicial vale posição e apostar em poucas paradas numa prova que vira
    cobra caro. `plano` é o mesmo da tela (`plano_clima`)."""
    if not plano:
        return 0.0
    voltas = int(etapa.get("voltas", 50))
    frac_molhada, virada = clima_fracao(plano, voltas)
    inicio_molhado = plano.get("inicio") == "molhado"
    pneu = (est or {}).get("pneu", "Médio")

    b = 0.0
    # 1) quem anda bem na chuva ganha quando o asfalto está molhado
    b += (float(p["atributos"].get("chuva", 75)) - 72.0) * 0.075 * frac_molhada
    # 2) composto de largada x condição inicial (constante para quem acerta,
    #    só o erro pesa de verdade)
    if (pneu in PNEUS_MOLHADO) != inicio_molhado:
        b -= 1.6 if frac_molhada in (0.0, 1.0) else 1.0
    else:
        b += 0.9
    # 3) prova que vira no meio: quem planejou menos paradas paga o pit extra
    if virada is not None:
        paradas = int((est or {}).get("paradas", 1) or 0)
        b -= 0.85 * max(0, 2 - paradas)
        # quem já vinha no composto certo para o final da prova leva vantagem
        final_molhado = plano.get("virada_para") == "molhado"
        b += 0.55 if (pneu in PNEUS_MOLHADO) == final_molhado else -0.55
    return b


def previsao_texto(plano):
    """Frase de previsão do tempo para o paddock/estratégia."""
    if not plano:
        return "☀️ Sem previsão de mudança para a corrida."
    inicio = plano.get("inicio", "seco")
    v, destino = plano.get("virada_volta"), plano.get("virada_para")
    largada = "🌧️ Largada com pista molhada" if inicio == "molhado" else "☀️ Largada com pista seca"
    if not v:
        return f"{largada} e sem previsão de mudança."
    if destino == "molhado":
        return f"{largada}, mas a **chuva chega por volta de {v}** — prepare o pneu de chuva."
    return f"{largada}, mas a **pista deve secar por volta de {v}** — cuidado ao apostar no pneu errado."


def simular_classificacao(game, etapa, molhado):
    rng = _rng(game)
    imp = game["importancia_carro"]
    linhas = []
    for p in titulares(game):
        eq = equipe(game, p["equipe_id"])
        base = imp * desempenho_carro(game, eq, etapa) + (1 - imp) * _perf_piloto_qualy(p, molhado)
        # compressão: na F1 real o grid inteiro cabe em ~2s; sem isso o resultado fica carimbado
        score = base * 0.72 + 22 + (p["forma"] - 50) * 0.03 + rng.gauss(0, 1.7)
        linhas.append({"piloto_id": p["id"], "equipe_id": eq["id"], "score": score})
    linhas.sort(key=lambda x: -x["score"])
    melhor = linhas[0]["score"]
    tempo_base = 65 + etapa["voltas"] * 0.35
    for i, l in enumerate(linhas):
        l["pos"] = i + 1
        l["gap"] = round((melhor - l["score"]) * 0.14, 3)
        l["tempo"] = tempo_base + l["gap"]
    return linhas


# -------------------------------------------------------------- estratégias
PNEUS_SECO = ["Macio", "Médio", "Duro"]
PNEUS_MOLHADO = ["Intermediário", "Chuva extrema"]
RITMOS = ["Conservar", "Normal", "Atacar"]
# efeito do ritmo NA TELA (corrida ao vivo) — nunca altera o resultado do motor
RITMO_TEMPO = {"Conservar": 0.55, "Normal": 0.0, "Atacar": -0.45}  # s por volta
RITMO_POSICAO = {"Conservar": 0.30, "Normal": 0.0, "Atacar": -0.35}  # posições (some na chegada)
RITMO_DESGASTE = {"Conservar": 0.8, "Normal": 1.0, "Atacar": 1.3}  # x a vida do pneu


def paradas_ideais(etapa):
    if etapa["desgaste"] <= 1.5:
        return 1
    if etapa["desgaste"] <= 2.3:
        return 1 if etapa["ultrap"] < 0.4 else 2
    return 2


# ------------------------------------------------- tela de treino (sessão)
def sessao_treino(game, etapa, molhado, grid):
    """Sessão de treino progressiva para a tela: cada piloto tem seus
    momentos de 'melhor tempo' no fim de semana e, ao fim dos 60 minutos,
    a tabela converge EXATAMENTE ao grid real do motor (`grid`)."""
    rng = _rng(game)
    pilotos = {}
    for g in grid:
        t0 = rng.randint(4, 30)  # primeira volta lançada
        t1 = rng.randint(34, 54) if rng.random() < 0.8 else None
        pilotos[g["piloto_id"]] = {
            "final": g["tempo"],
            "t0": t0,
            "t1": t1,
            "d0": round(rng.uniform(1.2, 4.5), 3),
            "d1": round(rng.uniform(0.12, 0.85), 3),
        }
    return {"duracao": 60, "t0": None, "grid": grid, "pilotos": pilotos}


def melhor_tempo_treino(sessao, pid, minuto):
    """Melhor tempo do piloto no minuto X da sessão (None = ainda sem volta)."""
    m = sessao["pilotos"].get(pid)
    if m is None or minuto < m["t0"]:
        return None
    if minuto >= sessao["duracao"]:
        return m["final"]
    if m["t1"] is not None and minuto >= m["t1"]:
        return round(m["final"] + m["d1"], 3)
    return round(m["final"] + m["d0"], 3)


# ------------------------------------------------- replay da corrida (tela)
PNEUS_DURACAO = {"Macio": 16.0, "Médio": 24.0, "Duro": 33.0, "Intermediário": 22.0, "Chuva extrema": 26.0}


def _sequencia_pneus(inicial, paradas, molhado):
    if molhado:
        p = inicial if inicial in PNEUS_MOLHADO else "Intermediário"
        return [inicial] + [p] * paradas
    rota = ["Médio", "Macio", "Duro"]
    i = rota.index(inicial) if inicial in rota else 0
    return [inicial] + [rota[(i + k) % 3] for k in range(1, paradas + 1)]


def _pits_planejadas(etapa, paradas, rng):
    """Voltas das paradas planejadas: exatas, únicas, dentro da prova e
    espalhadas por piloto (janela de ±voltas//6) para não encher um box só."""
    voltas = etapa["voltas"]
    k = max(0, min(int(paradas or 0), max(0, (voltas - 6) // 6)))
    desloc = rng.randint(-max(2, voltas // 6), max(2, voltas // 6))
    usadas, laps = set(), []
    for i in range(k):
        base = round(voltas * (i + 1) / (k + 1)) + desloc
        jitter = rng.randint(-2, 2)
        x = int(max(2, min(voltas - 1, base + jitter)))
        while x in usadas and x < voltas - 1:
            x += 1
        while x in usadas and x > 2:
            x -= 1
        usadas.add(x)
        laps.append(x)
    return sorted(laps)


def montar_replay(game, etapa, grid, resultado, molhado, eventos=None, sprint=False):
    """Replay volta a volta derivado do resultado REAL do motor (mesmo RNG
    determinístico do save): posições interpolam largada→chegada com ruído
    que desaparece na linha de chegada, paradas planejadas, quebras na
    volta certa e tempos de volta plausíveis. Nada aqui muda o resultado."""
    rng = _rng(game)
    voltas = etapa["voltas"]
    grides = {g["piloto_id"]: g["pos"] for g in grid}
    media = 58.0 + voltas * 0.48
    info = {}
    for l in resultado:
        pid = l["piloto_id"]
        est = l["estrategia"]
        pits = _pits_planejadas(etapa, int(est.get("paradas", 1) or 0), rng)
        info[pid] = {
            "equipe_id": str(l["equipe_id"]),
            "grid": int(grides.get(pid, l.get("grid", l["pos"]))),
            "final_pos": int(l["pos"]),
            "dnf": bool(l["dnf"]),
            "volta_dnf": int(l["volta_dnf"]),
            "motivo": str(l.get("motivo", "")),
            "gap_final": float(l.get("gap_seg") or 0.0),
            "pneus": _sequencia_pneus(est.get("pneu", "Médio"), len(pits), molhado),
            "paradas": len(pits),
            "pits_plano": pits,
            "ruido": [rng.gauss(0, 1.0) for _ in range(voltas + 2)],
            "tempos": [
                round(media + rng.uniform(-0.6, 0.6) - i * 0.04 - (int(l["pos"]) - 1) * 0.05, 3)
                for i in range(voltas + 2)
            ],
        }
    texto_ev = " ".join(eventos or [])
    return {"voltas": voltas, "info": info, "sc_lap": int(voltas * 0.55) if "Safety Car" in texto_ev else None}


def linhas_replay(rep, lap, pits_feitas, pneus_manual=None, ritmos=None, overcut=None):
    """Estado do replay na volta `lap` (1-based). `pits_feitas` = {pid: [voltas]}
    das paradas já executadas (manuais via 'Pit stop!' ou automáticas);
    `pneus_manual` = {pid: {nº da parada: pneu}} escolhidos na tela e
    `ritmos` = {pid: ritmo} ajustado ao vivo — ambos só mudam a exibição,
    o resultado final continua sendo o do motor."""
    lap = max(1, min(int(lap), rep["voltas"]))
    w = lap / rep["voltas"]
    fase = 4.0 * w * (1.0 - w)  # efeito do ritmo cresce no meio e zera na chegada
    campos, fora = [], []
    for pid, d in rep["info"].items():
        executadas = [x for x in sorted(pits_feitas.get(pid) or []) if x <= lap]
        n_pit = len(executadas)
        box_hoje = lap in executadas
        ritmo = (ritmos or {}).get(pid, "Normal")
        s = (
            w * d["final_pos"]
            + (1 - w) * d["grid"]
            + d["ruido"][lap] * (1 - w) ** 0.75
            + (3.4 if box_hoje else 0.0)
            + RITMO_POSICAO.get(ritmo, 0.0) * fase
        )
        s += _offset_overcut(overcut, pid, lap)
        pneu = d["pneus"][min(n_pit, len(d["pneus"]) - 1)]
        if pneus_manual:
            pneu = pneus_manual.get(pid, {}).get(n_pit, pneu)
        linha = {
            "pid": pid,
            "s": s,
            "box": box_hoje,
            "equipe_id": d["equipe_id"],
            "pneu": pneu,
            "pits": n_pit,
            "paradas": d["paradas"],
        }
        if d["dnf"] and lap >= d["volta_dnf"]:
            linha["fora"] = d["motivo"]
            fora.append(linha)
        else:
            campos.append(linha)
    campos.sort(key=lambda x: x["s"])
    lider_s = campos[0]["s"] if campos else 0.0
    saida, dif_lider = [], None
    for i, ln in enumerate(campos):
        d = rep["info"][ln["pid"]]
        sint = max(0.0, (ln["s"] - lider_s) * 0.9)
        dif1 = sint * (1 - w) + d["gap_final"] * w
        dif_ant = None if dif_lider is None else max(0.0, dif1 - dif_lider)
        ritmo = (ritmos or {}).get(ln["pid"], "Normal")
        tempo = d["tempos"][lap] + RITMO_TEMPO.get(ritmo, 0.0) + (21.5 if ln["box"] else 0.0)
        saida.append(
            {
                **ln,
                "pos": i + 1,
                "dif1": round(dif1, 1),
                "dif_ant": None if dif_ant is None else round(dif_ant, 1),
                "tempo": round(tempo, 3),
            }
        )
        dif_lider = dif1
    fora.sort(key=lambda x: rep["info"][x["pid"]]["final_pos"])
    for ln in fora:
        saida.append({**ln, "pos": len(saida) + 1, "dif1": None, "dif_ant": None, "tempo": None})
    return saida


def auto_pits(rep, lap, pits_feitas, pit_auto=None, recusadas=None):
    """Executa automaticamente as paradas planejadas cuja volta já passou
    (datadas na volta planejada — renders pulados não perdem paradas).
    `pit_auto` = {pid: bool} do Paddock: False = parada perguntada ao chefe
    (não executa sozinho); `recusadas` = {pid: [voltas]} de paradas que o
    chefe já mandou o piloto ficar na pista (nunca são executadas)."""
    for pid, d in rep["info"].items():
        if d.get("dnf"):
            continue
        if pit_auto is not None and not pit_auto.get(pid, False):
            continue
        rec = set((recusadas or {}).get(pid) or [])
        feitas = pits_feitas.get(pid)
        novos = [x for x in d["pits_plano"] if x not in rec and (x not in (feitas or [])) and lap >= x]
        if not novos:
            continue
        feitas = pits_feitas.setdefault(pid, [])
        feitas.extend(novos)
        feitas.sort()


def pits_pendentes(rep, lap, pits_feitas, recusadas=None, perguntar=None, apenas=None):
    """Paradas planejadas que venceram e ainda não foram resolvidas — cada uma
    vira a janela de Pit Stop (trocar o pneu? qual ritmo?). `perguntar` =
    {pid: bool} do Paddock: True (padrão) = consulta o chefe antes de parar;
    `apenas` = ids dos pilotos do jogador (só eles recebem a janela).
    Devolve [(pid, volta_planejada)] em ordem de volta."""
    pend = []
    for pid, d in rep["info"].items():
        if d["dnf"] or (apenas is not None and pid not in apenas):
            continue
        if perguntar is not None and not perguntar.get(pid, True):
            continue
        resolvidas = set(pits_feitas.get(pid) or []) | set((recusadas or {}).get(pid) or [])
        for x in d["pits_plano"]:
            if lap >= x and x not in resolvidas:
                pend.append((pid, x))
                break
    pend.sort(key=lambda t: t[1])
    return pend


def undercut_nesta_volta(lap, pits_feitas, meus_ids, posicoes, janela=3):
    """Rivais que estavam até `janela` posições atrás de um piloto do jogador e
    foram ao box nesta volta — o clássico undercut. `posicoes` = {pid: pos}
    ANTES dos boxes desta volta. Devolve [(meu_pid, rival_pid, pos_rival, pos_minha)]."""
    alertas = []
    for rival, voltas in (pits_feitas or {}).items():
        if rival in meus_ids or lap not in (voltas or []):
            continue
        pr = (posicoes or {}).get(rival)
        if pr is None:
            continue
        for pid in meus_ids:
            pm = posicoes.get(pid)
            if pm is None:
                continue
            if 0 < pr - pm <= janela:
                alertas.append((pid, rival, pr, pm))
    return alertas


def overcut_disponivel(lap, pits_feitas, meus_ids, posicoes, janela=3):
    """Rivais que estavam À FRENTE de um piloto do jogador e foram ao box nesta
    volta: ficar na pista e atacar (overcut) pode devolver a posição na saída
    deles. `posicoes` = {pid: pos} ANTES dos boxes desta volta.
    Devolve [(meu_pid, rival_pid, pos_rival, pos_minha)]."""
    alertas = []
    for rival, voltas in (pits_feitas or {}).items():
        if rival in meus_ids or lap not in (voltas or []):
            continue
        pr = (posicoes or {}).get(rival)
        if pr is None:
            continue
        for pid in meus_ids:
            pm = (posicoes or {}).get(pid)
            if pm is None:
                continue
            if 0 < pm - pr <= janela:
                alertas.append((pid, rival, pr, pm))
    return alertas


def _offset_overcut(overcut, pid, lap):
    """Ganho de posição (em "s", negativo = melhor) enquanto a janela de
    overcut está aberta. Some por completo ao fim da janela, então não mexe
    no resultado final do motor."""
    d = (overcut or {}).get(pid)
    if not d:
        return 0.0
    inicio = int(d.get("volta", 0))
    dur = max(1, int(d.get("laps", 3)))
    if lap < inicio or lap > inicio + dur:
        return 0.0
    return -0.85 * (1.0 - (lap - inicio) / (dur + 1.0))


def vida_pneu(etapa, pneu, laps_no_pneu, ritmo=None):
    """Fração de vida restante do composto (0..1) para a barra da tela.
    `ritmo` projeta o desgaste: Atacar consome mais, Conservar menos."""
    base = PNEUS_DURACAO.get(pneu, 24.0)
    fator = max(0.5, min(1.35, 1.55 - float(etapa.get("desgaste", 2.0)) * 0.32))
    dur = max(3.0, base * fator) / RITMO_DESGASTE.get(ritmo or "Normal", 1.0)
    return max(0.0, min(1.0, 1.0 - laps_no_pneu / dur))


def estrategia_ia(game, p, etapa, molhado, rng):
    if molhado:
        return {"pneu": "Intermediário" if rng.random() < 0.8 else "Chuva extrema", "paradas": 1, "ritmo": "Normal"}
    ideais = paradas_ideais(etapa)
    paradas = ideais if rng.random() < 0.78 else max(1, ideais + rng.choice([-1, 1]))
    pneu = rng.choices(["Macio", "Médio", "Duro"], weights=[35, 45, 20])[0]
    conc = p["atributos"]["concentracao"]
    ritmo = rng.choices(RITMOS, weights=[15, 55, 30 if conc > 82 else 15])[0]
    return {"pneu": pneu, "paradas": paradas, "ritmo": ritmo}


def _bonus_estrategia(est, etapa, molhado, p):
    """Bônus/penalidade (em pontos de score) da estratégia escolhida."""
    if molhado:
        if est["pneu"] in PNEUS_SECO:
            return -14.0
        b = 0.8 if est["pneu"] == "Intermediário" else -0.6
    else:
        if est["pneu"] in PNEUS_MOLHADO:
            return -12.0
        ideais = paradas_ideais(etapa)
        b = -abs(est["paradas"] - ideais) * 1.5
        if est["pneu"] == "Macio":
            b += 0.9 - max(0.0, (etapa["desgaste"] - 1.6)) * (1.4 if est["paradas"] == 1 else 0.4)
        elif est["pneu"] == "Duro":
            b += -0.5 + (0.9 if etapa["desgaste"] > 2.2 and est["paradas"] == 1 else 0.0)
        else:
            b += 0.3
    if est["ritmo"] == "Atacar":
        b += 0.75
    elif est["ritmo"] == "Conservar":
        b += -0.55 + (0.5 if p["atributos"]["fisico"] < 87 else 0.0)
    return b


def _prob_abandono(eq, p, est, molhado):
    mot_conf = 0.0  # confiabilidade do motor entra via equipe (já embutida no criar via update abaixo)
    prob = (100 - eq["confiabilidade"]) / 450.0 + (100 - p["atributos"]["concentracao"]) / 380.0
    if est["ritmo"] == "Atacar":
        prob += 0.025
    elif est["ritmo"] == "Conservar":
        prob -= 0.012
    if molhado:
        prob += 0.018
    if est["pneu"] in PNEUS_SECO and molhado:
        prob += 0.10
    return max(0.02, min(0.30, prob + mot_conf))


MOTIVOS_DNF = ["Motor", "Câmbio", "Batida", "Rodada", "Hidráulica", "Freios", "Suspensão", "Elétrica"]


def simular_corrida(game, etapa, grid, estrategias_jogador, molhado, sprint=False, clima=None):
    rng = _rng(game)
    imp = game["importancia_carro"]
    pos_grid = {g["piloto_id"]: g["pos"] for g in grid}
    peso_grid = (1 - etapa["ultrap"]) * (0.55 if not sprint else 0.7)
    eventos, linhas = [], []

    for p in titulares(game):
        eq = equipe(game, p["equipe_id"])
        if p["equipe_id"] == game["equipe_jogador"] and p["id"] in (estrategias_jogador or {}):
            est = estrategias_jogador[p["id"]]
        else:
            est = estrategia_ia(game, p, etapa, molhado, rng)
        base = imp * desempenho_carro(game, eq, etapa) + (1 - imp) * _perf_piloto_corrida(p, molhado, etapa)
        score = (
            base * 0.55
            + 36
            + _bonus_estrategia(est, etapa, molhado, p)
            + (p["forma"] - 50) * 0.035
            + rng.gauss(0, 2.4 if not sprint else 1.7)
        )
        # largada: ganha/perde terreno já na primeira volta
        score += (p["atributos"]["largada"] - 85) * 0.035
        # em pistas travadas (Mônaco, Singapura) quem larga na frente fica na frente
        score += (len(grid) - pos_grid[p["id"]]) * 0.16 * peso_grid
        # clima real do fim de semana (previsão que se confirma ou trai)
        score += ajuste_clima(clima, etapa, est, p)
        dnf = rng.random() < _prob_abandono(eq, p, est, molhado)
        linhas.append(
            {
                "piloto_id": p["id"],
                "equipe_id": eq["id"],
                "score": score,
                "grid": pos_grid[p["id"]],
                "estrategia": est,
                "dnf": dnf,
                "motivo": rng.choice(MOTIVOS_DNF) if dnf else "",
                "volta_dnf": rng.randint(1, etapa["voltas"] - 1) if dnf else etapa["voltas"],
            }
        )

    terminaram = sorted([l for l in linhas if not l["dnf"]], key=lambda x: -x["score"])
    abandonaram = sorted([l for l in linhas if l["dnf"]], key=lambda x: -x["volta_dnf"])
    ordem = terminaram + abandonaram

    safety_car = rng.random() < 0.28 and not sprint
    melhor = terminaram[0]["score"] if terminaram else 0
    _meta = game.get("meta") or {}
    tabela = (
        (_meta.get("pontos_corrida2") or db.PONTOS_SPRINT)
        if sprint
        else (_meta.get("pontos_corrida") or db.PONTOS_CORRIDA)
    )
    fator_gap = etapa["voltas"] * (0.16 if sprint else 0.55) * (0.55 if safety_car else 1.0)
    for i, l in enumerate(ordem):
        l["pos"] = i + 1
        l["pontos"] = tabela[i] if (i < len(tabela) and (not l["dnf"] or _meta.get("pontua_abandono"))) else 0
        l["gap_seg"] = None if l["dnf"] else round((melhor - l["score"]) * fator_gap, 1)
        l["status"] = f"Abandono ({l['motivo']}, volta {l['volta_dnf']})" if l["dnf"] else "Terminou"
        l.pop("score")

    if terminaram:
        cand = terminaram[:10]
        vr = max(cand, key=lambda l: piloto(game, l["piloto_id"])["atributos"]["velocidade"] + rng.gauss(0, 3))
        vr["volta_rapida"] = True
        eventos.append(f"⚡ Volta mais rápida: **{piloto(game, vr['piloto_id'])['nome']}**.")
    if safety_car:
        eventos.append("🟨 Safety Car no meio da prova agrupou todo o pelotão e embaralhou as estratégias!")
    if molhado:
        eventos.append("🌧️ Corrida com pista molhada — quem nasceu para a chuva brilhou (e quem errou o pneu, chorou).")
    if clima and clima.get("virada_volta"):
        virou_para_chuva = clima.get("virada_para") == "molhado"
        eventos.append(
            f"🌦️ {'A chuva chegou' if virou_para_chuva else 'A pista secou'} na volta "
            f"{clima['virada_volta']} — quem tinha o composto certo para a segunda metade "
            f"{'subiu no pelotão' if virou_para_chuva else 'ganhou a prova de estratégia'}."
        )
    for l in abandonaram[:4]:
        eventos.append(
            f"💥 {piloto(game, l['piloto_id'])['nome']} abandonou: {l['motivo'].lower()} na volta {l['volta_dnf']}."
        )
    if terminaram:
        v = piloto(game, terminaram[0]["piloto_id"])
        ganho = terminaram[0]["grid"] - 1
        if ganho >= 5:
            eventos.append(
                f"🚀 Recuperação espetacular de **{v['nome']}**: largou em {terminaram[0]['grid']}º e venceu!"
            )
    return ordem, eventos


# ----------------------------------------------------- aplicar resultado
def _patrocinador(nome, game=None):
    lista = (game or {}).get("patrocinadores") or db.PATROCINADORES
    return next((s for s in lista if s["nome"] == nome), lista[-1])


# ------------------------------------------------- eixos do carro (CM14)
EIXOS_CARRO = ("aerodinamica", "cambio", "freio", "eletrico", "direcao")


def eixos_carro(eq):
    """Eixos do painel Carro no estilo CM14 (aerodinâmica, câmbio, freio,
    sistema elétrico, direção): derivados do nível real do chassi + mix
    determinístico por equipe (média zero → a média dos eixos bate com o
    chassi) que responde ao foco de desenvolvimento. Confiabilidade é o
    campo real da equipe. Não altera cálculo de corrida."""
    mix = eq.get("eixos_mix")
    if not mix:
        base_txt = f"{eq.get('id', '')}{eq.get('nome', '')}"
        rnd = random.Random(sum(ord(c) for c in base_txt) * 31 + 7)
        cru = [rnd.uniform(-4.5, 4.5) for _ in EIXOS_CARRO]
        media = sum(cru) / len(cru)
        mix = {k: round(v - media, 3) for k, v in zip(EIXOS_CARRO, cru)}
        eq["eixos_mix"] = mix
    base = float(eq.get("nivel_carro", 80))
    saida = {k: int(round(max(35.0, min(99.0, base + float(mix.get(k, 0.0)))))) for k in EIXOS_CARRO}
    saida["confiabilidade"] = int(round(float(eq.get("confiabilidade", 85))))
    return saida


def evoluir_eixos(eq):
    """Desloca o mix dos eixos conforme o foco de desenvolvimento,
    preservando a média (o nível do chassi é quem manda na corrida)."""
    eixos_carro(eq)  # garante o mix
    mix = eq["eixos_mix"]
    foco = eq.get("foco") or "equilibrado"
    if foco == "chassi":
        mix["aerodinamica"] = round(mix.get("aerodinamica", 0.0) + 0.55, 3)
        mix["direcao"] = round(mix.get("direcao", 0.0) + 0.30, 3)
        for k in ("cambio", "freio", "eletrico"):
            mix[k] = round(mix.get(k, 0.0) - 0.283, 3)
    elif foco == "equilibrado":
        for k in EIXOS_CARRO:
            mix[k] = round(mix.get(k, 0.0) * 0.90, 3)
    # foco == 'confiabilidade': mix intocado (o eixo real é eq['confiabilidade'])
    media = sum(mix.get(k, 0.0) for k in EIXOS_CARRO) / len(EIXOS_CARRO)
    for k in EIXOS_CARRO:
        mix[k] = round(mix.get(k, 0.0) - media, 3)


def desenvolver_carros(game, etapa):
    """Desenvolvimento entre corridas: investimento + feedback (Acerto) dos pilotos."""
    rng = _rng(game)
    for eq in game["equipes"]:
        if eq["id"] != game["equipe_jogador"]:
            # IA: investe conforme caixa/prestígio, com ruído
            eq["investimento_corrida"] = int(
                max(300, min(2200, eq["investimento_corrida"] * rng.uniform(0.85, 1.15) + (eq["caixa"] - 100) * 4))
            )
            eq["foco"] = rng.choices(["equilibrado", "chassi", "confiabilidade"], weights=[5, 3, 2])[0]
        titulares_eq = titulares(game, eq["id"])
        teste = piloto_teste(game, eq["id"])
        feedback = (sum(t["atributos"]["acerto"] for t in titulares_eq) / max(1, len(titulares_eq))) * 0.7
        feedback += (teste["atributos"]["acerto"] * 0.3) if teste else 21
        investimento = eq["investimento_corrida"]  # US$ mil
        ganho = (investimento / 1000.0) * 0.22 * (feedback / 85.0)
        teto = 99.5
        if eq["foco"] == "chassi":
            ganho *= 1.35
        elif eq["foco"] == "confiabilidade":
            ganho *= 0.55
        ganho *= max(0.12, (teto - eq["nivel_carro"]) / 35.0)  # retorno decrescente
        ganho += rng.gauss(0, 0.08)
        eq["nivel_carro"] = round(max(40.0, min(teto, eq["nivel_carro"] + ganho)), 2)
        if eq["foco"] == "confiabilidade":
            eq["confiabilidade"] = round(min(98.0, eq["confiabilidade"] + investimento / 1000.0 * 0.35), 2)
        # desgaste natural da confiabilidade
        eq["confiabilidade"] = round(max(70.0, eq["confiabilidade"] - rng.uniform(0, 0.25)), 2)
        evoluir_eixos(eq)
        if eq["id"] != game["equipe_jogador"]:
            receita = _patrocinador(eq["patrocinador"], game)["por_corrida"] / 1000.0 + eq["pontos"] * 0.004
            custos = investimento / 1000.0 + sum(t["salario_corrida"] for t in titulares_eq) / 1000.0
            eq["caixa"] = round(max(-30.0, eq["caixa"] + receita - custos), 2)


def aplicar_resultado(game, etapa, grid, resultado, molhado, sprint=False, eventos=None):
    """Atualiza pontos/estatísticas/finanças do jogador. Retorna resumo financeiro (US$ mil)."""
    resumo = []
    pole = grid[0] if grid else None
    if pole and not sprint:
        pp = piloto(game, pole["piloto_id"])
        pp["poles"] += 1
        equipe(game, pole["equipe_id"])["poles"] += 1

    for l in resultado:
        p, eq = piloto(game, l["piloto_id"]), equipe(game, l["equipe_id"])
        p["pontos"] += l["pontos"]
        eq["pontos"] += l["pontos"]
        if not sprint:
            p["corridas"] += 1
            if l["dnf"]:
                p["abandonos"] += 1
            if l["pos"] == 1 and not l["dnf"]:
                p["vitorias"] += 1
                eq["vitorias"] += 1
                eq["vitorias_carreira"] += 1
            if l["pos"] <= 3 and not l["dnf"]:
                p["podios"] += 1
                eq["podios"] += 1
        # forma: compara resultado com a expectativa (grid)
        delta = (l["grid"] - l["pos"]) * 3 + (10 if l["pos"] == 1 else 0) - (12 if l["dnf"] else 0)
        p["forma"] = int(max(5, min(98, p["forma"] * 0.72 + 50 * 0.28 + delta)))

    # ---------------- finanças do jogador (corrida principal cobra os custos)
    eqj = equipe(game, game["equipe_jogador"])
    if not sprint:
        spon = _patrocinador(eqj["patrocinador"], game)
        pts_eq = sum(l["pontos"] for l in resultado if l["equipe_id"] == eqj["id"])
        podios = sum(1 for l in resultado if l["equipe_id"] == eqj["id"] and l["pos"] <= 3 and not l["dnf"])
        vits = sum(1 for l in resultado if l["equipe_id"] == eqj["id"] and l["pos"] == 1 and not l["dnf"])
        pts_bonus = round(pts_eq * float((game.get("meta") or {}).get("fator_pontos_bonus", 1.0)))
        rec = (
            spon["por_corrida"]
            + pts_bonus * spon["bonus_ponto"]
            + podios * spon["bonus_podio"]
            + vits * spon["bonus_vitoria"]
        )
        lancar_financa(game, f"Patrocínio {spon['nome']} + bônus ({etapa['gp']})", rec)
        resumo.append(("Patrocínio e bônus", rec))
        salarios = sum(
            p["salario_corrida"] for p in game["pilotos"] if p["equipe_id"] == eqj["id"] and not p["aposentado"]
        )
        lancar_financa(game, "Salários dos pilotos", -salarios)
        resumo.append(("Salários", -salarios))
        inv = eqj["investimento_corrida"]
        lancar_financa(game, "Investimento no carro", -inv)
        resumo.append(("Investimento no carro", -inv))
        danos = sum(
            420 for l in resultado if l["equipe_id"] == eqj["id"] and l["dnf"] and l["motivo"] in ("Batida", "Rodada")
        )
        if danos:
            lancar_financa(game, "Reparos (batidas)", -danos)
            resumo.append(("Reparos de batida", -danos))

    registro = {
        "ano": game["ano"],
        "rodada": game["rodada"] + 1,
        "gp": etapa["gp"],
        "circuito": etapa["circuito"],
        "molhado": molhado,
        "sprint": sprint,
        "grid": grid,
        "resultado": resultado,
        "eventos": eventos or [],
    }
    game["resultados"].append(registro)

    vencedor = next((l for l in resultado if l["pos"] == 1 and not l["dnf"]), None)
    if vencedor:
        pv = piloto(game, vencedor["piloto_id"])
        rot2 = (game.get("meta") or {}).get("rotulo_corrida2") or "Sprint"
        if sprint:
            noticia(
                game,
                f"⚡ **{pv['nome']}** ({equipe(game, pv['equipe_id'])['nome']}) venceu a "
                f"{rot2} da etapa **{etapa['gp']}** ({etapa['circuito']}).",
            )
        else:
            noticia(
                game,
                f"🏆 **{pv['nome']}** ({equipe(game, pv['equipe_id'])['nome']}) venceu "
                f"**{etapa['gp']}** em {etapa['circuito']}.",
            )

    if not sprint:
        desenvolver_carros(game, etapa)
        snap = {p["id"]: p["pontos"] for p in titulares(game)}
        game["historico_pontos"].append({"rodada": game["rodada"] + 1, "gp": etapa["gp"], "pontos": snap})
        game["historico_caixa"].append({"rodada": game["rodada"] + 1, "caixa": round(eqj["caixa"], 1)})
        if eqj["caixa"] < 0:
            noticia(
                game,
                "🔴 **ALERTA FINANCEIRO:** o caixa está negativo! Sem dinheiro na virada da "
                "temporada, a organização pode impor o fornecedor compulsório de 50% de desempenho.",
            )
        verificar_conquistas(game, resultado, etapa)
        # a virada de etapa (rodada + 1) acontece no botão "Continuar" da tela de
        # corrida — assim o replay/resultados continuam na mesma etapa até o fim
    return resumo


# ---------------------------------------------------------------- tabelas
def tabela_pilotos(game):
    return sorted(titulares(game), key=lambda p: (-p["pontos"], -p["vitorias"], -p["podios"]))


def tabela_construtores(game):
    return sorted(game["equipes"], key=lambda e: (-e["pontos"], -e["vitorias"], -e["podios"]))


def posicao_equipe(game, equipe_id):
    return [e["id"] for e in tabela_construtores(game)].index(equipe_id) + 1


# --------------------------------------------------------------- contratos
def salario_esperado(game, p, papel):
    ov = overall(p)
    base = max(35, max(0.0, ov - 70) ** 2 * 2.2 + max(0.0, ov - 88) ** 2 * 10 + max(0.0, p["potencial"] - ov) * 15)
    if papel == "P2":
        base *= 0.72
    elif papel in ("P3", "P4"):
        base *= 0.60
    elif papel == "teste":
        base *= 0.22
    return int(round(base / 10.0) * 10)


def negociar_piloto(game, piloto_id, papel, salario, anos):
    """Negocia para a PRÓXIMA temporada (como no original). Retorna (bool, mensagem)."""
    rng = _rng(game)
    p = piloto(game, piloto_id)
    eqj = equipe(game, game["equipe_jogador"])
    esperado = salario_esperado(game, p, papel)
    prob = 0.38 + (salario - esperado) / max(100.0, esperado * 0.9)
    prob += (eqj["prestigio"] - 68) * 0.008
    prob += (desempenho_carro(game, eqj) - 80) * 0.012
    if p["papel"] == "livre":
        prob += 0.20  # qualquer vaga na F1 é um sonho para quem está sem equipe
    if p["equipe_id"] == eqj["id"]:
        prob += 0.18  # renovar em casa é mais fácil
    if papel == "teste" and p["papel"] in PAPEIS_TITULARES and overall(p) > 84:
        prob -= 0.35  # titular bom não aceita virar reserva fácil
    if papel == "P1":
        prob += 0.08
    prob += (anos - 2) * 0.04
    prob = max(0.03, min(0.96, prob))
    if rng.random() < prob:
        game["contratos_proxima"][piloto_id] = {"papel": papel, "salario": int(salario), "anos": int(anos)}
        noticia(
            game,
            f"✍️ **{p['nome']}** fechou com a {eqj['nome']} para {game['ano'] + 1} "
            f"({papel}, {fmt_dinheiro_k(salario)}/corrida, {anos} ano(s)).",
        )
        _rot = {"P1": "1º piloto", "P2": "2º piloto", "P3": "3º piloto", "P4": "4º piloto"}.get(
            papel, "piloto de testes"
        )
        return True, f"{p['nome']} aceitou! Contrato assinado para {game['ano'] + 1} como {_rot}."
    motivos = [
        f"{p['nome']} recusou: achou {fmt_dinheiro_k(salario)}/corrida pouco (esperava algo perto de {fmt_dinheiro_k(esperado)}).",
        f"{p['nome']} agradeceu, mas não se convenceu com o projeto da equipe neste momento.",
        f"O estafe de {p['nome']} encerrou a conversa: quer garantias esportivas (e salariais) maiores.",
    ]
    return False, rng.choice(motivos)


def taxa_sinal(salario):
    """Taxa de sinalização do pré-contrato: equivalente a 3 corridas do salário (mín. 300)."""
    return max(300, int(salario) * 3)


def pre_contratar_piloto(game, piloto_id, papel, salario, anos):
    """Pré-contrato como no original: com o sinal pago, o acordo fecha na hora (sem
    chance de recusa), vale para a próxima temporada e a taxa não é devolvida se o
    contrato for cancelado. Retorna (bool, mensagem)."""
    p = piloto(game, piloto_id)
    eqj = equipe(game, game["equipe_jogador"])
    if p["aposentado"]:
        return False, f"{p['nome']} se aposentou — não há pré-contrato a assinar."
    if piloto_id in game["contratos_proxima"]:
        return False, f"Já existe um acordo com {p['nome']} para {game['ano'] + 1}."
    taxa = taxa_sinal(salario)
    if eqj["caixa"] < taxa / 1000.0:
        return False, (
            f"Caixa insuficiente para o sinal de {fmt_dinheiro_k(taxa)} (você tem {fmt_dinheiro_m(eqj['caixa'])})."
        )
    lancar_financa(game, f"Sinal — pré-contrato de {p['nome']}", -taxa)
    game["contratos_proxima"][piloto_id] = {
        "papel": papel,
        "salario": int(salario),
        "anos": int(anos),
        "pre": True,
        "sinal": taxa,
    }
    _rot = {"P1": "1º piloto", "P2": "2º piloto", "P3": "3º piloto", "P4": "4º piloto"}.get(papel, "piloto de testes")
    noticia(
        game,
        f"📝 **{p['nome']}** assinou pré-contrato com a {eqj['nome']} para {game['ano'] + 1} "
        f"(sinal de {fmt_dinheiro_k(taxa)} pagos; {_rot}, {fmt_dinheiro_k(salario)}/corrida).",
    )
    return True, (
        f"Pré-contrato fechado com {p['nome']}! Sinal de {fmt_dinheiro_k(taxa)} pago — sem chance de "
        f"recusa, ele veste seu macacão em {game['ano'] + 1} como {_rot} ({fmt_dinheiro_k(salario)}/corrida). "
        f"A taxa não é devolvida se você cancelar."
    )


# -------------------------------------------------------------- conquistas
def _desbloquear(game, cid):
    if cid not in game["conquistas"]:
        game["conquistas"].append(cid)
        c = next(x for x in db.CONQUISTAS if x["id"] == cid)
        noticia(game, f"🎖️ **Conquista desbloqueada:** {c['icone']} {c['nome']} — {c['desc']}")


def verificar_conquistas(game, resultado=None, etapa=None):
    eqj = equipe(game, game["equipe_jogador"])
    if resultado:
        if any(l["equipe_id"] == eqj["id"] and l["pos"] == 1 and not l["dnf"] for l in resultado):
            _desbloquear(game, "primeira_vitoria")
            if etapa is not None and desempenho_carro(game, eqj, etapa) < 75:
                _desbloquear(game, "zebra")
    if eqj["caixa"] > 250:
        _desbloquear(game, "magnata")
    if eqj["vitorias_carreira"] >= 50:
        _desbloquear(game, "cinquenta_vitorias")
    if game["temporadas_completas"] >= 10:
        _desbloquear(game, "decada")


# ----------------------------------------------------------- fim de temporada
def _evoluir_piloto(game, p, rng):
    p["idade"] += 1
    a = p["atributos"]
    for chave in a:
        if p["idade"] < p["auge_inicio"]:
            alvo = min(99, a[chave] + (p["potencial"] - overall(p)) * 0.16 + rng.uniform(0, 1.4))
            a[chave] = (
                int(round(min(99, max(a[chave], alvo))))
                if chave != "fisico"
                else int(round(min(97, a[chave] + rng.uniform(0, 1.0))))
            )
        elif p["idade"] <= p["auge_fim"]:  # PLATÔ do auge
            a[chave] = int(round(max(40, min(99, a[chave] + rng.gauss(0, 0.55)))))
        else:  # declínio gradual pós-auge
            queda = rng.uniform(0.6, 1.9) * (1.25 if chave in ("velocidade", "fisico", "largada") else 0.8)
            a[chave] = int(round(max(35, a[chave] - queda)))
    if p["papel"] == "teste" and p["idade"] < p["auge_inicio"]:
        a["acerto"] = min(99, a["acerto"] + 1)  # reserva aprende no simulador


def _gerar_jovem(game, rng):
    pool = game.get("regen_nomes") or db.REGEN_NOMES  # DBs podem definir a própria base (ex.: F1 Academy)
    idx = game["regen_usados"] % len(pool)
    game["regen_usados"] += 1
    nome1, sobrenome, pais, bandeira = pool[idx]
    ger = game["regen_usados"] // len(pool)
    pid = f"regen{game['regen_usados']}"
    nome = f"{nome1} {sobrenome}" + (f" {ger}º" if ger else "")
    base = rng.randint(68, 80)
    p = {
        "id": pid,
        "nome": nome,
        "sigla": sobrenome[:3].upper(),
        "numero": 80 + game["regen_usados"] % 18,
        "pais": pais,
        "bandeira": bandeira,
        "idade": rng.randint(17, 20),
        "equipe_id": None,
        "papel": "livre",
        "salario_corrida": 30,
        "contrato_anos": 0,
        "auge_inicio": rng.randint(23, 26),
        "potencial": rng.randint(82, 96),
        "atributos": {k: max(55, min(88, base + rng.randint(-6, 6))) for k in db.ATRIBUTOS},
        "pontos": 0,
        "vitorias": 0,
        "podios": 0,
        "poles": 0,
        "corridas": 0,
        "abandonos": 0,
        "titulos": 0,
        "forma": 50,
        "aposentado": False,
        "equipes_historico": [],
    }
    p["auge_fim"] = p["auge_inicio"] + rng.randint(4, 8)
    game["pilotos"].append(p)
    return p


def virar_temporada(game):
    """Fecha a temporada: prêmios, títulos, mercado, evolução, carros novos."""
    rng = _rng(game)
    eqj = equipe(game, game["equipe_jogador"])
    tab_p, tab_c = tabela_pilotos(game), tabela_construtores(game)
    campeao = tab_p[0] if tab_p else None
    if campeao:
        campeao["titulos"] += 1
    campea_constr = tab_c[0] if tab_c else None
    if campea_constr:
        campea_constr["titulos_construtores"] = campea_constr.get("titulos_construtores", 0) + 1

    game["historico_temporadas"].append(
        {
            "ano": game["ano"],
            "campeao_pilotos": campeao["nome"] if campeao else "-",
            "equipe_campea": campea_constr["nome"] if campea_constr else "-",
            "sua_posicao": posicao_equipe(game, eqj["id"]),
            "seus_pontos": eqj["pontos"],
        }
    )
    game["temporadas_completas"] += 1

    if campeao and campeao["equipe_id"] == eqj["id"]:
        _desbloquear(game, "campeao_pilotos")
    if campea_constr and campea_constr["id"] == eqj["id"]:
        _desbloquear(game, "campeao_construtores")
    if campeao and campea_constr and campeao["equipe_id"] == eqj["id"] and campea_constr["id"] == eqj["id"]:
        _desbloquear(game, "dobradinha")
    if eqj.get("usou_motor_fia") and posicao_equipe(game, eqj["id"]) <= 3:
        _desbloquear(game, "sobrevivente")

    # premiação de construtores
    for i, e in enumerate(tab_c):
        premio = db.PREMIACAO_CONSTRUTORES[i] if i < len(db.PREMIACAO_CONSTRUTORES) else max(18, 42 - (i - 11) * 3)
        if e["id"] == eqj["id"]:
            lancar_financa(game, f"Premiação de Construtores ({i + 1}º lugar)", premio * 1000)
        else:
            e["caixa"] += premio * 0.55  # IA já gastou parte no caminho

    # ------------------------------ pilotos: evolução/aposentadoria/contratos
    for p in list(game["pilotos"]):
        if p["aposentado"]:
            continue
        _evoluir_piloto(game, p, rng)
        p["contrato_anos"] = max(0, p["contrato_anos"] - 1)
        chance_aposentar = 0.0
        if p["idade"] > p["auge_fim"]:  # só após o fim do platô (turismo corre até os 50!)
            chance_aposentar += 0.15 + (p["idade"] - p["auge_fim"]) * 0.06
            if p["idade"] >= 45:
                chance_aposentar += 0.20
            if p["idade"] >= 50:
                chance_aposentar += 0.25
        if rng.random() < chance_aposentar:
            p["aposentado"] = True
            p["papel"] = "aposentado"
            if p["equipe_id"]:
                noticia(
                    game,
                    f"👋 **{p['nome']}** anuncia aposentadoria aos {p['idade']} anos "
                    f"({p['titulos']} título(s), {p['vitorias']} vitória(s) neste save).",
                )
            p["equipe_id"] = None
            if p["titulos"] >= db.HOF_MIN_TITULOS or p["vitorias"] >= db.HOF_MIN_VITORIAS:
                game["hall_da_fama"].append(
                    {
                        "nome": p["nome"],
                        "pais": p["pais"],
                        "bandeira": p["bandeira"],
                        "titulos": p["titulos"],
                        "vitorias": p["vitorias"],
                        "anos": f"até {game['ano']}",
                        "induzido_no_save": True,
                    }
                )
                noticia(game, f"🌟 **{p['nome']}** foi induzido ao Hall da Fama!")
                if eqj["id"] in p.get("equipes_historico", []):
                    _desbloquear(game, "hall_da_fama")
        elif p["contrato_anos"] == 0 and p["papel"] != "livre":
            p["equipe_id"] = None
            p["papel"] = "livre"

    # contratos que o jogador fechou valem a partir de agora
    for pid, c in game["contratos_proxima"].items():
        p = piloto(game, pid)
        if p and not p["aposentado"]:
            p["equipe_id"], p["papel"] = eqj["id"], c["papel"]
            p["salario_corrida"], p["contrato_anos"] = c["salario"], c["anos"]
            if eqj["id"] not in p["equipes_historico"]:
                p["equipes_historico"].append(eqj["id"])
        elif c.get("pre"):
            noticia(
                game,
                f"📄 O pré-contrato com **{p['nome']}** caiu no vazio: ele se aposentou antes de assinar. "
                f"O sinal de {fmt_dinheiro_k(c.get('sinal', 0))} não foi devolvido.",
            )
    game["contratos_proxima"] = {}

    # mercado da IA: preencher vagas, promover reservas, caçar jovens
    livres = sorted(
        [p for p in game["pilotos"] if p["papel"] == "livre" and not p["aposentado"]],
        key=lambda p: -(overall(p) * 0.75 + p["potencial"] * 0.25),
    )
    # IA contrata por prestígio; a equipe do jogador fica por último (quem não
    # negociou durante o ano pega o que sobrou — às pressas, como no original)
    ordem_mercado = sorted([e for e in game["equipes"] if e["id"] != eqj["id"]], key=lambda x: -x["prestigio"]) + [eqj]
    # fase 0 = vagas titulares (promovendo reservas se preciso), fase 1 = testes
    for fase in (0, 1):
        for e in ordem_mercado:
            vagas_tit = list((game.get("vagas_por_equipe") or {}).get(e["id"], ["P1", "P2"]))
            vagas_eq = vagas_tit if fase == 0 else ["teste"]
            for papel in vagas_eq:
                ocupados = [p for p in game["pilotos"] if p["equipe_id"] == e["id"] and p["papel"] == papel]
                if not ocupados and fase == 0 and not livres:
                    reservas = sorted(
                        [p for p in game["pilotos"] if p["papel"] == "teste" and not p["aposentado"]],
                        key=lambda x: (x["equipe_id"] != e["id"], -overall(x)),
                    )
                    if reservas:
                        livres.append(reservas[0])
                    else:
                        livres.append(_gerar_jovem(game, rng))
                while not ocupados and livres:
                    janela = livres[:5] if e["prestigio"] > 70 else livres[:9]
                    p = rng.choice(janela)
                    livres.remove(p)
                    p["equipe_id"], p["papel"] = e["id"], papel
                    p["salario_corrida"] = salario_esperado(game, p, papel)
                    p["contrato_anos"] = rng.randint(1, 3)
                    if e["id"] not in p["equipes_historico"]:
                        p["equipes_historico"].append(e["id"])
                    ocupados = [p]
                    if papel != "teste":
                        noticia(
                            game,
                            f"📰 Mercado: **{p['nome']}** assume como {papel} da {e['nome']} em {game['ano'] + 1}.",
                        )
    n_jovens = max(3, len(game["equipes"]) // 3)
    for _ in range(n_jovens):
        _gerar_jovem(game, rng)
    noticia(game, f"🌱 {n_jovens} jovens das categorias de base entraram no mercado de pilotos.")

    # ------------------------------ motores e patrocinador do jogador
    if game["motor_proxima"] and not eqj.get("motor_proprio"):
        novo = motor(game, game["motor_proxima"])
        if eqj["caixa"] * 1000 >= novo["preco"] * 1000 or novo["id"] == "fia":
            eqj["motor_id"] = novo["id"]
            noticia(game, f"⚙️ A {eqj['nome']} estreia em {game['ano'] + 1} com motor **{novo['nome']}**.")
        else:
            noticia(game, f"🚨 Sem caixa para pagar o motor {novo['nome']}, o acordo desmoronou!")
    game["motor_proxima"] = None
    if game["patrocinador_proxima"]:
        eqj["patrocinador"] = game["patrocinador_proxima"]
        noticia(game, f"🤝 Novo patrocinador master: **{eqj['patrocinador']}** estampa o carro em {game['ano'] + 1}.")
    game["patrocinador_proxima"] = None

    # cobra o motor de todas as equipes; quem não paga recebe o FIA
    for e in game["equipes"]:
        mot = motor(game, e["motor_id"])
        custo = mot["preco"] * (0.45 if e.get("motor_proprio") else 1.0)
        if not e.get("motor_proprio") and e["caixa"] < custo and mot["id"] != "fia":
            e["motor_id"] = "fia"
            e["usou_motor_fia"] = True
            noticia(
                game, f"😬 A {e['nome']} não pagou o fornecedor e correrá com o **compulsório da organização (50%)**."
            )
            mot, custo = motor(game, "fia"), 0.0
        if e["id"] == eqj["id"]:
            lancar_financa(game, f"Motor {mot['nome']} — temporada {game['ano'] + 1}", -custo * 1000)
        else:
            e["caixa"] -= custo
        # motores evoluem um tiquinho a cada ano
    for mot in game["motores"]:
        if mot["id"] != "fia":
            mot["potencia"] = int(max(70, min(99, mot["potencia"] + rng.randint(-1, 2))))
            mot["confiabilidade"] = int(max(75, min(97, mot["confiabilidade"] + rng.randint(-1, 2))))

    # ------------------------------ carros do ano seguinte
    mudanca_reg = (game["ano"] + 1) % 5 == 1 and game["ano"] >= 2026  # 2031, 2036...
    if mudanca_reg:
        noticia(game, "📐 **NOVO REGULAMENTO TÉCNICO!** O grid foi embaralhado — ninguém sabe quem acertou o conceito.")
    for e in game["equipes"]:
        base = 63 + (e["nivel_carro"] - 63) * (0.25 if mudanca_reg else 0.55)
        base += (e["prestigio"] - 70) * 0.10 + max(0.0, e["caixa"]) * 0.012
        base += rng.gauss(0, 3.2 if mudanca_reg else 1.7)
        e["nivel_carro"] = round(max(52.0, min(97.0, base)), 1)
        mot = motor(game, e["motor_id"])
        e["confiabilidade"] = round(
            max(72.0, min(97.0, (e["confiabilidade"] + mot["confiabilidade"]) / 2 + rng.gauss(0, 1.5))), 1
        )
        e["prestigio"] = int(max(20, min(99, e["prestigio"] + (6 - posicao_equipe(game, e["id"]) if tab_c else 0))))
        e["pontos"] = e["vitorias"] = e["podios"] = e["poles"] = 0
    for p in game["pilotos"]:
        p["pontos"] = 0
        p["forma"] = 50

    game["calendario"] = [
        dict(e)
        for e in (game.get("calendario_base") or game["calendario"])
        if game["incluir_canceladas"] or not e.get("cancelavel")
    ]
    game["ano"] += 1
    game["rodada"] = 0
    game["historico_pontos"] = []
    verificar_conquistas(game)
    noticia(
        game,
        f"📅 Temporada **{game['ano']}** no ar! {[e for e in game['equipes'] if e['id'] == eqj['id']][0]['nome']} "
        f"estreia o carro novo (nível {eqj['nivel_carro']:.0f}) no {game['calendario'][0]['gp']}. Boa sorte, chefe!",
    )
    return {
        "campeao_pilotos": campeao["nome"] if campeao else "-",
        "campea_construtores": campea_constr["nome"] if campea_constr else "-",
    }
