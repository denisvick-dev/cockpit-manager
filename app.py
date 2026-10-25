# -*- coding: utf-8 -*-
"""
🏎️ COCKPIT MANAGER — Edição Streamlit (DB F1 2026)

Remake feito por fã, inspirado no Cockpit Manager '14 (Cartola Games, 2014)
e na DB F1 2026 v1.0 by Jonathan Daniel (blog Cockpit Manager - Brasil).

Rode com:  streamlit run app.py
"""

import json

import streamlit as st

import armazenamento
import bandeiras as bnd
import simulacao as sim
from paginas.ajuda import pagina_ajuda
from paginas.campeonato import pagina_campeonato
from paginas.carro import pagina_carro
from paginas.comum import (
    MENUS,
    exibir_confirmacao_novo_jogo,
    ir_para,
    meta_game,
    mostrar_flash,
)
from paginas.corrida import pagina_corrida
from paginas.escritorio import pagina_escritorio
from paginas.financas import pagina_financas
from paginas.hall import pagina_hall
from paginas.inicio import tela_inicial
from paginas.motores import pagina_motores
from paginas.pilotos import pagina_pilotos
from paginas.save import pagina_save
from ui import tema

st.set_page_config(page_title="Cockpit Manager", page_icon="🏎️", layout="wide", initial_sidebar_state="expanded")

# estado da sessão
if "game" not in st.session_state:
    st.session_state.game = None
if "menu" not in st.session_state:
    st.session_state.menu = MENUS[0]
if "fds" not in st.session_state:
    st.session_state.fds = None
if "flash" not in st.session_state:
    st.session_state.flash = None
if "tema_claro" not in st.session_state:
    st.session_state.tema_claro = False

# tema/CSS do jogo (tokens de fonte, componentes e acessibilidade) — ui/tema.py
tema.aplicar(claro=bool(st.session_state.tema_claro))


# ======================================================================
#  APP PRINCIPAL
# ======================================================================
game = st.session_state.game
if game is None:
    mostrar_flash()
    tela_inicial()
else:
    eqj = sim.equipe(game, game["equipe_jogador"])
    with st.sidebar:
        total_etapas = max(1, len(game["calendario"]))
        st.markdown(
            '<div class="side-brand"><div class="logo-mini">CM</div>'
            '<div><div class="b1">COCKPIT</div><div class="b2">MANAGER</div></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="side-team" style="background:linear-gradient(125deg,{eqj["cor"]} 0%, rgba(13,17,26,.94) 62%)">'
            f"{bnd.img_bandeira(eqj['bandeira'], 26)}"
            f'<div class="nome">{eqj["nome"]}</div>'
            f'<div class="meta">{meta_game(game).get("nome", "F1 2026")} · grid com {len(sim.titulares(game))} pilotos</div></div>',
            unsafe_allow_html=True,
        )
        st.progress(
            min(1.0, game["rodada"] / total_etapas),
            text=f"Temporada {game['ano']} · {game['rodada']}/{total_etapas} etapas concluídas",
        )
        tabela_p = sim.tabela_pilotos(game)
        pos_piloto = next((i + 1 for i, p in enumerate(tabela_p) if p["equipe_id"] == eqj["id"]), None)
        st.markdown(
            '<div class="side-stats">'
            f'<div class="side-stat"><div class="lab">Caixa</div>'
            f'<div class="val">{sim.fmt_dinheiro_m(eqj["caixa"]).replace("US$ ", "$")}</div></div>'
            f'<div class="side-stat"><div class="lab">Construtores</div>'
            f'<div class="val">{sim.posicao_equipe(game, eqj["id"])}º · {eqj["pontos"]} pts</div></div>'
            f'<div class="side-stat"><div class="lab">Melhor piloto</div>'
            f'<div class="val">{f"{pos_piloto}º" if pos_piloto else "—"}</div></div>'
            f'<div class="side-stat"><div class="lab">Etapa</div>'
            f'<div class="val">{min(game["rodada"] + 1, total_etapas)}/{total_etapas}</div></div></div>',
            unsafe_allow_html=True,
        )
        # próximo compromisso + atalho para a corrida
        if game["rodada"] < len(game["calendario"]):
            prox = game["calendario"][game["rodada"]]
            st.markdown(
                f'<div class="side-next">{bnd.img_bandeira(prox["bandeira"], 20)}'
                f'<div><div class="sn-gp">{prox["gp"]}</div>'
                f'<div class="sn-meta">{prox["circuito"]} · {prox["voltas"]} voltas</div></div></div>',
                unsafe_allow_html=True,
            )
            if st.button("🏁 Ir para a corrida", width="stretch", key="side_ir_corrida"):
                ir_para("🏁 Corrida")
        st.radio("Menu", MENUS, key="menu", label_visibility="collapsed")
        st.divider()
        st.toggle("☀️ Tema claro", key="tema_claro", help="Alterna entre o visual noturno e o claro.")
        auto = armazenamento.auto_save_info()
        if auto:
            st.caption(f"💾 Auto-save: etapa {auto['rodada']} · {auto['ano']} · {auto['modificado']}")
        else:
            st.caption("💾 O auto-save começa ao concluir a primeira etapa.")
        if st.button("🆕 Novo jogo", width="stretch"):
            st.session_state.novo_jogo_pendente = True
        if st.session_state.get("novo_jogo_pendente", False):
            exibir_confirmacao_novo_jogo()
        save_json = json.dumps(game, ensure_ascii=False)
        st.download_button(
            "⬇️ Baixar save (.json)",
            save_json,
            file_name=f"cockpit_save_{game['ano']}_etapa{game['rodada'] + 1}.json",
            mime="application/json",
            width="stretch",
        )
        st.caption(
            "Fan remake inspirado no Cockpit Manager '14 (Cartola Games) · "
            "[DB F1 2026](http://cockpitmanager.blogspot.com/2026/05/db-f1-2026-v10-by-jonathan-daniel.html)"
        )

    mostrar_flash()
    pagina = st.session_state.menu
    if pagina == "🏠 Escritório":
        pagina_escritorio(game)
    elif pagina == "🏁 Corrida":
        pagina_corrida(game)
    elif pagina == "🔧 Carro & Investimentos":
        pagina_carro(game)
    elif pagina == "👨‍✈️ Pilotos & Contratos":
        pagina_pilotos(game)
    elif pagina == "⚙️ Motores":
        pagina_motores(game)
    elif pagina == "💰 Patrocinadores & Finanças":
        pagina_financas(game)
    elif pagina == "📊 Campeonato":
        pagina_campeonato(game)
    elif pagina == "🏆 Hall da Fama & Conquistas":
        pagina_hall(game)
    elif pagina == "💾 Salvar / Carregar":
        pagina_save(game)
    else:
        pagina_ajuda()
