# -*- coding: utf-8 -*-
"""
🏎️ COCKPIT MANAGER — Edição Streamlit (DB F1 2026)

Remake feito por fã, inspirado no Cockpit Manager '14 (Cartola Games, 2014)
e na DB F1 2026 v1.0 by Jonathan Daniel (blog Cockpit Manager - Brasil).

Rode com:  streamlit run app.py
"""
import json
import re

import pandas as pd
import streamlit as st

import bandeiras as bnd
import dados2026 as db
import dbs as dbsmod
import editor_db
import simulacao as sim

st.set_page_config(page_title="Cockpit Manager", page_icon="🏎️", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
  :root{
    --cm-red:#C8102E; --cm-red2:#E02444; --cm-bg:#0B0F14; --cm-panel:#151C25;
    --cm-border:rgba(148,163,184,.16); --cm-text:#F4F7FB; --cm-muted:#94A3B8;
  }
  .stApp{
    background:
      radial-gradient(1100px 520px at 85% -10%, rgba(200,16,46,.14), transparent 60%),
      radial-gradient(900px 480px at -10% 0%, rgba(31,78,121,.16), transparent 55%),
      linear-gradient(180deg,#0B0F14 0%, #0D111A 100%);
    color:var(--cm-text);
  }
  .block-container{max-width:1480px; padding:2rem 2.4rem 3.2rem;}
  @media (max-width:760px){ .block-container{padding:1.1rem .9rem 2rem;} }
  h1,h2{letter-spacing:-.02em; color:#F8FAFC; font-weight:700;}
  h3{letter-spacing:.045em; color:#E2E8F0; font-weight:600;}
  a{color:#E4636F !important;}
  footer{visibility:hidden;} .stDeployButton{display:none;}

  /* ---------- bandeiras (imagens padronizadas 96x72) ---------- */
  .flag-img{border-radius:4px; object-fit:contain; vertical-align:-3px;
    box-shadow:0 1px 5px rgba(0,0,0,.45), 0 0 0 1px rgba(255,255,255,.14);}

  /* ---------- hero / marcas ---------- */
  .hero{border:1px solid var(--cm-border); border-radius:22px; overflow:hidden; margin-bottom:1.15rem;
    background:linear-gradient(115deg, rgba(200,16,46,.30), rgba(21,28,37,.94) 46%, rgba(10,14,23,.98));
    box-shadow:0 22px 55px rgba(0,0,0,.35);}
  .hero-inner{padding:1.65rem 1.8rem 1.25rem; display:flex; gap:1.15rem; align-items:center;}
  .logo-mark{width:66px;height:66px;flex:0 0 66px;border-radius:18px;display:flex;align-items:center;justify-content:center;
    background:linear-gradient(145deg,#D61437,#93021C); color:#fff; font-size:1.45rem; font-weight:700; letter-spacing:-.05em;
    box-shadow:0 14px 30px rgba(200,16,46,.35), inset 0 1px 0 rgba(255,255,255,.35);}
  .kicker{font-size:.68rem; font-weight:700; letter-spacing:.19em; text-transform:uppercase; color:#E88A90;}
  .hero h1{font-size:2.55rem; line-height:.98; margin:.18rem 0 .35rem;}
  .hero p{margin:0; color:#CBD5E1; max-width:820px; font-size:.98rem;}
  .chips{display:flex; flex-wrap:wrap; gap:.45rem; padding:0 1.8rem 1.35rem;}
  .chip{border:1px solid rgba(255,255,255,.16); background:rgba(255,255,255,.06); color:#E2E8F0;
    border-radius:999px; padding:.30rem .68rem; font-size:.76rem; font-weight:600;}
  .chip.hot{background:rgba(200,16,46,.18); border-color:rgba(224,36,68,.5); color:#FFD7D3;}
  .checker{height:10px; opacity:.92; background:repeating-conic-gradient(#E5E7EB 0% 25%, #111827 0% 50%); background-size:18px 18px;}
  @media (max-width:760px){ .hero-inner{padding:1.15rem} .hero h1{font-size:2rem} .logo-mark{width:52px;height:52px;flex-basis:52px} .chips{padding:0 1.15rem 1.1rem} }

  .page-head{border-bottom:1px solid var(--cm-border); margin:.1rem 0 1.15rem; padding-bottom:.85rem;}
  .page-head .kicker{color:#E4636F;}
  .page-head h1{font-size:2rem; margin:.12rem 0 .15rem;}
  .page-head p{margin:0; color:var(--cm-muted);}

  /* ---------- cartao da equipe ---------- */
  .team-bar{position:relative; overflow:hidden; border-radius:18px; padding:20px 22px; color:#fff; margin-bottom:14px;
    border:1px solid rgba(255,255,255,.14); box-shadow:0 18px 42px rgba(0,0,0,.32);}
  .team-bar::after{content:""; position:absolute; inset:0; pointer-events:none;
    background:linear-gradient(115deg, rgba(255,255,255,.16), transparent 42%);}
  .team-main{position:relative; z-index:1; display:flex; align-items:center; gap:16px;}
  .team-flag{background:rgba(255,255,255,.10); border:1px solid rgba(255,255,255,.18); border-radius:14px; padding:9px 11px;}
  .team-bar .kicker{color:rgba(255,255,255,.82);}
  .team-bar h2{margin:.08rem 0 .12rem; color:#fff; font-size:1.65rem; line-height:1.05;}
  .team-bar p{margin:0; color:rgba(255,255,255,.88);}

  /* ---------- metricas, botoes, abas e tabelas ---------- */
  div[data-testid="stMetric"]{background:linear-gradient(160deg, rgba(255,255,255,.055), rgba(255,255,255,.018));
    border:1px solid var(--cm-border); border-radius:15px; padding:13px 14px; box-shadow:0 10px 24px rgba(0,0,0,.20);}
  div[data-testid="stMetric"] label{font-size:.68rem !important; letter-spacing:.13em; text-transform:uppercase; color:var(--cm-muted) !important; font-weight:600;}
  div[data-testid="stMetric"] div[data-testid="stMetricValue"]{font-weight:700; letter-spacing:-.025em;}
  .stButton>button,.stDownloadButton>button{border-radius:12px; border:1px solid rgba(255,255,255,.14);
    font-weight:600; padding:.58rem 1rem; transition:transform .12s ease, box-shadow .12s ease, filter .12s ease;}
  .stButton>button:hover,.stDownloadButton>button:hover{transform:translateY(-1px); filter:brightness(1.08);}
  .stButton>button[kind="primary"],.stDownloadButton>button[kind="primary"]{
    background:linear-gradient(135deg,#D61437,#93021C); color:#fff; border-color:rgba(255,255,255,.12);
    box-shadow:0 12px 28px rgba(200,16,46,.28);}
  .stTabs [data-baseweb="tab-list"]{gap:5px; border-bottom:1px solid var(--cm-border); padding-bottom:6px;}
  .stTabs [data-baseweb="tab"]{border-radius:10px 10px 0 0; padding:.48rem .78rem; font-weight:700;}
  .stTabs [aria-selected="true"]{background:rgba(200,16,46,.14); color:#fff;}
  div[data-testid="stDataFrame"],div[data-testid="stDataEditor"]{border:1px solid var(--cm-border);
    border-radius:14px; overflow:hidden; box-shadow:0 10px 28px rgba(0,0,0,.18);}
  div[data-testid="stExpander"]{border:1px solid var(--cm-border); border-radius:13px; background:rgba(255,255,255,.022);}
  div[data-baseweb="select"]>div,input,textarea{border-radius:11px !important;}
  div[data-testid="stAlert"]{border-radius:13px;}
  hr{border-color:var(--cm-border);}

  /* ---------- sidebar profissional ---------- */
  section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0E131A 0%,#090D13 100%); border-right:1px solid var(--cm-border);}
  .side-brand{display:flex; gap:10px; align-items:center; margin:.15rem 0 .9rem;}
  .logo-mini{width:42px;height:42px;border-radius:12px;display:flex;align-items:center;justify-content:center;
    background:linear-gradient(145deg,#D61437,#93021C); color:#fff; font-weight:700; box-shadow:0 9px 20px rgba(200,16,46,.30);}
  .side-brand .b1{font-weight:700; letter-spacing:.08em; line-height:.95; color:#fff;}
  .side-brand .b2{font-size:.65rem; letter-spacing:.24em; color:#E88A90; font-weight:700;}
  .side-team{border-radius:15px; padding:13px 14px; margin-bottom:.75rem; color:#fff;
    border:1px solid rgba(255,255,255,.13); box-shadow:0 12px 28px rgba(0,0,0,.25);}
  .side-team .nome{font-size:1.02rem; font-weight:700; line-height:1.15; margin:.35rem 0 .18rem;}
  .side-team .meta{font-size:.74rem; color:rgba(255,255,255,.82); line-height:1.45;}
  section[data-testid="stSidebar"] div[role="radiogroup"] label{border:1px solid transparent; border-radius:11px;
    padding:.42rem .62rem; margin-bottom:2px; transition:background .12s ease,border-color .12s ease;}
  section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{background:rgba(255,255,255,.055);}
  section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked){
    background:linear-gradient(90deg, rgba(200,16,46,.24), rgba(200,16,46,.07)); border-color:rgba(224,36,68,.4);}

  /* ---------- barras de desempenho e noticias ---------- */
  .stat{margin:.35rem 0 .75rem;}
  .stat-top{display:flex; justify-content:space-between; gap:12px; font-size:.82rem; color:#CBD5E1; margin-bottom:.28rem;}
  .stat-top strong{color:#fff; font-size:.9rem;}
  .stat-track{height:9px; border-radius:999px; background:rgba(255,255,255,.075); overflow:hidden; border:1px solid rgba(255,255,255,.06);}
  .stat-fill{height:100%; border-radius:999px;}
  .stat small{color:var(--cm-muted);}
  .news-card{background:linear-gradient(120deg, rgba(255,255,255,.045), rgba(255,255,255,.018));
    border:1px solid var(--cm-border); border-left:4px solid var(--cm-red); border-radius:11px;
    padding:9px 13px; margin-bottom:7px; box-shadow:0 8px 20px rgba(0,0,0,.16);}
  .small{opacity:.72; font-size:.83em;}
  .race-hero{border:1px solid var(--cm-border); border-radius:18px; padding:18px 20px; margin-bottom:12px;
    background:linear-gradient(115deg, rgba(200,16,46,.22), rgba(21,28,37,.92) 48%, rgba(10,14,23,.98));}
  .race-hero h1{font-size:1.85rem; margin:.1rem 0;}
  ::-webkit-scrollbar{width:10px;height:10px} ::-webkit-scrollbar-thumb{background:#26324A;border-radius:99px}

  /* ---------- polimento final ---------- */
  [data-testid="stAppDeployButton"], .stDeployButton{display:none !important}
  div[data-testid="stMetricValue"]{font-size:1.5rem !important; line-height:1.15 !important}
  div[data-testid="stMetricValue"] > div{white-space:normal !important; overflow:visible !important}
  .stTabs [data-baseweb="tab-list"]{padding-left:4px}
  div[role="radiogroup"] > label{width:100%; box-sizing:border-box}
  .side-stats{display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:10px}
  .side-stat{background:linear-gradient(145deg, rgba(255,255,255,.055), rgba(255,255,255,.02));
    border:1px solid var(--cm-border); border-radius:12px; padding:9px 11px}
  .side-stat .lab{font-size:.62rem; letter-spacing:.14em; text-transform:uppercase; color:var(--cm-muted)}
  .side-stat .val{font-size:1rem; font-weight:600; margin-top:3px; white-space:nowrap}
  .flag-img{box-shadow:0 1px 4px rgba(0,0,0,.35)}
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


CFG_BANDEIRA = {"Bandeira": st.column_config.ImageColumn("", width=38)}


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
#  COMPONENTES VISUAIS
# ======================================================================
def titulo_pagina(kicker, titulo, subtitulo=None):
    sub = f"<p>{subtitulo}</p>" if subtitulo else ""
    st.markdown(f'<div class="page-head"><div class="kicker">{kicker}</div><h1>{titulo}</h1>{sub}</div>',
                unsafe_allow_html=True)


def cabecalho_inicial():
    st.markdown("""
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
    """, unsafe_allow_html=True)


def barra_stat(rotulo, valor, obs="", cor="#C8102E"):
    v = max(0.0, min(100.0, float(valor)))
    small = f"<small>{obs}</small>" if obs else ""
    st.markdown(
        f'<div class="stat"><div class="stat-top"><span>{rotulo}</span><strong>{v:.0f}</strong></div>'
        f'<div class="stat-track"><div class="stat-fill" style="width:{v:.0f}%;'
        f'background:linear-gradient(90deg,{cor},#E4636F)"></div></div>{small}</div>',
        unsafe_allow_html=True)


# ======================================================================
#  TELA INICIAL (seleção de DB, equipe, tamanho do grid, editor de DBs)
# ======================================================================
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
        "👥 Pilotos no grid (titulares) — começa em 22", minimo, maximo, padrao,
        help=f"Grid natural desta DB: {natural}. Acima disso, as equipes inscrevem 3º e 4º carros "
             f"com reservas e jovens do mercado; abaixo, os carros excedentes sao cortados.",
        key=f"qtd_grid{key_suffix}")


def tela_inicial():
    cabecalho_inicial()
    st.caption("Remake de fã inspirado no *Cockpit Manager '14* (Cartola Games) e na "
               "[DB F1 2026 by Jonathan Daniel]"
               "(http://cockpitmanager.blogspot.com/2026/05/db-f1-2026-v10-by-jonathan-daniel.html). "
               "Escolha uma **base de dados (DB)**, a sua equipe e **quantos pilotos terá o grid** — "
               "ou crie a sua própria categoria na aba 🛠️ **Criar / editar DB**.")

    disp = dbs_disponiveis()
    db_chave = st.selectbox(
        "📚 Base de dados (DB)", list(disp.keys()),
        format_func=lambda k: f"{disp[k]['meta'].get('nome', k)} — {disp[k]['meta'].get('categoria', '')}")
    sel_db = disp[db_chave]
    meta = sel_db["meta"]
    ci1, ci2, ci3, ci4 = st.columns(4)
    ci1.metric("Categoria", meta.get("categoria", "—"))
    ci2.metric("Ano inicial", meta.get("ano", "—"))
    ci3.metric("Equipes", len(sel_db["equipes"]))
    ci4.metric("Pilotos no grid / Etapas", f"{dbsmod.grid_natural(sel_db)} / {len(sel_db['calendario'])}")
    if meta.get("descricao"):
        st.info(meta["descricao"])
    tem_cancelavel = any(e.get("cancelavel") for e in sel_db["calendario"])

    tab_equipe, tab_criar, tab_editor, tab_load = st.tabs(
        ["🏁 Escolher uma equipe", "🆕 Criar minha equipe", "🛠️ Criar / editar DB", "💾 Carregar save"])

    with tab_equipe:
        nomes = {e["id"]: f"[{bnd.codigo_texto(e['bandeira'])}] {e['nome']} — carro {e['nivel_carro']:.0f} · caixa {sim.fmt_dinheiro_m(e['caixa'])}"
                 for e in sel_db["equipes"]}
        eq_id = st.selectbox(f"Sua equipe para {meta.get('ano', '')}", list(nomes.keys()), format_func=lambda x: nomes[x])
        eq = next(e for e in sel_db["equipes"] if e["id"] == eq_id)
        mot = next((m for m in sel_db["motores"] if m["id"] == eq["motor_id"]), sel_db["motores"][0])
        rot = meta.get("rotulo_fornecedor", "Motor")
        st.markdown(f'<div class="team-bar" style="background:linear-gradient(112deg,{eq["cor"]} 0%, rgba(13,17,26,.93) 58%, #0D111A 100%)">'
                    f'<div class="team-main"><div class="team-flag">{bnd.img_bandeira(eq["bandeira"], 44)}</div>'
                    f'<div><div class="kicker">{eq["pais"]}</div><h2>{eq["nome_completo"]}</h2>'
                    f'<p>{rot} {"próprio" if eq.get("motor_proprio") else "cliente"}: <b>{mot["nome"]}</b> '
                    f'(desempenho {mot["potencia"]}) · Prestígio: {eq["prestigio"]}</p></div></div></div>', unsafe_allow_html=True)
        quad = sorted([p for p in sel_db["pilotos"] if p["equipe_id"] == eq_id],
                      key=lambda p: {"P1": 0, "P2": 1, "P3": 2, "P4": 3, "teste": 4}.get(p["papel"], 5))
        st.dataframe(pd.DataFrame([{
            "Bandeira": bnd.url_bandeira(p['bandeira']), "Piloto": p['nome'], "#": p["numero"], "Idade": p["idade"],
            "Função": {"P1": "1o piloto", "P2": "2o piloto", "P3": "3o piloto", "P4": "4o piloto", "teste": "Testes/reserva"}.get(p["papel"], p["papel"]),
            "Overall": sim.overall(p), "Salário/corrida": sim.fmt_dinheiro_k(p["salario_corrida"]),
        } for p in quad]), hide_index=True, width="stretch", column_config=CFG_BANDEIRA)

        qtd_grid = _slider_grid(sel_db)
        c1, c2, c3 = st.columns(3)
        incluir = True
        if tem_cancelavel:
            incluir = c1.checkbox("Calendário completo (inclui etapas canceláveis da DB)", value=True)
        imp = c2.slider("Importância do carro (%)", 30, 90,
                        int(float(meta.get("importancia_carro_sugerida", 0.6)) * 100), 5,
                        help="Sugerido pela DB: F1 60%, Indy 45%, Stock 40%, DTM 50%.") / 100.0
        semente = c3.number_input("semente (aleatoriedade)", 1, 99999, 2026)
        if st.button("🚥 Iniciar carreira", type="primary", width="stretch"):
            st.session_state.game = sim.criar_novo_jogo(eq_id, int(semente), incluir, imp,
                                                        db_dados=sel_db, qtd_pilotos=qtd_grid)
            st.session_state.fds = None
            st.session_state.menu = MENUS[0]
            flash("success", f"Bem-vindo ao comando da {eq['nome']}! Primeira parada: "
                             f"{sel_db['calendario'][0]['gp']}. Grid com {qtd_grid} pilotos.")
            st.rerun()

    with tab_criar:
        st.write(f"Entre como **equipe extra** no grid da DB **{meta.get('nome')}**, do seu jeito — "
                 f"como no modo 'nova equipe' do original. O grid terá o tamanho natural da DB + os seus 2 carros.")
        c1, c2 = st.columns(2)
        nome_custom = c1.text_input("Nome da equipe", "Minha Equipe")
        pais_custom = c2.text_input("País sede", "Brasil")
        cor_custom = c1.color_picker("Cor do carro", "#009C3B")
        fornecedores_disp = [m for m in sel_db["motores"] if not m.get("proprio_de") and m["id"] != "fia"]
        mot_custom = c2.selectbox(f"{meta.get('rotulo_fornecedor', 'Motor')}", fornecedores_disp,
                                  format_func=lambda m: f"{m['nome']} — desempenho {m['potencia']} · US$ {m['preco']:.0f} mi/ano")
        perfil = st.radio("Perfil do projeto", ["🥾 Estreante pé-rapado", "💼 Investidor sério", "🏭 Projeto de montadora"],
                          horizontal=True)
        perfil_map = {"🥾 Estreante pé-rapado": (70.0, 55, 35), "💼 Investidor sério": (140.0, 62, 50),
                      "🏭 Projeto de montadora": (190.0, 70, 60)}
        caixa_c, carro_c, prest_c = perfil_map[perfil]
        livres = [p for p in sel_db["pilotos"] if p["papel"] == "livre"]
        if len(livres) < 3:
            st.warning("Esta DB tem poucos pilotos livres para montar uma equipe nova. "
                       "Edite a DB na aba 🛠️ e adicione pilotos 'livre', ou escolha outra DB.")
        else:
            fmt_p = lambda pid: next(f"[{bnd.codigo_texto(p['bandeira'])}] {p['nome']} (ovr {sim.overall(p)}, {p['idade']} anos)" for p in livres if p["id"] == pid)
            ids_livres = [p["id"] for p in livres]
            c1, c2, c3 = st.columns(3)
            p1 = c1.selectbox("1o piloto", ids_livres, format_func=fmt_p)
            p2 = c2.selectbox("2o piloto", ids_livres, index=min(1, len(ids_livres) - 1), format_func=fmt_p)
            pt = c3.selectbox("Piloto de testes", ids_livres, index=min(2, len(ids_livres) - 1), format_func=fmt_p)
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
                st.session_state.game = sim.criar_novo_jogo("custom", 2026, True,
                                                            float(meta.get("importancia_carro_sugerida", 0.6)),
                                                            equipe_custom=eq_c, pilotos_custom=contr,
                                                            db_dados=sel_db)
                st.session_state.fds = None
                st.session_state.menu = MENUS[0]
                flash("success", f"A {nome_custom} nasceu na {meta.get('categoria')}! Boa sorte, chefe!")
                st.rerun()

    with tab_editor:
        editor_db.aba_editor_db(disp)

    with tab_load:
        up = st.file_uploader("Arquivo de save (.json)", type="json", key="load_save")
        if up and st.button("Carregar save", type="primary"):
            try:
                dados = json.loads(up.read().decode("utf-8"))
                assert "equipes" in dados and "pilotos" in dados and "ano" in dados
                dados.setdefault("meta", {"nome": "Save (F1 2026)", "categoria": "Fórmula 1",
                                          "rotulo_fornecedor": "Motor", "rotulo_corrida2": "Sprint",
                                          "pontos_corrida": db.PONTOS_CORRIDA, "pontos_corrida2": db.PONTOS_SPRINT})
                dados.setdefault("patrocinadores", db.PATROCINADORES)
                dados.setdefault("calendario_base", dados.get("calendario", []))
                st.session_state.game = dados
                st.session_state.fds = None
                flash("success", f"Save carregado: temporada {dados['ano']}, etapa {dados['rodada'] + 1}.")
                st.rerun()
            except Exception as e:
                st.error(f"Arquivo inválido: {e}")


# ======================================================================
#  COMPONENTES REUTILIZÁVEIS
# ======================================================================
ROTULOS_PAPEL = {"P1": "1o piloto", "P2": "2o piloto", "P3": "3o piloto", "P4": "4o piloto",
                 "teste": "Testes/reserva", "livre": "Livre"}


def meta_game(game):
    return (game or {}).get("meta") or {}


def rot_fornecedor(game):
    return meta_game(game).get("rotulo_fornecedor", "Motor")


def rot_corrida2(game):
    return meta_game(game).get("rotulo_corrida2") or "Sprint"


def df_pilotos_equipe(game, equipe_id):
    linhas = []
    for p in sorted([x for x in game["pilotos"] if x["equipe_id"] == equipe_id and not x["aposentado"]],
                    key=lambda x: {"P1": 0, "P2": 1, "P3": 2, "P4": 3, "teste": 4}.get(x["papel"], 5)):
        a = p["atributos"]
        linhas.append({"Bandeira": bnd.url_bandeira(p['bandeira']), "Piloto": p['nome'], "#": p["numero"], "Idade": p["idade"],
                       "Função": ROTULOS_PAPEL.get(p["papel"], p["papel"]),
                       "Overall": sim.overall(p), "Velocidade": a["velocidade"], "Chuva": a["chuva"],
                       "Concentração": a["concentracao"], "Largada": a["largada"],
                       "Ultrapassagem": a["ultrapassagem"], "Acerto": a["acerto"], "Físico": a["fisico"],
                       "Forma": p["forma"], "Pontos": p["pontos"],
                       "Salário/corrida": p["salario_corrida"], "Contrato": f"{p['contrato_anos']} ano(s)"})
    return pd.DataFrame(linhas)


def barra_equipe(eq):
    st.markdown(
        f'<div class="team-bar" style="background:linear-gradient(112deg,{eq["cor"]} 0%, rgba(13,17,26,.93) 58%, #0D111A 100%)">'
        f'<div class="team-main"><div class="team-flag">{bnd.img_bandeira(eq["bandeira"], 44)}</div>'
        f'<div><div class="kicker">Sua equipe · {eq["pais"]}</div><h2>{eq["nome_completo"]}</h2>'
        f'<p>Prestígio {eq["prestigio"]} · {eq.get("titulos_construtores", 0)} título(s) de construtores na história</p></div></div></div>',
        unsafe_allow_html=True)


def painel_fim_temporada(game):
    tab_p, tab_c = sim.tabela_pilotos(game), sim.tabela_construtores(game)
    st.success(f"🏁 **Fim da temporada {game['ano']}!**")
    if tab_p:
        camp = tab_p[0]
        st.markdown(f"🏆 Campeão de Pilotos: {bnd.img_bandeira(camp['bandeira'])} **{camp['nome']}** "
                    f"({sim.equipe(game, camp['equipe_id'])['nome']}) — {camp['pontos']} pts", unsafe_allow_html=True)
    if tab_c:
        st.markdown(f"🏭 Campeã de Construtores: {bnd.img_bandeira(tab_c[0]['bandeira'])} **{tab_c[0]['nome']}** — {tab_c[0]['pontos']} pts", unsafe_allow_html=True)
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
        barra_stat("Chassi / aerodinâmica", eqj["nivel_carro"], cor=eqj["cor"])
        barra_stat(f"{rot_fornecedor(game)} — {mot['nome']} {'(próprio)' if eqj.get('motor_proprio') else '(cliente)'}",
                   mot["potencia"], cor="#F59E0B")
        barra_stat("Desempenho combinado", sim.desempenho_carro(game, eqj))
        barra_stat("Confiabilidade", eqj["confiabilidade"], cor="#22C55E")
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
            st.markdown(f"### 📅 Próxima corrida: {bnd.img_bandeira(etapa['bandeira'], 22)} {etapa['gp']}", unsafe_allow_html=True)
            st.write(f"**{etapa['circuito']}** — {etapa['pais']} · {etapa['voltas']} voltas · {etapa['data']}"
                     + (f" · ⚡ **fim de semana com {rot_corrida2(game)} + corrida principal**" if etapa["sprint"] else ""))
            st.write(f"🌧️ Chance histórica de chuva: **{etapa['chuva'] * 100:.0f}%** · "
                     f"Desgaste de pneus: **{etapa['desgaste']:.1f}/3** · "
                     f"Ultrapassagem: **{etapa['ultrap'] * 100:.0f}%**")
            st.button("▶️ CONTINUAR — ir para a corrida", type="primary", width="stretch",
                      on_click=ir_para, args=("🏁 Corrida",))

    st.subheader("👨‍✈️ Seus pilotos")
    st.dataframe(df_pilotos_equipe(game, eqj["id"]), hide_index=True, width="stretch",
                 column_config={**CFG_BANDEIRA,
                                **{c: st.column_config.ProgressColumn(c, min_value=0, max_value=100, format="%d")
                                   for c in ["Velocidade", "Chuva", "Concentração", "Largada", "Ultrapassagem", "Acerto", "Físico", "Forma"]}})

    st.subheader("📰 Notícias do paddock")
    for n in game["noticias"][:8]:
        _txt = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", bnd.substituir_emojis(n["texto"]))
        st.markdown(f'<div class="news-card"><span class="small">{n["ano"]} · etapa {n["rodada"]}</span><br>{_txt}</div>',
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
        "Pos": g["pos"], "Bandeira": bnd.url_bandeira(sim.piloto(game, g['piloto_id'])['bandeira']), "Piloto": sim.piloto(game, g['piloto_id'])['nome'],
        "Equipe": sim.equipe(game, g["equipe_id"])["nome"], "": "⭐" if g["equipe_id"] == game["equipe_jogador"] else "",
        "Tempo": fmt_tempo(g["tempo"]), "Gap": "—" if g["gap"] == 0 else f"+{g['gap']:.3f}",
    } for g in grid])


def df_resultado(game, resultado):
    linhas = []
    for l in resultado:
        p = sim.piloto(game, l["piloto_id"])
        est = l["estrategia"]
        linhas.append({
            "Pos": l["pos"], "Bandeira": bnd.url_bandeira(p['bandeira']), "Piloto": p['nome'], "Equipe": sim.equipe(game, l["equipe_id"])["nome"],
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

    st.markdown(
        f'<div class="race-hero"><div class="kicker">Etapa {game["rodada"] + 1} · {game["ano"]}</div>'
        f'<h1>{bnd.img_bandeira(etapa["bandeira"], 36)} {etapa["gp"]}</h1>'
        f'<p style="margin:0;color:#CBD5E1">{etapa["circuito"]} · {etapa["pais"]}</p></div>',
        unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Etapa", f"{game['rodada'] + 1}/{len(game['calendario'])} · {game['ano']}")
    c2.metric("Voltas", etapa["voltas"])
    c3.metric("Clima", "🌧️ Molhado" if molhado else "☀️ Seco")
    c4.metric("Formato", f"⚡ {rot_corrida2(game)} + principal" if etapa["sprint"] else "Corrida única")
    st.caption(f"Características: peso do motor {etapa['potencia'] * 100:.0f}% · facilidade de ultrapassar "
               f"{etapa['ultrap'] * 100:.0f}% · desgaste {etapa['desgaste']:.1f}/3 → estratégia típica: "
               f"**{sim.paradas_ideais(etapa)} parada(s)**")

    # ---------------- estratégia dos seus dois pilotos
    st.subheader("🎯 Sua estratégia (pneu, paradas e ritmo — o coração do Cockpit Manager)")
    estrategias = {}
    cols = st.columns(len(meus))
    opcoes_pneu = sim.PNEUS_MOLHADO + sim.PNEUS_SECO if molhado else sim.PNEUS_SECO
    for col, p in zip(cols, meus):
        with col, st.container(border=True):
            st.markdown(bnd.com_bandeira(p['bandeira'], f"**#{p['numero']} {p['nome']}** ({ROTULOS_PAPEL.get(p['papel'], p['papel'])})"), unsafe_allow_html=True)
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
        st.subheader(f"⚡ {rot_corrida2(game)} (primeira corrida do fim de semana)")
        if fds["sprint"] is None:
            if st.button(f"▶️ Simular {rot_corrida2(game)}", width="stretch"):
                grid_s = sim.simular_classificacao(game, etapa, molhado)
                est_s = {pid: {**e, "paradas": sim.paradas_ideais(etapa)} for pid, e in estrategias.items()}
                res_s, ev_s = sim.simular_corrida(game, etapa, grid_s, est_s, molhado, sprint=True)
                sim.aplicar_resultado(game, etapa, grid_s, res_s, molhado, sprint=True, eventos=ev_s)
                fds["sprint"] = res_s
                st.rerun()
        else:
            st.dataframe(df_resultado(game, fds["sprint"]), hide_index=True, width="stretch", column_config=CFG_BANDEIRA)
            st.caption(f"Pontos da {rot_corrida2(game)} já somados ao campeonato.")

    # ---------------- classificação
    st.divider()
    st.subheader("⏱️ Classificação")
    if fds["grid"] is None:
        if st.button("▶️ Simular classificação", width="stretch",
                     disabled=(etapa["sprint"] and fds["sprint"] is None)):
            fds["grid"] = sim.simular_classificacao(game, etapa, molhado)
            pole = sim.piloto(game, fds["grid"][0]["piloto_id"])
            flash("info", f"Pole position: {pole['nome']} ({fmt_tempo(fds['grid'][0]['tempo'])})")
            st.rerun()
        if etapa["sprint"] and fds["sprint"] is None:
            st.caption(f"Primeiro simule a {rot_corrida2(game)}.")
    else:
        st.dataframe(df_grid(game, fds["grid"]), hide_index=True, width="stretch", column_config=CFG_BANDEIRA)

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
        st.dataframe(df_resultado(game, fds["resultado"]), hide_index=True, width="stretch", column_config=CFG_BANDEIRA)
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
    titulo_pagina("Engenharia", "Carro & Investimentos", "Desenvolva o chassi, proteja a confiabilidade e acompanhe as rivais.")
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
        linhas.append({"Bandeira": bnd.url_bandeira(e['bandeira']), "Equipe": e['nome'], "": "⭐" if e["id"] == eqj["id"] else "",
                       "Chassi": round(e["nivel_carro"], 1), "Motor": m["nome"],
                       "Potência": m["potencia"], "Desempenho": round(sim.desempenho_carro(game, e), 1),
                       "Confiabilidade": round(e["confiabilidade"]), "Prestígio": e["prestigio"],
                       "Caixa (mi)": round(e["caixa"], 1)})
    df = pd.DataFrame(linhas)
    st.dataframe(df, hide_index=True, width="stretch",
                 column_config={**CFG_BANDEIRA,
                                **{c: st.column_config.ProgressColumn(c, min_value=0, max_value=100, format="%.0f")
                                   for c in ["Chassi", "Potência", "Desempenho", "Confiabilidade"]}})
    st.bar_chart(df.set_index("Equipe")["Desempenho"])


# ======================================================================
#  PILOTOS & CONTRATOS
# ======================================================================
def pagina_pilotos(game):
    eqj = sim.equipe(game, game["equipe_jogador"])
    titulo_pagina("Mercado", "Pilotos & Contratos", "Seus pilotos de hoje — e as negociações que desenham o amanhã.")
    tab1, tab2, tab3 = st.tabs(["Minha equipe", "🤝 Negociar (próxima temporada)", "🌍 Todos os pilotos"])

    with tab1:
        st.dataframe(df_pilotos_equipe(game, eqj["id"]), hide_index=True, width="stretch", column_config=CFG_BANDEIRA)
        total_sal = sum(p["salario_corrida"] for p in game["pilotos"] if p["equipe_id"] == eqj["id"])
        st.caption(f"Custo total de salários: {sim.fmt_dinheiro_k(total_sal)} por corrida.")
        if game["contratos_proxima"]:
            st.subheader(f"✍️ Já contratados para {game['ano'] + 1}")
            for pid, c in list(game["contratos_proxima"].items()):
                p = sim.piloto(game, pid)
                col1, col2 = st.columns([5, 1])
                col1.markdown(bnd.com_bandeira(p['bandeira'], f"**{p['nome']}** — {c['papel']} · {sim.fmt_dinheiro_k(c['salario'])}/corrida · {c['anos']} ano(s)"), unsafe_allow_html=True)
                if col2.button("Cancelar", key=f"canc_{pid}"):
                    del game["contratos_proxima"][pid]
                    st.rerun()

    with tab2:
        st.caption("Como no original: você negocia **durante** a temporada, mas o piloto só veste seu macacão "
                   "na **próxima**. Salários são por corrida.")
        ativos = [p for p in game["pilotos"] if not p["aposentado"]]
        ativos.sort(key=lambda p: -sim.overall(p))
        sel = st.selectbox("Piloto", ativos,
                           format_func=lambda p: f"[{bnd.codigo_texto(p['bandeira'])}] {p['nome']} — ovr {sim.overall(p)} · {p['idade']} anos · "
                                                 f"{(sim.equipe(game, p['equipe_id'])['nome'] if p['equipe_id'] else 'LIVRE')} ({p['papel']})")
        a = sel["atributos"]
        st.bar_chart(pd.Series({db.ATRIBUTOS[k]: v for k, v in a.items()}))
        st.caption(f"Auge: {sel['auge_inicio']}–{sel['auge_fim']} anos (platô) · Potencial: {sel['potencial']} · "
                   f"Vitórias no save: {sel['vitorias']} · Títulos: {sel['titulos']}")
        with st.form("form_contrato"):
            _vagas = list((game.get("vagas_por_equipe") or {}).get(eqj["id"], ["P1", "P2"])) + ["teste"]
            papel = st.radio("Papel oferecido", _vagas, horizontal=True,
                             format_func=lambda x: ROTULOS_PAPEL.get(x, x))
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
            linhas.append({"Bandeira": bnd.url_bandeira(p['bandeira']), "Piloto": p['nome'], "Idade": p["idade"],
                           "Equipe": sim.equipe(game, p["equipe_id"])["nome"] if p["equipe_id"] else "— LIVRE —",
                           "Papel": p["papel"], "Overall": sim.overall(p), "Potencial": p["potencial"],
                           "Pontos": p["pontos"], "Vitórias*": p["vitorias"], "Pódios*": p["podios"],
                           "Títulos*": p["titulos"], "Salário": p["salario_corrida"]})
        st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch", column_config=CFG_BANDEIRA)
        st.caption("* Estatísticas acumuladas dentro deste save.")


# ======================================================================
#  MOTORES
# ======================================================================
def pagina_motores(game):
    eqj = sim.equipe(game, game["equipe_jogador"])
    titulo_pagina("Fornecedores", f"{rot_fornecedor(game)}s", "Desempenho de verdade custa caro. Ficar sem caixa sai mais caro ainda.")
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
    titulo_pagina("Dinheiro", "Patrocinadores & Finanças", "Quem paga a conta, para onde vai cada centavo — e o que sobra no fim.")
    lista_spon = game.get("patrocinadores") or db.PATROCINADORES
    spon = next((s for s in lista_spon if s["nome"] == eqj["patrocinador"]), lista_spon[-1])
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
              for s in lista_spon]
    st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch", column_config=CFG_BANDEIRA)
    elegiveis = [s for s in lista_spon if eqj["prestigio"] >= s["prestigio_min"]]
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
    titulo_pagina("Classificação", f"Campeonato {game['ano']}", "Pilotos, construtores, evolução dos pontos e todos os resultados.")
    tab1, tab2, tab3, tab4 = st.tabs(["👨‍✈️ Pilotos", "🏭 Construtores", "📈 Evolução", "🗓️ Calendário & Resultados"])

    with tab1:
        linhas = []
        for i, p in enumerate(sim.tabela_pilotos(game)):
            linhas.append({"Pos": i + 1, "Bandeira": bnd.url_bandeira(p['bandeira']), "Piloto": p['nome'],
                           "Equipe": sim.equipe(game, p["equipe_id"])["nome"] if p["equipe_id"] else "—",
                           "": "⭐" if p["equipe_id"] == game["equipe_jogador"] else "",
                           "Pontos": p["pontos"], "Vitórias": p["vitorias"], "Pódios": p["podios"],
                           "Poles": p["poles"], "Abandonos": p["abandonos"], "Forma": p["forma"]})
        st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch", column_config=CFG_BANDEIRA)
    with tab2:
        linhas = [{"Pos": i + 1, "Bandeira": bnd.url_bandeira(e['bandeira']), "Equipe": e['nome'],
                   "": "⭐" if e["id"] == game["equipe_jogador"] else "", "Pontos": e["pontos"],
                   "Vitórias": e["vitorias"], "Pódios": e["podios"], "Poles": e["poles"]}
                  for i, e in enumerate(sim.tabela_construtores(game))]
        st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch", column_config=CFG_BANDEIRA)
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
            with st.expander(f"{i + 1}. [{bnd.codigo_texto(etapa['bandeira'])}] {etapa['gp']} — {etapa['circuito']} · {etapa['voltas']} voltas"
                             + (f" · ⚡{rot_corrida2(game)}" if etapa["sprint"] else "") + (" ✅" if regs else "")):
                if regs:
                    r = regs[-1]
                    st.caption("🌧️ Corrida molhada" if r["molhado"] else "☀️ Corrida seca")
                    st.dataframe(df_resultado(game, r["resultado"]), hide_index=True, width="stretch", column_config=CFG_BANDEIRA)
                else:
                    st.caption("Ainda não disputada.")


# ======================================================================
#  HALL DA FAMA & CONQUISTAS
# ======================================================================
def pagina_hall(game):
    titulo_pagina("Legado", "Hall da Fama & Conquistas", "As lendas da categoria — e as suas 10 conquistas para caçar.")
    tab1, tab2 = st.tabs(["🌟 Hall da Fama", "🎖️ Conquistas (10)"])
    with tab1:
        st.caption(f"Pilotos do seu save entram para a eternidade ao se aposentar com "
                   f"**≥ {db.HOF_MIN_TITULOS} títulos** ou **≥ {db.HOF_MIN_VITORIAS} vitórias** na carreira.")
        st.dataframe(pd.DataFrame([{
            "Bandeira": bnd.url_bandeira(h['bandeira']), "Lenda": h['nome'], "País": h["pais"], "Títulos": h["titulos"],
            "Vitórias": h["vitorias"], "Era": h["anos"],
            "Origem": "induzido no seu save ✨" if h.get("induzido_no_save") else "histórico",
        } for h in sorted(game["hall_da_fama"], key=lambda x: (-x["titulos"], -x["vitorias"]))]),
            hide_index=True, width="stretch", column_config=CFG_BANDEIRA)
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
    titulo_pagina("Sistema", "Salvar / Carregar", "Baixe o save da sua carreira e continue quando quiser.")
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
    titulo_pagina("Manual", "Como Jogar", "Tudo o que um chefe de equipe precisa saber antes da primeira largada.")
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

### 🏎️ As 7 DBs embutidas
- **F1 2026** — a DB clássica: 11 equipes, 24 etapas, novo regulamento, Bortoleto na Audi.
- **F1 Academy** — a base feminina da F1: 18 monopostos **Tatuus idênticos**, 6 equipes reais de 2026
  (Prema, ART, Campos, MP, Rodin, Hitech) e formandas que sobem a cada virada — carro igual, talento à mostra.
- **F1 Legends** — o time dos sonhos: Schumacher, Senna, Fangio, Clark, Prost e Moss em circuitos
  clássicos (Nordschleife, Spa original, Reims, Monza com banking) com motores de época (DFV, Climax, Repco).
- **Fórmula Indy** — ovais, ruas e mistos; todos pontuam (50 pts a vitória) e as **500 Milhas** são o auge do ano.
- **Indy Legends** — as lendas da IndyCar (Foyt, Unser, Mario Andretti, Mears, Montoya) nas 500 Milhas e
  nos ovais clássicos: Milwaukee, Pocono, Michigan e o histórico Ontario Motor Speedway.
- **Stock Car** — sprint no sábado (55 pts) + principal no domingo (80 pts), grid de 34 SUVs V8, Corrida do Milhão e Endurance.
- **DTM** — GT3 alemães com **duas corridas iguais** por fim de semana (25 pts cada vitória).
Em cada DB, o "fornecedor" muda de nome (motor, montadora, chassi ou carro GT3), mas o coração do jogo é o mesmo.

### 👥 Tamanho do grid (começa em 22)
Na tela inicial você escolhe quantos pilotos titulares o grid terá. Acima do natural da DB, as equipes
inscrevem **3º e 4º carros** com reservas e jovens; o mercado mantém o grid cheio temporada após temporada.

### 🛠️ Editor de DBs
Na aba **Criar / editar DB** (tela inicial) você edita equipes, pilotos (atributos!), calendário e
fornecedores de qualquer DB — ou cria a sua categoria do zero. Depois é só **Validar**, jogar na hora,
**baixar o .json** para compartilhar com a comunidade ou salvar em `minhas_dbs/` para ela virar uma
DB permanente no seu jogo. DBs recebidas de outros criadores entram pelo *upload* do editor.

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
        total_etapas = max(1, len(game["calendario"]))
        st.markdown(
            '<div class="side-brand"><div class="logo-mini">CM</div>'
            '<div><div class="b1">COCKPIT</div><div class="b2">MANAGER</div></div></div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div class="side-team" style="background:linear-gradient(125deg,{eqj["cor"]} 0%, rgba(13,17,26,.94) 62%)">'
            f'{bnd.img_bandeira(eqj["bandeira"], 26)}'
            f'<div class="nome">{eqj["nome"]}</div>'
            f'<div class="meta">{meta_game(game).get("nome", "F1 2026")} · grid com {len(sim.titulares(game))} pilotos</div></div>',
            unsafe_allow_html=True)
        st.progress(min(1.0, game["rodada"] / total_etapas),
                    text=f"Temporada {game['ano']} · {game['rodada']}/{total_etapas} etapas concluídas")
        st.markdown(
            '<div class="side-stats">'
            f'<div class="side-stat"><div class="lab">Caixa</div>'
            f'<div class="val">{sim.fmt_dinheiro_m(eqj["caixa"]).replace("US$ ", "$")}</div></div>'
            f'<div class="side-stat"><div class="lab">Construtores</div>'
            f'<div class="val">{sim.posicao_equipe(game, eqj["id"])}º · {eqj["pontos"]} pts</div></div></div>',
            unsafe_allow_html=True)
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
