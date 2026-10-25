# -*- coding: utf-8 -*-
"""Patrocinadores & Finanças: extrato, gráficos e contratos."""

import pandas as pd
import streamlit as st

import dados2026 as db
import simulacao as sim

from .comum import CFG_BANDEIRA, botao_csv, flash, titulo_pagina

def pagina_financas(game):
    eqj = sim.equipe(game, game["equipe_jogador"])
    titulo_pagina(
        "Dinheiro", "Patrocinadores & Finanças", "Quem paga a conta, para onde vai cada centavo — e o que sobra no fim."
    )
    lista_spon = game.get("patrocinadores") or db.PATROCINADORES
    spon = next((s for s in lista_spon if s["nome"] == eqj["patrocinador"]), lista_spon[-1])
    salarios = sum(p["salario_corrida"] for p in game["pilotos"] if p["equipe_id"] == eqj["id"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Caixa", sim.fmt_dinheiro_m(eqj["caixa"]))
    c2.metric("Patrocinador atual", spon["nome"])
    c3.metric("Receita fixa/corrida", sim.fmt_dinheiro_k(spon["por_corrida"]))
    saldo = spon["por_corrida"] - salarios - eqj["investimento_corrida"]
    c4.metric(
        "Saldo/corrida (sem bônus)",
        f"+ {sim.fmt_dinheiro_k(saldo)}" if saldo >= 0 else f"− {sim.fmt_dinheiro_k(-saldo)}",
    )
    if saldo < 0:
        st.warning(
            "Você gasta mais do que recebe por corrida (antes dos bônus por ponto/pódio). "
            "Ou pontua muito, ou corta salário/investimento, ou troca o patrocinador na virada."
        )

    st.subheader(f"🤝 Patrocinadores disponíveis para {game['ano'] + 1} (seu prestígio: {eqj['prestigio']})")
    linhas = [
        {
            "Patrocinador": s["nome"],
            "": "⭐ atual" if s["nome"] == eqj["patrocinador"] else "",
            "Fixo/corrida": s["por_corrida"],
            "Bônus/ponto": s["bonus_ponto"],
            "Bônus/pódio": s["bonus_podio"],
            "Bônus/vitória": s["bonus_vitoria"],
            "Prestígio mín.": s["prestigio_min"],
            "Status": "✅ assina" if eqj["prestigio"] >= s["prestigio_min"] else "🔒 prestígio insuficiente",
        }
        for s in lista_spon
    ]
    st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch", column_config=CFG_BANDEIRA)
    elegiveis = [s for s in lista_spon if eqj["prestigio"] >= s["prestigio_min"]]
    novo = st.selectbox(
        "Negociar para a próxima temporada", elegiveis, format_func=lambda s: f"{s['nome']} — {s['desc']}"
    )
    if game["patrocinador_proxima"]:
        st.success(f"Fechado: **{game['patrocinador_proxima']}** estreia no carro em {game['ano'] + 1}.")
    if st.button("✍️ Assinar com este patrocinador", type="primary"):
        game["patrocinador_proxima"] = novo["nome"]
        flash("success", f"{novo['nome']} será o patrocinador master em {game['ano'] + 1}!")
        st.rerun()

    if game["historico_caixa"]:
        st.subheader("📈 Evolução do caixa")
        caixa = pd.DataFrame(game["historico_caixa"]).set_index("rodada")["caixa"]
        st.line_chart(caixa, x_label="Etapa", y_label="Caixa (US$ mi)")
        variacao = float(caixa.iloc[-1]) - float(caixa.iloc[0]) if len(caixa) > 1 else 0.0
        st.caption(
            f"Da primeira à última etapa: **{'+' if variacao >= 0 else '−'}"
            f"{sim.fmt_dinheiro_m(abs(variacao)).replace('US$ ', 'US$ ')}** de variação."
        )
    st.subheader("🧾 Extrato")
    if game["extrato"]:
        ext = pd.DataFrame(game["extrato"])
        anos = sorted({int(a) for a in ext["temporada"]})
        if len(anos) > 1:
            escolha = st.selectbox("Temporada", ["Todas"] + anos, key="extrato_ano")
            if escolha != "Todas":
                ext = ext[ext["temporada"] == escolha]
        entradas = float(ext.loc[ext["valor"] > 0, "valor"].sum())
        saidas = float(ext.loc[ext["valor"] < 0, "valor"].sum())
        c1, c2, c3 = st.columns(3)
        c1.metric("Entradas", sim.fmt_dinheiro_k(entradas))
        c2.metric("Saídas", f"−{sim.fmt_dinheiro_k(abs(saidas))}")
        c3.metric("Saldo do filtro", sim.fmt_dinheiro_k(entradas + saidas))
        ext_view = ext.rename(
            columns={"temporada": "Ano", "etapa": "Etapa", "descricao": "Descrição", "valor": "US$ mil"}
        )
        st.dataframe(
            ext_view,
            hide_index=True,
            width="stretch",
            column_config={
                "US$ mil": st.column_config.NumberColumn("US$ mil", format="%d"),
                "Ano": st.column_config.NumberColumn("Ano", format="%d"),
            },
        )
        botao_csv(ext_view, f"extrato_{game['ano']}_etapa{game['rodada']}.csv", key="csv_extrato")
    else:
        st.info("🧾 Nenhum lançamento ainda. Corra a primeira etapa para o extrato começar a contar.")
