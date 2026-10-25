# -*- coding: utf-8 -*-
"""Corrida: treino, classificação, transmissão ao vivo, rádio e resumo pós-prova."""

import os
import time

import pandas as pd
import streamlit as st

import bandeiras as bnd
import simulacao as sim

from .comum import (
    CFG_BANDEIRA,
    ROTULOS_PAPEL,
    _continuar_da_corrida,
    botao_csv,
    flash,
    fmt_tempo,
    painel_fim_temporada,
    rot_corrida2,
)

# a página vive em paginas/, mas os arquivos estáticos ficam na raiz do projeto
RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATALHOS_HTML = os.path.join(RAIZ_PROJETO, "static", "atalhos.html")


def obter_fds(game, etapa):
    chave = f"{game['ano']}-{game['rodada']}"
    if not st.session_state.fds or st.session_state.fds.get("chave") != chave:
        molhado = sim.sortear_clima(game, etapa)
        st.session_state.fds = {
            "chave": chave,
            "molhado": molhado,
            "clima": sim.plano_clima(game, etapa, molhado),
            "grid": None,
            "sprint": None,
            "resultado": None,
            "resumo": None,
            "eventos": [],
            "treino": None,
            "treino_ok": False,
            "replay": None,
            "paddock_ok": False,
            "passo_ui": None,
        }
    return st.session_state.fds


def df_grid(game, grid):
    return pd.DataFrame(
        [
            {
                "Pos": g["pos"],
                "Bandeira": bnd.url_bandeira(sim.piloto(game, g["piloto_id"])["bandeira"]),
                "Piloto": sim.piloto(game, g["piloto_id"])["nome"],
                "Equipe": sim.equipe(game, g["equipe_id"])["nome"],
                "": "⭐" if g["equipe_id"] == game["equipe_jogador"] else "",
                "Tempo": fmt_tempo(g["tempo"]),
                "Gap": "—" if g["gap"] == 0 else f"+{g['gap']:.3f}",
            }
            for g in grid
        ]
    )


def df_resultado(game, resultado):
    linhas = []
    for l in resultado:
        p = sim.piloto(game, l["piloto_id"])
        est = l["estrategia"]
        linhas.append(
            {
                "Pos": l["pos"],
                "Bandeira": bnd.url_bandeira(p["bandeira"]),
                "Piloto": p["nome"],
                "Equipe": sim.equipe(game, l["equipe_id"])["nome"],
                "": "⭐" if l["equipe_id"] == game["equipe_jogador"] else "",
                "Grid": l["grid"],
                "▲▼": l["grid"] - l["pos"],
                "Pneu": est["pneu"],
                "Paradas": est["paradas"],
                "Ritmo": est["ritmo"],
                "Gap/Status": l["status"] if l["dnf"] else ("Vencedor" if l["pos"] == 1 else f"+{l['gap_seg']:.1f}s"),
                "VR": "⚡" if l.get("volta_rapida") else "",
                "Pontos": l["pontos"],
            }
        )
    return pd.DataFrame(linhas)


def _cor_texto(hex_cor):
    """Texto legível (preto/branco) para o fundo colorido da equipe."""
    try:
        c = str(hex_cor).lstrip("#")
        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        return "#0B0E14" if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "#FFFFFF"
    except Exception:
        return "#FFFFFF"


def _chip_equipe(eq):
    return f'<span class="eq-chip" style="background:{eq["cor"]};color:{_cor_texto(eq["cor"])}">{eq["nome"]}</span>'


def _barra_html(pct):
    cor = "#22C55E" if pct > 0.5 else ("#EAB308" if pct > 0.25 else "#EF4444")
    return f'<div class="barra"><i style="width:{pct * 100:.0f}%;background:{cor}"></i></div>'


def _clima_txt(molhado):
    return "🌧️ Molhado" if molhado else "☀️ Ensolarado"


def _tyre_badge(pneu):
    """Composto como bolinha colorida + letra (S/M/H/I/W), com tooltip."""
    cores = {
        "Macio": ("#E02444", "S"),
        "Médio": ("#EAB308", "M"),
        "Duro": ("#E5E7EB", "H"),
        "Intermediário": ("#22C55E", "I"),
        "Chuva extrema": ("#3B82F6", "W"),
    }
    cor, letra = cores.get(pneu, ("#94A3B8", "?"))
    return f'<span class="tyre" title="{pneu}" style="--t:{cor}"><i></i>{letra}</span>'


def _delta_pos(atual, grid):
    """Seta de posições ganhas/perdidas em relação ao grid."""
    if not grid:
        return '<span class="dpos eq">•</span>'
    d = int(grid) - int(atual)
    if d > 0:
        return f'<span class="dpos up">▲{d}</span>'
    if d < 0:
        return f'<span class="dpos dn">▼{abs(d)}</span>'
    return '<span class="dpos eq">=</span>'


def _html_tabela_viva(game, linhas, mostrar_pits=False, meus_ids=(), grids=None, mostra_delta=False):
    """Torre de tempos da transmissão: faixa na cor da equipe, setas de
    posição, composto como bolinha colorida, barra de diferença e destaque
    para os seus carros."""
    grids = grids or {}
    th = ["Pos.", "Nome", "Equipe", "Últ. volta", "Dif. ant.", "Dif 1º"]
    if mostrar_pits:
        th += ["Pneu", "Paradas"]
    cab = "".join(f"<th>{t}</th>" for t in th)

    validos = [l for l in linhas if not l.get("fora") and l.get("dif1") is not None]
    max_gap = max((l["dif1"] for l in validos), default=0.0) or 1.0

    corpo = []
    for l in linhas:
        p = sim.piloto(game, l["pid"])
        eq = sim.equipe(game, l["equipe_id"])
        pos = l["pos"]
        classes = []
        if l["pid"] in meus_ids:
            classes.append("meu")
        if l.get("fora"):
            classes.append("fora")
        if pos == 1 and not l.get("fora"):
            classes.append("lider")
        tr = f'<tr class="{" ".join(classes)}" style="--eq:{eq["cor"]}">' if classes else f'<tr style="--eq:{eq["cor"]}">'

        cls_pos = "pos" + (" p1" if pos == 1 else " p2" if pos == 2 else " p3" if pos == 3 else "")
        delta = _delta_pos(pos, grids.get(l["pid"])) if mostra_delta and not l.get("fora") else ""
        eu = '<span class="tag-vc">VC</span>' if l["pid"] in meus_ids else ""

        if l.get("fora"):
            ult = f"💥 {l['fora']}"
        elif l.get("box"):
            ult = f'<span class="badge-box">BOX</span> {fmt_tempo(l["tempo"])}'
        else:
            ult = fmt_tempo(l["tempo"]) if l.get("tempo") is not None else "—"

        dif_ant = "—" if l.get("dif_ant") is None else f"+{l['dif_ant']:.1f}"
        if l.get("dif1") is None or pos == 1:
            dif1 = "—" if l.get("dif1") is None else '<span class="gap-lider">LÍDER</span>'
            barra = ""
        else:
            pct = max(2.0, min(100.0, l["dif1"] / max_gap * 100))
            dif1 = f"+{l['dif1']:.1f}"
            barra = f'<div class="gap-bar"><i style="width:{pct:.0f}%"></i></div>'

        extra = ""
        if mostrar_pits:
            extra = (f'<td>{_tyre_badge(l.get("pneu", "—"))}</td>'
                     f'<td>{l.get("pits", 0)}/{l.get("paradas", 0)}</td>')

        corpo.append(
            f'{tr}<td class="{cls_pos}"><span class="pos-n">{pos}</span>{delta}</td>'
            f'<td class="nome-cel">{p["nome"]}{eu}</td>'
            f'<td>{_chip_equipe(eq)}</td><td class="mono">{ult}</td>'
            f'<td class="mono">{dif_ant}</td>'
            f'<td class="mono">{dif1}{barra}</td>{extra}</tr>'
        )
    return (
        '<div class="sessao-card tabela-wrap" style="padding-top:8px">'
        f'<table class="tbl-viva"><thead><tr>{cab}</tr></thead>'
        f"<tbody>{''.join(corpo)}</tbody></table></div>"
    )


def _html_tabela_treino(game, grid, sessao, minuto):
    """Tabela do treino: ordem pelo melhor tempo do minuto atual; ao fim
    (minuto 60) os tempos batem exatamente com o grid do motor."""
    entries = []
    for g in grid:
        t = sim.melhor_tempo_treino(sessao, g["piloto_id"], minuto) if sessao else None
        entries.append((g, t))
    entries.sort(key=lambda e: (e[1] is None, e[1] if e[1] is not None else 0.0, e[0]["pos"]))
    corpo = []
    lider = entries[0][1] if entries and entries[0][1] is not None else None
    for i, (g, t) in enumerate(entries):
        p = sim.piloto(game, g["piloto_id"])
        eq = sim.equipe(game, g["equipe_id"])
        meu = g["equipe_id"] == game["equipe_jogador"]
        classes = []
        if meu:
            classes.append("meu")
        if i == 0:
            classes.append("lider")
        tr = f'<tr class="{" ".join(classes)}" style="--eq:{eq["cor"]}">' if classes else f'<tr style="--eq:{eq["cor"]}">'
        pos = i + 1
        cls_pos = "pos" + (" p1" if pos == 1 else " p2" if pos == 2 else " p3" if pos == 3 else "")
        tempo_txt = fmt_tempo(t) if t is not None else "—"
        gap = ""
        if t is not None and lider is not None and i > 0:
            gap = f'<div class="gap-txt">+{t - lider:.3f}</div>'
        eu = '<span class="tag-vc">VC</span>' if meu else ""
        corpo.append(
            f'{tr}<td class="{cls_pos}"><span class="pos-n">{pos}</span></td>'
            f'<td class="nome-cel">{p["nome"]}{eu}</td>'
            f"<td>{_chip_equipe(eq)}</td><td class=\"mono\">{tempo_txt}{gap}</td></tr>"
        )
    cab = "<th>Pos.</th><th>Nome</th><th>Equipe</th><th>Melhor tempo</th>"
    return (
        '<div class="sessao-card tabela-wrap" style="padding-top:8px">'
        f'<table class="tbl-viva"><thead><tr>{cab}</tr></thead>'
        f"<tbody>{''.join(corpo)}</tbody></table></div>"
    )


@st.fragment(run_every=0.5)
def _frag_treino(game, etapa, molhado, fds):
    """Relógio da sessão de treino (60 min em ~15 s): barra e tempos ao vivo."""
    sess = fds.get("treino")
    if not sess or fds.get("grid") is None or sess.get("t0") is None:
        return
    dur = int(sess["duracao"])
    minuto = min(dur, int((time.time() - float(sess["t0"])) * dur / 15.0))
    if minuto >= dur:
        sess["concluido"] = True
        st.rerun()
    restante = dur - minuto
    c1, c2 = st.columns([3.2, 1])
    c1.progress(minuto / dur, text=f"⏱️ Tempo de treino restante: {restante} min")
    c2.markdown(f"**Clima:** {_clima_txt(molhado)}")
    st.markdown(_html_tabela_treino(game, fds["grid"], sess, minuto), unsafe_allow_html=True)
    if st.button("⏭️ Concluir treino agora", key="concluir_treino"):
        sess["t0"] = time.time() - 16.0
        st.rerun()


def _rot_pneu(p):
    """Rótulo de composto com durabilidade base, como no original: 'Duro (33 voltas)'."""
    return f"{p} ({int(sim.PNEUS_DURACAO.get(p, 24))} voltas)"


def _pit_dismiss():
    """X/ESC recusa parada planejada ou ignora aviso de pneu no stint atual."""
    fds = st.session_state.get("fds")
    if not (isinstance(fds, dict) and fds.get("replay")):
        return
    stt = fds["replay"]
    ped = _pit_pedido(stt)
    if ped and ped.get("planejada"):
        pid, volta = ped.get("pid"), int(ped.get("volta") or 0)
        rec = stt.setdefault("pits_recusados", {}).setdefault(pid, [])
        if volta and volta not in rec:
            rec.append(volta)
        nome = "seu piloto"
        try:
            nome = sim.piloto(st.session_state.get("game") or {}, pid)["nome"]
        except Exception:
            pass
        stt.setdefault("feed", []).append(
            f"🚪 Janela do box fechada sem troca — **{nome}** segue na pista (volta {volta})."
        )
    elif ped and ped.get("esgotado"):
        pid, volta = ped.get("pid"), int(ped.get("volta") or 0)
        feitos = [x for x in stt["pits"].get(pid, []) if x <= volta]
        stt.setdefault("pneus_esgotados_recusados", {})[pid] = len(feitos)
        stt.setdefault("feed", []).append(
            f"🚪 Janela fechada sem troca — o piloto segue na pista com o pneu esgotado (volta {volta})."
        )
    stt["pit_aberto"] = None


def _atalhos_corrida():
    """Atalhos de teclado da corrida (espaço pausa, 1/2/4 velocidade, P/O box).

    O script vive em `static/atalhos.html` e clica nos botões da própria página.
    Degrada em silêncio: sem o arquivo ou com o iframe bloqueado, os botões
    continuam funcionando normalmente."""
    try:
        if os.path.isfile(ATALHOS_HTML):
            st.iframe(ATALHOS_HTML, height=0)
    except Exception:  # noqa: BLE001 — atalhos são acessório, nunca derrubam a tela
        pass


def _chip_pista(plano, lap):
    """Chip com a condição da pista na volta atual + aviso de virada próxima."""
    cond = sim.condicao_pista(plano, lap)
    icone = "🌧️ Pista molhada" if cond == "molhado" else "☀️ Pista seca"
    extra = ""
    v = (plano or {}).get("virada_volta")
    if v:
        destino = (plano or {}).get("virada_para")
        alvo = "chuva" if destino == "molhado" else "pista secando"
        if lap < v:
            extra = f" · {alvo} por volta de {v}"
        elif lap < v + 4:
            extra = f" · {alvo} agora!"
    return f'<span class="pista-chip {cond}">{icone} · volta {lap}{extra}</span>'


def _pit_pedido(stt):
    """Normaliza o pedido de box aberto: {pid, volta, planejada} ou None."""
    ped = stt.get("pit_aberto")
    if not ped:
        return None
    if isinstance(ped, dict):
        return ped
    # compatibilidade: versões antigas guardavam só o id do piloto
    return {"pid": ped, "volta": int(stt.get("lap") or 1), "planejada": False}


@st.dialog("Pit Stop", width="small", on_dismiss=_pit_dismiss)
def _pit_dialog(game, etapa, molhado, fds, meus, lap, voltas):
    """Janela de box que aparece em TODA parada: pergunta se troca o pneu
    (e qual composto) e qual será o ritmo do próximo stint. A corrida fica
    congelada enquanto a janela está aberta; nada é executado sem resposta."""
    stt = fds["replay"]
    ped = _pit_pedido(stt)
    if ped is None:
        return
    pid = ped.get("pid")
    p = next((x for x in meus if x["id"] == pid), None)
    if p is None or stt.get("concluido"):
        stt["pit_aberto"] = None
        return
    planejada = bool(ped.get("planejada", False))
    esgotado = bool(ped.get("esgotado", False))
    volta_pit = int(ped.get("volta") or lap)
    st.markdown('<div class="pit-titulo">Pit Stop</div>', unsafe_allow_html=True)
    st.markdown(f"**Piloto:** {bnd.img_bandeira(p['bandeira'], 18)} {p['nome']}", unsafe_allow_html=True)
    if planejada:
        st.markdown(
            f'<div class="radio-box">📻 <b>Muro:</b> {p["nome"]}, hora do pit stop '
            f"(volta {volta_pit}/{voltas}). <b>Trocar de pneu?</b></div>",
            unsafe_allow_html=True,
        )
    elif esgotado:
        st.markdown(
            f'<div class="radio-box">📻 <b>Muro:</b> {p["nome"]}, o pneu acabou na volta '
            f"{volta_pit}/{voltas}. <b>Entrar no box?</b></div>",
            unsafe_allow_html=True,
        )
    else:
        st.caption(f"Ordem do comando na volta {lap} de {voltas}.")
    exec_pits = [x for x in stt["pits"].get(pid, []) if x <= lap]
    seq = stt["rep"]["info"][pid]["pneus"]
    prox = seq[min(len(exec_pits) + 1, len(seq) - 1)]
    plano_clima = fds.get("clima")
    cond = sim.condicao_pista(plano_clima, volta_pit or lap)
    molhado_agora = cond == "molhado"
    opcoes = sim.PNEUS_MOLHADO + sim.PNEUS_SECO if molhado_agora else sim.PNEUS_SECO
    pneu = st.selectbox(
        "Novos pneus",
        opcoes,
        format_func=_rot_pneu,
        index=opcoes.index(prox) if prox in opcoes else 0,
        key=f"dlg_pneu_{pid}_{fds['chave']}",
    )
    st.markdown(_chip_pista(plano_clima, volta_pit or lap), unsafe_allow_html=True)
    if molhado_agora and pneu in sim.PNEUS_SECO:
        st.error("⚠️ Slick na chuva — vai perder muito tempo na volta de saída.")
    if not molhado_agora and pneu in sim.PNEUS_MOLHADO:
        st.error("⚠️ Pneu de chuva no seco derrete em poucas voltas.")
    ritmo_atual = (stt.get("ritmos") or {}).get(pid, "Normal")
    ritmo = st.radio(
        "Ritmo do próximo stint",
        sim.RITMOS,
        index=sim.RITMOS.index(ritmo_atual),
        horizontal=True,
        help="Atacar = voltas mais rápidas e mais desgaste; Conservar = protege o pneu novo e o carro.",
        key=f"dlg_ritmo_{pid}_{fds['chave']}",
    )
    # projeção de posição: quanto custa parar agora
    pneus_man = stt.get("pneus_manual") or {}
    rit_stt = stt.get("ritmos") or {}
    overcut_stt = stt.get("overcut_ativo") or {}
    linhas_agora = sim.linhas_replay(stt["rep"], lap, stt["pits"], pneus_man, rit_stt, overcut_stt)
    pos_agora = next((ln["pos"] for ln in linhas_agora if ln["pid"] == pid), None)
    pits_novo = {k: list(v) for k, v in stt["pits"].items()}
    pits_novo[pid] = sorted(set(pits_novo.get(pid, []) + [volta_pit]))
    linhas_depois = sim.linhas_replay(stt["rep"], lap, pits_novo, pneus_man, rit_stt, overcut_stt)
    pos_depois = next((ln["pos"] for ln in linhas_depois if ln["pid"] == pid), None)
    if pos_agora and pos_depois:
        delta = pos_depois - pos_agora
        txt = "mantém a posição" if delta == 0 else (f"perde {delta}" if delta > 0 else f"ganha {abs(delta)}")
        st.markdown(
            f'<div class="proj-box"><b>Posição:</b> P{pos_agora} agora → '
            f'<b>P{pos_depois}</b> saindo do box <span class="proj-delta">{txt}</span></div>',
            unsafe_allow_html=True,
        )
    st.caption(f"Volta atual: **{lap} / {voltas}** · pneu no carro: **{prox}** · ritmo atual: **{ritmo_atual}**")
    if st.button("Trocar pneu e voltar ✓", type="primary", width="stretch", key=f"dlg_confirma_{pid}_{fds['chave']}"):
        feitas = stt["pits"].setdefault(pid, [])
        if volta_pit not in feitas:
            feitas.append(volta_pit)
            feitas.sort()
        n = len([x for x in feitas if x <= volta_pit])
        stt.setdefault("pneus_manual", {}).setdefault(pid, {})[n] = pneu
        stt.setdefault("ritmos", {})[pid] = ritmo
        stt.setdefault("undercut_ativo", {}).pop(pid, None)
        stt.setdefault("feed", []).append(
            f"🛠️ Box para **{p['nome']}** na volta {volta_pit} → pneu **{pneu}** · ritmo **{ritmo}**."
        )
        stt["pit_aberto"] = None
        st.rerun()
    rotulo_fora = "Continuar na pista ✕" if planejada or esgotado else "Cancelar ordem ✕"
    if st.button(rotulo_fora, width="stretch", key=f"dlg_cancela_{pid}_{fds['chave']}"):
        if planejada:
            rec = stt.setdefault("pits_recusados", {}).setdefault(pid, [])
            if volta_pit not in rec:
                rec.append(volta_pit)
            stt.setdefault("ritmos", {})[pid] = ritmo
            stt.setdefault("feed", []).append(
                f"🚫 **{p['nome']}** dispensou o box na volta {volta_pit} e segue na "
                f"pista com pneu **{prox}** · ritmo **{ritmo}**."
            )
        elif esgotado:
            feitos = [x for x in stt["pits"].get(pid, []) if x <= volta_pit]
            stt.setdefault("pneus_esgotados_recusados", {})[pid] = len(feitos)
            stt.setdefault("ritmos", {})[pid] = ritmo
            stt.setdefault("feed", []).append(
                f"🚫 **{p['nome']}** continuou na pista na volta {volta_pit} mesmo com o pneu esgotado."
            )
        else:
            stt.setdefault("feed", []).append(f"🚫 Ordem de box cancelada para **{p['nome']}** na volta {lap}.")
        stt["pit_aberto"] = None
        st.rerun()


@st.fragment(run_every=0.4)
def _frag_corrida(game, etapa, molhado, fds, meus):
    """Corrida ao vivo: volta a volta (replay fiel ao resultado do motor),
    boxes manuais/automáticos, vida dos pneus e feed de eventos."""
    stt = fds.get("replay")
    if not stt or stt.get("concluido"):
        return
    rep = stt["rep"]
    voltas = int(rep["voltas"])
    agora = time.time()
    pausado = bool(stt.get("pausado"))
    if (_pit_pedido(stt) is not None or pausado) and not stt.get("pulou"):
        # corrida congelada: janela do box aberta ou pausa pedida pelo chefe
        pausa = float(stt.setdefault("pausa_t0", agora))
        stt["t0"] = float(stt["t0"]) + max(0.0, agora - pausa)
        stt["pausa_t0"] = agora
    else:
        stt.pop("pausa_t0", None)
    velocidade = int(stt.get("velocidade") or 1)
    s_por_volta = max(0.2, min(0.55, 24.0 / max(1, voltas)))
    if stt.get("pulou"):
        lap = voltas
    else:
        lap = min(voltas, int((agora - float(stt["t0"])) / s_por_volta * velocidade))
    lap = max(1, lap)
    # 🟥 bandeira vermelha: a prova para na volta do acidente e só volta na relargada
    red_lap = rep.get("red_lap")
    if red_lap and lap >= red_lap and not stt.get("red_ok") and not stt.get("pulou"):
        if lap > red_lap:
            stt["t0"] = agora - (s_por_volta * red_lap) / max(1, velocidade)
        lap = red_lap
    stt["lap"] = lap
    feed = stt.setdefault("feed", [])
    perguntar = stt.setdefault("pit_perguntar", {})
    recusadas = stt.setdefault("pits_recusados", {})
    meus_ids = {p["id"] for p in meus}
    # rivais param sozinhos; os seus pilotos recebem a janela (ou param sozinhos
    # se o "Perguntar em cada pit stop" do Paddock foi desmarcado)
    auto = {pid: True if pid not in meus_ids else not perguntar.get(pid, True) for pid in rep["info"]}
    sim.auto_pits(rep, lap, stt["pits"], auto, recusadas)
    if _pit_pedido(stt) is None and lap < voltas and not pausado:
        pend = sim.pits_pendentes(
            rep, lap, stt["pits"], recusadas, {pid: perguntar.get(pid, True) for pid in meus_ids}, apenas=meus_ids
        )
        for pid_pend, volta_pend in pend:
            if lap - volta_pend > 2:
                # janela vencida (aba em segundo plano): o piloto já passou do box
                rec = recusadas.setdefault(pid_pend, [])
                if volta_pend not in rec:
                    rec.append(volta_pend)
                    feed.append(
                        f"⌛ Janela do box perdida na volta {volta_pend} — "
                        f"**{sim.piloto(game, pid_pend)['nome']}** seguiu na pista."
                    )
                continue
            stt["pit_aberto"] = {"pid": pid_pend, "volta": volta_pend, "planejada": True}
            stt["pausa_t0"] = time.time()  # congela a prova já nesta volta
            st.session_state.pop(f"dlg_pneu_{pid_pend}_{fds['chave']}", None)
            st.session_state.pop(f"dlg_ritmo_{pid_pend}_{fds['chave']}", None)
            break
        if _pit_pedido(stt) is None:
            recusas_esgotado = stt.setdefault("pneus_esgotados_recusados", {})
            pneus_man = stt.get("pneus_manual", {})
            ritmos = stt.get("ritmos", {})
            for pid_esgotado in sim.pneus_esgotados(
                etapa, rep, lap, stt["pits"], pneus_man, ritmos, apenas=meus_ids
            ):
                feitos = [x for x in stt["pits"].get(pid_esgotado, []) if x <= lap]
                if recusas_esgotado.get(pid_esgotado) == len(feitos):
                    continue
                stt["pit_aberto"] = {
                    "pid": pid_esgotado,
                    "volta": lap,
                    "planejada": False,
                    "esgotado": True,
                }
                stt["pausa_t0"] = time.time()
                st.session_state.pop(f"dlg_pneu_{pid_esgotado}_{fds['chave']}", None)
                st.session_state.pop(f"dlg_ritmo_{pid_esgotado}_{fds['chave']}", None)
                break
    marcados = stt.setdefault("feed_dnf", [])
    for pid, d in rep["info"].items():
        if d["dnf"] and d["volta_dnf"] <= lap and pid not in marcados:
            marcados.append(pid)
            feed.append(
                f"💥 {sim.piloto(game, pid)['nome']} abandonou: {d['motivo'].lower()} na volta {d['volta_dnf']}."
            )
    if rep.get("sc_lap") and lap >= rep["sc_lap"] and not stt.get("sc_ok"):
        stt["sc_ok"] = True
        feed.append("🟨 Safety Car agrupou o pelotão — estratégias embaralhadas!")
    if rep.get("vsc_lap") and lap >= rep["vsc_lap"] and not stt.get("vsc_ok"):
        stt["vsc_ok"] = True
        feed.append("🟨 Virtual Safety Car: todo mundo segurou o ritmo e as diferenças derreteram.")
    sc_fim = (rep.get("sc_lap") or 0) + int(rep.get("sc_dur") or 0)
    if rep.get("sc_lap") and lap > sc_fim and not stt.get("sc_fim_ok"):
        stt["sc_fim_ok"] = True
        feed.append("🟩 Safety Car na garagem — corrida relançada!")
    vsc_fim = (rep.get("vsc_lap") or 0) + int(rep.get("vsc_dur") or 0)
    if rep.get("vsc_lap") and lap > vsc_fim and not stt.get("vsc_fim_ok"):
        stt["vsc_fim_ok"] = True
        feed.append("🟩 Virtual Safety Car encerrado — vale acelerar.")
    if red_lap and lap >= red_lap and not stt.get("red_msg_ok"):
        stt["red_msg_ok"] = True
        feed.append("🟥 Bandeira vermelha! Prova interrompida — aguardando a relargada.")
    if lap >= voltas:
        stt["concluido"] = True
        st.rerun()
    mostrar = bool(st.session_state.get("ver_pits", False))
    ritmos = stt.setdefault(
        "ritmos", {l["piloto_id"]: l["estrategia"].get("ritmo", "Normal") for l in (fds.get("resultado") or [])}
    )
    pneus_man = stt.setdefault("pneus_manual", {})
    linhas = sim.linhas_replay(rep, lap, stt["pits"], pneus_man, ritmos, stt.get("overcut_ativo"))
    plano_clima = stt.get("clima") or fds.get("clima")
    cond = sim.condicao_pista(plano_clima, lap)
    cond_ant = stt.get("clima_visto")
    if cond_ant is not None and cond != cond_ant:
        feed.append(
            "🌧️ **A pista está molhando!** Pneu de chuva agora, chefe."
            if cond == "molhado"
            else "☀️ **A pista está secando!** Hora de voltar para o slick."
        )
    stt["clima_visto"] = cond

    # ---- undercut: rival que estava logo atrás parou agora
    # (as posições são as de ANTES dos boxes desta volta — é ali que a ameaça nasce)
    ativo = stt.setdefault("undercut_ativo", {})
    pits_antes = {k: [x for x in (v or []) if x < lap] for k, v in stt["pits"].items()}
    linhas_antes = sim.linhas_replay(rep, max(1, lap - 1), pits_antes, pneus_man, ritmos)
    pos_antes = {ln["pid"]: ln["pos"] for ln in linhas_antes if ln.get("pos") and not ln.get("fora")}
    for pid in meus_ids:
        uc = ativo.get(pid)
        if uc and lap - int(uc["volta"]) > 2:
            ativo.pop(pid, None)
    for pid, rival, pr, pm in sim.undercut_nesta_volta(lap, stt["pits"], meus_ids, pos_antes):
        if ativo.get(pid, {}).get("rival") == rival and ativo[pid].get("volta") == lap:
            continue
        ativo[pid] = {"rival": rival, "volta": lap}
        feed.append(
            f"⚔️ **{sim.piloto(game, rival)['nome']}** (P{pr}) foi ao box na volta {lap} — "
            f"undercut sobre **{sim.piloto(game, pid)['nome']}** (P{pm})!"
        )

    # ---- overcut: rival À FRENTE parou — ficar na pista e atacar devolve a posição
    overcut = stt.setdefault("overcut_ativo", {})
    janela_overcut = 3
    for pid in list(overcut):
        d = overcut[pid]
        piorou = any(volta_pit and d["volta"] <= volta_pit <= d["volta"] + janela_overcut
                     for volta_pit in (stt["pits"].get(pid) or []))
        if piorou:
            overcut.pop(pid, None)
            feed.append(
                f"🔧 **{sim.piloto(game, pid)['nome']}** foi ao box — overcut abandonado."
            )
        elif lap - int(d["volta"]) > janela_overcut:
            overcut.pop(pid, None)
            atual = next((ln["pos"] for ln in linhas if ln["pid"] == pid), None)
            ganho = (d.get("pos") or atual or 0) - (atual or 0)
            feed.append(
                f"🔧 Overcut concluído para **{sim.piloto(game, pid)['nome']}**: "
                + (f"ganhou {ganho} posição(ões) na pista!" if ganho > 0 else "posição mantida.")
            )
    for pid, rival, pr, pm in sim.overcut_disponivel(lap, stt["pits"], meus_ids, pos_antes):
        if overcut.get(pid, {}).get("rival") == rival and overcut[pid].get("volta") == lap:
            continue
        overcut[pid] = {"rival": rival, "volta": lap, "pos": pm, "laps": janela_overcut}
        feed.append(
            f"🔧 **{sim.piloto(game, rival)['nome']}** (P{pr}) parou na volta {lap} — "
            f"overcut: **{sim.piloto(game, pid)['nome']}** (P{pm}) pode ficar na pista e atacar!"
        )

    grids_rep = {pid: d["grid"] for pid, d in rep["info"].items()}
    c1, c2 = st.columns([2.3, 1], gap="medium")
    with c1:
        st.markdown(_html_tabela_viva(game, linhas, mostrar, meus_ids, grids_rep, mostra_delta=True),
                    unsafe_allow_html=True)
    with c2:
        st.markdown(
            f'<div class="voltas-box"><div class="lab">Voltas</div><div class="n">{lap} / {voltas}</div></div>',
            unsafe_allow_html=True,
        )
        st.markdown(_chip_pista(plano_clima, lap), unsafe_allow_html=True)
        if red_lap and lap >= red_lap and not stt.get("red_ok"):
            st.markdown(
                '<div class="bandeira-vermelha">🟥 <b>Bandeira vermelha!</b> '
                "Prova interrompida — o pelotão se junta para a relargada.</div>",
                unsafe_allow_html=True,
            )
            if st.button("🟥 Relargada", type="primary", width="stretch", key=f"relargada_{fds['chave']}"):
                stt["red_ok"] = True
                stt["t0"] = time.time() - (s_por_volta * max(1, lap)) / max(1, velocidade)
                st.rerun()
        elif int(rep.get("sc_dur") or 0) and rep.get("sc_lap") and rep["sc_lap"] <= lap <= sc_fim:
            st.markdown('<div class="pausa-chip">🟨 Safety Car na pista</div>', unsafe_allow_html=True)
        elif int(rep.get("vsc_dur") or 0) and rep.get("vsc_lap") and rep["vsc_lap"] <= lap <= vsc_fim:
            st.markdown('<div class="pausa-chip">🟨 Virtual Safety Car</div>', unsafe_allow_html=True)
        if pausado:
            st.markdown('<div class="pausa-chip">⏸ Corrida pausada</div>', unsafe_allow_html=True)
        cc = st.columns([1.15, 1, 1, 1])
        if cc[0].button(
            "▶ Retomar" if pausado else "⏸ Pausar",
            key="pausar_corrida",
            help="Congela a prova para pensar com calma (atalho: espaço).",
        ):
            stt["pausado"] = not pausado
            st.rerun()
        for col, opcao in zip(cc[1:], (1, 2, 4)):
            if col.button(
                f"{opcao}×",
                key=f"vel_{opcao}",
                type="primary" if velocidade == opcao else "secondary",
                help=f"Correr em {opcao}× (atalho: {opcao}).",
            ):
                stt["velocidade"] = opcao
                st.rerun()
        st.caption("⌨️ espaço pausa · 1/2/4 velocidade · P/O box do 1º/2º piloto")
        for p in meus:
            ln = next((x for x in linhas if x["pid"] == p["id"]), None)
            exec_pits = [x for x in stt["pits"].get(p["id"], []) if x <= lap]
            plano = int(rep["info"][p["id"]]["paradas"])
            ultimo = max(exec_pits, default=0)
            pneu = ln["pneu"] if ln else "—"
            ritmo = ritmos.get(p["id"], "Normal")
            vida = sim.vida_pneu(etapa, pneu, lap - ultimo, ritmo)
            papel = ROTULOS_PAPEL.get(p["papel"], p["papel"])
            alerta = ""
            if cond == "molhado" and pneu in sim.PNEUS_SECO:
                alerta = '<div class="alerta">⚠️ Slick na chuva — chame o box!</div>'
            elif cond == "seco" and pneu in sim.PNEUS_MOLHADO:
                alerta = '<div class="alerta">⚠️ Pneu de chuva no seco — troque já!</div>'
            pergunta_ok = perguntar.get(p["id"], True)
            rec_p = recusadas.get(p["id"]) or []
            proxima = next(
                (x for x in rep["info"][p["id"]]["pits_plano"] if x not in exec_pits and x not in rec_p), None
            )
            pedido_pit = _pit_pedido(stt)
            if pedido_pit is not None and pedido_pit.get("pid") == p["id"]:
                prox_txt = "📻 <b>No box — responda a janela!</b>"
            elif proxima:
                prox_txt = f"Próxima parada: volta {proxima}"
            else:
                prox_txt = "Sem paradas previstas no plano"
            oc = overcut.get(p["id"])
            oc_html = ""
            if oc and lap - int(oc["volta"]) <= janela_overcut:
                rival_oc = sim.piloto(game, oc["rival"])["nome"]
                oc_html = (
                    f'<div class="overcut-card">🔧 <b>{rival_oc}</b> parou — fique na pista e '
                    f"ataque para devolver a posição.</div>"
                )
            uc = ativo.get(p["id"])
            uc_html = ""
            if uc and lap - int(uc["volta"]) <= 2:
                nome_rival = sim.piloto(game, uc["rival"])["nome"]
                uc_html = (
                    f'<div class="undercut-card">⚔️ <b>{nome_rival}</b> parou na volta '
                    f"{uc['volta']} — responda ou perde a posição.</div>"
                )
            st.markdown(
                f'<div class="box-piloto"><div class="papel">{papel}</div>'
                f'<div class="nome">{bnd.img_bandeira(p["bandeira"], 18)} {p["nome"]}</div>'
                f'<div class="mini">Paradas: {len(exec_pits)}/{plano} · Pneus: <b>{pneu}</b> · '
                f"Pit: {'pergunta' if pergunta_ok else 'automático'}</div>"
                f"{_barra_html(vida)}"
                f'<div class="mini">Vida do pneu: {vida * 100:.0f}%</div>'
                f'<div class="mini">{prox_txt}</div>{alerta}{uc_html}{oc_html}</div>',
                unsafe_allow_html=True,
            )
            if oc_html and st.button(
                "🔥 Ficar e atacar",
                key=f"oc_{p['id']}_{fds['chave']}",
                width="stretch",
                help="Overcut: mantém o piloto na pista com ritmo Atacar para ganhar a posição na saída do rival.",
            ):
                rk_oc = f"ritmo_vivo_{p['id']}_{fds['chave']}"
                st.session_state[rk_oc] = "Atacar"
                ritmos[p["id"]] = "Atacar"
                feed.append(
                    f"🔥 **{p['nome']}** fica na pista e ataca (overcut) na volta {lap}."
                )
                st.rerun()
            if uc_html and st.button(
                "⚡ Responder agora",
                key=f"uc_{p['id']}_{fds['chave']}",
                type="primary",
                width="stretch",
                help="Undercut do rival: abrir o box imediatamente para devolver a posição.",
            ):
                stt["pit_aberto"] = {"pid": p["id"], "volta": lap, "planejada": False}
                stt["pausa_t0"] = time.time()
                st.session_state.pop(f"dlg_pneu_{p['id']}_{fds['chave']}", None)
                st.session_state.pop(f"dlg_ritmo_{p['id']}_{fds['chave']}", None)
                st.rerun()
            # ---- estratégia ao vivo: ritmo e chamada de box ----
            rk = f"ritmo_vivo_{p['id']}_{fds['chave']}"
            if rk not in st.session_state or st.session_state[rk] != ritmo:
                st.session_state[rk] = ritmo
            novo_ritmo = st.radio(
                "Ritmo",
                sim.RITMOS,
                key=rk,
                help="Ajuste durante a corrida: Atacar acelera as voltas e "
                "consome mais pneu; Conservar faz o contrário.",
            )
            if novo_ritmo != ritmo:
                ritmos[p["id"]] = novo_ritmo
                feed.append(f"🎯 **{p['nome']}** mudou para ritmo **{novo_ritmo}** na volta {lap}.")
            restam = plano + 1 - len(exec_pits)  # dá pra forçar UMA parada extra
            if st.button(
                "Pit stop!",
                key=f"pit_{p['id']}_{fds['chave']}",
                disabled=(restam <= 0 or lap >= voltas),
                help="Abrir o Pit Stop: escolha os novos pneus e confirme a parada.",
            ):
                stt["pit_aberto"] = {"pid": p["id"], "volta": lap, "planejada": False}
                stt["pausa_t0"] = time.time()  # prova congelada com a janela aberta
                st.session_state.pop(f"dlg_pneu_{p['id']}_{fds['chave']}", None)
                st.session_state.pop(f"dlg_ritmo_{p['id']}_{fds['chave']}", None)
        if feed:
            st.markdown('<div class="feed-race">' + "<br>".join(feed[-4:]) + "</div>", unsafe_allow_html=True)
        proximas = []
        for p in meus:
            exec_p = [x for x in stt["pits"].get(p["id"], []) if x <= lap]
            rec_p = recusadas.get(p["id"]) or []
            nxt = next(
                (x for x in rep["info"][p["id"]]["pits_plano"] if x not in exec_p and x not in rec_p),
                None,
            )
            if nxt and nxt > lap:
                proximas.append(nxt)
        alvo_pit = min(proximas) if proximas else None
        if st.button(
            f"⏩ Próxima parada (volta {alvo_pit})" if alvo_pit else "⏩ Sem paradas previstas",
            key="proxima_parada",
            disabled=alvo_pit is None,
            help="Avança a transmissão até a próxima parada planejada dos seus pilotos.",
        ) and alvo_pit is not None:
            spv = max(0.2, min(0.55, 24.0 / max(1, voltas)))
            stt["pausado"] = False
            stt["t0"] = time.time() - spv * alvo_pit / max(1, velocidade)
            st.rerun()
        if st.button("⏭️ Concluir corrida agora", key="concluir_corrida"):
            stt["pit_aberto"] = None
            stt["pulou"] = True
            st.rerun()
    if _pit_pedido(stt):
        _pit_dialog(game, etapa, molhado, fds, meus, lap, voltas)


# ======================================================================
#  FLUXO DA CORRIDA — treino → paddock → corrida (uma etapa por vez)
# ======================================================================
PASSOS_CORRIDA = ["Treino", "Paddock", "Corrida", "Resultado"]


def _status_passos(fds, rep_state):
    """Descobre em que passo o jogador está e até onde ele pode navegar.

    - Treino: 0 a grade ainda está sendo definida.
    - Paddock: 1 treino confirmado, hora de acertar pneus e dar a largada.
    - Corrida: 2 prova em andamento (o grid está congelado: não dá para voltar).
    - Resultado: 3 bandeirada.
    """
    if rep_state is not None:
        return (3 if rep_state.get("concluido") else 2), (3 if rep_state.get("concluido") else 2)
    liberado = 1 if (fds.get("treino_ok") or fds.get("paddock_ok")) else 0
    passo = fds.get("passo_ui")
    passo = liberado if passo is None else max(0, min(int(passo), liberado))
    return passo, liberado


def _stepper(passo, liberado):
    """Trilha dos passos (só o passo atual aparece com destaque)."""
    partes = []
    for i, nome in enumerate(PASSOS_CORRIDA):
        if i > 2:  # "Resultado" só entra na trilha depois da bandeirada
            continue
        classe = "agora" if i == passo else ("done" if i < passo else "")
        partes.append(
            f'<div class="wz-step {classe}"><span class="wz-n">{i + 1}</span>{nome}</div>'
        )
        if i < 2:
            partes.append(f'<div class="wz-trilha{" done" if i < passo else ""}"></div>')
    if passo == 3:
        partes.append('<div class="wz-trilha done"></div>')
        partes.append('<div class="wz-step agora"><span class="wz-n">4</span>Resultado</div>')
    st.markdown(f'<div class="wizard">{"".join(partes)}</div>', unsafe_allow_html=True)


def _hero_corrida(game, etapa, molhado, previsao):
    """Cabeçalho compacto do fim de semana: GP, circuito e os números que importam."""
    chips = [
        f"Etapa {game['rodada'] + 1}/{len(game['calendario'])}",
        f"{etapa['voltas']} voltas",
        "🌧️ Molhado" if molhado else "☀️ Seco",
        f"{sim.paradas_ideais(etapa)} parada(s) típica(s)",
    ]
    if etapa.get("sprint"):
        chips.append(f"⚡ {rot_corrida2(game)} + principal")
    st.markdown(
        f'<div class="race-hero compacto"><div class="kicker">{game["ano"]} · {etapa["pais"]}</div>'
        f"<h1>{bnd.img_bandeira(etapa['bandeira'], 30)} {etapa['gp']}</h1>"
        f'<p style="margin:0;color:#CBD5E1">{etapa["circuito"]}</p>'
        f'<div class="migalha">'
        + "".join(f"<span>{c}</span>" for c in chips)
        + f'<span class="destaque">🌦️ {previsao}</span></div></div>',
        unsafe_allow_html=True,
    )


def _detalhes_etapa(etapa, fds):
    """O que é contexto (e não decisão) fica guardado num expander fechado."""
    with st.expander("ℹ️ Detalhes da etapa", expanded=False):
        st.markdown(
            f"- **Peso do motor:** {etapa['potencia'] * 100:.0f}% · "
            f"**facilidade de ultrapassar:** {etapa['ultrap'] * 100:.0f}% · "
            f"**desgaste dos pneus:** {etapa['desgaste']:.1f}/3 · "
            f"**chance de chuva:** {etapa['chuva'] * 100:.0f}%"
        )
        st.markdown(f"- **Previsão do tempo:** {sim.previsao_texto(fds.get('clima'))}")


def _passo_treino(game, etapa, molhado, fds, bloqueado, pode_avancar):
    """Passo 1: treino classificatório — cronômetro, grade e botão de avançar."""
    sess = fds.get("treino")
    if not sess or not sess.get("t0"):
        # cronômetro parado: grade neutra com '-' (sem spoiler do grid)
        st.progress(0.0, text="⏱️ Treino classificatório · 60 min")
        neutro = [
            {"piloto_id": p["id"], "equipe_id": p["equipe_id"], "pos": i + 1}
            for i, p in enumerate(
                sorted(
                    sim.titulares(game),
                    key=lambda x: (
                        sim.equipe(game, x["equipe_id"])["nome"],
                        ["P1", "P2", "P3", "P4"].index(x["papel"]) if x["papel"] in ("P1", "P2", "P3", "P4") else 9,
                    ),
                )
            )
        ]
        st.markdown(_html_tabela_treino(game, neutro, None, 0), unsafe_allow_html=True)
        if st.button("⏱️ Iniciar treino", type="primary", width="stretch", key="iniciar_treino", disabled=bloqueado):
            grid = sim.simular_classificacao(game, etapa, molhado)
            fds["grid"] = grid
            fds["treino"] = sim.sessao_treino(game, etapa, molhado, grid)
            fds["treino"]["t0"] = time.time()
            st.rerun()
        if bloqueado:
            st.caption(f"🏁 Primeiro simule o {rot_corrida2(game)}.")
        _detalhes_etapa(etapa, fds)
        return

    if not sess.get("concluido"):
        _frag_treino(game, etapa, molhado, fds)
        return

    # sessão encerrada: grade final congelada + pole + passagem para o paddock
    st.progress(1.0, text="⏱️ Treino encerrado — grid fechado")
    st.markdown(_html_tabela_treino(game, fds["grid"], sess, int(sess["duracao"])), unsafe_allow_html=True)
    pole = sim.piloto(game, fds["grid"][0]["piloto_id"])
    st.caption(
        f"🏆 **Pole position:** {pole['nome']} ({fmt_tempo(fds['grid'][0]['tempo'])}) · {len(fds['grid'])} no grid"
    )
    if pode_avancar:
        if st.button("➡️ Ir para o Paddock", type="primary", width="stretch", key="ir_corrida"):
            fds["treino_ok"] = True
            fds["passo_ui"] = 1
            flash("success", "Grid fechado — acerte os pneus no Paddock e dê a largada!")
            st.rerun()
    with st.expander("👀 Ver detalhes da etapa", expanded=False):
        st.markdown(
            f"Peso do motor **{etapa['potencia'] * 100:.0f}%** · ultrapassagem "
            f"**{etapa['ultrap'] * 100:.0f}%** · desgaste **{etapa['desgaste']:.1f}/3** — "
            f"estratégia típica: **{sim.paradas_ideais(etapa)} parada(s)**."
        )
        st.markdown(f"Previsão: {sim.previsao_texto(fds.get('clima'))}")


def _passo_paddock(game, etapa, molhado, fds, meus, estrategias, opcoes_pneu, bloqueado):
    """Passo 2: paddock enxuto — pneus, grid e a largada."""
    st.markdown(
        f'<div class="paddock-head"><div class="paddock-kick">Paddock</div>'
        f'<div class="paddock-gp">{etapa["gp"]} — {etapa["voltas"]} voltas '
        f"{bnd.img_bandeira(etapa['bandeira'], 20)}</div></div>",
        unsafe_allow_html=True,
    )
    grid_pos = {g["piloto_id"]: g["pos"] for g in (fds.get("grid") or [])}
    pit_auto = {}
    colsp = st.columns(len(meus))
    for col, p in zip(colsp, meus):
        with col, st.container(border=True):
            st.markdown(
                bnd.com_bandeira(
                    p["bandeira"], f"**#{p['numero']} {p['nome']}** ({ROTULOS_PAPEL.get(p['papel'], p['papel'])})"
                ),
                unsafe_allow_html=True,
            )
            pos = grid_pos.get(p["id"])
            st.caption(f"Largada: **{f'{pos}º' if pos else '—'}**")
            pneu_pad = st.selectbox(
                "Pneus",
                opcoes_pneu,
                index=0 if molhado else 1,
                format_func=_rot_pneu,
                key=f"pad_pneu_{p['id']}_{fds['chave']}",
                label_visibility="collapsed",
            )
            if molhado and pneu_pad in sim.PNEUS_SECO:
                st.caption("⚠️ Slick na chuva — vai doer.")
            if not molhado and pneu_pad in sim.PNEUS_MOLHADO:
                st.caption("⚠️ Pneu de chuva no seco derrete.")
            estrategias.setdefault(p["id"], {"paradas": sim.paradas_ideais(etapa), "ritmo": "Normal"})
            estrategias[p["id"]]["pneu"] = pneu_pad
            pit_auto[p["id"]] = st.checkbox(
                "Perguntar em cada pit stop",
                value=True,
                help="A cada parada planejada abre a janela do Pit Stop (pneu + ritmo). "
                "Desmarque para o box fazer as paradas sozinho.",
                key=f"pad_perg_{p['id']}_{fds['chave']}",
            )

    with st.expander("📋 Grid de largada", expanded=not fds.get("grid")):
        if fds.get("grid"):
            linhas_ini = [
                {
                    "pid": g["piloto_id"],
                    "equipe_id": g["equipe_id"],
                    "pos": g["pos"],
                    "tempo": None,
                    "dif_ant": None,
                    "dif1": None,
                    "box": False,
                }
                for g in fds["grid"]
            ]
            st.markdown(_html_tabela_viva(game, linhas_ini, False, {p["id"] for p in meus}), unsafe_allow_html=True)
        else:
            st.info("🏁 O grid aparece aqui depois do treino.")

    paddock_ok = bool(fds.get("paddock_ok"))
    pode_largar = bool(fds.get("treino_ok")) and bool(fds.get("grid")) and not bloqueado and paddock_ok
    if not paddock_ok:
        # ainda escolhendo: confirmar guarda a estratégia, largar só depois
        c1, c2 = st.columns(2)
        if c1.button("✅ Confirmar estratégia", width="stretch", key="paddock_confirmar"):
            fds["paddock_ok"] = True
            flash("success", "Paddock confirmado — pneus e avisos de pit stop valendo. Agora é só dar a largada!")
            st.rerun()
        c2.button("🚦 Dar largada!", type="primary", width="stretch", key="dar_largada", disabled=not pode_largar)
        if not fds.get("treino_ok"):
            st.caption("⏱️ Confirme o treino para liberar a largada.")
        else:
            st.caption("✅ Confirme a estratégia para liberar a largada.")
    else:
        if st.button("🚦 Dar largada!", type="primary", width="stretch", key="dar_largada", disabled=not pode_largar):
            _largar(game, etapa, molhado, fds, meus, estrategias, pit_auto)
        st.caption("✅ Estratégia confirmada — boa sorte, chefe!")
    if not bloqueado and fds.get("passo_ui") != 0:
        if st.button("← Revisar treino", key="voltar_treino"):
            fds["passo_ui"] = 0
            st.rerun()


def _largar(game, etapa, molhado, fds, meus, estrategias, pit_auto):
    """Cria o replay e joga o jogador no passo da corrida."""
    eqj = sim.equipe(game, game["equipe_jogador"])
    res, ev = sim.simular_corrida(game, etapa, fds["grid"], estrategias, molhado, clima=fds.get("clima"))
    fds["resumo"] = sim.aplicar_resultado(game, etapa, fds["grid"], res, molhado, eventos=ev)
    fds["resultado"], fds["eventos"] = res, ev
    venceu = any(l["equipe_id"] == eqj["id"] and l["pos"] == 1 and not l["dnf"] for l in res)
    fds["replay"] = {
        "rep": sim.montar_replay(game, etapa, fds["grid"], res, molhado, eventos=ev),
        "t0": time.time(),
        "pits": {},
        "feed": [],
        "feed_dnf": [],
        "sc_ok": False,
        "lap": 0,
        "pulou": False,
        "concluido": False,
        "venceu": venceu,
        "balloons_ok": False,
        "ritmos": {pid: e.get("ritmo", "Normal") for pid, e in estrategias.items()},
        "pneus_manual": {},
        "pit_perguntar": pit_auto,
        "pit_aberto": None,
        "pits_recusados": {},
        "clima": fds.get("clima"),
        "clima_visto": None,
        "pausado": False,
        "velocidade": 1,
    }
    st.rerun()


def _passo_corrida(game, etapa, molhado, fds, meus):
    """Passo 3: transmissão ao vivo, sem os blocos de preparação na tela."""
    c1, c2 = st.columns([1, 2.4], vertical_alignment="center")
    c1.checkbox(
        "Ver pits/pneus",
        key="ver_pits",
        help="Mostra composto e número de paradas na torre de tempos.",
    )
    c2.caption("📻 Em cada parada a prova pausa e abre o **Pit Stop** — ou chame o box com **Pit stop!**.")
    _atalhos_corrida()
    _frag_corrida(game, etapa, molhado, fds, meus)


def _passo_resultado(game, etapa, molhado, fds, meus, rep_state, eqj):
    """Passo 4: bandeirada — classificação, volta rápida, stints e finanças."""
    if rep_state.get("venceu") and not rep_state.get("balloons_ok"):
        rep_state["balloons_ok"] = True
        st.balloons()
    st.dataframe(df_resultado(game, fds["resultado"]), hide_index=True, width="stretch", column_config=CFG_BANDEIRA)
    botao_csv(
        df_resultado(game, fds["resultado"]).drop(columns=["Bandeira"], errors="ignore"),
        f"resultado_{game['ano']}_etapa{game['rodada'] + 1}.csv",
        key="csv_resultado_corrida",
    )
    vr = sim.volta_mais_rapida(fds["resultado"])
    if vr:
        p_vr = sim.piloto(game, vr["piloto_id"])
        st.markdown(
            f"⚡ **Volta mais rápida:** {bnd.com_bandeira(p_vr['bandeira'], p_vr['nome'])} — "
            f"{sim.equipe(game, vr['equipe_id'])['nome']} · +1 ponto"
        )
    with st.expander("📻 O que aconteceu na prova", expanded=False):
        for ev in fds["eventos"]:
            st.markdown(f"- {ev}")

    # gráfico de stints (degradação dos seus pilotos)
    if rep_state.get("rep"):
        rep_final = rep_state["rep"]
        with st.expander("📈 Stints e degradação dos pneus", expanded=True):
            dados = {}
            for p in meus:
                stints = sim.stints_corrida(rep_final, p["id"], rep_state.get("pits"), rep_state.get("pneus_manual"))
                tempos = rep_final["info"][p["id"]]["tempos"][: int(rep_final["voltas"])]
                if tempos:
                    dados[p["nome"]] = pd.Series(tempos, index=range(1, len(tempos) + 1))
                if stints:
                    st.caption(
                        f"**{p['nome']}** — "
                        + " → ".join(
                            f"{s['pneu']} (v.{s['inicio']}-{s['fim']}, {s['tempo_medio']}s)"
                            for s in stints
                            if s["tempo_medio"]
                        )
                    )
            if dados:
                st.line_chart(pd.DataFrame(dados), x_label="Volta", y_label="Tempo de volta (s)")
                st.caption("As quedas verticais são as paradas no box; a subida lenta é a degradação.")
    if fds["resumo"]:
        st.markdown(
            "**💰 Balanço do fim de semana:** "
            + " · ".join(
                f"{d} {sim.fmt_dinheiro_k(v) if v >= 0 else '−' + sim.fmt_dinheiro_k(-v)}" for d, v in fds["resumo"]
            )
            + f" → caixa atual: **{sim.fmt_dinheiro_m(eqj['caixa'])}**"
        )
    prox = "Encerrar a temporada 🏁" if game["rodada"] >= len(game["calendario"]) else "Continuar ▶️"
    st.button(prox, type="primary", width="stretch", on_click=_continuar_da_corrida)


def pagina_corrida(game):
    if game["rodada"] >= len(game["calendario"]):
        painel_fim_temporada(game)
        return
    etapa = game["calendario"][game["rodada"]]
    fds = obter_fds(game, etapa)
    rep_state = fds.get("replay")
    molhado = fds["molhado"]
    eqj = sim.equipe(game, game["equipe_jogador"])
    meus = sim.titulares(game, eqj["id"])
    opcoes_pneu = sim.PNEUS_MOLHADO + sim.PNEUS_SECO if molhado else sim.PNEUS_SECO
    bloqueado = bool(etapa.get("sprint") and fds.get("sprint") is None)
    passo, liberado = _status_passos(fds, rep_state)

    # estratégia padrão de cada piloto (o Paddock sobrescreve os pneus)
    estrategias = {p["id"]: {"paradas": sim.paradas_ideais(etapa), "ritmo": "Normal"} for p in meus}

    _hero_corrida(game, etapa, molhado, sim.previsao_texto(fds.get("clima")))
    _stepper(passo, liberado)

    # a primeira corrida do fim de semana (Stock Car, DTM, F1 Academy) vem antes do treino
    if etapa.get("sprint") and passo == 0:
        if fds.get("sprint") is None:
            est_s = {}
            colss = st.columns(len(meus))
            for col, p in zip(colss, meus):
                with col, st.container(border=True):
                    st.markdown(
                        bnd.com_bandeira(p["bandeira"], f"**#{p['numero']} {p['nome']}**"), unsafe_allow_html=True
                    )
                    pneu_s = st.selectbox(
                        "Pneu de largada",
                        opcoes_pneu,
                        index=0 if molhado else 1,
                        format_func=_rot_pneu,
                        key=f"pneu_s_{p['id']}_{fds['chave']}",
                    )
                    est_s[p["id"]] = {
                        "pneu": pneu_s,
                        "paradas": sim.paradas_ideais(etapa),
                        "ritmo": estrategias.get(p["id"], {}).get("ritmo", "Normal"),
                    }
            if st.button(f"▶️ Simular {rot_corrida2(game)}", width="stretch", key="simular_sprint"):
                grid_s = sim.simular_classificacao(game, etapa, molhado)
                res_s, ev_s = sim.simular_corrida(
                    game, etapa, grid_s, est_s, molhado, sprint=True, clima=fds.get("clima")
                )
                sim.aplicar_resultado(game, etapa, grid_s, res_s, molhado, sprint=True, eventos=ev_s)
                fds["sprint"] = res_s
                st.rerun()
        else:
            st.dataframe(
                df_resultado(game, fds["sprint"]), hide_index=True, width="stretch", column_config=CFG_BANDEIRA
            )
            st.caption(f"Pontos da {rot_corrida2(game)} já somados ao campeonato.")
        st.divider()

    if passo == 0:
        _passo_treino(game, etapa, molhado, fds, bloqueado, pode_avancar=True)
    elif passo == 1:
        _passo_paddock(game, etapa, molhado, fds, meus, estrategias, opcoes_pneu, bloqueado)
    elif passo == 2:
        _passo_corrida(game, etapa, molhado, fds, meus)
    else:
        _passo_resultado(game, etapa, molhado, fds, meus, rep_state, eqj)
