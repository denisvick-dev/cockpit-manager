# -*- coding: utf-8 -*-
"""Campeonato: pilotos, construtores e evolução."""

import pandas as pd
import streamlit as st

import bandeiras as bnd
import simulacao as sim

from .comum import CFG_BANDEIRA, botao_csv, rot_corrida2, titulo_pagina
from .corrida import df_resultado


def pagina_campeonato(game):
    titulo_pagina(
        "Classificação",
        f"Campeonato {game['ano']}",
        "Pilotos, construtores, evolução dos pontos e todos os resultados.",
    )
    tab1, tab2, tab3, tab4 = st.tabs(["👨‍✈️ Pilotos", "🏭 Construtores", "📈 Evolução", "🗓️ Calendário & Resultados"])

    with tab1:
        tabela = sim.tabela_pilotos(game)
        if not game["resultados"]:
            st.info("🏁 Nenhuma corrida disputada ainda — a tabela ganha vida depois da primeira bandeirada.")
        lider_pts = tabela[0]["pontos"] if tabela else 0
        linhas = []
        for i, p in enumerate(tabela):
            pos = i + 1
            hist = sim.ultimas_corridas(game, p["id"], 5)
            linhas.append(
                {
                    "Pos": pos,
                    "Bandeira": bnd.url_bandeira(p["bandeira"]),
                    "Piloto": p["nome"],
                    "Equipe": sim.equipe(game, p["equipe_id"])["nome"] if p["equipe_id"] else "—",
                    "": "⭐" if p["equipe_id"] == game["equipe_jogador"] else "",
                    "Pontos": p["pontos"],
                    "Gap": None if pos == 1 else lider_pts - p["pontos"],
                    "Últimas 5": sim.forma_texto(hist),
                    "Vitórias": p["vitorias"],
                    "Pódios": p["podios"],
                    "Poles": p["poles"],
                    "Abandonos": p["abandonos"],
                    "Forma": p["forma"],
                }
            )
        st.dataframe(
            pd.DataFrame(linhas),
            hide_index=True,
            width="stretch",
            column_config={
                **CFG_BANDEIRA,
                "Gap": st.column_config.NumberColumn(
                    "Gap", help="Pontos atrás do líder (vazio = líder)", format="%d atrás"
                ),
                "Últimas 5": st.column_config.TextColumn(
                    "Últimas 5",
                    help="Posições nas últimas 5 corridas (D = abandono), da mais antiga para a mais recente",
                ),
            },
        )
        _csv_pilotos = pd.DataFrame(linhas).drop(columns=["Bandeira"])
        botao_csv(
            _csv_pilotos,
            f"campeonato_pilotos_{game['ano']}_etapa{game['rodada']}.csv",
            key="csv_pilotos",
        )
        if tabela:
            meu = next((p for p in tabela if p["equipe_id"] == game["equipe_jogador"]), None)
            if meu:
                st.caption(
                    f"Seu melhor piloto: **{meu['nome']}** — {meu['pontos']} pts, "
                    f"forma {sim.forma_texto(sim.ultimas_corridas(game, meu['id'], 5))}."
                )
    with tab2:
        construtores = sim.tabela_construtores(game)
        if not game["resultados"]:
            st.info("🏭 A tabela de construtores aparece depois da primeira corrida.")
        lider_c = construtores[0]["pontos"] if construtores else 0
        linhas = [
            {
                "Pos": i + 1,
                "Bandeira": bnd.url_bandeira(e["bandeira"]),
                "Equipe": e["nome"],
                "": "⭐" if e["id"] == game["equipe_jogador"] else "",
                "Pontos": e["pontos"],
                "Gap": None if i == 0 else lider_c - e["pontos"],
                "Vitórias": e["vitorias"],
                "Pódios": e["podios"],
                "Poles": e["poles"],
            }
            for i, e in enumerate(construtores)
        ]
        st.dataframe(
            pd.DataFrame(linhas),
            hide_index=True,
            width="stretch",
            column_config={
                **CFG_BANDEIRA,
                "Gap": st.column_config.NumberColumn(
                    "Gap", help="Pontos atrás do líder (vazio = líder)", format="%d atrás"
                ),
            },
        )
        botao_csv(
            pd.DataFrame(linhas).drop(columns=["Bandeira"]),
            f"campeonato_construtores_{game['ano']}_etapa{game['rodada']}.csv",
            key="csv_construtores",
        )
    with tab3:
        if game["historico_pontos"]:
            quantos = st.slider("Quantos pilotos mostrar", 3, 12, 8, key="evolucao_top")
            tab = sim.tabela_pilotos(game)[:quantos]
            dados = {p["nome"]: [h["pontos"].get(p["id"], 0) for h in game["historico_pontos"]] for p in tab}
            st.line_chart(
                pd.DataFrame(dados, index=[h["rodada"] for h in game["historico_pontos"]]),
                x_label="Etapa",
                y_label="Pontos",
            )
            st.caption("Cada linha é um piloto; a curva dobra de valor a cada corrida que ele pontua.")
        else:
            st.info("📈 Complete a primeira corrida para ver a curva de pontos.")
        if game["historico_temporadas"]:
            st.subheader("📜 Temporadas anteriores")
            st.dataframe(
                pd.DataFrame(game["historico_temporadas"]).rename(
                    columns={
                        "ano": "Ano",
                        "campeao_pilotos": "Campeão (Pilotos)",
                        "equipe_campea": "Campeã (Construtores)",
                        "sua_posicao": "Sua posição",
                        "seus_pontos": "Seus pontos",
                    }
                ),
                hide_index=True,
                width="stretch",
            )
    with tab4:
        for i, etapa in enumerate(game["calendario"]):
            regs = [
                r for r in game["resultados"] if r["ano"] == game["ano"] and r["rodada"] == i + 1 and not r["sprint"]
            ]
            with st.expander(
                f"{i + 1}. [{bnd.codigo_texto(etapa['bandeira'])}] {etapa['gp']} — {etapa['circuito']} · {etapa['voltas']} voltas"
                + (f" · ⚡{rot_corrida2(game)}" if etapa["sprint"] else "")
                + (" ✅" if regs else "")
            ):
                if regs:
                    r = regs[-1]
                    st.caption("🌧️ Corrida molhada" if r["molhado"] else "☀️ Corrida seca")
                    st.dataframe(
                        df_resultado(game, r["resultado"]), hide_index=True, width="stretch", column_config=CFG_BANDEIRA
                    )
                    botao_csv(
                        df_resultado(game, r["resultado"]).drop(columns=["Bandeira"]),
                        f"resultado_{r['ano']}_etapa{r['rodada']}.csv",
                        key=f"csv_res_{r['ano']}_{r['rodada']}",
                    )
                else:
                    st.caption("Ainda não disputada.")
