# -*- coding: utf-8 -*-
"""Componentes e helpers compartilhados pelas páginas (títulos, painéis, chips, formatação)."""

import pandas as pd
import streamlit as st

import armazenamento
import bandeiras as bnd
import simulacao as sim

MENUS = [
    "🏠 Escritório",
    "🏁 Corrida",
    "🔧 Carro & Investimentos",
    "👨‍✈️ Pilotos & Contratos",
    "⚙️ Motores",
    "💰 Patrocinadores & Finanças",
    "📊 Campeonato",
    "🏆 Hall da Fama & Conquistas",
    "💾 Salvar / Carregar",
    "❓ Como Jogar",
]


CFG_BANDEIRA = {"Bandeira": st.column_config.ImageColumn("", width=38)}


ROTULOS_PAPEL = {
    "P1": "1o piloto",
    "P2": "2o piloto",
    "P3": "3o piloto",
    "P4": "4o piloto",
    "teste": "Testes/reserva",
    "livre": "Livre",
}


def ir_para(menu):
    st.session_state.menu = menu


def _continuar_da_corrida():
    """Pós-corrida → Escritório. Como `on_click` roda ANTES dos widgets da
    próxima execução, dá pra trocar o menu sem WidgetAlreadyInstantiated.
    Também é o ponto do AUTO-SAVE: a etapa acabou de ser gravada no save."""
    st.session_state.game["rodada"] += 1
    st.session_state.fds = None
    armazenamento.auto_salvar(st.session_state.game)
    ir_para("🏠 Escritório")


def botao_csv(df, arquivo: str, rotulo: str = "⬇️ Exportar CSV", key: str | None = None) -> None:
    """Botão de download de um DataFrame em CSV (Excel pt-BR: `;` + BOM)."""
    st.download_button(
        rotulo,
        armazenamento.csv_bytes(df),
        file_name=arquivo,
        mime="text/csv",
        key=key,
    )


def fmt_tempo(seg):
    m, s = divmod(seg, 60)
    return f"{int(m)}:{s:06.3f}"


def flash(tipo, texto):
    st.session_state.flash = (tipo, texto)


def iniciar_novo_jogo():
    st.session_state.game = None
    st.session_state.fds = None
    st.session_state.novo_jogo_pendente = False


def exibir_confirmacao_novo_jogo():
    st.warning(
        "A carreira atual será encerrada nesta sessão. Salve o jogo antes de continuar, se quiser retomá-lo depois."
    )
    col_cancelar, col_confirmar = st.columns(2)
    if col_cancelar.button("Cancelar", key="cancelar_novo_jogo", width="stretch"):
        st.session_state.novo_jogo_pendente = False
        st.rerun()
    if col_confirmar.button("Começar novo jogo", key="confirmar_novo_jogo", type="primary", width="stretch"):
        iniciar_novo_jogo()
        st.rerun()


def mostrar_flash():
    if st.session_state.flash:
        tipo, texto = st.session_state.flash
        getattr(st, tipo, st.info)(texto)
        st.session_state.flash = None


def titulo_pagina(kicker, titulo, subtitulo=None):
    sub = f"<p>{subtitulo}</p>" if subtitulo else ""
    st.markdown(
        f'<div class="page-head"><div class="kicker">{kicker}</div><h1>{titulo}</h1>{sub}</div>', unsafe_allow_html=True
    )


def cabecalho_inicial():
    st.markdown(
        """
    <div class="hero">
      <div class="hero-inner">
        <div class="logo-mark">CM</div>
        <div>
          <div class="kicker">Manager de automobilismo · Edição Streamlit</div>
          <h1>Cockpit Manager</h1>
          <p>Comande uma equipe temporada após temporada: pilotos, carro, fornecedores,
             patrocinadores, estratégia de corrida e mercado — sem limite de anos.</p>
        </div>
      </div>
      <div class="chips">
        <span class="chip hot">F1 2026</span><span class="chip hot">F1 Academy</span>
        <span class="chip">F1 Legends</span><span class="chip">Fórmula Indy</span>
        <span class="chip">Indy Legends</span><span class="chip">Stock Car</span>
        <span class="chip">DTM</span>
        <span class="chip">🛠️ Editor de DBs</span><span class="chip">👥 Grid a partir de 22</span>
      </div>
      <div class="checker"></div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def barra_stat(rotulo, valor, obs="", cor="#C8102E"):
    v = max(0.0, min(100.0, float(valor)))
    small = f"<small>{obs}</small>" if obs else ""
    st.markdown(
        f'<div class="stat"><div class="stat-top"><span>{rotulo}</span><strong>{v:.0f}</strong></div>'
        f'<div class="stat-track"><div class="stat-fill" style="width:{v:.0f}%;'
        f'background:linear-gradient(90deg,{cor},#E4636F)"></div></div>{small}</div>',
        unsafe_allow_html=True,
    )


def meta_game(game):
    return (game or {}).get("meta") or {}


def rot_fornecedor(game):
    return meta_game(game).get("rotulo_fornecedor", "Motor")


def rot_corrida2(game):
    return meta_game(game).get("rotulo_corrida2") or "Sprint"


def df_pilotos_equipe(game, equipe_id):
    linhas = []
    for p in sorted(
        [x for x in game["pilotos"] if x["equipe_id"] == equipe_id and not x["aposentado"]],
        key=lambda x: {"P1": 0, "P2": 1, "P3": 2, "P4": 3, "teste": 4}.get(x["papel"], 5),
    ):
        a = p["atributos"]
        linhas.append(
            {
                "Bandeira": bnd.url_bandeira(p["bandeira"]),
                "Piloto": p["nome"],
                "#": p["numero"],
                "Idade": p["idade"],
                "Função": ROTULOS_PAPEL.get(p["papel"], p["papel"]),
                "Overall": sim.overall(p),
                "Velocidade": a["velocidade"],
                "Chuva": a["chuva"],
                "Concentração": a["concentracao"],
                "Largada": a["largada"],
                "Ultrapassagem": a["ultrapassagem"],
                "Acerto": a["acerto"],
                "Físico": a["fisico"],
                "Forma": p["forma"],
                "Pontos": p["pontos"],
                "Salário": p["salario_corrida"],
                "Contrato": int(p.get("contrato_anos", 0)),
            }
        )
    return pd.DataFrame(linhas)


def barra_equipe(eq):
    st.markdown(
        f'<div class="team-bar" style="background:linear-gradient(112deg,{eq["cor"]} 0%, rgba(13,17,26,.93) 58%, #0D111A 100%)">'
        f'<div class="team-main"><div class="team-flag">{bnd.img_bandeira(eq["bandeira"], 44)}</div>'
        f'<div><div class="kicker">Sua equipe · {eq["pais"]}</div><h2>{eq["nome_completo"]}</h2>'
        f"<p>Prestígio {eq['prestigio']} · {eq.get('titulos_construtores', 0)} título(s) de construtores na história</p></div></div></div>",
        unsafe_allow_html=True,
    )


def _fmt_k_bruto(valor_k):
    """US$ mil no estilo do original: 'US$ 14.266'."""
    return f"US$ {valor_k:,.0f}".replace(",", ".")


def _plinha(k, v, v_cor=None):
    """Linha de painel: rótulo à esquerda, valor à direita (estilo CM14)."""
    cor = f' style="color:{v_cor}"' if v_cor else ""
    return f'<div class="plinha"><span class="k">{k}</span><b{cor}>{v}</b></div>'


def _painel(titulo, corpo):
    """Painel fechado (título + linhas) do Escritório."""
    st.markdown(f'<div class="painel"><h4>{titulo}</h4><div class="corpo">{corpo}</div></div>', unsafe_allow_html=True)


def _painel_ini(titulo):
    """Abre um painel que conterá widgets Streamlit (notícias, Continuar)."""
    st.markdown(f'<div class="painel"><h4>{titulo}</h4><div class="corpo">', unsafe_allow_html=True)


def _painel_fim():
    st.markdown("</div></div>", unsafe_allow_html=True)


def painel_fim_temporada(game):
    tab_p, tab_c = sim.tabela_pilotos(game), sim.tabela_construtores(game)
    st.success(f"🏁 **Fim da temporada {game['ano']}!**")
    if tab_p:
        camp = tab_p[0]
        st.markdown(
            f"🏆 Campeão de Pilotos: {bnd.img_bandeira(camp['bandeira'])} **{camp['nome']}** "
            f"({sim.equipe(game, camp['equipe_id'])['nome']}) — {camp['pontos']} pts",
            unsafe_allow_html=True,
        )
    if tab_c:
        st.markdown(
            f"🏭 Campeã de Construtores: {bnd.img_bandeira(tab_c[0]['bandeira'])} **{tab_c[0]['nome']}** — {tab_c[0]['pontos']} pts",
            unsafe_allow_html=True,
        )
    eqj = sim.equipe(game, game["equipe_jogador"])
    st.markdown(f"Sua equipe terminou em **{sim.posicao_equipe(game, eqj['id'])}º** com {eqj['pontos']} pontos.")
    if game["contratos_proxima"]:
        st.info(
            "✍️ Contratos já fechados para a próxima temporada: "
            + ", ".join(sim.piloto(game, pid)["nome"] for pid in game["contratos_proxima"])
        )
    else:
        st.warning(
            "Você não fechou nenhum contrato novo. Passe em **Pilotos & Contratos**, **Motores** e "
            "**Patrocinadores** antes de virar a temporada (renovações valem ouro!)."
        )
    if st.button("📅 Virar a temporada (mercado, evolução dos pilotos, carro novo)", type="primary", width="stretch"):
        res = sim.virar_temporada(game)
        st.session_state.fds = None
        flash(
            "success",
            f"Temporada {game['ano']} começou! Campeões de {game['ano'] - 1}: "
            f"{res['campeao_pilotos']} / {res['campea_construtores']}.",
        )
        st.balloons()
        st.rerun()
