# -*- coding: utf-8 -*-
"""Tela inicial: escolha da DB, da equipe e do tamanho do grid (e o editor de DBs)."""


import pandas as pd
import streamlit as st

import armazenamento
import bandeiras as bnd
import dbs as dbsmod
import editor_db
import simulacao as sim

from .comum import CFG_BANDEIRA, MENUS, cabecalho_inicial, flash

def dbs_disponiveis():
    """DBs embutidas + personalizadas salvas em minhas_dbs/ + validadas no editor."""
    disp = dbsmod.dbs_embutidas()
    personalizadas, _ = dbsmod.carregar_dbs_personalizadas()
    disp.update(personalizadas)
    if st.session_state.get("db_validada"):
        dv = st.session_state.db_validada
        disp[f"custom:editor:{dv['meta']['id']}"] = dv
    saida = {}
    for chave, dados in disp.items():
        norm, erros, _ = dbsmod.validar_e_normalizar(dados)
        if norm:
            saida[chave] = norm
    return saida


def _slider_grid(sel_db, key_suffix=""):
    natural = dbsmod.grid_natural(sel_db)
    maximo = dbsmod.grid_maximo(sel_db)
    minimo = 22 if maximo >= 22 else max(4, len(sel_db["equipes"]))
    padrao = max(minimo, min(maximo, natural))
    return st.slider(
        "👥 Pilotos no grid (titulares)" + (" — começa em 22" if minimo == 22 else ""),
        minimo,
        maximo,
        padrao,
        help=f"Grid natural desta DB: {natural}. Acima disso, as equipes inscrevem 3º e 4º carros "
        f"com reservas e jovens do mercado; abaixo, os carros excedentes sao cortados.",
        key=f"qtd_grid{key_suffix}",
    )


def tela_inicial():
    cabecalho_inicial()
    st.caption(
        "Remake de fã inspirado no *Cockpit Manager '14* (Cartola Games) e na "
        "[DB F1 2026 by Jonathan Daniel]"
        "(http://cockpitmanager.blogspot.com/2026/05/db-f1-2026-v10-by-jonathan-daniel.html). "
        "Escolha uma **base de dados (DB)**, a sua equipe e **quantos pilotos terá o grid** — "
        "ou crie a sua própria categoria na aba 🛠️ **Criar / editar DB**."
    )

    disp = dbs_disponiveis()
    db_chave = st.selectbox(
        "📚 Base de dados (DB)",
        list(disp.keys()),
        format_func=lambda k: f"{disp[k]['meta'].get('nome', k)} — {disp[k]['meta'].get('categoria', '')}",
    )
    sel_db = disp[db_chave]
    if sel_db["meta"].get("anos_historicos"):
        _anos = [int(a) for a in sel_db["meta"]["anos_historicos"]]
        ano_hist = st.selectbox(
            "📅 Temporada histórica",
            _anos,
            help="Como no original: escolha o ano — grids, equipes, motores, calendário e "
            "pontuação daquela temporada (décadas de 1950 a 2020).",
        )
        _norm_h, _erros_h, _ = dbsmod.validar_e_normalizar(dbsmod.db_f1_historica(ano_hist))
        if _norm_h:
            sel_db = _norm_h
        elif _erros_h:
            st.error(f"Temporada inválida: {'; '.join(_erros_h)}")
    meta = sel_db["meta"]
    ci1, ci2, ci3, ci4 = st.columns(4)
    ci1.metric("Categoria", meta.get("categoria", "—"))
    ci2.metric("Ano inicial", meta.get("ano", "—"))
    ci3.metric("Equipes", len(sel_db["equipes"]))
    ci4.metric("Pilotos no grid / Etapas", f"{dbsmod.grid_natural(sel_db)} / {len(sel_db['calendario'])}")
    if meta.get("descricao"):
        st.info(meta["descricao"])
    tem_cancelavel = any(e.get("cancelavel") for e in sel_db["calendario"])
    st.text_input(
        "👤 Seu nome (gerente)",
        value="",
        key="gerente",
        placeholder="ex.: Vick",
        help='Como no original: seu nome aparece no topo do Escritório ("Vick 1999, 2ª etapa").',
    )

    tab_equipe, tab_criar, tab_editor, tab_load = st.tabs(
        ["🏁 Escolher uma equipe", "🆕 Criar minha equipe", "🛠️ Criar / editar DB", "💾 Carregar save"]
    )

    with tab_equipe:
        nomes = {
            e[
                "id"
            ]: f"[{bnd.codigo_texto(e['bandeira'])}] {e['nome']} — carro {e['nivel_carro']:.0f} · caixa {sim.fmt_dinheiro_m(e['caixa'])}"
            for e in sel_db["equipes"]
        }
        eq_id = st.selectbox(
            f"Sua equipe para {meta.get('ano', '')}", list(nomes.keys()), format_func=lambda x: nomes[x]
        )
        eq = next(e for e in sel_db["equipes"] if e["id"] == eq_id)
        mot = next((m for m in sel_db["motores"] if m["id"] == eq["motor_id"]), sel_db["motores"][0])
        rot = meta.get("rotulo_fornecedor", "Motor")
        st.markdown(
            f'<div class="team-bar" style="background:linear-gradient(112deg,{eq["cor"]} 0%, rgba(13,17,26,.93) 58%, #0D111A 100%)">'
            f'<div class="team-main"><div class="team-flag">{bnd.img_bandeira(eq["bandeira"], 44)}</div>'
            f'<div><div class="kicker">{eq["pais"]}</div><h2>{eq["nome_completo"]}</h2>'
            f"<p>{rot} {'próprio' if eq.get('motor_proprio') else 'cliente'}: <b>{mot['nome']}</b> "
            f"(desempenho {mot['potencia']}) · Prestígio: {eq['prestigio']}</p></div></div></div>",
            unsafe_allow_html=True,
        )
        quad = sorted(
            [p for p in sel_db["pilotos"] if p["equipe_id"] == eq_id],
            key=lambda p: {"P1": 0, "P2": 1, "P3": 2, "P4": 3, "teste": 4}.get(p["papel"], 5),
        )
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Bandeira": bnd.url_bandeira(p["bandeira"]),
                        "Piloto": p["nome"],
                        "#": p["numero"],
                        "Idade": p["idade"],
                        "Função": {
                            "P1": "1o piloto",
                            "P2": "2o piloto",
                            "P3": "3o piloto",
                            "P4": "4o piloto",
                            "teste": "Testes/reserva",
                        }.get(p["papel"], p["papel"]),
                        "Overall": sim.overall(p),
                        "Salário/corrida": sim.fmt_dinheiro_k(p["salario_corrida"]),
                    }
                    for p in quad
                ]
            ),
            hide_index=True,
            width="stretch",
            column_config=CFG_BANDEIRA,
        )

        qtd_grid = _slider_grid(sel_db)
        c1, c2, c3 = st.columns(3)
        incluir = True
        if tem_cancelavel:
            incluir = c1.checkbox("Calendário completo (inclui etapas canceláveis da DB)", value=True)
        imp = (
            c2.slider(
                "Importância do carro (%)",
                30,
                90,
                int(float(meta.get("importancia_carro_sugerida", 0.6)) * 100),
                5,
                help="Sugerido pela DB: F1 60%, Indy 45%, Stock 40%, DTM 50%.",
            )
            / 100.0
        )
        semente = c3.number_input("semente (aleatoriedade)", 1, 99999, 2026)
        if st.button("🚥 Iniciar carreira", type="primary", width="stretch"):
            st.session_state.game = sim.criar_novo_jogo(
                eq_id, int(semente), incluir, imp, db_dados=sel_db, qtd_pilotos=qtd_grid
            )
            st.session_state.game["gerente"] = str(st.session_state.get("gerente", "") or "").strip()
            st.session_state.fds = None
            st.session_state.menu = MENUS[0]
            flash(
                "success",
                f"Bem-vindo ao comando da {eq['nome']}! Primeira parada: "
                f"{sel_db['calendario'][0]['gp']}. Grid com {qtd_grid} pilotos.",
            )
            st.rerun()

    with tab_criar:
        st.write(
            f"Entre como **equipe extra** no grid da DB **{meta.get('nome')}**, do seu jeito — "
            f"como no modo 'nova equipe' do original. O grid terá o tamanho natural da DB + os seus 2 carros."
        )
        c1, c2 = st.columns(2)
        nome_custom = c1.text_input("Nome da equipe", "Minha Equipe")
        pais_custom = c2.text_input("País sede", "Brasil")
        cor_custom = c1.color_picker("Cor do carro", "#009C3B")
        fornecedores_disp: list[dict] = [m for m in sel_db["motores"] if not m.get("proprio_de") and m["id"] != "fia"]
        mot_custom = c2.selectbox(
            f"{meta.get('rotulo_fornecedor', 'Motor')}",
            fornecedores_disp,
            format_func=lambda m: f"{m['nome']} — desempenho {m['potencia']} · US$ {m['preco']:.0f} mi/ano",
        )
        assert mot_custom is not None  # selectbox com lista não vazia sempre escolhe um valor
        perfil = st.radio(
            "Perfil do projeto",
            ["🥾 Estreante pé-rapado", "💼 Investidor sério", "🏭 Projeto de montadora"],
            horizontal=True,
        )
        perfil_map = {
            "🥾 Estreante pé-rapado": (70.0, 55, 35),
            "💼 Investidor sério": (140.0, 62, 50),
            "🏭 Projeto de montadora": (190.0, 70, 60),
        }
        caixa_c, carro_c, prest_c = perfil_map[perfil]
        livres = [p for p in sel_db["pilotos"] if p["papel"] == "livre"]
        if len(livres) < 3:
            st.warning(
                "Esta DB tem poucos pilotos livres para montar uma equipe nova. "
                "Edite a DB na aba 🛠️ e adicione pilotos 'livre', ou escolha outra DB."
            )
        else:
            fmt_p = lambda pid: next(
                f"[{bnd.codigo_texto(p['bandeira'])}] {p['nome']} (ovr {sim.overall(p)}, {p['idade']} anos)"
                for p in livres
                if p["id"] == pid
            )
            ids_livres = [p["id"] for p in livres]
            c1, c2, c3 = st.columns(3)
            p1 = c1.selectbox("1o piloto", ids_livres, format_func=fmt_p)
            p2 = c2.selectbox("2o piloto", ids_livres, index=min(1, len(ids_livres) - 1), format_func=fmt_p)
            pt = c3.selectbox("Piloto de testes", ids_livres, index=min(2, len(ids_livres) - 1), format_func=fmt_p)
            if len({p1, p2, pt}) < 3:
                st.error("Escolha três pilotos diferentes.")
            elif st.button("🚥 Fundar equipe e iniciar", type="primary", width="stretch"):
                eq_c = {
                    "id": "custom",
                    "nome": nome_custom,
                    "nome_completo": nome_custom,
                    "pais": pais_custom,
                    "bandeira": "🏁",
                    "cor": cor_custom,
                    "motor_id": mot_custom["id"],
                    "motor_proprio": False,
                    "nivel_carro": carro_c,
                    "confiabilidade": 84,
                    "caixa": caixa_c,
                    "prestigio": prest_c,
                    "investimento_corrida": 1000,
                    "titulos_construtores": 0,
                    "patrocinador": "Lanchonetes BigBurguer",
                }
                contr = [
                    (pid, papel, sim.salario_esperado(None, next(p for p in livres if p["id"] == pid), papel))
                    for pid, papel in [(p1, "P1"), (p2, "P2"), (pt, "teste")]
                ]
                st.session_state.game = sim.criar_novo_jogo(
                    "custom",
                    2026,
                    True,
                    float(meta.get("importancia_carro_sugerida", 0.6)),
                    equipe_custom=eq_c,
                    pilotos_custom=contr,
                    db_dados=sel_db,
                )
                st.session_state.game["gerente"] = str(st.session_state.get("gerente", "") or "").strip()
                st.session_state.fds = None
                st.session_state.menu = MENUS[0]
                flash("success", f"A {nome_custom} nasceu na {meta.get('categoria')}! Boa sorte, chefe!")
                st.rerun()

    with tab_editor:
        editor_db.aba_editor_db(disp)

    with tab_load:
        st.subheader("🗂️ Continuar de um slot")
        slots = armazenamento.listar_saves()
        if not slots:
            st.caption("Nenhum slot salvo ainda — a tela **Salvar / Carregar** cria o primeiro.")
        else:
            nomes = [s["nome"] for s in slots]
            rotulos = {
                s["nome"]: f"{'(auto) ' if s['auto'] else ''}{s['nome']} — {s['equipe']}, {s['ano']} · etapa {s['rodada']}"
                for s in slots
            }
            escolha = st.selectbox("Slot", nomes, key="inicio_slot", format_func=lambda n: rotulos.get(n, n))
            if st.button("📂 Continuar esta carreira", type="primary", key="inicio_carregar"):
                try:
                    dados, avisos = armazenamento.carregar(escolha)
                    st.session_state.game = dados
                    st.session_state.fds = None
                    st.session_state.menu = MENUS[0]
                    flash(
                        "success",
                        f"Save carregado: temporada {dados['ano']}, etapa {dados['rodada'] + 1}."
                        + (f" ({avisos[0]})" if avisos else ""),
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Arquivo inválido: {e}")
        st.divider()
        st.subheader("📥 Enviar um arquivo")
        up = st.file_uploader("Arquivo de save (.json)", type="json", key="load_save")
        if up and st.button("Carregar save", type="primary"):
            try:
                dados, avisos = armazenamento.desserializar(up.read())
                st.session_state.game = dados
                st.session_state.fds = None
                st.session_state.menu = MENUS[0]
                flash(
                    "success",
                    f"Save carregado: temporada {dados['ano']}, etapa {dados['rodada'] + 1}."
                    + (f" ({avisos[0]})" if avisos else ""),
                )
                st.rerun()
            except Exception as e:
                st.error(f"Arquivo inválido: {e}")
