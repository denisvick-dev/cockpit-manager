# -*- coding: utf-8 -*-
"""
🏎️ COCKPIT MANAGER — Edição Streamlit (DB F1 2026)

Remake feito por fã, inspirado no Cockpit Manager '14 (Cartola Games, 2014)
e na DB F1 2026 v1.0 by Jonathan Daniel (blog Cockpit Manager - Brasil).

Rode com:  streamlit run app.py
"""
import json

import pandas as pd
import streamlit as st

import dados2026 as db
import simulacao as sim

st.set_page_config(page_title="Cockpit Manager — F1 2026", page_icon="🏎️", layout="wide")

st.markdown("""
<style>
  .team-bar {border-radius:10px; padding:14px 18px; color:#fff; margin-bottom:10px;}
  .team-bar h2 {margin:0; color:#fff;}
  .team-bar p {margin:2px 0 0 0; opacity:.92;}
  .news-card {background:rgba(255,255,255,.04); border-left:4px solid #E10600;
              border-radius:6px; padding:8px 12px; margin-bottom:6px;}
  .small {opacity:.75; font-size:.85em;}
  div[data-testid="stMetric"] {background:rgba(255,255,255,.03); border:1px solid rgba(255,255,255,.07);
                               border-radius:10px; padding:10px;}
</style>
""", unsafe_allow_html=True)

MENUS = ["🏠 Escritório", "🏁 Corrida", "🔧 Carro & Investimentos", "👨‍✈️ Pilotos & Contratos",
         "⚙️ Motores", "💰 Patrocinadores & Finanças", "📊 Campeonato",
         "🏆 Hall da Fama & Conquistas", "💾 Salvar / Carregar", "❓ Como Jogar"]

if "game" not in st.session_state:
    st.session_state.game = None
if "menu" not in st.session_state:
    st.session_state.menu = MENUS[0]
if "fds" not in st.session_state:
    st.session_state.fds = None
if "flash" not in st.session_state:
    st.session_state.flash = None


def ir_para(menu):
    st.session_state.menu = menu


def fmt_tempo(seg):
    m, s = divmod(seg, 60)
    return f"{int(m)}:{s:06.3f}"


def flash(tipo, texto):
    st.session_state.flash = (tipo, texto)


def mostrar_flash():
    if st.session_state.flash:
        tipo, texto = st.session_state.flash
        getattr(st, tipo, st.info)(texto)
        st.session_state.flash = None


# ======================================================================
#  TELA INICIAL
# ======================================================================
def tela_inicial():
    st.title("🏎️ Cockpit Manager — Edição Streamlit")
    st.subheader("DB F1 2026 · O 'Brasfoot da Fórmula 1' de volta ao navegador")
    st.caption("Remake de fã inspirado no *Cockpit Manager '14* (Cartola Games) e na "
               "[DB F1 2026 by Jonathan Daniel]"
               "(http://cockpitmanager.blogspot.com/2026/05/db-f1-2026-v10-by-jonathan-daniel.html). "
               "Contrate pilotos, desenvolva o carro, negocie motores e patrocinadores, "
               "acerte a estratégia de pneus e paradas — e não deixe o caixa zerar, "
               "senão a FIA te impõe o motor de 50% de potência!")

    tab_equipe, tab_criar, tab_load = st.tabs(["🏁 Escolher uma equipe", "🆕 Criar minha equipe", "💾 Carregar save"])

    with tab_equipe:
        nomes = {e["id"]: f"{e['bandeira']} {e['nome']} — carro {e['nivel_carro']} · caixa {sim.fmt_dinheiro_m(e['caixa'])}"
                 for e in db.EQUIPES}
        eq_id = st.selectbox("Sua equipe para 2026", list(nomes.keys()), format_func=lambda x: nomes[x])
        eq = next(e for e in db.EQUIPES if e["id"] == eq_id)
        mot = next(m for m in db.MOTORES if m["id"] == eq["motor_id"])
        st.markdown(f'<div class="team-bar" style="background:linear-gradient(90deg,{eq["cor"]},#151B2D)">'
                    f'<h2>{eq["bandeira"]} {eq["nome_completo"]}</h2>'
                    f'<p>Motor {"próprio" if eq["motor_proprio"] else "cliente"}: <b>{mot["nome"]}</b> '
                    f'(potência {mot["potencia"]}) · Títulos de construtores: {eq["titulos_construtores"]} · '
                    f'Prestígio: {eq["prestigio"]}</p></div>', unsafe_allow_html=True)
        quad = [p for p in db.PILOTOS if p["equipe_id"] == eq_id]
        st.dataframe(pd.DataFrame([{
            "Piloto": f"{p['bandeira']} {p['nome']}", "#": p["numero"], "Idade": p["idade"],
            "Função": {"P1": "1º piloto", "P2": "2º piloto", "teste": "Testes/reserva"}[p["papel"]],
            "Overall": sim.overall(p), "Salário/corrida": sim.fmt_dinheiro_k(p["salario_corrida"]),
        } for p in quad]), hide_index=True, width="stretch")

        c1, c2, c3 = st.columns(3)
        incluir = c1.checkbox("Calendário com 24 etapas (inclui Bahrein e Arábia Saudita)", value=True,
                              help="Na DB original as 24 etapas foram mantidas mesmo com os cancelamentos de 2026.")
        imp = c2.slider("Importância do carro (%)", 30, 90, 60, 5,
                        help="Padrão 60% das DBs da comunidade — reflete a F1 moderna.") / 100.0
        semente = c3.number_input("semente (aleatoriedade)", 1, 99999, 2026)
        if st.button("🚥 Iniciar carreira", type="primary", width="stretch"):
            st.session_state.game = sim.criar_novo_jogo(eq_id, int(semente), incluir, imp)
            st.session_state.fds = None
            flash("success", f"Bem-vindo ao comando da {eq['nome']}! Primeira parada: GP da Austrália 🇦🇺")
            st.rerun()

    with tab_criar:
        st.write("Entre como a **12ª equipe** do grid, do seu jeito — como no modo 'nova equipe' do original.")
        c1, c2 = st.columns(2)
        nome_custom = c1.text_input("Nome da equipe", "Minha Equipe F1")
        pais_custom = c2.text_input("País sede", "Brasil")
        cor_custom = c1.color_picker("Cor do carro", "#009C3B")
        motores_disp = [m for m in db.MOTORES if not m["proprio_de"] and m["id"] != "fia"]
        mot_custom = c2.selectbox("Motor (fornecedores independentes/clientes)", motores_disp,
                                  format_func=lambda m: f"{m['nome']} — potência {m['potencia']} · US$ {m['preco']:.0f} mi/ano")
        perfil = st.radio("Perfil do projeto", ["🥾 Estreante pé-rapado", "💼 Investidor sério", "🏭 Projeto de montadora"],
                          horizontal=True)
        perfil_map = {"🥾 Estreante pé-rapado": (70.0, 55, 35), "💼 Investidor sério": (140.0, 62, 50),
                      "🏭 Projeto de montadora": (190.0, 70, 60)}
        caixa_c, carro_c, prest_c = perfil_map[perfil]
        livres = [p for p in db.PILOTOS if p["papel"] == "livre"]
        fmt_p = lambda pid: next(f"{p['bandeira']} {p['nome']} (ovr {sim.overall(p)}, {p['idade']} anos)" for p in livres if p["id"] == pid)
        ids_livres = [p["id"] for p in livres]
        c1, c2, c3 = st.columns(3)
        p1 = c1.selectbox("1º piloto", ids_livres, format_func=fmt_p)
        p2 = c2.selectbox("2º piloto", ids_livres, index=1, format_func=fmt_p)
        pt = c3.selectbox("Piloto de testes", ids_livres, index=2, format_func=fmt_p)
        incluir_c = st.checkbox("24 etapas (Bahrein + Arábia Saudita)", value=True, key="inc_c")
        if len({p1, p2, pt}) < 3:
            st.error("Escolha três pilotos diferentes.")
        elif st.button("🚥 Fundar equipe e iniciar", type="primary", width="stretch"):
            eq_c = {"id": "custom", "nome": nome_custom, "nome_completo": nome_custom,
                    "pais": pais_custom, "bandeira": "🏁", "cor": cor_custom,
                    "motor_id": mot_custom["id"], "motor_proprio": False, "nivel_carro": carro_c,
                    "confiabilidade": 84, "caixa": caixa_c, "prestigio": prest_c,
                    "investimento_corrida": 1000, "titulos_construtores": 0,
                    "patrocinador": "Lanchonetes BigBurguer"}
            contr = [(pid, papel, sim.salario_esperado(None, next(p for p in livres if p["id"] == pid), papel))
                     for pid, papel in [(p1, "P1"), (p2, "P2"), (pt, "teste")]]
            st.session_state.game = sim.criar_novo_jogo("custom", 2026, incluir_c, 0.60,
                                                        equipe_custom=eq_c, pilotos_custom=contr)
            st.session_state.fds = None
            flash("success", f"A {nome_custom} nasceu! 24 carros no grid em 2026. Boa sorte, chefe!")
            st.rerun()

    with tab_load:
        up = st.file_uploader("Arquivo de save (.json)", type="json")
        if up and st.button("Carregar save", type="primary"):
            try:
                dados = json.loads(up.read().decode("utf-8"))
                assert "equipes" in dados and "pilotos" in dados and "ano" in dados
                st.session_state.game = dados
                st.session_state.fds = None
                flash("success", f"Save carregado: temporada {dados['ano']}, etapa {dados['rodada'] + 1}.")
                st.rerun()
            except Exception as e:
                st.error(f"Arquivo inválido: {e}")


# ======================================================================
#  COMPONENTES REUTILIZÁVEIS
# ======================================================================
def df_pilotos_equipe(game, equipe_id):
    linhas = []
    for p in sorted([x for x in game["pilotos"] if x["equipe_id"] == equipe_id and not x["aposentado"]],
                    key=lambda x: {"P1": 0, "P2": 1, "teste": 2}.get(x["papel"], 3)):
        a = p["atributos"]
        linhas.append({"Piloto": f"{p['bandeira']} {p['nome']}", "#": p["numero"], "Idade": p["idade"],
                       "Função": {"P1": "1º piloto", "P2": "2º piloto", "teste": "Testes"}[p["papel"]],
                       "Overall": sim.overall(p), "Velocidade": a["velocidade"], "Chuva": a["chuva"],
                       "Concentração": a["concentracao"], "Largada": a["largada"],
                       "Ultrapassagem": a["ultrapassagem"], "Acerto": a["acerto"], "Físico": a["fisico"],
                       "Forma": p["forma"], "Pontos": p["pontos"],
                       "Salário/corrida": p["salario_corrida"], "Contrato": f"{p['contrato_anos']} ano(s)"})
    return pd.DataFrame(linhas)


def barra_equipe(eq):
    st.markdown(f'<div class="team-bar" style="background:linear-gradient(90deg,{eq["cor"]},#151B2D)">'
                f'<h2>{eq["bandeira"]} {eq["nome_completo"]}</h2></div>', unsafe_allow_html=True)


def painel_fim_temporada(game):
    tab_p, tab_c = sim.tabela_pilotos(game), sim.tabela_construtores(game)
    st.success(f"🏁 **Fim da temporada {game['ano']}!**")
    if tab_p:
        camp = tab_p[0]
        st.markdown(f"🏆 Campeão de Pilotos: **{camp['bandeira']} {camp['nome']}** "
                    f"({sim.equipe(game, camp['equipe_id'])['nome']}) — {camp['pontos']} pts")
    if tab_c:
        st.markdown(f"🏭 Campeã de Construtores: **{tab_c[0]['bandeira']} {tab_c[0]['nome']}** — {tab_c[0]['pontos']} pts")
    eqj = sim.equipe(game, game["equipe_jogador"])
    st.markdown(f"Sua equipe terminou em **{sim.posicao_equipe(game, eqj['id'])}º** com {eqj['pontos']} pontos.")
    if game["contratos_proxima"]:
        st.info("✍️ Contratos já fechados para a próxima temporada: " +
                ", ".join(sim.piloto(game, pid)["nome"] for pid in game["contratos_proxima"]))
    else:
        st.warning("Você não fechou nenhum contrato novo. Passe em **Pilotos & Contratos**, **Motores** e "
                   "**Patrocinadores** antes de virar a temporada (renovações valem ouro!).")
    if st.button("📅 Virar a temporada (mercado, evolução dos pilotos, carro novo)", type="primary", width="stretch"):
        res = sim.virar_temporada(game)
        st.session_state.fds = None
        flash("success", f"Temporada {game['ano']} começou! Campeões de {game['ano'] - 1}: "
                         f"{res['campeao_pilotos']} / {res['campea_construtores']}.")
        st.balloons()
        st.rerun()


# ======================================================================
#  ESCRITÓRIO (tela principal, como o "resumo" do CM14)
# ======================================================================
def pagina_escritorio(game):
    eqj = sim.equipe(game, game["equipe_jogador"])
    barra_equipe(eqj)
    fim = game["rodada"] >= len(game["calendario"])
    mot = sim.motor(game, eqj["motor_id"])

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Temporada", game["ano"])
    c2.metric("Etapa", "Fim!" if fim else f"{game['rodada'] + 1}/{len(game['calendario'])}")
    c3.metric("Caixa", sim.fmt_dinheiro_m(eqj["caixa"]))
    c4.metric("Construtores", f"{sim.posicao_equipe(game, eqj['id'])}º · {eqj['pontos']} pts")
    c5.metric("Vitórias (carreira)", eqj["vitorias_carreira"])

    col_carro, col_prox = st.columns([1, 1])
    with col_carro:
        st.subheader("🔧 Seu carro")
        st.write(f"Nível do chassi: **{eqj['nivel_carro']:.1f}**")
        st.progress(min(1.0, eqj["nivel_carro"] / 100))
        st.write(f"Motor **{mot['nome']}** — potência **{mot['potencia']}** "
                 f"{'(próprio)' if eqj.get('motor_proprio') else '(cliente)'}")
        st.progress(mot["potencia"] / 100)
        st.write(f"Desempenho combinado: **{sim.desempenho_carro(game, eqj):.1f}** · "
                 f"Confiabilidade: **{eqj['confiabilidade']:.0f}**")
        st.write(f"Investimento por corrida: **{sim.fmt_dinheiro_k(eqj['investimento_corrida'])}** "
                 f"· Foco: **{eqj['foco']}** · Patrocinador: **{eqj['patrocinador']}**")
        ranking = sorted(game["equipes"], key=lambda e: -sim.desempenho_carro(game, e))
        st.caption(f"Seu carro é o {ranking.index(eqj) + 1}º mais rápido do grid hoje "
                   f"(melhor: {ranking[0]['nome']}, {sim.desempenho_carro(game, ranking[0]):.1f}).")
    with col_prox:
        if fim:
            painel_fim_temporada(game)
        else:
            etapa = game["calendario"][game["rodada"]]
            st.subheader(f"📅 Próxima corrida: {etapa['bandeira']} {etapa['gp']}")
            st.write(f"**{etapa['circuito']}** — {etapa['pais']} · {etapa['voltas']} voltas · {etapa['data']}"
                     + (" · ⚡ **fim de semana Sprint**" if etapa["sprint"] else ""))
            st.write(f"🌧️ Chance histórica de chuva: **{etapa['chuva'] * 100:.0f}%** · "
                     f"Desgaste de pneus: **{etapa['desgaste']:.1f}/3** · "
                     f"Ultrapassagem: **{etapa['ultrap'] * 100:.0f}%**")
            st.button("▶️ CONTINUAR — ir para a corrida", type="primary", width="stretch",
                      on_click=ir_para, args=("🏁 Corrida",))

    st.subheader("👨‍✈️ Seus pilotos")
    st.dataframe(df_pilotos_equipe(game, eqj["id"]), hide_index=True, width="stretch",
                 column_config={c: st.column_config.ProgressColumn(c, min_value=0, max_value=100, format="%d")
                                for c in ["Velocidade", "Chuva", "Concentração", "Largada", "Ultrapassagem", "Acerto", "Físico", "Forma"]})

    st.subheader("📰 Notícias do paddock")
    for n in game["noticias"][:8]:
        st.markdown(f'<div class="news-card"><span class="small">{n["ano"]} · etapa {n["rodada"]}</span><br>{n["texto"]}</div>',
                    unsafe_allow_html=True)


# ======================================================================
#  CORRIDA
# ======================================================================
def obter_fds(game, etapa):
    chave = f"{game['ano']}-{game['rodada']}"
    if not st.session_state.fds or st.session_state.fds.get("chave") != chave:
        st.session_state.fds = {"chave": chave, "molhado": sim.sortear_clima(game, etapa),
                                "grid": None, "sprint": None, "resultado": None, "resumo": None, "eventos": []}
    return st.session_state.fds


def df_grid(game, grid):
    return pd.DataFrame([{
        "Pos": g["pos"], "Piloto": f"{sim.piloto(game, g['piloto_id'])['bandeira']} {sim.piloto(game, g['piloto_id'])['nome']}",
        "Equipe": sim.equipe(game, g["equipe_id"])["nome"], "": "⭐" if g["equipe_id"] == game["equipe_jogador"] else "",
        "Tempo": fmt_tempo(g["tempo"]), "Gap": "—" if g["gap"] == 0 else f"+{g['gap']:.3f}",
    } for g in grid])


def df_resultado(game, resultado):
    linhas = []
    for l in resultado:
        p = sim.piloto(game, l["piloto_id"])
        est = l["estrategia"]
        linhas.append({
            "Pos": l["pos"], "Piloto": f"{p['bandeira']} {p['nome']}", "Equipe": sim.equipe(game, l["equipe_id"])["nome"],
            "": "⭐" if l["equipe_id"] == game["equipe_jogador"] else "",
            "Grid": l["grid"], "▲▼": l["grid"] - l["pos"],
            "Pneu": est["pneu"], "Paradas": est["paradas"], "Ritmo": est["ritmo"],
            "Gap/Status": l["status"] if l["dnf"] else ("Vencedor" if l["pos"] == 1 else f"+{l['gap_seg']:.1f}s"),
            "VR": "⚡" if l.get("volta_rapida") else "", "Pontos": l["pontos"],
        })
    return pd.DataFrame(linhas)


def pagina_corrida(game):
    if game["rodada"] >= len(game["calendario"]):
        painel_fim_temporada(game)
        return
    etapa = game["calendario"][game["rodada"]]
    fds = obter_fds(game, etapa)
    molhado = fds["molhado"]
    eqj = sim.equipe(game, game["equipe_jogador"])
    meus = sim.titulares(game, eqj["id"])

    st.header(f"{etapa['bandeira']} {etapa['gp']} — {etapa['circuito']}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Etapa", f"{game['rodada'] + 1}/{len(game['calendario'])} · {game['ano']}")
    c2.metric("Voltas", etapa["voltas"])
    c3.metric("Clima", "🌧️ Molhado" if molhado else "☀️ Seco")
    c4.metric("Formato", "⚡ Sprint + GP" if etapa["sprint"] else "GP clássico")
    st.caption(f"Características: peso do motor {etapa['potencia'] * 100:.0f}% · facilidade de ultrapassar "
               f"{etapa['ultrap'] * 100:.0f}% · desgaste {etapa['desgaste']:.1f}/3 → estratégia típica: "
               f"**{sim.paradas_ideais(etapa)} parada(s)**")

    # ---------------- estratégia dos seus dois pilotos
    st.subheader("🎯 Sua estratégia (pneu, paradas e ritmo — o coração do Cockpit Manager)")
    estrategias = {}
    cols = st.columns(len(meus))
    opcoes_pneu = sim.PNEUS_MOLHADO + sim.PNEUS_SECO if molhado else sim.PNEUS_SECO
    for col, p in zip(cols, meus):
        with col:
            st.markdown(f"**{p['bandeira']} #{p['numero']} {p['nome']}** ({p['papel']})")
            pneu = st.selectbox("Pneu de largada", opcoes_pneu, index=0 if molhado else 1,
                                key=f"pneu_{p['id']}_{fds['chave']}")
            paradas = st.radio("Paradas nos boxes", [1, 2, 3],
                               index=[1, 2, 3].index(sim.paradas_ideais(etapa)),
                               horizontal=True, key=f"par_{p['id']}_{fds['chave']}")
            ritmo = st.radio("Ritmo", sim.RITMOS, index=1, horizontal=True,
                             help="Atacar = mais rápido, desgasta pneu e aumenta risco de batida/quebra. "
                                  "Conservar = protege carro e pneus.",
                             key=f"rit_{p['id']}_{fds['chave']}")
            estrategias[p["id"]] = {"pneu": pneu, "paradas": paradas, "ritmo": ritmo}
            if molhado and pneu in sim.PNEUS_SECO:
                st.error("⚠️ Pneu slick na chuva?! Isso vai doer...")
            if not molhado and pneu in sim.PNEUS_MOLHADO:
                st.error("⚠️ Pneu de chuva no seco derrete em 3 voltas!")

    # ---------------- sprint
    if etapa["sprint"]:
        st.divider()
        st.subheader("⚡ Corrida Sprint (sábado)")
        if fds["sprint"] is None:
            if st.button("▶️ Simular Sprint", width="stretch"):
                grid_s = sim.simular_classificacao(game, etapa, molhado)
                est_s = {pid: {**e, "paradas": sim.paradas_ideais(etapa)} for pid, e in estrategias.items()}
                res_s, ev_s = sim.simular_corrida(game, etapa, grid_s, est_s, molhado, sprint=True)
                sim.aplicar_resultado(game, etapa, grid_s, res_s, molhado, sprint=True, eventos=ev_s)
                fds["sprint"] = res_s
                st.rerun()
        else:
            st.dataframe(df_resultado(game, fds["sprint"]), hide_index=True, width="stretch")
            st.caption("Pontos da sprint (8-7-6-5-4-3-2-1) já somados ao campeonato.")

    # ---------------- classificação
    st.divider()
    st.subheader("⏱️ Classificação")
    if fds["grid"] is None:
        if st.button("▶️ Simular classificação", width="stretch",
                     disabled=(etapa["sprint"] and fds["sprint"] is None)):
            fds["grid"] = sim.simular_classificacao(game, etapa, molhado)
            pole = sim.piloto(game, fds["grid"][0]["piloto_id"])
            flash("info", f"Pole position: {pole['bandeira']} {pole['nome']} ({fmt_tempo(fds['grid'][0]['tempo'])})")
            st.rerun()
        if etapa["sprint"] and fds["sprint"] is None:
            st.caption("Primeiro simule a Sprint de sábado.")
    else:
        st.dataframe(df_grid(game, fds["grid"]), hide_index=True, width="stretch")

    # ---------------- corrida principal
    st.divider()
    st.subheader("🏁 Corrida principal")
    if fds["resultado"] is None:
        if st.button("🚥 LARGADA!", type="primary", width="stretch", disabled=fds["grid"] is None):
            res, ev = sim.simular_corrida(game, etapa, fds["grid"], estrategias, molhado)
            fds["resumo"] = sim.aplicar_resultado(game, etapa, fds["grid"], res, molhado, eventos=ev)
            fds["resultado"], fds["eventos"] = res, ev
            venceu = any(l["equipe_id"] == eqj["id"] and l["pos"] == 1 and not l["dnf"] for l in res)
            if venceu:
                st.balloons()
            st.rerun()
    else:
        st.dataframe(df_resultado(game, fds["resultado"]), hide_index=True, width="stretch")
        for ev in fds["eventos"]:
            st.markdown(f"- {ev}")
        if fds["resumo"]:
            st.markdown("**💰 Balanço do fim de semana:** " +
                        " · ".join(f"{d} {sim.fmt_dinheiro_k(v) if v >= 0 else '−' + sim.fmt_dinheiro_k(-v)}"
                                   for d, v in fds["resumo"]) +
                        f" → caixa atual: **{sim.fmt_dinheiro_m(eqj['caixa'])}**")
        prox = "Encerrar a temporada 🏁" if game["rodada"] >= len(game["calendario"]) else "Continuar ▶️"
        if st.button(prox, type="primary", width="stretch"):
            st.session_state.fds = None
            ir_para("🏠 Escritório")
            st.rerun()


# ======================================================================
#  CARRO & INVESTIMENTOS
# ======================================================================
def pagina_carro(game):
    eqj = sim.equipe(game, game["equipe_jogador"])
    mot = sim.motor(game, eqj["motor_id"])
    st.header("🔧 Carro & Investimentos")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nível do chassi", f"{eqj['nivel_carro']:.1f}")
    c2.metric(f"Motor {mot['nome']}", f"{mot['potencia']} pot / {mot['confiabilidade']} conf")
    c3.metric("Desempenho combinado", f"{sim.desempenho_carro(game, eqj):.1f}")
    c4.metric("Confiabilidade do carro", f"{eqj['confiabilidade']:.0f}")

    st.subheader("💸 Investimento por corrida")
    inv = st.slider("Quanto investir no desenvolvimento a cada corrida (US$ mil)", 0, 3000,
                    int(eqj["investimento_corrida"]), 50)
    eqj["investimento_corrida"] = inv
    eqj["foco"] = st.radio("Foco do desenvolvimento",
                           ["equilibrado", "chassi", "confiabilidade"],
                           index=["equilibrado", "chassi", "confiabilidade"].index(eqj["foco"]),
                           horizontal=True,
                           format_func=lambda x: {"equilibrado": "⚖️ Equilibrado", "chassi": "🏎️ Chassi/aero (mais velocidade)",
                                                  "confiabilidade": "🛡️ Confiabilidade (menos abandonos)"}[x])
    teste = sim.piloto_teste(game, eqj["id"])
    feedback = (sum(t["atributos"]["acerto"] for t in sim.titulares(game, eqj["id"])) / 2) * 0.7 + \
               ((teste["atributos"]["acerto"] * 0.3) if teste else 21)
    ganho = (inv / 1000.0) * 0.22 * (feedback / 85.0) * max(0.12, (99.5 - eqj["nivel_carro"]) / 35.0)
    st.info(f"Feedback dos pilotos (Acerto): **{feedback:.0f}** → ganho estimado de "
            f"**+{ganho:.2f}** de nível por corrida. Piloto de testes com Acerto alto acelera tudo — "
            f"o seu é {teste['nome'] if teste else '—'} (Acerto {teste['atributos']['acerto'] if teste else '—'}).")
    st.caption("⚠️ Investir demais quebra o caixa (e sem caixa, sem motor decente na próxima temporada). "
               "No CM14 original, esse era O erro fatal dos novatos.")

    st.subheader("📏 Nível das equipes (como em Campeonato → Equipes do original)")
    linhas = []
    for e in sorted(game["equipes"], key=lambda x: -sim.desempenho_carro(game, x)):
        m = sim.motor(game, e["motor_id"])
        linhas.append({"Equipe": f"{e['bandeira']} {e['nome']}", "": "⭐" if e["id"] == eqj["id"] else "",
                       "Chassi": round(e["nivel_carro"], 1), "Motor": m["nome"],
                       "Potência": m["potencia"], "Desempenho": round(sim.desempenho_carro(game, e), 1),
                       "Confiabilidade": round(e["confiabilidade"]), "Prestígio": e["prestigio"],
                       "Caixa (mi)": round(e["caixa"], 1)})
    df = pd.DataFrame(linhas)
    st.dataframe(df, hide_index=True, width="stretch",
                 column_config={c: st.column_config.ProgressColumn(c, min_value=0, max_value=100, format="%.0f")
                                for c in ["Chassi", "Potência", "Desempenho", "Confiabilidade"]})
    st.bar_chart(df.set_index("Equipe")["Desempenho"])


# ======================================================================
#  PILOTOS & CONTRATOS
# ======================================================================
def pagina_pilotos(game):
    eqj = sim.equipe(game, game["equipe_jogador"])
    st.header("👨‍✈️ Pilotos & Contratos")
    tab1, tab2, tab3 = st.tabs(["Minha equipe", "🤝 Negociar (próxima temporada)", "🌍 Todos os pilotos"])

    with tab1:
        st.dataframe(df_pilotos_equipe(game, eqj["id"]), hide_index=True, width="stretch")
        total_sal = sum(p["salario_corrida"] for p in game["pilotos"] if p["equipe_id"] == eqj["id"])
        st.caption(f"Custo total de salários: {sim.fmt_dinheiro_k(total_sal)} por corrida.")
        if game["contratos_proxima"]:
            st.subheader(f"✍️ Já contratados para {game['ano'] + 1}")
            for pid, c in list(game["contratos_proxima"].items()):
                p = sim.piloto(game, pid)
                col1, col2 = st.columns([5, 1])
                col1.write(f"**{p['bandeira']} {p['nome']}** — {c['papel']} · {sim.fmt_dinheiro_k(c['salario'])}/corrida · {c['anos']} ano(s)")
                if col2.button("Cancelar", key=f"canc_{pid}"):
                    del game["contratos_proxima"][pid]
                    st.rerun()

    with tab2:
        st.caption("Como no original: você negocia **durante** a temporada, mas o piloto só veste seu macacão "
                   "na **próxima**. Salários são por corrida.")
        ativos = [p for p in game["pilotos"] if not p["aposentado"]]
        ativos.sort(key=lambda p: -sim.overall(p))
        sel = st.selectbox("Piloto", ativos,
                           format_func=lambda p: f"{p['bandeira']} {p['nome']} — ovr {sim.overall(p)} · {p['idade']} anos · "
                                                 f"{(sim.equipe(game, p['equipe_id'])['nome'] if p['equipe_id'] else 'LIVRE')} ({p['papel']})")
        a = sel["atributos"]
        st.bar_chart(pd.Series({db.ATRIBUTOS[k]: v for k, v in a.items()}))
        st.caption(f"Auge: {sel['auge_inicio']}–{sel['auge_fim']} anos (platô) · Potencial: {sel['potencial']} · "
                   f"Vitórias no save: {sel['vitorias']} · Títulos: {sel['titulos']}")
        with st.form("form_contrato"):
            papel = st.radio("Papel oferecido", ["P1", "P2", "teste"], horizontal=True,
                             format_func=lambda x: {"P1": "1º piloto", "P2": "2º piloto", "teste": "Testes/reserva"}[x])
            esperado = sim.salario_esperado(game, sel, papel)
            salario = st.number_input(f"Salário oferecido (US$ mil/corrida) — o mercado pagaria ±{sim.fmt_dinheiro_k(esperado)}",
                                      min_value=10, max_value=6000, value=int(esperado), step=10)
            anos = st.slider("Duração (anos)", 1, 4, 2)
            if st.form_submit_button("✍️ Fazer proposta", type="primary", width="stretch"):
                ok, msg = sim.negociar_piloto(game, sel["id"], papel, int(salario), anos)
                flash("success" if ok else "error", msg)
                st.rerun()

    with tab3:
        linhas = []
        for p in sorted(ativos, key=lambda x: -x["pontos"]):
            linhas.append({"Piloto": f"{p['bandeira']} {p['nome']}", "Idade": p["idade"],
                           "Equipe": sim.equipe(game, p["equipe_id"])["nome"] if p["equipe_id"] else "— LIVRE —",
                           "Papel": p["papel"], "Overall": sim.overall(p), "Potencial": p["potencial"],
                           "Pontos": p["pontos"], "Vitórias*": p["vitorias"], "Pódios*": p["podios"],
                           "Títulos*": p["titulos"], "Salário": p["salario_corrida"]})
        st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch")
        st.caption("* Estatísticas acumuladas dentro deste save.")


# ======================================================================
#  MOTORES
# ======================================================================
def pagina_motores(game):
    eqj = sim.equipe(game, game["equipe_jogador"])
    st.header("⚙️ Motores")
    atual = sim.motor(game, eqj["motor_id"])
    st.write(f"Motor atual: **{atual['nome']}** — potência {atual['potencia']}, confiabilidade {atual['confiabilidade']}"
             + (" · **motor próprio** (custo interno reduzido; herança da equipe, como na DB: Audi/Ferrari/Mercedes/Red Bull)."
                if eqj.get("motor_proprio") else f" · custo de US$ {atual['preco']:.0f} mi/temporada."))
    df = pd.DataFrame([{"Motor": m["nome"], "": "⭐ atual" if m["id"] == eqj["motor_id"] else "",
                        "Potência": m["potencia"], "Confiabilidade": m["confiabilidade"],
                        "Preço (mi/ano)": m["preco"],
                        "Obs.": ("de fábrica" if m["proprio_de"] else "independente/cliente")}
                       for m in sorted(game["motores"], key=lambda x: -x["potencia"])])
    st.dataframe(df, hide_index=True, width="stretch",
                 column_config={c: st.column_config.ProgressColumn(c, min_value=0, max_value=100, format="%d")
                                for c in ["Potência", "Confiabilidade"]})
    for m in game["motores"]:
        st.caption(f"**{m['nome']}** — {m['desc']}")

    if eqj.get("motor_proprio"):
        st.info("Equipes com motor próprio não trocam de fornecedor (fidelidade à DB). "
                "Seu motor evolui um pouco a cada temporada junto com o investimento da fábrica.")
    else:
        st.subheader(f"🔁 Contrato para {game['ano'] + 1}")
        disponiveis = [m for m in game["motores"] if not m["proprio_de"] and m["id"] != "fia"]
        escolhido = st.selectbox("Próximo motor", disponiveis,
                                 format_func=lambda m: f"{m['nome']} — pot {m['potencia']} · US$ {m['preco']:.0f} mi/ano")
        if game["motor_proxima"]:
            st.success(f"Acordo fechado: motor **{sim.motor(game, game['motor_proxima'])['nome']}** em {game['ano'] + 1} "
                       f"(o valor é debitado na virada da temporada).")
        if st.button("✍️ Assinar contrato de motor", type="primary"):
            game["motor_proxima"] = escolhido["id"]
            flash("success", f"Motor {escolhido['nome']} garantido para {game['ano'] + 1} — se houver caixa para pagar!")
            st.rerun()
        st.caption("🚨 Se na virada da temporada o caixa não cobrir o motor, entra o lendário "
                   "**motor FIA compulsório (50% de potência)** — pesadelo de todo jogador de CM14.")


# ======================================================================
#  PATROCINADORES & FINANÇAS
# ======================================================================
def pagina_financas(game):
    eqj = sim.equipe(game, game["equipe_jogador"])
    st.header("💰 Patrocinadores & Finanças")
    spon = next(s for s in db.PATROCINADORES if s["nome"] == eqj["patrocinador"])
    salarios = sum(p["salario_corrida"] for p in game["pilotos"] if p["equipe_id"] == eqj["id"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Caixa", sim.fmt_dinheiro_m(eqj["caixa"]))
    c2.metric("Patrocinador atual", spon["nome"])
    c3.metric("Receita fixa/corrida", sim.fmt_dinheiro_k(spon["por_corrida"]))
    saldo = spon["por_corrida"] - salarios - eqj["investimento_corrida"]
    c4.metric("Saldo/corrida (sem bônus)", f"+ {sim.fmt_dinheiro_k(saldo)}" if saldo >= 0 else f"− {sim.fmt_dinheiro_k(-saldo)}")
    if saldo < 0:
        st.warning("Você gasta mais do que recebe por corrida (antes dos bônus por ponto/pódio). "
                   "Ou pontua muito, ou corta salário/investimento, ou troca o patrocinador na virada.")

    st.subheader(f"🤝 Patrocinadores disponíveis para {game['ano'] + 1} (seu prestígio: {eqj['prestigio']})")
    linhas = [{"Patrocinador": s["nome"], "": "⭐ atual" if s["nome"] == eqj["patrocinador"] else "",
               "Fixo/corrida": s["por_corrida"], "Bônus/ponto": s["bonus_ponto"],
               "Bônus/pódio": s["bonus_podio"], "Bônus/vitória": s["bonus_vitoria"],
               "Prestígio mín.": s["prestigio_min"],
               "Status": "✅ assina" if eqj["prestigio"] >= s["prestigio_min"] else "🔒 prestígio insuficiente"}
              for s in db.PATROCINADORES]
    st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch")
    elegiveis = [s for s in db.PATROCINADORES if eqj["prestigio"] >= s["prestigio_min"]]
    novo = st.selectbox("Negociar para a próxima temporada", elegiveis,
                        format_func=lambda s: f"{s['nome']} — {s['desc']}")
    if game["patrocinador_proxima"]:
        st.success(f"Fechado: **{game['patrocinador_proxima']}** estreia no carro em {game['ano'] + 1}.")
    if st.button("✍️ Assinar com este patrocinador", type="primary"):
        game["patrocinador_proxima"] = novo["nome"]
        flash("success", f"{novo['nome']} será o patrocinador master em {game['ano'] + 1}!")
        st.rerun()

    if game["historico_caixa"]:
        st.subheader("📈 Evolução do caixa (US$ mi)")
        st.line_chart(pd.DataFrame(game["historico_caixa"]).set_index("rodada")["caixa"])
    st.subheader("🧾 Extrato")
    if game["extrato"]:
        st.dataframe(pd.DataFrame(game["extrato"]).rename(columns={
            "temporada": "Ano", "etapa": "Etapa", "descricao": "Descrição", "valor": "US$ mil"}),
            hide_index=True, width="stretch")
    else:
        st.caption("Nenhum lançamento ainda. Bora correr!")


# ======================================================================
#  CAMPEONATO
# ======================================================================
def pagina_campeonato(game):
    st.header(f"📊 Campeonato {game['ano']}")
    tab1, tab2, tab3, tab4 = st.tabs(["👨‍✈️ Pilotos", "🏭 Construtores", "📈 Evolução", "🗓️ Calendário & Resultados"])

    with tab1:
        linhas = []
        for i, p in enumerate(sim.tabela_pilotos(game)):
            linhas.append({"Pos": i + 1, "Piloto": f"{p['bandeira']} {p['nome']}",
                           "Equipe": sim.equipe(game, p["equipe_id"])["nome"] if p["equipe_id"] else "—",
                           "": "⭐" if p["equipe_id"] == game["equipe_jogador"] else "",
                           "Pontos": p["pontos"], "Vitórias": p["vitorias"], "Pódios": p["podios"],
                           "Poles": p["poles"], "Abandonos": p["abandonos"], "Forma": p["forma"]})
        st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch")
    with tab2:
        linhas = [{"Pos": i + 1, "Equipe": f"{e['bandeira']} {e['nome']}",
                   "": "⭐" if e["id"] == game["equipe_jogador"] else "", "Pontos": e["pontos"],
                   "Vitórias": e["vitorias"], "Pódios": e["podios"], "Poles": e["poles"]}
                  for i, e in enumerate(sim.tabela_construtores(game))]
        st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch")
    with tab3:
        if game["historico_pontos"]:
            tab = sim.tabela_pilotos(game)[:8]
            dados = {p["nome"]: [h["pontos"].get(p["id"], 0) for h in game["historico_pontos"]] for p in tab}
            st.line_chart(pd.DataFrame(dados, index=[h["rodada"] for h in game["historico_pontos"]]))
        else:
            st.caption("Complete corridas para ver a evolução dos pontos.")
        if game["historico_temporadas"]:
            st.subheader("📜 Temporadas anteriores")
            st.dataframe(pd.DataFrame(game["historico_temporadas"]).rename(columns={
                "ano": "Ano", "campeao_pilotos": "Campeão (Pilotos)", "equipe_campea": "Campeã (Construtores)",
                "sua_posicao": "Sua posição", "seus_pontos": "Seus pontos"}), hide_index=True, width="stretch")
    with tab4:
        for i, etapa in enumerate(game["calendario"]):
            regs = [r for r in game["resultados"] if r["ano"] == game["ano"] and r["rodada"] == i + 1 and not r["sprint"]]
            with st.expander(f"{i + 1}. {etapa['bandeira']} {etapa['gp']} — {etapa['circuito']} · {etapa['voltas']} voltas"
                             + (" · ⚡Sprint" if etapa["sprint"] else "") + (" ✅" if regs else "")):
                if regs:
                    r = regs[-1]
                    st.caption("🌧️ Corrida molhada" if r["molhado"] else "☀️ Corrida seca")
                    st.dataframe(df_resultado(game, r["resultado"]), hide_index=True, width="stretch")
                else:
                    st.caption("Ainda não disputada.")


# ======================================================================
#  HALL DA FAMA & CONQUISTAS
# ======================================================================
def pagina_hall(game):
    st.header("🏆 Hall da Fama & Conquistas")
    tab1, tab2 = st.tabs(["🌟 Hall da Fama", "🎖️ Conquistas (10)"])
    with tab1:
        st.caption(f"Pilotos do seu save entram para a eternidade ao se aposentar com "
                   f"**≥ {db.HOF_MIN_TITULOS} títulos** ou **≥ {db.HOF_MIN_VITORIAS} vitórias** na carreira.")
        st.dataframe(pd.DataFrame([{
            "Lenda": f"{h['bandeira']} {h['nome']}", "País": h["pais"], "Títulos": h["titulos"],
            "Vitórias": h["vitorias"], "Era": h["anos"],
            "Origem": "induzido no seu save ✨" if h.get("induzido_no_save") else "histórico",
        } for h in sorted(game["hall_da_fama"], key=lambda x: (-x["titulos"], -x["vitorias"]))]),
            hide_index=True, width="stretch")
    with tab2:
        cols = st.columns(2)
        for i, c in enumerate(db.CONQUISTAS):
            ok = c["id"] in game["conquistas"]
            cols[i % 2].markdown(f"{'✅' if ok else '🔒'} {c['icone']} **{c['nome']}** — {c['desc']}")
        st.progress(len(game["conquistas"]) / len(db.CONQUISTAS),
                    text=f"{len(game['conquistas'])}/{len(db.CONQUISTAS)} conquistas")


# ======================================================================
#  SALVAR / CARREGAR
# ======================================================================
def pagina_save(game):
    st.header("💾 Salvar / Carregar")
    save_json = json.dumps(game, ensure_ascii=False, indent=1)
    st.download_button("⬇️ Baixar save (.json)", save_json,
                       file_name=f"cockpit_save_{game['ano']}_etapa{game['rodada'] + 1}.json",
                       mime="application/json", type="primary")
    st.caption("Guarde o arquivo e carregue na tela inicial para continuar a carreira em qualquer lugar.")
    st.divider()
    if st.checkbox("Entendo que começar um jogo novo apaga a carreira atual desta sessão"):
        if st.button("🗑️ Abandonar carreira e voltar ao início", type="primary"):
            st.session_state.game = None
            st.session_state.fds = None
            st.rerun()


# ======================================================================
#  COMO JOGAR
# ======================================================================
def pagina_ajuda():
    st.header("❓ Como Jogar — Cockpit Manager (Streamlit)")
    st.markdown("""
Comande uma equipe de F1 temporada após temporada, **sem limite de anos** — exatamente como o original de 2014.

### 🔁 O ciclo do jogo
1. **Escritório** — confira caixa, carro, pilotos, notícias e a próxima corrida. Clique em **Continuar**.
2. **Corrida** — veja o clima, monte a **estratégia de cada piloto** (pneu de largada, nº de paradas, ritmo),
   dispute a Sprint (se houver), a classificação e a corrida.
3. **Entre corridas** — o carro evolui sozinho conforme seu **investimento por corrida** e o **Acerto**
   (feedback) dos pilotos. Ajuste em *Carro & Investimentos*.
4. **Durante o ano inteiro** — negocie em *Pilotos & Contratos*, *Motores* e *Patrocinadores* pensando
   na **próxima temporada**. Na virada, tudo entra em vigor, pilotos envelhecem/evoluem, veteranos
   se aposentam e jovens da base sobem.

### 🏎️ Desempenho
- **Carro = 60%** do resultado (padrão das DBs da comunidade; ajustável ao criar o jogo). Dentro do carro,
  **um motor bom pesa muito**, principalmente em Monza, Baku, Spa e Las Vegas.
- **Piloto = 40%**, com 7 atributos clássicos: Velocidade, Chuva, Concentração, Largada, Ultrapassagem,
  Acerto de carro e Físico. Velocidade alta + Concentração baixa = rápido numa volta, mas vive na brita.
- **Auge com platô**: o piloto evolui até o início do auge, fica anos no topo e só depois declina
  (melhoria desta edição em relação à crítica clássica ao CM14).

### 🎯 Estratégia
| Pneu | Quando rende |
|---|---|
| Macio | Ritmo forte de largada; sofre em pista de desgaste alto com 1 parada |
| Médio | O coringa seguro |
| Duro | Ideal para 1 parada em pista abrasiva (Bahrein, Barcelona, Catar) |
| Intermediário / Chuva extrema | Obrigatórios com pista molhada — slick na chuva = desastre |

- **Paradas**: desgaste alto pede 2; pista travada (Mônaco, Hungaroring) premia parar menos (posição de pista!).
- **Ritmo "Atacar"**: ganha tempo, mas aumenta abandono e desgaste. **"Conservar"** protege carros frágeis.
- Em pistas sem ultrapassagem (Mônaco!), **classificação é a corrida**.

### 💸 Dinheiro (não seja a próxima Caterham)
Receita: patrocinador por corrida + bônus por ponto/pódio/vitória + premiação de Construtores no fim do ano.
Despesa: salários por corrida, investimento no carro, reparos e o **motor** na virada da temporada.
**Sem caixa para o motor? Motor FIA compulsório com 50% de potência.** Você foi avisado.

### ✍️ Mercado
Piloto bom custa caro e olha seu prestígio + nível do carro antes de assinar. Jovens com potencial alto
e salário baixo são o atalho clássico das equipes pequenas. Lembre que contratos valem **só na temporada seguinte**.

### 🌟 Hall da Fama & Conquistas
10 conquistas para caçar (como no original!) e um Hall da Fama com Senna, Schumacher, Lauda, Hunt...
Seus pilotos entram nele ao pendurar o capacete com 2+ títulos ou 30+ vitórias neste save.

---
**Créditos**: Jogo original *Cockpit Manager '14* — Cartola Games (2014), evolução do *Projeto F1* de Antonio Neto.
DB F1 2026 v1.0 por **Jonathan Daniel** — blog [Cockpit Manager - Brasil](http://cockpitmanager.blogspot.com/2026/05/db-f1-2026-v10-by-jonathan-daniel.html).
Este é um remake gratuito feito por fã, sem afiliação com F1, FIA ou Cartola Games.
""")


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
        st.markdown(f"## 🏎️ {eqj['bandeira']} {eqj['nome']}")
        st.caption(f"Temporada {game['ano']} · Etapa {min(game['rodada'] + 1, len(game['calendario']))}/{len(game['calendario'])}")
        st.metric("Caixa", sim.fmt_dinheiro_m(eqj["caixa"]))
        st.metric("Construtores", f"{sim.posicao_equipe(game, eqj['id'])}º · {eqj['pontos']} pts")
        st.radio("Menu", MENUS, key="menu", label_visibility="collapsed")
        st.divider()
        save_json = json.dumps(game, ensure_ascii=False)
        st.download_button("💾 Salvar (.json)", save_json,
                           file_name=f"cockpit_save_{game['ano']}.json", mime="application/json",
                           width="stretch")
        st.caption("Fan remake inspirado no Cockpit Manager '14 (Cartola Games) · "
                   "[DB F1 2026](http://cockpitmanager.blogspot.com/2026/05/db-f1-2026-v10-by-jonathan-daniel.html)")

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
