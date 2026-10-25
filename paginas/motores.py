# -*- coding: utf-8 -*-
"""Motores: fornecedores e contratos."""

import pandas as pd
import streamlit as st

import simulacao as sim

from .comum import flash, rot_fornecedor, titulo_pagina

def pagina_motores(game):
    eqj = sim.equipe(game, game["equipe_jogador"])
    titulo_pagina(
        "Fornecedores",
        f"{rot_fornecedor(game)}s",
        "Desempenho de verdade custa caro. Ficar sem caixa sai mais caro ainda.",
    )
    atual = sim.motor(game, eqj["motor_id"])
    st.write(
        f"Motor atual: **{atual['nome']}** — potência {atual['potencia']}, confiabilidade {atual['confiabilidade']}"
        + (
            " · **motor próprio** (custo interno reduzido; herança da equipe, como na DB: Audi/Ferrari/Mercedes/Red Bull)."
            if eqj.get("motor_proprio")
            else f" · custo de US$ {atual['preco']:.0f} mi/temporada."
        )
    )
    df = pd.DataFrame(
        [
            {
                "Motor": m["nome"],
                "": "⭐ atual" if m["id"] == eqj["motor_id"] else "",
                "Potência": m["potencia"],
                "Confiabilidade": m["confiabilidade"],
                "Preço (mi/ano)": m["preco"],
                "Obs.": ("de fábrica" if m["proprio_de"] else "independente/cliente"),
            }
            for m in sorted(game["motores"], key=lambda x: -x["potencia"])
        ]
    )
    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
        column_config={
            c: st.column_config.ProgressColumn(c, min_value=0, max_value=100, format="%d")
            for c in ["Potência", "Confiabilidade"]
        },
    )
    for m in game["motores"]:
        st.caption(f"**{m['nome']}** — {m['desc']}")

    if eqj.get("motor_proprio"):
        st.info(
            "Equipes com motor próprio não trocam de fornecedor (fidelidade à DB). "
            "Seu motor evolui um pouco a cada temporada junto com o investimento da fábrica."
        )
    else:
        st.subheader(f"🔁 Contrato para {game['ano'] + 1}")
        disponiveis: list[dict] = [m for m in game["motores"] if not m["proprio_de"] and m["id"] != "fia"]
        escolhido = st.selectbox(
            "Próximo motor",
            disponiveis,
            format_func=lambda m: f"{m['nome']} — pot {m['potencia']} · US$ {m['preco']:.0f} mi/ano",
        )
        assert escolhido is not None  # selectbox com lista não vazia sempre escolhe um valor
        if game["motor_proxima"]:
            st.success(
                f"Acordo fechado: motor **{sim.motor(game, game['motor_proxima'])['nome']}** em {game['ano'] + 1} "
                f"(o valor é debitado na virada da temporada)."
            )
        if st.button("✍️ Assinar contrato de motor", type="primary"):
            game["motor_proxima"] = escolhido["id"]
            flash(
                "success", f"Motor {escolhido['nome']} garantido para {game['ano'] + 1} — se houver caixa para pagar!"
            )
            st.rerun()
        st.caption(
            "🚨 Se na virada da temporada o caixa não cobrir o motor, entra o lendário "
            "**motor FIA compulsório (50% de potência)** — pesadelo de todo jogador de CM14."
        )
