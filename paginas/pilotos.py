# -*- coding: utf-8 -*-
"""Pilotos & Contratos: mercado, renovações e academia."""

import pandas as pd
import streamlit as st

import bandeiras as bnd
import dados2026 as db
import simulacao as sim

from .comum import CFG_BANDEIRA, ROTULOS_PAPEL, botao_csv, df_pilotos_equipe, flash, titulo_pagina

def pagina_pilotos(game):
    eqj = sim.equipe(game, game["equipe_jogador"])
    titulo_pagina("Mercado", "Pilotos & Contratos", "Seus pilotos de hoje — e as negociações que desenham o amanhã.")
    tab1, tab2, tab3 = st.tabs(["Minha equipe", "🤝 Negociar (próxima temporada)", "🌍 Todos os pilotos"])

    with tab1:
        st.dataframe(
            df_pilotos_equipe(game, eqj["id"]),
            hide_index=True,
            width="stretch",
            column_config={
                **CFG_BANDEIRA,
                "Overall": st.column_config.ProgressColumn(
                    "Overall", min_value=0, max_value=100, format="%d"
                ),
                "Salário": st.column_config.NumberColumn("Salário/corrida", format="US$ %d mil"),
                "Contrato": st.column_config.NumberColumn(
                    "Contrato", help="Anos restantes (0 = renova ou sai na virada)", format="%d ano(s)"
                ),
            },
        )
        total_sal = sum(p["salario_corrida"] for p in game["pilotos"] if p["equipe_id"] == eqj["id"])
        st.caption(f"Custo total de salários: {sim.fmt_dinheiro_k(total_sal)} por corrida.")
        expirando = [
            p for p in game["pilotos"]
            if p["equipe_id"] == eqj["id"] and not p["aposentado"] and int(p.get("contrato_anos", 0)) <= 1
        ]
        if expirando and not game["contratos_proxima"]:
            nomes = ", ".join(p["nome"] for p in expirando)
            st.warning(
                f"⏳ Contrato terminando: **{nomes}**. Negocie na aba **🤝 Negociar** "
                f"(ou feche um pré-contrato) antes da virada da temporada."
            )
        if game["contratos_proxima"]:
            st.subheader(f"✍️ Já contratados para {game['ano'] + 1}")
            for pid, c in list(game["contratos_proxima"].items()):
                p = sim.piloto(game, pid)
                col1, col2 = st.columns([5, 1])
                marca = " · 📝 pré (sinal pago)" if c.get("pre") else ""
                col1.markdown(
                    bnd.com_bandeira(
                        p["bandeira"],
                        f"**{p['nome']}** — {c['papel']} · {sim.fmt_dinheiro_k(c['salario'])}/corrida · {c['anos']} ano(s){marca}",
                    ),
                    unsafe_allow_html=True,
                )
                if col2.button("Cancelar", key=f"canc_{pid}"):
                    del game["contratos_proxima"][pid]
                    if c.get("pre"):
                        flash(
                            "warning",
                            f"Pré-contrato de {p['nome']} cancelado — a sinalização de "
                            f"{sim.fmt_dinheiro_k(c.get('sinal', 0))} **não** é devolvida.",
                        )
                    st.rerun()

    with tab2:
        st.caption(
            "Como no original: você negocia **durante** a temporada, mas o piloto só veste seu macacão "
            "na **próxima**. Salários são por corrida — ou feche na hora com um **pré-contrato** (sinal pago)."
        )
        ativos: list[dict] = [p for p in game["pilotos"] if not p["aposentado"]]
        ativos.sort(key=lambda p: -sim.overall(p))
        sel = st.selectbox(
            "Piloto",
            ativos,
            key="piloto_sel",
            format_func=lambda p: (
                f"[{bnd.codigo_texto(p['bandeira'])}] {p['nome']} — ovr {sim.overall(p)} · {p['idade']} anos · "
                f"{(sim.equipe(game, p['equipe_id'])['nome'] if p['equipe_id'] else 'LIVRE')} ({p['papel']})"
            ),
        )
        assert sel is not None  # selectbox com lista não vazia sempre escolhe um valor
        a = sel["atributos"]
        st.bar_chart(pd.Series({db.ATRIBUTOS[k]: v for k, v in a.items()}))
        st.caption(
            f"Auge: {sel['auge_inicio']}–{sel['auge_fim']} anos (platô) · Potencial: {sel['potencial']} · "
            f"Vitórias no save: {sel['vitorias']} · Títulos: {sel['titulos']}"
        )
        with st.form("form_contrato"):
            _vagas = list((game.get("vagas_por_equipe") or {}).get(eqj["id"], ["P1", "P2"])) + ["teste"]
            papel = st.radio("Papel oferecido", _vagas, horizontal=True, format_func=lambda x: ROTULOS_PAPEL.get(x, x))
            esperado = sim.salario_esperado(game, sel, papel)
            salario = st.number_input(
                f"Salário oferecido (US$ mil/corrida) — o mercado pagaria ±{sim.fmt_dinheiro_k(esperado)}",
                min_value=10,
                max_value=6000,
                value=int(esperado),
                step=10,
            )
            anos = st.slider("Duração (anos)", 1, 4, 2)
            tipo = st.radio(
                "Tipo de acordo",
                ["✍️ Proposta comum — grátis, ele pode recusar", "📝 Pré-contrato — fecha na hora, com sinal"],
                key="tipo_acordo",
                help="Como no original: o pré-contrato paga uma taxa de sinalização de 3 corridas do "
                "salário AGORA e fecha o acordo sem chance de recusa. A taxa não é devolvida se "
                "você cancelar (e some se o piloto se aposentar antes da virada).",
            )
            taxa = sim.taxa_sinal(int(salario))
            if tipo.startswith("📝"):
                st.caption(
                    f"💸 Sinal a pagar agora: **{sim.fmt_dinheiro_k(taxa)}** (3 corridas do salário) · "
                    f"seu caixa: {sim.fmt_dinheiro_m(eqj['caixa'])}"
                )
            if st.form_submit_button(
                "📝 Assinar pré-contrato" if tipo.startswith("📝") else "✍️ Fazer proposta",
                type="primary",
                width="stretch",
            ):
                if tipo.startswith("📝"):
                    ok, msg = sim.pre_contratar_piloto(game, sel["id"], papel, int(salario), anos)
                    flash("success" if ok else "error", msg)
                else:
                    r = sim.negociar_piloto_detalhado(game, sel["id"], papel, int(salario), anos)
                    if r["status"] == "aceita":
                        flash("success", r["mensagem"])
                    elif r["status"] == "contra":
                        flash("warning", f"🔄 {r['mensagem']}")
                    else:
                        flash("error", r["mensagem"])
                st.rerun()

        # ---------------- contraproposta em aberto (negociação em rodadas)
        nego = (game.get("negociacoes") or {}).get(sel["id"])
        if nego and sel["id"] not in game["contratos_proxima"]:
            pedido = nego["pedido"]
            st.warning(
                f"🔄 **Contraproposta de {sel['nome']}** (rodada {nego['rodada']} de 3): "
                f"{sim.fmt_dinheiro_k(pedido['salario'])}/corrida por {pedido['anos']} ano(s) "
                f"como {ROTULOS_PAPEL.get(nego['papel'], nego['papel'])}."
            )
            st.caption(
                "Aceitar o pedido quase sempre fecha. Cobrir com menos é possível — mas se ele "
                "recusar duas vezes, a conversa termina até a próxima temporada."
            )
            c1, c2, c3 = st.columns(3)
            if c1.button("✅ Aceitar o pedido", type="primary", width="stretch", key="nego_aceitar"):
                r = sim.negociar_piloto_detalhado(game, sel["id"], nego["papel"], pedido["salario"], pedido["anos"])
                flash("success" if r["status"] == "aceita" else "warning", r["mensagem"])
                st.rerun()
            with c2:
                novo_sal = st.number_input(
                    "Contra-oferta (US$ mil/corrida)",
                    min_value=10,
                    max_value=6000,
                    value=int(pedido["salario"] * 0.9),
                    step=10,
                    key="nego_salario",
                )
                if st.button("📨 Enviar contra-oferta", width="stretch", key="nego_enviar"):
                    r = sim.negociar_piloto_detalhado(game, sel["id"], nego["papel"], int(novo_sal), pedido["anos"])
                    flash("success" if r["status"] == "aceita" else "warning", r["mensagem"])
                    st.rerun()
            if c3.button("🚪 Encerrar conversa", width="stretch", key="nego_encerrar"):
                game.setdefault("negociacoes", {}).pop(sel["id"], None)
                flash("info", f"Negociação com {sel['nome']} encerrada.")
                st.rerun()

    with tab3:
        linhas = []
        for p in sorted(ativos, key=lambda x: -x["pontos"]):
            linhas.append(
                {
                    "Bandeira": bnd.url_bandeira(p["bandeira"]),
                    "Piloto": p["nome"],
                    "Idade": p["idade"],
                    "Equipe": sim.equipe(game, p["equipe_id"])["nome"] if p["equipe_id"] else "— LIVRE —",
                    "Papel": p["papel"],
                    "Overall": sim.overall(p),
                    "Potencial": p["potencial"],
                    "Pontos": p["pontos"],
                    "Vitórias*": p["vitorias"],
                    "Pódios*": p["podios"],
                    "Títulos*": p["titulos"],
                    "Salário": p["salario_corrida"],
                }
            )
        st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch", column_config=CFG_BANDEIRA)
        botao_csv(
            pd.DataFrame(linhas).drop(columns=["Bandeira"], errors="ignore"),
            f"pilotos_{game['ano']}_etapa{game['rodada']}.csv",
            key="csv_pilotos_mercado",
        )
        st.caption("* Estatísticas acumuladas dentro deste save.")
