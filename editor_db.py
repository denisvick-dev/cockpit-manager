# -*- coding: utf-8 -*-
"""
Editor de DBs do Cockpit Manager (aba "Criar / editar DB").

Permite criar uma DB do zero ou editar qualquer DB existente
(equipes, pilotos, calendário e fornecedores) com tabelas editáveis,
validar, baixar em .json, salvar na pasta minhas_dbs/ e jogar na hora.
"""

import copy
import json
from typing import cast

import pandas as pd
import streamlit as st

import dados2026 as f1
import dbs
import simulacao as sim

_COLS_ATTR = {
    "velocidade": "Velocidade",
    "chuva": "Chuva",
    "concentracao": "Concentração",
    "largada": "Largada",
    "ultrapassagem": "Ultrap.",
    "acerto": "Acerto",
    "fisico": "Físico",
}


# ------------------------------------------------------------------ helpers
def _nomes_equipes(db_dados):
    return [e["nome"] for e in db_dados["equipes"]]


def df_equipes(db_dados):
    mot = {m["id"]: m["nome"] for m in db_dados["motores"]}
    return pd.DataFrame(
        [
            {
                "Nome": e["nome"],
                "País": e["pais"],
                "Bandeira": e["bandeira"],
                "Cor": e["cor"],
                "Fornecedor": mot.get(e["motor_id"], ""),
                "Nível do carro": float(e["nivel_carro"]),
                "Confiabilidade": float(e["confiabilidade"]),
                "Caixa (US$ mi)": float(e["caixa"]),
                "Prestígio": int(e["prestigio"]),
                "Invest./corrida": int(e["investimento_corrida"]),
            }
            for e in db_dados["equipes"]
        ]
    )


def df_pilotos(db_dados):
    eq = {e["id"]: e["nome"] for e in db_dados["equipes"]}
    linhas = []
    for p in db_dados["pilotos"]:
        a = p["atributos"]
        linhas.append(
            {
                "Nome": p["nome"],
                "Sigla": p["sigla"],
                "Nº": int(p["numero"]),
                "País": p["pais"],
                "Bandeira": p["bandeira"],
                "Idade": int(p["idade"]),
                "Equipe": eq.get(p["equipe_id"], "") or "",
                "Papel": p["papel"],
                "Salário": int(p["salario_corrida"]),
                "Contrato": int(p["contrato_anos"]),
                "Auge início": int(p["auge_inicio"]),
                "Auge fim": int(p["auge_fim"]),
                "Potencial": int(p["potencial"]),
                **{_COLS_ATTR[k]: int(a[k]) for k in _COLS_ATTR},
            }
        )
    return pd.DataFrame(linhas)


def df_calendario(db_dados):
    return pd.DataFrame(
        [
            {
                "Etapa": c["gp"],
                "Circuito": c["circuito"],
                "País": c["pais"],
                "Bandeira": c["bandeira"],
                "Voltas": int(c["voltas"]),
                "Data": c["data"],
                "2 corridas": bool(c["sprint"]),
                "Peso motor": float(c["potencia"]),
                "Ultrapassagem": float(c["ultrap"]),
                "Desgaste": float(c["desgaste"]),
                "Chuva": float(c["chuva"]),
            }
            for c in db_dados["calendario"]
        ]
    )


def df_fornecedores(db_dados):
    return pd.DataFrame(
        [
            {
                "Nome": m["nome"],
                "Potência": int(m["potencia"]),
                "Confiabilidade": int(m["confiabilidade"]),
                "Preço (mi/ano)": float(m["preco"]),
            }
            for m in db_dados["motores"]
            if m["id"] != "fia"
        ]
    )


def _linhas(df):
    if df is None:
        return []
    return [r for r in df.fillna("").to_dict("records")]


def reconstruir(meta, dfe, dfp, dfc, dfm, base):
    equipes = []
    for r in _linhas(dfe):
        if not str(r.get("Nome", "")).strip():
            continue
        equipes.append(
            {
                "nome": r["Nome"],
                "nome_completo": r["Nome"],
                "pais": r.get("País") or "Brasil",
                "bandeira": r.get("Bandeira") or "🏁",
                "cor": r.get("Cor") or "#3366FF",
                "motor": r.get("Fornecedor") or "",
                "nivel_carro": r.get("Nível do carro") or 80,
                "confiabilidade": r.get("Confiabilidade") or 85,
                "caixa": r.get("Caixa (US$ mi)") or 80,
                "prestigio": r.get("Prestígio") or 70,
                "investimento_corrida": r.get("Invest./corrida") or 900,
                "patrocinador": "Seguros Prisma",
                "titulos_construtores": 0,
                "motor_proprio": False,
            }
        )
    pilotos = []
    inv = {v: k for k, v in _COLS_ATTR.items()}
    for r in _linhas(dfp):
        if not str(r.get("Nome", "")).strip():
            continue
        pilotos.append(
            {
                "nome": r["Nome"],
                "sigla": r.get("Sigla") or "",
                "numero": r.get("Nº") or 0,
                "pais": r.get("País") or "Brasil",
                "bandeira": r.get("Bandeira") or "🏁",
                "idade": r.get("Idade") or 25,
                "equipe": r.get("Equipe") or "",
                "papel": r.get("Papel") or "livre",
                "salario_corrida": r.get("Salário") or 100,
                "contrato_anos": r.get("Contrato") or 2,
                "auge_inicio": r.get("Auge início") or 25,
                "auge_fim": r.get("Auge fim") or 32,
                "potencial": r.get("Potencial") or 85,
                "atributos": {inv[c]: r.get(c) or 75 for c in _COLS_ATTR.values()},
            }
        )
    calendario = []
    for r in _linhas(dfc):
        if not str(r.get("Etapa", "")).strip():
            continue
        calendario.append(
            {
                "gp": r["Etapa"],
                "circuito": r.get("Circuito") or r["Etapa"],
                "pais": r.get("País") or "Brasil",
                "bandeira": r.get("Bandeira") or "🏁",
                "voltas": r.get("Voltas") or 30,
                "data": r.get("Data") or "",
                "sprint": bool(r.get("2 corridas")),
                "potencia": r.get("Peso motor") or 0.5,
                "ultrap": r.get("Ultrapassagem") or 0.5,
                "desgaste": r.get("Desgaste") or 2,
                "chuva": r.get("Chuva") or 0.2,
            }
        )
    motores = []
    for r in _linhas(dfm):
        if not str(r.get("Nome", "")).strip():
            continue
        motores.append(
            {
                "nome": r["Nome"],
                "potencia": r.get("Potência") or 88,
                "confiabilidade": r.get("Confiabilidade") or 88,
                "preco": r.get("Preço (mi/ano)") or 10,
                "desc": "",
            }
        )
    return {
        "meta": meta,
        "equipes": equipes,
        "pilotos": pilotos,
        "motores": motores,
        "calendario": calendario,
        "hall_da_fama": copy.deepcopy(base.get("hall_da_fama") or []),
        "patrocinadores": copy.deepcopy(base.get("patrocinadores") or f1.PATROCINADORES),
    }


def _parse_pontos(texto, padrao):
    try:
        v = [int(x.strip()) for x in str(texto).split(",") if x.strip()]
        return v or list(padrao)
    except Exception:
        return list(padrao)


# ----------------------------------------------------------------------
def aba_editor_db(dbs_disponiveis):
    st.markdown(
        "Monte sua própria base de dados — como os criadores de DB da comunidade do CM14! "
        "Edite as tabelas (dá para **adicionar/remover linhas**), valide e jogue, baixe ou salve a DB."
    )
    ss = st.session_state
    if "editor_db" not in ss:
        ss.editor_db = copy.deepcopy(dbs_disponiveis["f1_2026"])
        ss.editor_rev = 0
        ss.db_validada = None

    # ---- carregar base / nova / upload
    c1, c2 = st.columns([2, 1])
    base_id = c1.selectbox(
        "Começar a partir de…",
        list(dbs_disponiveis.keys()),
        format_func=lambda k: dbs_disponiveis[k]["meta"].get("nome", k),
        key="editor_base_sel",
    )
    colb = c2.columns(2)
    if colb[0].button("📥 Carregar base", width="stretch"):
        ss.editor_db = copy.deepcopy(dbs_disponiveis[base_id])
        ss.editor_rev += 1
        ss.db_validada = None
        st.rerun()
    if colb[1].button("✨ DB em branco", width="stretch"):
        ss.editor_db = dbs.modelo_db_vazia()
        ss.editor_rev += 1
        ss.db_validada = None
        st.rerun()
    up = st.file_uploader("…ou envie uma DB .json (a sua ou de outro criador)", type="json", key="editor_upload")
    if up is not None and ss.get("_editor_upload_nome") != up.name + str(up.size):
        try:
            dados, erros, _ = dbs.validar_e_normalizar(json.loads(up.read().decode("utf-8")))
            if dados:
                ss.editor_db = dados
                ss.editor_rev += 1
                ss.db_validada = dados
                ss["_editor_upload_nome"] = up.name + str(up.size)
                st.success("DB carregada e válida! Veja as tabelas abaixo ou jogue direto.")
                st.rerun()
            else:
                st.error("DB inválida: " + " · ".join(erros))
        except Exception as e:
            st.error(f"Não consegui ler o arquivo: {e}")

    ed = ss.editor_db
    meta_ed = ed.get("meta") or {}
    rev = ss.editor_rev

    # ---- meta
    st.subheader("🏷️ Sobre a DB")
    m1, m2, m3 = st.columns(3)
    nome_db = m1.text_input("Nome da DB", value=meta_ed.get("nome", ""), key=f"ed_nome_{rev}")
    categoria = m2.text_input("Categoria", value=meta_ed.get("categoria", ""), key=f"ed_cat_{rev}")
    ano_db = m3.number_input("Ano inicial", 1950, 2100, int(meta_ed.get("ano", 2026)), key=f"ed_ano_{rev}")
    m4, m5 = st.columns(2)
    rot_forn = m4.selectbox(
        "Os fornecedores são…",
        ["Motor", "Montadora", "Carro GT3", "Chassi"],
        index=["Motor", "Montadora", "Carro GT3", "Chassi"].index(meta_ed.get("rotulo_fornecedor", "Motor"))
        if meta_ed.get("rotulo_fornecedor", "Motor") in ["Motor", "Montadora", "Carro GT3", "Chassi"]
        else 0,
        key=f"ed_forn_{rev}",
    )
    rot2_atual = meta_ed.get("rotulo_corrida2") or "Nenhuma"
    op_rot2 = ["Sprint", "Corrida 1", "Corrida sprint", "Nenhuma"]
    rot2 = m5.selectbox(
        "Etapas com 2 corridas têm antes uma…",
        op_rot2,
        index=op_rot2.index(rot2_atual) if rot2_atual in op_rot2 else 0,
        key=f"ed_rot2_{rev}",
    )
    preset = st.selectbox("Sistema de pontuação (preset)", list(dbs.PRESETS_PONTUACAO.keys()), key=f"ed_preset_{rev}")
    pts_preset, pts2_preset = dbs.PRESETS_PONTUACAO[preset]
    p1, p2 = st.columns(2)
    pts_txt = p1.text_input(
        "Pontos — corrida principal",
        value=", ".join(map(str, meta_ed.get("pontos_corrida") or pts_preset)),
        key=f"ed_pts_{rev}",
        help="Edite livremente ou troque o preset e clique em 'Usar preset'.",
    )
    pts2_txt = p2.text_input(
        "Pontos — corrida 2/sprint",
        value=", ".join(map(str, meta_ed.get("pontos_corrida2") or pts2_preset)),
        key=f"ed_pts2_{rev}",
    )

    def _cb_preset(_rev=rev):
        _a, _b = dbs.PRESETS_PONTUACAO[st.session_state[f"ed_preset_{_rev}"]]
        st.session_state[f"ed_pts_{_rev}"] = ", ".join(map(str, _a))
        st.session_state[f"ed_pts2_{_rev}"] = ", ".join(map(str, _b))

    st.button("↩️ Usar preset selecionado nos campos de pontos", on_click=_cb_preset)

    # ---- tabelas
    st.subheader("📋 Tabelas da DB")
    tab_e, tab_p, tab_c, tab_m = st.tabs(["🏭 Equipes", "👨‍✈️ Pilotos", "🗓️ Calendário", "⚙️ Fornecedores"])
    with tab_e:
        dfe = st.data_editor(
            df_equipes(ed),
            num_rows="dynamic",
            width="stretch",
            key=f"ed_eq_{rev}",
            column_config={"Cor": st.column_config.TextColumn("Cor (hex)", help="Ex.: #E10600")},
        )
    with tab_p:
        st.caption(
            "Papel: P1–P4 (titulares), teste (reserva) ou livre. A coluna Equipe deve usar o nome exato da aba Equipes."
        )
        dfp = st.data_editor(
            df_pilotos(ed),
            num_rows="dynamic",
            width="stretch",
            key=f"ed_pil_{rev}",
            height=420,
            column_config={
                "Papel": st.column_config.SelectboxColumn("Papel", options=["P1", "P2", "P3", "P4", "teste", "livre"]),
                "Equipe": st.column_config.SelectboxColumn("Equipe", options=_nomes_equipes(ed) + [""]),
            },
        )
    with tab_c:
        dfc = st.data_editor(df_calendario(ed), num_rows="dynamic", width="stretch", key=f"ed_cal_{rev}")
    with tab_m:
        st.caption("O fornecedor compulsório de 50% é adicionado automaticamente (tradição é tradição).")
        dfm = st.data_editor(df_fornecedores(ed), num_rows="dynamic", width="stretch", key=f"ed_mot_{rev}")

    meta_nova = {
        "id": dbs.slugificar(nome_db or meta_ed.get("id", "minha_db")),
        "nome": nome_db or "Minha DB",
        "categoria": categoria or "Categoria Personalizada",
        "ano": int(ano_db),
        "descricao": str(meta_ed.get("descricao", "")),
        "rotulo_fornecedor": rot_forn,
        "rotulo_corrida2": None if rot2 == "Nenhuma" else rot2,
        "pontos_corrida": _parse_pontos(pts_txt, f1.PONTOS_CORRIDA),
        "pontos_corrida2": _parse_pontos(pts2_txt, f1.PONTOS_SPRINT),
        "importancia_carro_sugerida": float(meta_ed.get("importancia_carro_sugerida", 0.55)),
        "fator_pontos_bonus": float(meta_ed.get("fator_pontos_bonus", 1.0)),
        "pontua_abandono": bool(meta_ed.get("pontua_abandono", False)),
    }

    # ---- ações
    st.divider()
    if st.button("✅ Validar DB", type="primary", width="stretch"):
        bruta = reconstruir(meta_nova, dfe, dfp, dfc, dfm, ed)
        dados, erros, avisos = dbs.validar_e_normalizar(bruta)
        ss.db_validada = dados
        for a in avisos:
            st.warning("⚠️ " + a)
        if dados:
            ss.editor_db = copy.deepcopy(dados)  # tabelas passam a refletir a versão normalizada
            st.success(
                f"DB válida! {len(dados['equipes'])} equipes · {len(dados['pilotos'])} pilotos · "
                f"grid natural de {dbs.grid_natural(dados)} · {len(dados['calendario'])} etapas."
            )
        else:
            for e in erros:
                st.error("❌ " + e)

    if ss.get("db_validada"):
        dados = cast(dict, ss.db_validada)  # guardado pelo `if` acima (st.session_state)
        a1, a2 = st.columns(2)
        a1.download_button(
            "⬇️ Baixar DB (.json) para compartilhar",
            json.dumps(dados, ensure_ascii=False, indent=1),
            file_name=f"{dados['meta']['id']}.json",
            mime="application/json",
            width="stretch",
        )
        if a2.button("💾 Salvar na pasta minhas_dbs/ (neste computador)", width="stretch"):
            ok, info = dbs.salvar_db_personalizada(dados)
            if ok:
                st.success(f"Salva em {info} — ela aparecerá na lista de DBs ao recarregar a página.")
            else:
                st.error(f"Não consegui salvar em disco: {info}. Baixe o .json como backup.")
        st.subheader("▶️ Jogar com esta DB agora")
        eqs = {e["id"]: e["nome"] for e in dados["equipes"]}
        eq_sel = st.selectbox("Sua equipe", list(eqs.keys()), format_func=lambda k: eqs[k], key="ed_jogar_eq")
        maxg = dbs.grid_maximo(dados)
        ming = 22 if maxg >= 22 else max(4, len(dados["equipes"]))
        qtd = st.slider(
            "Pilotos no grid", ming, maxg, max(ming, min(maxg, dbs.grid_natural(dados))), key="ed_jogar_qtd"
        )
        if st.button("🚥 Iniciar carreira nesta DB", type="primary", width="stretch"):
            ss.game = sim.criar_novo_jogo(
                eq_sel,
                2026,
                True,
                float(dados["meta"].get("importancia_carro_sugerida", 0.55)),
                db_dados=dados,
                qtd_pilotos=qtd,
            )
            ss.fds = None
            ss.flash = ("success", f"Carreira iniciada na DB '{dados['meta']['nome']}'! Boa sorte, chefe!")
            st.rerun()
