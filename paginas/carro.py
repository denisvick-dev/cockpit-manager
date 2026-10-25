# -*- coding: utf-8 -*-
"""Carro & Investimentos: os 6 eixos e o desenvolvimento."""

import math

import pandas as pd
import streamlit as st

import bandeiras as bnd
import simulacao as sim

from .comum import CFG_BANDEIRA, titulo_pagina

EIXOS_RADAR = [
    ("aerodinamica", "Aero"),
    ("cambio", "Câmbio"),
    ("freio", "Freio"),
    ("eletrico", "Elétrico"),
    ("direcao", "Direção"),
    ("confiabilidade", "Confiab."),
]


def radar_svg(series, tamanho=300):
    """Radar dos 6 eixos em SVG puro (sem dependências novas).

    `series` = [(nome, cor_hex, {eixo: valor 0-100}), ...] — cada série vira um
    polígono e uma entrada na legenda.
    """
    cx = cy = tamanho / 2
    raio = tamanho / 2 - 34
    n = len(EIXOS_RADAR)

    def ponto(i, valor):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        r = raio * max(0.0, min(100.0, valor)) / 100.0
        return cx + r * math.cos(ang), cy + r * math.sin(ang)

    partes = ['<svg viewBox="0 0 %d %d" class="radar" role="img" aria-label="Comparação dos eixos do carro">' % (tamanho, tamanho)]
    # grade (5 anéis) + eixos
    for anel in (20, 40, 60, 80, 100):
        pts = " ".join(f"{ponto(i, anel)[0]:.1f},{ponto(i, anel)[1]:.1f}" for i in range(n))
        partes.append(f'<polygon points="{pts}" class="radar-grade"/>')
    for i in range(n):
        x, y = ponto(i, 100)
        partes.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" class="radar-eixo"/>')
    # séries
    for nome, cor, valores in series:
        vals = [valores.get(k, 0) for k, _ in EIXOS_RADAR]
        pts = " ".join(f"{ponto(i, v)[0]:.1f},{ponto(i, v)[1]:.1f}" for i, v in enumerate(vals))
        partes.append(f'<polygon points="{pts}" class="radar-serie" style="stroke:{cor}; fill:{cor}"/>')
        for i, v in enumerate(vals):
            x, y = ponto(i, v)
            partes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.6" fill="{cor}"/>')
    # rótulos
    for i, (_, rotulo) in enumerate(EIXOS_RADAR):
        x, y = ponto(i, 118)
        anc = "middle"
        if x > cx + 6:
            anc = "start"
        elif x < cx - 6:
            anc = "end"
        partes.append(
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anc}" dominant-baseline="middle" '
            f'class="radar-rotulo">{rotulo}</text>'
        )
    partes.append("</svg>")
    legenda = "".join(
        f'<span class="radar-leg"><i style="background:{cor}"></i>{nome}</span>' for nome, cor, _ in series
    )
    return '<div class="radar-wrap">' + "".join(partes) + f'<div class="radar-legenda">{legenda}</div></div>'


def pagina_carro(game):
    eqj = sim.equipe(game, game["equipe_jogador"])
    mot = sim.motor(game, eqj["motor_id"])
    titulo_pagina(
        "Engenharia", "Carro & Investimentos", "Desenvolva o chassi, proteja a confiabilidade e acompanhe as rivais."
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nível do chassi", f"{eqj['nivel_carro']:.1f}")
    c2.metric(f"Motor {mot['nome']}", f"{mot['potencia']} pot / {mot['confiabilidade']} conf")
    c3.metric("Desempenho combinado", f"{sim.desempenho_carro(game, eqj):.1f}")
    c4.metric("Confiabilidade do carro", f"{eqj['confiabilidade']:.0f}")

    st.subheader("💸 Investimento por corrida")
    inv = st.slider(
        "Quanto investir no desenvolvimento a cada corrida (US$ mil)", 0, 3000, int(eqj["investimento_corrida"]), 50
    )
    eqj["investimento_corrida"] = inv
    eqj["foco"] = st.radio(
        "Foco do desenvolvimento",
        ["equilibrado", "chassi", "confiabilidade"],
        index=["equilibrado", "chassi", "confiabilidade"].index(eqj["foco"]),
        horizontal=True,
        format_func=lambda x: {
            "equilibrado": "⚖️ Equilibrado",
            "chassi": "🏎️ Chassi/aero (mais velocidade)",
            "confiabilidade": "🛡️ Confiabilidade (menos abandonos)",
        }[x],
    )
    teste = sim.piloto_teste(game, eqj["id"])
    feedback = (sum(t["atributos"]["acerto"] for t in sim.titulares(game, eqj["id"])) / 2) * 0.7 + (
        (teste["atributos"]["acerto"] * 0.3) if teste else 21
    )
    ganho = (inv / 1000.0) * 0.22 * (feedback / 85.0) * max(0.12, (99.5 - eqj["nivel_carro"]) / 35.0)
    st.info(
        f"Feedback dos pilotos (Acerto): **{feedback:.0f}** → ganho estimado de "
        f"**+{ganho:.2f}** de nível por corrida. Piloto de testes com Acerto alto acelera tudo — "
        f"o seu é {teste['nome'] if teste else '—'} (Acerto {teste['atributos']['acerto'] if teste else '—'})."
    )
    st.caption(
        "⚠️ Investir demais quebra o caixa (e sem caixa, sem motor decente na próxima temporada). "
        "No CM14 original, esse era O erro fatal dos novatos."
    )

    st.subheader("📏 Nível das equipes (como em Campeonato → Equipes do original)")
    linhas = []
    for e in sorted(game["equipes"], key=lambda x: -sim.desempenho_carro(game, x)):
        m = sim.motor(game, e["motor_id"])
        linhas.append(
            {
                "Bandeira": bnd.url_bandeira(e["bandeira"]),
                "Equipe": e["nome"],
                "": "⭐" if e["id"] == eqj["id"] else "",
                "Chassi": round(e["nivel_carro"], 1),
                "Motor": m["nome"],
                "Potência": m["potencia"],
                "Desempenho": round(sim.desempenho_carro(game, e), 1),
                "Confiabilidade": round(e["confiabilidade"]),
                "Prestígio": e["prestigio"],
                "Caixa (mi)": round(e["caixa"], 1),
            }
        )
    df = pd.DataFrame(linhas)
    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
        column_config={
            **CFG_BANDEIRA,
            **{
                c: st.column_config.ProgressColumn(c, min_value=0, max_value=100, format="%.0f")
                for c in ["Chassi", "Potência", "Desempenho", "Confiabilidade"]
            },
        },
    )
    st.bar_chart(df.set_index("Equipe")["Desempenho"])

    # ---------------- comparador de carros (radar dos 6 eixos)
    st.divider()
    st.subheader("🎯 Comparador de carros")
    st.caption("Escolha uma rival e veja, eixo por eixo, onde o seu carro ganha e onde perde tempo.")
    rivais = {e["nome"]: e for e in game["equipes"] if e["id"] != eqj["id"]}
    sugestao = next(
        (e["nome"] for e in sorted(game["equipes"], key=lambda x: -sim.desempenho_carro(game, x)) if e["id"] != eqj["id"]),
        None,
    )
    nomes = list(rivais)
    escolhida = st.selectbox(
        "Rival",
        nomes,
        index=nomes.index(sugestao) if sugestao in nomes else 0,
        key="rival_radar",
    )
    rival = rivais[escolhida]
    meus_eixos = sim.eixos_carro(eqj)
    eixos_rival = sim.eixos_carro(rival)
    st.markdown(
        radar_svg([(eqj["nome"], "#E02444", meus_eixos), (rival["nome"], "#38BDF8", eixos_rival)]),
        unsafe_allow_html=True,
    )
    deltas = []
    for chave, rotulo in EIXOS_RADAR:
        d = round(meus_eixos.get(chave, 0) - eixos_rival.get(chave, 0), 1)
        deltas.append(
            {
                "Eixo": rotulo,
                eqj["nome"]: meus_eixos.get(chave, 0),
                rival["nome"]: eixos_rival.get(chave, 0),
                "Diferença": d,
            }
        )
    st.dataframe(
        pd.DataFrame(deltas),
        hide_index=True,
        width="stretch",
        column_config={
            "Diferença": st.column_config.NumberColumn("Diferença", format="%+.1f"),
            eqj["nome"]: st.column_config.ProgressColumn(eqj["nome"], min_value=0, max_value=100, format="%.0f"),
            rival["nome"]: st.column_config.ProgressColumn(rival["nome"], min_value=0, max_value=100, format="%.0f"),
        },
    )
    melhor = max(deltas, key=lambda x: x["Diferença"])
    pior = min(deltas, key=lambda x: x["Diferença"])
    if melhor["Diferença"] > 0:
        st.success(f"Sua vantagem está em **{melhor['Eixo']}** ({melhor['Diferença']:+.1f} pts vs. {rival['nome']}).")
    if pior["Diferença"] < 0:
        st.warning(f"O ponto a atacar é **{pior['Eixo']}** ({pior['Diferença']:+.1f} pts). Desenvolva aqui primeiro.")
