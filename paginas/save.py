# -*- coding: utf-8 -*-
"""Salvar / Carregar: slots locais (pasta `saves/`), auto-save e download do JSON."""

import streamlit as st

import armazenamento

from .comum import iniciar_novo_jogo, titulo_pagina


def _carregar_slot(nome: str) -> None:
    try:
        save, avisos = armazenamento.carregar(nome)
    except (OSError, ValueError) as e:
        st.error(f"Não consegui abrir esse slot: {e}")
        return
    st.session_state.game = save
    st.session_state.fds = None
    st.session_state.menu = "🏠 Escritório"
    for aviso in avisos:
        st.toast(aviso, icon="ℹ️")
    st.toast(f"Carreira carregada: {save['ano']}, etapa {save['rodada'] + 1}.", icon="✅")
    st.rerun()


def _tabela_slots(slots: list[dict]) -> None:
    st.dataframe(
        [
            {
                "Slot": s["nome"] + (" (auto)" if s["auto"] else ""),
                "Equipe": s["equipe"],
                "Ano": s["ano"],
                "Etapa": s["rodada"],
                "Versão": s["versao"],
                "Salvo": s["modificado"],
                "Tamanho": f"{s['tamanho_kb']} KB",
            }
            for s in slots
        ],
        hide_index=True,
        width="stretch",
    )


def pagina_save(game):
    titulo_pagina(
        "Sistema",
        "Salvar / Carregar",
        "Slots locais, auto-save a cada etapa e download do save para jogar em outra máquina.",
    )

    tab_slots, tab_download, tab_novo = st.tabs(["🗂️ Slots locais", "⬇️ Baixar / Compartilhar", "🆕 Nova carreira"])

    with tab_slots:
        st.subheader("💾 Salvar a carreira atual")
        c1, c2 = st.columns([3, 1])
        equipe = next((e for e in game["equipes"] if e["id"] == game["equipe_jogador"]), {})
        sugestao = f"{armazenamento.nome_seguro(equipe.get('nome', 'carreira'))}_{game['ano']}"
        nome = c1.text_input(
            "Nome do slot",
            value=f"carreira_{sugestao}",
            key="slot_nome",
            help="Vira um arquivo em saves/. Salvar com um nome existente sobrescreve o slot.",
        )
        if c2.button("Salvar", type="primary", width="stretch", key="slot_salvar"):
            caminho = armazenamento.salvar(game, nome)
            st.success(f"Salvo em `{caminho}`.")
            st.rerun()

        auto = armazenamento.auto_save_info()
        if auto:
            st.info(
                f"💾 **Auto-save** da etapa {auto['rodada']} ({auto['ano']}) — "
                f"{auto['modificado']}. Ele é atualizado ao fim de cada etapa."
            )
        else:
            st.caption("O auto-save é criado automaticamente ao concluir a primeira etapa.")

        st.subheader("📂 Carregar um slot")
        slots = armazenamento.listar_saves()
        if not slots:
            st.caption("Nenhum slot ainda — salve a carreira acima para vê-la aqui.")
        else:
            _tabela_slots(slots)
            nomes = [s["nome"] for s in slots]
            escolha = st.selectbox("Slot", nomes, key="slot_escolhido", format_func=lambda n: n)
            c1, c2 = st.columns(2)
            if c1.button("📥 Carregar este slot", width="stretch", key="slot_carregar"):
                _carregar_slot(escolha)
            if c2.button("🗑️ Apagar este slot", width="stretch", key="slot_apagar"):
                armazenamento.apagar(escolha)
                st.toast(f"Slot {escolha} apagado.", icon="🗑️")
                st.rerun()

    with tab_download:
        save_json = armazenamento.serializar(game, identado=True)
        st.download_button(
            "⬇️ Baixar save (.json)",
            save_json,
            file_name=f"cockpit_save_{game['ano']}_etapa{game['rodada'] + 1}.json",
            mime="application/json",
            type="primary",
        )
        st.caption(
            f"Formato **v{armazenamento.VERSAO_SAVE}** — guarde o arquivo e carregue na tela inicial "
            "para continuar a carreira em qualquer máquina. Saves antigos são migrados automaticamente."
        )

    with tab_novo:
        st.caption("A carreira desta sessão será encerrada (os slots em `saves/` não são afetados).")
        if st.checkbox("Entendo que começar um jogo novo apaga a carreira atual desta sessão"):
            if st.button("🗑️ Abandonar carreira e voltar ao início", type="primary"):
                iniciar_novo_jogo()
                st.rerun()
