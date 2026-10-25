# -*- coding: utf-8 -*-
"""Escritório: o resumo da equipe, como no CM14."""

import re

import streamlit as st

import armazenamento
import bandeiras as bnd
import simulacao as sim

from .comum import _fmt_k_bruto, _painel, _painel_fim, _painel_ini, _plinha, ir_para, painel_fim_temporada, rot_corrida2, rot_fornecedor
from .corrida import obter_fds

def linha_tempo(game):
    """Timeline horizontal do calendário: etapas concluídas, a próxima e as futuras."""
    itens = []
    for i, et in enumerate(game["calendario"]):
        if i < game["rodada"]:
            estado = "done"
        elif i == game["rodada"]:
            estado = "agora"
        else:
            estado = "futuro"
        sprint = '<span class="tl-sprint">⚡</span>' if et.get("sprint") else ""
        dica = f"{et['gp']} · {et['circuito']} · {et['data']}"
        itens.append(
            f'<div class="tl-item {estado}" title="{dica}">'
            f'<div class="tl-dot">{i + 1}</div>'
            f'<div class="tl-gp">{et["gp"]}{sprint}</div></div>'
        )
    return '<div class="timeline-wrap"><div class="timeline">' + "".join(itens) + "</div></div>"


def pagina_escritorio(game):
    """Escritório fiel ao CM14: cabeçalho (gerente · ano · etapa / equipe) e
    painéis Carro, Contratos, Pilotos, Finanças, Notícias e Próxima corrida."""
    eqj = sim.equipe(game, game["equipe_jogador"])
    fim = game["rodada"] >= len(game["calendario"])
    mot = sim.motor(game, eqj["motor_id"])
    gerente = str(game.get("gerente", "") or "").strip()
    etapa_n = min(game["rodada"] + 1, len(game["calendario"]))
    quem = f"{gerente} " if gerente else ""
    pos_eq = sim.posicao_equipe(game, eqj["id"])
    st.markdown(
        f'<div class="office-head"><div class="quem">{quem}{game["ano"]}, {etapa_n}ª etapa</div>'
        f'<div class="time">{eqj["nome"]}</div>'
        f'<div class="office-meta">{bnd.img_bandeira(eqj["bandeira"], 22)}'
        f'<span class="om"><b>{pos_eq}º</b> construtores</span>'
        f'<span class="om"><b>{eqj["pontos"]}</b> pts</span>'
        f'<span class="om"><b>{eqj["vitorias"]}</b> vitórias</span>'
        f'<span class="om"><b>{sim.fmt_dinheiro_m(eqj["caixa"])}</b> caixa</span></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(linha_tempo(game), unsafe_allow_html=True)
    st.caption(
        f"🗓️ {game['rodada']} de {len(game['calendario'])} etapas concluídas · "
        "⚡ = fim de semana com corrida extra (sprint). Passe o mouse para ver circuito e data."
    )
    if fim:
        painel_fim_temporada(game)
        return

    col1, col2, col3 = st.columns([1.05, 1.0, 1.0], gap="medium")

    with col1:
        ex = sim.eixos_carro(eqj)
        conf = ex["confiabilidade"]
        conf_cor = "#4ADE80" if conf >= 85 else ("#FACC15" if conf >= 75 else "#F87171")
        _painel(
            "Carro",
            "".join(
                [
                    _plinha("Aerodinâmica", f"{ex['aerodinamica']}%"),
                    _plinha("Caixa de câmbio", f"{ex['cambio']}%"),
                    _plinha("Freio", f"{ex['freio']}%"),
                    _plinha("Sistema elétrico", f"{ex['eletrico']}%"),
                    _plinha("Direção", f"{ex['direcao']}%"),
                    _plinha("Confiabilidade", f"{conf}%", conf_cor),
                ]
            ),
        )
        _painel(
            "Contratos",
            _plinha(
                rot_fornecedor(game),
                f"{bnd.img_bandeira(eqj['bandeira'], 16)} {mot['nome']}"
                + (" (próprio)" if eqj.get("motor_proprio") else ""),
            ),
        )

    with col2:
        rot_p = {"P1": "1º Piloto", "P2": "2º Piloto", "P3": "3º Piloto", "P4": "4º Piloto"}
        tits = sorted(
            [p for p in game["pilotos"] if p["equipe_id"] == eqj["id"] and not p["aposentado"] and p["papel"] in rot_p],
            key=lambda p: list(rot_p).index(p["papel"]),
        )
        corpo_p = "".join(
            _plinha(rot_p[p["papel"]], f"{bnd.img_bandeira(p['bandeira'], 16)} {p['nome']}") for p in tits
        )
        teste = sim.piloto_teste(game, eqj["id"])
        if teste:
            corpo_p += _plinha("P. Testes", f"{bnd.img_bandeira(teste['bandeira'], 16)} {teste['nome']}")
        _painel("Pilotos", corpo_p or '<span class="k">Sem pilotos registrados.</span>')

        fa = game.get("financas_ano") or {}
        if int(fa.get("ano", -1)) != int(game["ano"]):
            fa = {"ano": int(game["ano"]), "receitas": 0.0, "despesas": 0.0}
        bal = round(float(fa["receitas"]) - float(fa["despesas"]), 1)
        bal_cor = "#4ADE80" if bal >= 0 else "#F87171"
        _painel(
            "Finanças",
            "".join(
                [
                    _plinha("Receitas", _fmt_k_bruto(float(fa["receitas"]))),
                    _plinha("Despesas", _fmt_k_bruto(float(fa["despesas"]))),
                    _plinha(f"Balanço {game['ano']}", _fmt_k_bruto(bal), bal_cor),
                    _plinha("Caixa", _fmt_k_bruto(round(float(eqj["caixa"]) * 1000.0, 1))),
                ]
            ),
        )

    with col3:
        novas = max(0, len(game["noticias"]) - int(game.get("noticias_lidas", 0)))
        aberto = bool(st.session_state.get("ver_noticias", False))
        _painel_ini("Notícias")
        uma = novas == 1
        rot_novo = (
            (f"📰 Você tem {novas} nova{'s' if not uma else ''} notíci{'as' if not uma else 'a'}")
            if novas > 0
            else "📰 Ver notícias"
        )
        if st.button(rot_novo, key="btn_noticias", width="stretch"):
            st.session_state.ver_noticias = not aberto
            if not aberto:
                game["noticias_lidas"] = len(game["noticias"])
            st.rerun()
        if aberto:
            if not game["noticias"]:
                st.caption("Sem notícias no paddock.")
            for n in game["noticias"][:8]:
                _txt = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", bnd.substituir_emojis(n["texto"]))
                st.markdown(
                    f'<div class="news-card"><span class="small">{n["ano"]} · '
                    f"etapa {n['rodada']}</span><br>{_txt}</div>",
                    unsafe_allow_html=True,
                )
        _painel_fim()

        etapa = game["calendario"][game["rodada"]]
        fds_prox = obter_fds(game, etapa)
        clima_txt = "🌧️ Molhado" if fds_prox["molhado"] else "☀️ Seco"
        _painel_ini("Próxima corrida")
        st.markdown(
            _plinha("Circuito", etapa["circuito"])
            + _plinha("Grande Prêmio", f"{bnd.img_bandeira(etapa['bandeira'], 16)} {etapa['gp']}")
            + _plinha("Data", etapa["data"])
            + _plinha("Voltas", str(etapa["voltas"]))
            + _plinha("Clima", clima_txt)
            + _plinha("Estratégia típica", f"{sim.paradas_ideais(etapa)} parada(s)")
            + (_plinha("Formato", f"⚡ {rot_corrida2(game)} + principal") if etapa["sprint"] else ""),
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="previsao-tempo" style="margin:8px 0 6px">'
            f"<b>Previsão</b> · {sim.previsao_texto(fds_prox.get('clima'))}</div>",
            unsafe_allow_html=True,
        )
        st.button(
            "▶️ CONTINUAR",
            type="primary",
            width="stretch",
            on_click=ir_para,
            args=("🏁 Corrida",),
            help=f"{etapa['gp']} — {etapa['circuito']} · {etapa['pais']}",
        )
        _painel_fim()

    # ---------------- modo temporada rápida (sem transmissão)
    restantes = len(game["calendario"]) - game["rodada"]
    with st.expander("⏩ Simular etapas em lote (sem transmissão)"):
        st.caption(
            "Roda as próximas etapas direto no motor — sprint, classificação e corrida — "
            "com a estratégia padrão da equipe. O auto-save é atualizado no fim."
        )
        quantas = st.slider("Quantas etapas simular", 1, max(1, restantes), 1, key="lote_n")
        if st.button("▶️ Simular agora", type="primary", key="lote_simular"):
            resumos = sim.simular_etapas(game, quantas)
            armazenamento.auto_salvar(game)
            st.session_state.lote_resumo = resumos
            st.rerun()
        resumos = st.session_state.get("lote_resumo") or []
        if resumos:
            st.dataframe(
                [
                    {
                        "Etapa": r["rodada"],
                        "GP": r["gp"],
                        "Clima": "🌧️" if r["molhado"] else "☀️",
                        "Vencedor": r["vencedor"],
                        "Sua melhor posição": r["minha_melhor_pos"] or "—",
                    }
                    for r in resumos
                ],
                hide_index=True,
                width="stretch",
            )
            st.caption("Resumo das últimas etapas simuladas em lote. O campeonato já está atualizado.")
