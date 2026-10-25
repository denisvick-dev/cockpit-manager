# -*- coding: utf-8 -*-
"""Hall da Fama & Conquistas."""

import pandas as pd
import streamlit as st

import bandeiras as bnd
import dados2026 as db

from .comum import CFG_BANDEIRA, titulo_pagina


def pagina_hall(game):
    titulo_pagina("Legado", "Hall da Fama & Conquistas", "As lendas da categoria — e as suas 10 conquistas para caçar.")
    tab1, tab2 = st.tabs(["🌟 Hall da Fama", "🎖️ Conquistas (10)"])
    with tab1:
        st.caption(
            f"Pilotos do seu save entram para a eternidade ao se aposentar com "
            f"**≥ {db.HOF_MIN_TITULOS} títulos** ou **≥ {db.HOF_MIN_VITORIAS} vitórias** na carreira."
        )
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Bandeira": bnd.url_bandeira(h["bandeira"]),
                        "Lenda": h["nome"],
                        "País": h["pais"],
                        "Títulos": h["titulos"],
                        "Vitórias": h["vitorias"],
                        "Era": h["anos"],
                        "Origem": "induzido no seu save ✨" if h.get("induzido_no_save") else "histórico",
                    }
                    for h in sorted(game["hall_da_fama"], key=lambda x: (-x["titulos"], -x["vitorias"]))
                ]
            ),
            hide_index=True,
            width="stretch",
            column_config=CFG_BANDEIRA,
        )
    with tab2:
        cols = st.columns(2)
        for i, c in enumerate(db.CONQUISTAS):
            ok = c["id"] in game["conquistas"]
            cols[i % 2].markdown(f"{'✅' if ok else '🔒'} {c['icone']} **{c['nome']}** — {c['desc']}")
        st.progress(
            len(game["conquistas"]) / len(db.CONQUISTAS),
            text=f"{len(game['conquistas'])}/{len(db.CONQUISTAS)} conquistas",
        )
