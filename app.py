# -*- coding: utf-8 -*-
"""
🏎️ COCKPIT MANAGER — Edição Streamlit (DB F1 2026)

Remake feito por fã, inspirado no Cockpit Manager '14 (Cartola Games, 2014)
e na DB F1 2026 v1.0 by Jonathan Daniel (blog Cockpit Manager - Brasil).

Rode com:  streamlit run app.py
"""

import json
import os
import re
import time

import pandas as pd
import streamlit as st

import bandeiras as bnd
import dados2026 as db
import dbs as dbsmod
import editor_db
import simulacao as sim

st.set_page_config(page_title="Cockpit Manager", page_icon="🏎️", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
<style>
  :root{
    --cm-red:#C8102E; --cm-red2:#E02444; --cm-bg:#0B0F14; --cm-panel:#151C25;
    --cm-border:rgba(148,163,184,.16); --cm-text:#F4F7FB; --cm-muted:#94A3B8;
    /* sistema tipográfico do jogo (todas auto-hospedadas em static/fonts) */
    --cm-font-brand:"Formula1","Titillium Web",sans-serif;   /* títulos, marcas, indicadores */
    --cm-font-ui:"Manrope","Inter",system-ui,sans-serif;     /* interface, tabelas HTML, números */
    --cm-font-text:"Inter","Manrope",system-ui,sans-serif;   /* texto corrido, manuais, dataframes */
    --cm-font-mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,monospace;
  }
  .stApp{
    background:
      radial-gradient(1100px 520px at 85% -10%, rgba(200,16,46,.14), transparent 60%),
      radial-gradient(900px 480px at -10% 0%, rgba(31,78,121,.16), transparent 55%),
      linear-gradient(180deg,#0B0F14 0%, #0D111A 100%);
    color:var(--cm-text);
    font-family:var(--cm-font-ui);
    -webkit-font-smoothing:antialiased; -moz-osx-font-smoothing:grayscale;
    text-rendering:optimizeLegibility;
  }
  .block-container{max-width:1480px; padding:2rem 2.4rem 3.2rem;}
  @media (max-width:760px){ .block-container{padding:1.1rem .9rem 2rem;} }
  /* ---------- tipografia: Formula1 Display (títulos) ---------- */
  h1,h2{letter-spacing:-.01em; color:#F8FAFC; font-weight:700; font-family:var(--cm-font-brand);
    text-wrap:balance;}
  h3{letter-spacing:.04em; color:#E2E8F0; font-weight:400; font-family:var(--cm-font-brand);
    text-wrap:balance;}
  h4,h5,h6,[data-testid="stHeading"]{font-family:var(--cm-font-brand); letter-spacing:.04em;
    text-wrap:balance;}
  /* Formula1 Display: títulos, marcas e indicadores. Manrope: interface. Inter: texto. */
  .kicker,.logo-mark,.logo-mini,.side-brand .b1,.side-brand .b2,.chip.hot{font-family:var(--cm-font-brand);}

  /* ---------- tipografia: Manrope (interface inteira) ---------- */
  button,[data-testid="stBaseButton"],[data-testid^="stBaseButton"],[data-testid="stDownloadButton"],
  [data-testid="stFormSubmitButton"] button,
  input,textarea,select,[data-baseweb="select"] *,[data-baseweb="input"] *,[data-baseweb="textarea"] *,
  [data-testid="stWidgetLabel"],[data-testid="stWidgetLabel"] *,
  [data-baseweb="tab"], [data-testid="stTabs"] button,
  [data-testid="stExpander"] summary,[data-testid="stFileUploader"] *,
  [data-testid="stMetricLabel"],[data-testid="stMetricDelta"],
  [data-testid="stTooltipContent"] *,[data-testid="stToast"] *,
  section[data-testid="stSidebar"] div[role="radiogroup"] label,
  section[data-testid="stSidebar"] [data-testid="stSidebarNav"] *{
    font-family:var(--cm-font-ui);
  }
  button,[data-testid^="stBaseButton"]{font-weight:600; letter-spacing:.012em;}
  [data-testid="stWidgetLabel"] p{font-weight:600; letter-spacing:.01em;}
  [data-testid="stMetricLabel"]{letter-spacing:.06em; text-transform:uppercase; font-weight:700;}

  /* ---------- tipografia: Inter (texto corrido + dataframes) ---------- */
  [data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li,
  [data-testid="stMarkdownContainer"] blockquote,[data-testid="stMarkdownContainer"] table,
  [data-testid="stMarkdownContainer"] td,[data-testid="stMarkdownContainer"] th,
  [data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p,
  [data-testid="stAlertContent"],[data-testid="stExpanderDetails"] p,
  [data-testid="stExpanderDetails"] li,[data-testid="stTable"],
  [data-testid="stDataFrame"]{
    font-family:var(--cm-font-text);
  }
  [data-testid="stMarkdownContainer"] p{text-wrap:pretty; line-height:1.62;}
  [data-testid="stMarkdownContainer"] li{line-height:1.58;}

  /* ---------- tipografia: números tabulares e código ---------- */
  [data-testid="stMetricValue"],[data-testid="stMetricDelta"],.tbl-viva td,.tbl-viva th,
  .voltas-box .n,.plinha b,.side-stat .val,.race-sub,.feed-race{
    font-variant-numeric:tabular-nums lining-nums;
  }
  code,pre,kbd,[data-testid="stCode"],[data-testid="stCodeBlock"]{font-family:var(--cm-font-mono);}
  [data-testid="stIconMaterial"],[data-testid="stIconMaterial"] *,.material-symbols-rounded{
    font-family:"Material Symbols Rounded","Material Icons" !important;
  }
  ::selection{background:rgba(200,16,46,.45); color:#fff;}
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

  /* ---------- telas de treino e corrida (fidelidade ao original) ---------- */
  .sessao-card{border:1px solid var(--cm-border); border-radius:16px;
    background:linear-gradient(165deg, rgba(255,255,255,.045), rgba(255,255,255,.015));
    padding:16px 18px 14px; margin-bottom:10px; box-shadow:0 14px 30px rgba(0,0,0,.18);}
  .sessao-titulo{text-align:center; font-size:1.5rem; font-weight:800; letter-spacing:.02em;
    text-decoration:underline; text-underline-offset:6px; margin:0 0 .25rem;}
  .sessao-circuito{text-align:center; font-style:italic; color:#CBD5E1; font-size:1.04rem;}
  .sessao-gp{text-align:center; font-weight:700; margin:.18rem 0 .35rem; font-size:1.15rem;
    display:flex; align-items:center; justify-content:center; gap:8px;}
  .sessao-linha{display:flex; flex-wrap:wrap; gap:14px; align-items:center; justify-content:space-between;
    margin:.35rem 0 .7rem; font-size:.9rem; color:#CBD5E1;}
  .tbl-viva{width:100%; border-collapse:collapse; font-size:.86rem;}
  .tbl-viva,.eq-chip,.voltas-box,.feed-race,.banner-circuito{font-family:var(--cm-font-ui);}
  .voltas-box .n,.race-titulo,.sessao-titulo,.side-stat .val{font-family:var(--cm-font-brand);}
  .tbl-viva th{font-size:.66rem; text-transform:uppercase; letter-spacing:.11em; color:var(--cm-muted);
    padding:7px 8px; border-bottom:1px solid var(--cm-border); text-align:left; background:#10151E;}
  .tbl-viva td{padding:5.5px 8px; border-bottom:1px solid rgba(255,255,255,.055); color:#E7ECF3;
    white-space:nowrap;}
  .tbl-viva tr.meu td{background:rgba(200,16,46,.14);}
  .tbl-viva tr.fora td{color:#7B8798;}
  .tbl-viva td.pos{font-weight:800; width:38px;}
  .tbl-viva td.p1{color:#FFD966;} .tbl-viva td.p2{color:#D7DEE9;} .tbl-viva td.p3{color:#E0A96D;}

  /* ---------- torre de tempos (transmissão) ---------- */
  .tabela-wrap{max-height:66vh; overflow:auto; scrollbar-width:thin;}
  .tabela-wrap::-webkit-scrollbar{width:9px; height:9px;}
  .tabela-wrap::-webkit-scrollbar-thumb{background:rgba(148,163,184,.28); border-radius:99px;}
  .tbl-viva thead th{position:sticky; top:0; z-index:2; backdrop-filter:blur(6px);}
  .tbl-viva tbody tr{position:relative; transition:background .12s ease;}
  .tbl-viva tbody tr td:first-child{box-shadow:inset 3px 0 0 var(--eq, transparent); padding-left:12px;}
  .tbl-viva tbody tr:hover td{background:rgba(255,255,255,.045);}
  .tbl-viva tr.meu td{background:linear-gradient(90deg, rgba(200,16,46,.22), rgba(200,16,46,.07) 55%, transparent);}
  .tbl-viva tr.meu td:first-child{box-shadow:inset 3px 0 0 var(--cm-red2);}
  .tbl-viva tr.lider td:first-child{box-shadow:inset 3px 0 0 #FFD966;}
  .tbl-viva tr.fora{opacity:.62;}
  .tbl-viva .pos-n{font-family:var(--cm-font-brand); font-size:.98rem; letter-spacing:.02em;}
  .dpos{margin-left:4px; font-size:.64rem; font-weight:700; vertical-align:1px;}
  .dpos.up{color:#4ADE80;} .dpos.dn{color:#F87171;} .dpos.eq{color:#64748B;}
  .tag-vc{margin-left:6px; padding:1px 5px; border-radius:5px; font-size:.58rem; font-weight:800;
    letter-spacing:.1em; color:#fff; background:var(--cm-red); vertical-align:1.5px;}
  .nome-cel{font-weight:600;}
  .tbl-viva td.mono{font-variant-numeric:tabular-nums; color:#CBD5E1;}
  .badge-box{display:inline-block; padding:1px 6px; border-radius:5px; font-size:.6rem; font-weight:800;
    letter-spacing:.09em; color:#0B0F14; background:#F59E0B; animation:pulsa 1.1s ease-in-out infinite;}
  @keyframes pulsa{0%,100%{opacity:1} 50%{opacity:.45}}
  .gap-bar{height:3px; width:60px; margin-top:3px; border-radius:99px; background:rgba(255,255,255,.07); overflow:hidden;}
  .gap-bar i{display:block; height:100%; border-radius:99px;
    background:linear-gradient(90deg, rgba(74,222,128,.85), rgba(250,204,21,.85) 55%, rgba(248,113,113,.9));}
  .gap-lider{font-size:.6rem; font-weight:800; letter-spacing:.1em; color:#FFD966;}
  .gap-txt{font-size:.66rem; color:#94A3B8; margin-top:1px;}
  .tyre{display:inline-flex; align-items:center; gap:5px; font-size:.72rem; font-weight:800;
    font-variant-numeric:tabular-nums; color:#E7ECF3;}
  .tyre i{width:11px; height:11px; border-radius:50%; display:inline-block;
    background:var(--t); box-shadow:0 0 0 2px rgba(0,0,0,.45), 0 0 8px color-mix(in srgb, var(--t) 55%, transparent);}
  .eq-chip{display:inline-block; min-width:82px; text-align:center; border-radius:6px;
    padding:2.5px 9px; font-weight:700; font-size:.79rem; text-shadow:0 1px 2px rgba(0,0,0,.4);}
  .voltas-box{border:1px solid rgba(224,36,68,.75); border-radius:14px; text-align:center;
    padding:9px 8px 11px; background:linear-gradient(160deg, rgba(200,16,46,.20), rgba(200,16,46,.07));}
  .voltas-box .lab{font-size:.64rem; letter-spacing:.22em; color:#F3B9BF; text-transform:uppercase; font-weight:700;}
  .voltas-box .n{font-size:1.75rem; font-weight:800; line-height:1.1;}
  .box-piloto{border:1px solid var(--cm-border); border-radius:13px; padding:10px 12px 11px;
    margin-bottom:9px; background:linear-gradient(150deg, rgba(255,255,255,.05), rgba(255,255,255,.015));}
  .box-piloto .papel{font-size:.64rem; letter-spacing:.16em; text-transform:uppercase; color:var(--cm-muted); font-weight:700;}
  .box-piloto .nome{font-weight:700; display:flex; gap:7px; align-items:center; font-size:.98rem; margin-top:1px;}
  .box-piloto .mini{font-size:.78rem; color:#CBD5E1; margin-top:3px;}
  .barra{height:9px; border-radius:999px; background:rgba(255,255,255,.08); overflow:hidden;
    margin-top:7px; border:1px solid rgba(255,255,255,.07);}
  .barra i{display:block; height:100%; border-radius:999px; transition:width .3s ease;}
  .feed-race{font-size:.78rem; color:#CBD5E1; border-left:3px solid var(--cm-red);
    padding:2px 0 2px 9px; margin-top:8px; line-height:1.5;}
  .banner-circuito{background:linear-gradient(120deg, rgba(200,16,46,.16), rgba(16,21,30,.92));
    border:1px solid var(--cm-border); border-radius:13px; padding:11px 14px; text-align:center;
    margin-top:14px; font-size:.92rem; color:#E7ECF3;}
  .paddock-head{border:1px solid rgba(224,36,68,.55); border-radius:14px; text-align:center;
    padding:12px 16px 13px; margin:2px 0 12px;
    background:linear-gradient(135deg, rgba(200,16,46,.16), rgba(13,17,26,.6) 65%);}
  .paddock-kick{font-size:.64rem; letter-spacing:.3em; text-transform:uppercase; color:#F3B9BF; font-weight:800;}
  .paddock-gp{font-family:var(--cm-font-brand); font-weight:700; font-size:1.12rem; margin-top:4px;
    display:flex; align-items:center; justify-content:center; gap:9px;}
  .pit-titulo{text-align:center; font-family:var(--cm-font-brand); font-weight:800; font-size:1.2rem;
    text-decoration:underline; text-underline-offset:5px; margin-bottom:8px;}
  .radio-box{border:1px solid rgba(224,36,68,.6); border-radius:11px; padding:9px 11px 10px;
    margin:0 0 10px; font-size:.86rem; line-height:1.45; color:#F6DDE0;
    background:linear-gradient(135deg, rgba(200,16,46,.20), rgba(16,21,30,.85));}
  .radio-box b{color:#fff;}
  .banner-circuito b{color:#fff;}
  .race-titulo{text-align:center; margin:.2rem 0 .1rem; font-size:1.35rem; font-weight:800;}
  .race-sub{text-align:center; font-style:italic; color:#CBD5E1; font-size:.98rem;}
  .previsao-tempo{border:1px solid rgba(56,189,248,.34); border-radius:12px; padding:8px 12px;
    margin:6px 0 4px; font-size:.86rem; color:#DDE7F3;
    background:linear-gradient(120deg, rgba(56,189,248,.14), rgba(16,21,30,.86));}
  .previsao-tempo b{color:#BAE6FD; letter-spacing:.08em; text-transform:uppercase; font-size:.7rem;}
  .pista-chip{display:inline-flex; align-items:center; gap:6px; border-radius:999px; padding:3px 10px;
    font-size:.74rem; font-weight:700; border:1px solid rgba(255,255,255,.16); margin-bottom:6px;}
  .pista-chip.seco{background:rgba(250,204,21,.16); color:#FDE68A;}
  .pista-chip.molhado{background:rgba(56,189,248,.18); color:#BAE6FD;}
  .box-piloto .alerta{font-size:.76rem; margin-top:4px; color:#FCA5A5; font-weight:700;}
  .proj-box{border:1px solid rgba(148,163,184,.28); border-radius:10px; padding:7px 10px;
    margin:2px 0 6px; font-size:.82rem; color:#DDE7F3; background:rgba(255,255,255,.035);}
  .proj-delta{margin-left:6px; font-size:.72rem; font-weight:800; letter-spacing:.06em;
    text-transform:uppercase; color:#FCD34D;}
  .overcut-card{margin-top:7px; border:1px solid rgba(56,189,248,.55); border-radius:9px;
    padding:6px 9px; font-size:.76rem; line-height:1.4; color:#BAE6FD;
    background:linear-gradient(120deg, rgba(56,189,248,.20), rgba(16,21,30,.85));}
  .undercut-card{margin-top:7px; border:1px solid rgba(245,158,11,.55); border-radius:9px;
    padding:6px 9px; font-size:.76rem; line-height:1.4; color:#FDE68A;
    background:linear-gradient(120deg, rgba(245,158,11,.22), rgba(16,21,30,.85));}
  .pausa-chip{border:1px solid rgba(250,204,21,.5); border-radius:10px; padding:5px 10px;
    margin:0 0 6px; font-size:.76rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase;
    color:#FDE68A; background:rgba(250,204,21,.13); text-align:center;}

  /* ---------- escritório: painéis do original ---------- */
  .office-head{text-align:center; margin:.3rem 0 1rem;}
  .office-head .quem{font-size:.95rem; color:#CBD5E1; letter-spacing:.05em;}
  .office-head .time{font-size:2.05rem; font-weight:800; font-style:italic; line-height:1.15; margin-top:.08rem;}
  .office-meta{display:flex; flex-wrap:wrap; gap:8px; justify-content:center; align-items:center;
    margin-top:.55rem;}
  .office-meta .om{display:inline-flex; gap:5px; align-items:baseline; border-radius:999px;
    padding:3px 11px; font-size:.76rem; color:#CBD5E1; border:1px solid var(--cm-border);
    background:linear-gradient(145deg, rgba(255,255,255,.06), rgba(255,255,255,.015));}
  .office-meta .om b{font-family:var(--cm-font-brand); font-size:.86rem; color:#F8FAFC;}
  .painel{border:1px solid var(--cm-border); border-radius:14px; overflow:hidden;
    background:linear-gradient(165deg, rgba(255,255,255,.05), rgba(255,255,255,.015));
    margin-bottom:12px; box-shadow:0 12px 26px rgba(0,0,0,.18);}
  .painel h4{margin:0; padding:7px 10px; font-size:.74rem; letter-spacing:.16em; text-transform:uppercase;
    text-align:center; background:linear-gradient(120deg, rgba(200,16,46,.40), rgba(200,16,46,.14));
    border-bottom:1px solid var(--cm-border); color:#FFE7EA;}
  .painel .corpo{padding:10px 14px 12px;}
  .plinha{display:flex; justify-content:space-between; align-items:center; gap:10px;
    font-size:.9rem; padding:4px 0; color:#E7ECF3; border-bottom:1px dashed rgba(255,255,255,.07);}
  .plinha:last-child{border-bottom:none;}
  .plinha .k{color:#B8C2D2;}
  .plinha b{font-variant-numeric:tabular-nums;}

  /* ---------- polimento final ---------- */
  [data-testid="stAppDeployButton"], .stDeployButton{display:none !important}
  div[data-testid="stMetricValue"]{font-size:1.5rem !important; line-height:1.15 !important;
    font-family:var(--cm-font-brand); letter-spacing:.01em}
  div[data-testid="stMetricValue"] > div{white-space:normal !important; overflow:visible !important}
  .stTabs [data-baseweb="tab-list"]{padding-left:4px}
  div[role="radiogroup"] > label{width:100%; box-sizing:border-box}
  .side-stats{display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:10px}
  .side-stat{background:linear-gradient(145deg, rgba(255,255,255,.055), rgba(255,255,255,.02));
    border:1px solid var(--cm-border); border-radius:12px; padding:9px 11px}
  .side-stat .lab{font-size:.62rem; letter-spacing:.14em; text-transform:uppercase; color:var(--cm-muted)}
  .side-stat .val{font-size:1rem; font-weight:600; margin-top:3px; white-space:nowrap}
  .flag-img{box-shadow:0 1px 4px rgba(0,0,0,.35)}

  /* ---------- polimento de interação ---------- */
  .painel{transition:border-color .15s ease, transform .15s ease, box-shadow .15s ease;}
  .painel:hover{border-color:rgba(224,36,68,.35); box-shadow:0 16px 34px rgba(0,0,0,.26);}
  .stButton > button, [data-testid^="stBaseButton"]{transition:transform .12s ease, filter .12s ease,
    box-shadow .12s ease; border-radius:11px;}
  .stButton > button:hover, [data-testid^="stBaseButton"]:hover{transform:translateY(-1px); filter:brightness(1.07);}
  [data-testid^="stBaseButton"]:active{transform:translateY(0);}
  *:focus-visible{outline:2px solid rgba(224,36,68,.75); outline-offset:2px; border-radius:8px;}
  html{scrollbar-width:thin; scrollbar-color:rgba(148,163,184,.32) transparent;}
  ::-webkit-scrollbar{width:10px; height:10px;}
  ::-webkit-scrollbar-thumb{background:rgba(148,163,184,.28); border-radius:99px;}
  ::-webkit-scrollbar-thumb:hover{background:rgba(148,163,184,.45);}
  @media (prefers-reduced-motion:reduce){*{animation:none !important; transition:none !important;}}
</style>
""",
    unsafe_allow_html=True,
)

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


def _continuar_da_corrida():
    """Pós-corrida → Escritório. Como `on_click` roda ANTES dos widgets da
    próxima execução, dá pra trocar o menu sem WidgetAlreadyInstantiated."""
    st.session_state.game["rodada"] += 1
    st.session_state.fds = None
    ir_para("🏠 Escritório")


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


# ======================================================================
#  COMPONENTES VISUAIS
# ======================================================================
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
        up = st.file_uploader("Arquivo de save (.json)", type="json", key="load_save")
        if up and st.button("Carregar save", type="primary"):
            try:
                dados = json.loads(up.read().decode("utf-8"))
                assert "equipes" in dados and "pilotos" in dados and "ano" in dados
                dados.setdefault(
                    "meta",
                    {
                        "nome": "Save (F1 2026)",
                        "categoria": "Fórmula 1",
                        "rotulo_fornecedor": "Motor",
                        "rotulo_corrida2": "Sprint",
                        "pontos_corrida": db.PONTOS_CORRIDA,
                        "pontos_corrida2": db.PONTOS_SPRINT,
                    },
                )
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
ROTULOS_PAPEL = {
    "P1": "1o piloto",
    "P2": "2o piloto",
    "P3": "3o piloto",
    "P4": "4o piloto",
    "teste": "Testes/reserva",
    "livre": "Livre",
}


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
                "Salário/corrida": p["salario_corrida"],
                "Contrato": f"{p['contrato_anos']} ano(s)",
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


# ======================================================================
#  ESCRITÓRIO (tela principal, como o "resumo" do CM14)
# ======================================================================
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


# ======================================================================
#  CORRIDA
# ======================================================================
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


# ------------------------------------------------------------------ telas
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


def _cabecalho_treino(etapa):
    """Cabeçalho da tela de treino (fiel ao original): Treino / circuito / GP."""
    st.markdown(
        f'<div class="sessao-card">'
        f'<div class="sessao-titulo">Treino</div>'
        f'<div class="sessao-circuito">{etapa["circuito"]}</div>'
        f'<div class="sessao-gp">{etapa["gp"]} {bnd.img_bandeira(etapa["bandeira"], 22)}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _cabecalho_corrida(game, etapa, molhado, com_checkbox=False):
    """Cabeçalho da tela de corrida: GP — Etapa X de N, circuito e clima."""
    rodada = game["rodada"] + 1
    total = len(game["calendario"])
    st.markdown(f'<div class="race-titulo">{etapa["gp"]} — Etapa {rodada} de {total}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="race-sub">{bnd.img_bandeira(etapa["bandeira"], 20)} {etapa["circuito"]}</div>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([1, 1])
    c1.markdown(f"**Clima:** {_clima_txt(molhado)}")
    if com_checkbox:
        c2.checkbox("Ver pits/pneus", key="ver_pits", help="Mostra colunas de composto e paradas na tabela ao vivo.")
        st.caption(
            "📻 Em **cada parada** a prova pausa e abre a janela do **Pit Stop**: trocar de "
            "pneu (e qual composto) e o **ritmo do próximo stint**. Também dá para chamar o "
            "box a qualquer momento com o **Pit stop!**."
        )


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
    """X/ESC na janela do box: para parada planejada vale "seguir na pista"
    (não insiste de novo na mesma volta); para ordem manual, só cancela."""
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
    stt["pit_aberto"] = None


ATALHOS_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "atalhos.html")


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
    volta_pit = int(ped.get("volta") or lap)
    st.markdown('<div class="pit-titulo">Pit Stop</div>', unsafe_allow_html=True)
    st.markdown(f"**Piloto:** {bnd.img_bandeira(p['bandeira'], 18)} {p['nome']}", unsafe_allow_html=True)
    if planejada:
        st.markdown(
            f'<div class="radio-box">📻 <b>Muro:</b> {p["nome"]}, hora do pit stop '
            f"(volta {volta_pit}/{voltas}). <b>Trocar de pneu?</b></div>",
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
    rotulo_fora = "Continuar na pista ✕" if planejada else "Cancelar ordem ✕"
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
    if stt.get("pulou"):
        lap = voltas
    else:
        s_por_volta = max(0.2, min(0.55, 24.0 / max(1, voltas)))
        lap = min(voltas, int((agora - float(stt["t0"])) / s_por_volta * velocidade))
    lap = max(1, lap)
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
        ):
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

    st.markdown(
        f'<div class="race-hero"><div class="kicker">Etapa {game["rodada"] + 1} · {game["ano"]}</div>'
        f"<h1>{bnd.img_bandeira(etapa['bandeira'], 36)} {etapa['gp']}</h1>"
        f'<p style="margin:0;color:#CBD5E1">{etapa["circuito"]} · {etapa["pais"]}</p></div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Etapa", f"{game['rodada'] + 1}/{len(game['calendario'])} · {game['ano']}")
    c2.metric("Voltas", etapa["voltas"])
    c3.metric("Clima", "🌧️ Molhado" if molhado else "☀️ Seco")
    c4.metric("Formato", f"⚡ {rot_corrida2(game)} + principal" if etapa["sprint"] else "Corrida única")
    st.caption(
        f"Características: peso do motor {etapa['potencia'] * 100:.0f}% · facilidade de ultrapassar "
        f"{etapa['ultrap'] * 100:.0f}% · desgaste {etapa['desgaste']:.1f}/3 → estratégia típica: "
        f"**{sim.paradas_ideais(etapa)} parada(s)**"
    )
    previsao = sim.previsao_texto(fds.get("clima"))
    st.markdown(f'<div class="previsao-tempo"><b>Previsão do tempo</b> · {previsao}</div>', unsafe_allow_html=True)

    # ---------------- estratégia: os ajustes ficam no Paddock (pneus/grid) e
    # no rádio ao vivo; aqui só nasce o padrão de cada piloto.
    estrategias = {p["id"]: {"paradas": sim.paradas_ideais(etapa), "ritmo": "Normal"} for p in meus}

    # ---------------- sprint
    if etapa["sprint"]:
        st.divider()
        st.subheader(f"⚡ {rot_corrida2(game)} (primeira corrida do fim de semana)")
        if fds["sprint"] is None:
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
            if st.button(f"▶️ Simular {rot_corrida2(game)}", width="stretch"):
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

    # ---------------- tela de treino classificatório
    st.divider()
    st.subheader("⏱️ Treino classificatório")
    bloqueado = bool(etapa["sprint"] and fds["sprint"] is None)
    _cabecalho_treino(etapa)
    sess = fds.get("treino")
    if not sess or not sess.get("t0"):
        # cronômetro parado: grade neutra com '-' (sem spoiler do grid)
        cm1, cm2 = st.columns([3.2, 1])
        cm1.progress(0.0, text="⏱️ Tempo de treino restante: 60 min")
        cm2.markdown(f"**Clima:** {_clima_txt(molhado)}")
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
    elif not sess.get("concluido"):
        _frag_treino(game, etapa, molhado, fds)
    else:
        # sessão encerrada: grade final congelada + pole + passagem para a corrida
        cm1, cm2 = st.columns([3.2, 1])
        cm1.progress(1.0, text="⏱️ Tempo de treino restante: 0 min")
        cm2.markdown(f"**Clima:** {_clima_txt(molhado)}")
        st.markdown(_html_tabela_treino(game, fds["grid"], sess, int(sess["duracao"])), unsafe_allow_html=True)
        pole = sim.piloto(game, fds["grid"][0]["piloto_id"])
        st.caption(
            f"🏆 **Pole position:** {pole['nome']} ({fmt_tempo(fds['grid'][0]['tempo'])}) · {len(fds['grid'])} no grid"
        )
        if not fds.get("treino_ok"):
            if st.button("➡️ Ir para corrida!", type="primary", width="stretch", key="ir_corrida"):
                fds["treino_ok"] = True
                flash(
                    "success",
                    "Treino encerrado e grid confirmado — prepare a estratégia e dê a largada na tela abaixo!",
                )
                st.rerun()
        else:
            st.caption("✅ Treino concluído — role até a tela da corrida e aperte **Dar largada!**")

    # ---------------- tela da corrida
    st.divider()
    _cabecalho_corrida(game, etapa, molhado, com_checkbox=bool(rep_state) and not rep_state.get("concluido"))
    if rep_state is not None and not rep_state.get("concluido"):
        _atalhos_corrida()
        _frag_corrida(game, etapa, molhado, fds, meus)
    elif rep_state is None:
        # ---- pré-largada: grid + Paddock (pneus/grid/pit) + Dar largada! ----
        treino_ok = bool(fds.get("treino_ok"))
        c1, c2 = st.columns([2.3, 1], gap="medium")
        with c1:
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
                st.info("🏁 O grid de largada aparece aqui depois do treino.")
        with c2:
            st.markdown(
                f'<div class="voltas-box"><div class="lab">Voltas</div>'
                f'<div class="n">0 / {etapa["voltas"]}</div></div>',
                unsafe_allow_html=True,
            )
        # ---- Paddock (fiel ao original): pneus com durabilidade, grid e aviso de pit stop
        st.markdown(
            f'<div class="paddock-head"><div class="paddock-kick">Paddock</div>'
            f'<div class="paddock-gp">{etapa["gp"]} — {etapa["voltas"]} voltas '
            f"{bnd.img_bandeira(etapa['bandeira'], 20)}</div></div>",
            unsafe_allow_html=True,
        )
        pit_auto = {}
        grid_pos = {g["piloto_id"]: g["pos"] for g in (fds.get("grid") or [])}
        colsp = st.columns(len(meus))
        for col, p in zip(colsp, meus):
            with col, st.container(border=True):
                st.markdown(
                    bnd.com_bandeira(
                        p["bandeira"], f"**#{p['numero']} {p['nome']}** ({ROTULOS_PAPEL.get(p['papel'], p['papel'])})"
                    ),
                    unsafe_allow_html=True,
                )
                pneu_pad = st.selectbox(
                    "Pneus",
                    opcoes_pneu,
                    index=0 if molhado else 1,
                    format_func=_rot_pneu,
                    key=f"pad_pneu_{p['id']}_{fds['chave']}",
                )
                if molhado and pneu_pad in sim.PNEUS_SECO:
                    st.error("⚠️ Pneu slick na chuva?! Isso vai doer...")
                if not molhado and pneu_pad in sim.PNEUS_MOLHADO:
                    st.error("⚠️ Pneu de chuva no seco derrete em 3 voltas!")
                estrategias.setdefault(p["id"], {"paradas": sim.paradas_ideais(etapa), "ritmo": "Normal"})
                estrategias[p["id"]]["pneu"] = pneu_pad
                pos = grid_pos.get(p["id"])
                st.markdown(f"**Grid:** {f'{pos}º lugar' if pos else '—'}")
                pit_auto[p["id"]] = st.checkbox(
                    "Perguntar em cada pit stop",
                    value=True,
                    help="A cada parada planejada abre a janela do Pit Stop para você "
                    "decidir: trocar o pneu (e qual composto) e o novo ritmo. "
                    "Desmarque para o box fazer as paradas sozinho.",
                    key=f"pad_perg_{p['id']}_{fds['chave']}",
                )
        if st.button("✅ Confirmar", type="primary", width="stretch", key="paddock_confirmar"):
            fds["paddock_ok"] = True
            flash("success", "Paddock confirmado — pneus e avisos de pit stop valendo. Agora é só dar a largada!")
            st.rerun()
        if fds.get("paddock_ok"):
            st.caption("✅ Paddock confirmado — estratégia valendo para a largada.")
        paddock_ok = bool(fds.get("paddock_ok"))
        pode_largar = treino_ok and bool(fds.get("grid")) and not bloqueado and paddock_ok
        if st.button("🚦 Dar largada!", type="primary", width="stretch", key="dar_largada", disabled=not pode_largar):
            res, ev = sim.simular_corrida(
                game, etapa, fds["grid"], estrategias, molhado, clima=fds.get("clima")
            )
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
        if bloqueado:
            st.caption(f"🏁 Simule o {rot_corrida2(game)} primeiro.")
        elif not treino_ok:
            st.caption("⏱️ Complete o treino para liberar a largada.")
        elif not paddock_ok:
            st.caption("✅ Confirme o Paddock para liberar a largada.")
    else:
        # ---- pós-corrida: classificação final, eventos e finanças
        if rep_state.get("venceu") and not rep_state.get("balloons_ok"):
            rep_state["balloons_ok"] = True
            st.balloons()
        st.dataframe(df_resultado(game, fds["resultado"]), hide_index=True, width="stretch", column_config=CFG_BANDEIRA)
        for ev in fds["eventos"]:
            st.markdown(f"- {ev}")
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
    st.markdown(
        f'<div class="banner-circuito"><b>{etapa["circuito"]} — {etapa["gp"]}</b><br>'
        f"Clima: {_clima_txt(molhado)}</div>",
        unsafe_allow_html=True,
    )


# ======================================================================
#  CARRO & INVESTIMENTOS
# ======================================================================
def pagina_carro(game):
    eqj = sim.equipe(game, game["equipe_jogador"])
    mot = sim.motor(game, eqj["motor_id"])
    titulo_pagina(
        "Engenharia", "Carro & Investimentos", "Desenvolva o chassi, proteja a confiabilidade e acompanhe as rivais."
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Nível do chassi", f"{eqj['nivel_carro']:.1f}")
    c2.metric(f"Motor {mot['nome']}", f"{mot['potencia']} pot / {mot['confiabilidade']} conf")
    c3.metric("Desempenho combinado", f"{sim.desempenho_carro(game, eqj):.1f}")
    c4.metric("Confiabilidade do carro", f"{eqj['confiabilidade']:.0f}")

    st.subheader("💸 Investimento por corrida")
    inv = st.slider(
        "Quanto investir no desenvolvimento a cada corrida (US$ mil)", 0, 3000, int(eqj["investimento_corrida"]), 50
    )
    eqj["investimento_corrida"] = inv
    eqj["foco"] = st.radio(
        "Foco do desenvolvimento",
        ["equilibrado", "chassi", "confiabilidade"],
        index=["equilibrado", "chassi", "confiabilidade"].index(eqj["foco"]),
        horizontal=True,
        format_func=lambda x: {
            "equilibrado": "⚖️ Equilibrado",
            "chassi": "🏎️ Chassi/aero (mais velocidade)",
            "confiabilidade": "🛡️ Confiabilidade (menos abandonos)",
        }[x],
    )
    teste = sim.piloto_teste(game, eqj["id"])
    feedback = (sum(t["atributos"]["acerto"] for t in sim.titulares(game, eqj["id"])) / 2) * 0.7 + (
        (teste["atributos"]["acerto"] * 0.3) if teste else 21
    )
    ganho = (inv / 1000.0) * 0.22 * (feedback / 85.0) * max(0.12, (99.5 - eqj["nivel_carro"]) / 35.0)
    st.info(
        f"Feedback dos pilotos (Acerto): **{feedback:.0f}** → ganho estimado de "
        f"**+{ganho:.2f}** de nível por corrida. Piloto de testes com Acerto alto acelera tudo — "
        f"o seu é {teste['nome'] if teste else '—'} (Acerto {teste['atributos']['acerto'] if teste else '—'})."
    )
    st.caption(
        "⚠️ Investir demais quebra o caixa (e sem caixa, sem motor decente na próxima temporada). "
        "No CM14 original, esse era O erro fatal dos novatos."
    )

    st.subheader("📏 Nível das equipes (como em Campeonato → Equipes do original)")
    linhas = []
    for e in sorted(game["equipes"], key=lambda x: -sim.desempenho_carro(game, x)):
        m = sim.motor(game, e["motor_id"])
        linhas.append(
            {
                "Bandeira": bnd.url_bandeira(e["bandeira"]),
                "Equipe": e["nome"],
                "": "⭐" if e["id"] == eqj["id"] else "",
                "Chassi": round(e["nivel_carro"], 1),
                "Motor": m["nome"],
                "Potência": m["potencia"],
                "Desempenho": round(sim.desempenho_carro(game, e), 1),
                "Confiabilidade": round(e["confiabilidade"]),
                "Prestígio": e["prestigio"],
                "Caixa (mi)": round(e["caixa"], 1),
            }
        )
    df = pd.DataFrame(linhas)
    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
        column_config={
            **CFG_BANDEIRA,
            **{
                c: st.column_config.ProgressColumn(c, min_value=0, max_value=100, format="%.0f")
                for c in ["Chassi", "Potência", "Desempenho", "Confiabilidade"]
            },
        },
    )
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
                marca = " · 📝 pré (sinal pago)" if c.get("pre") else ""
                col1.markdown(
                    bnd.com_bandeira(
                        p["bandeira"],
                        f"**{p['nome']}** — {c['papel']} · {sim.fmt_dinheiro_k(c['salario'])}/corrida · {c['anos']} ano(s){marca}",
                    ),
                    unsafe_allow_html=True,
                )
                if col2.button("Cancelar", key=f"canc_{pid}"):
                    del game["contratos_proxima"][pid]
                    if c.get("pre"):
                        flash(
                            "warning",
                            f"Pré-contrato de {p['nome']} cancelado — a sinalização de "
                            f"{sim.fmt_dinheiro_k(c.get('sinal', 0))} **não** é devolvida.",
                        )
                    st.rerun()

    with tab2:
        st.caption(
            "Como no original: você negocia **durante** a temporada, mas o piloto só veste seu macacão "
            "na **próxima**. Salários são por corrida — ou feche na hora com um **pré-contrato** (sinal pago)."
        )
        ativos: list[dict] = [p for p in game["pilotos"] if not p["aposentado"]]
        ativos.sort(key=lambda p: -sim.overall(p))
        sel = st.selectbox(
            "Piloto",
            ativos,
            format_func=lambda p: (
                f"[{bnd.codigo_texto(p['bandeira'])}] {p['nome']} — ovr {sim.overall(p)} · {p['idade']} anos · "
                f"{(sim.equipe(game, p['equipe_id'])['nome'] if p['equipe_id'] else 'LIVRE')} ({p['papel']})"
            ),
        )
        assert sel is not None  # selectbox com lista não vazia sempre escolhe um valor
        a = sel["atributos"]
        st.bar_chart(pd.Series({db.ATRIBUTOS[k]: v for k, v in a.items()}))
        st.caption(
            f"Auge: {sel['auge_inicio']}–{sel['auge_fim']} anos (platô) · Potencial: {sel['potencial']} · "
            f"Vitórias no save: {sel['vitorias']} · Títulos: {sel['titulos']}"
        )
        with st.form("form_contrato"):
            _vagas = list((game.get("vagas_por_equipe") or {}).get(eqj["id"], ["P1", "P2"])) + ["teste"]
            papel = st.radio("Papel oferecido", _vagas, horizontal=True, format_func=lambda x: ROTULOS_PAPEL.get(x, x))
            esperado = sim.salario_esperado(game, sel, papel)
            salario = st.number_input(
                f"Salário oferecido (US$ mil/corrida) — o mercado pagaria ±{sim.fmt_dinheiro_k(esperado)}",
                min_value=10,
                max_value=6000,
                value=int(esperado),
                step=10,
            )
            anos = st.slider("Duração (anos)", 1, 4, 2)
            tipo = st.radio(
                "Tipo de acordo",
                ["✍️ Proposta comum — grátis, ele pode recusar", "📝 Pré-contrato — fecha na hora, com sinal"],
                key="tipo_acordo",
                help="Como no original: o pré-contrato paga uma taxa de sinalização de 3 corridas do "
                "salário AGORA e fecha o acordo sem chance de recusa. A taxa não é devolvida se "
                "você cancelar (e some se o piloto se aposentar antes da virada).",
            )
            taxa = sim.taxa_sinal(int(salario))
            if tipo.startswith("📝"):
                st.caption(
                    f"💸 Sinal a pagar agora: **{sim.fmt_dinheiro_k(taxa)}** (3 corridas do salário) · "
                    f"seu caixa: {sim.fmt_dinheiro_m(eqj['caixa'])}"
                )
            if st.form_submit_button(
                "📝 Assinar pré-contrato" if tipo.startswith("📝") else "✍️ Fazer proposta",
                type="primary",
                width="stretch",
            ):
                if tipo.startswith("📝"):
                    ok, msg = sim.pre_contratar_piloto(game, sel["id"], papel, int(salario), anos)
                else:
                    ok, msg = sim.negociar_piloto(game, sel["id"], papel, int(salario), anos)
                flash("success" if ok else "error", msg)
                st.rerun()

    with tab3:
        linhas = []
        for p in sorted(ativos, key=lambda x: -x["pontos"]):
            linhas.append(
                {
                    "Bandeira": bnd.url_bandeira(p["bandeira"]),
                    "Piloto": p["nome"],
                    "Idade": p["idade"],
                    "Equipe": sim.equipe(game, p["equipe_id"])["nome"] if p["equipe_id"] else "— LIVRE —",
                    "Papel": p["papel"],
                    "Overall": sim.overall(p),
                    "Potencial": p["potencial"],
                    "Pontos": p["pontos"],
                    "Vitórias*": p["vitorias"],
                    "Pódios*": p["podios"],
                    "Títulos*": p["titulos"],
                    "Salário": p["salario_corrida"],
                }
            )
        st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch", column_config=CFG_BANDEIRA)
        st.caption("* Estatísticas acumuladas dentro deste save.")


# ======================================================================
#  MOTORES
# ======================================================================
def pagina_motores(game):
    eqj = sim.equipe(game, game["equipe_jogador"])
    titulo_pagina(
        "Fornecedores",
        f"{rot_fornecedor(game)}s",
        "Desempenho de verdade custa caro. Ficar sem caixa sai mais caro ainda.",
    )
    atual = sim.motor(game, eqj["motor_id"])
    st.write(
        f"Motor atual: **{atual['nome']}** — potência {atual['potencia']}, confiabilidade {atual['confiabilidade']}"
        + (
            " · **motor próprio** (custo interno reduzido; herança da equipe, como na DB: Audi/Ferrari/Mercedes/Red Bull)."
            if eqj.get("motor_proprio")
            else f" · custo de US$ {atual['preco']:.0f} mi/temporada."
        )
    )
    df = pd.DataFrame(
        [
            {
                "Motor": m["nome"],
                "": "⭐ atual" if m["id"] == eqj["motor_id"] else "",
                "Potência": m["potencia"],
                "Confiabilidade": m["confiabilidade"],
                "Preço (mi/ano)": m["preco"],
                "Obs.": ("de fábrica" if m["proprio_de"] else "independente/cliente"),
            }
            for m in sorted(game["motores"], key=lambda x: -x["potencia"])
        ]
    )
    st.dataframe(
        df,
        hide_index=True,
        width="stretch",
        column_config={
            c: st.column_config.ProgressColumn(c, min_value=0, max_value=100, format="%d")
            for c in ["Potência", "Confiabilidade"]
        },
    )
    for m in game["motores"]:
        st.caption(f"**{m['nome']}** — {m['desc']}")

    if eqj.get("motor_proprio"):
        st.info(
            "Equipes com motor próprio não trocam de fornecedor (fidelidade à DB). "
            "Seu motor evolui um pouco a cada temporada junto com o investimento da fábrica."
        )
    else:
        st.subheader(f"🔁 Contrato para {game['ano'] + 1}")
        disponiveis: list[dict] = [m for m in game["motores"] if not m["proprio_de"] and m["id"] != "fia"]
        escolhido = st.selectbox(
            "Próximo motor",
            disponiveis,
            format_func=lambda m: f"{m['nome']} — pot {m['potencia']} · US$ {m['preco']:.0f} mi/ano",
        )
        assert escolhido is not None  # selectbox com lista não vazia sempre escolhe um valor
        if game["motor_proxima"]:
            st.success(
                f"Acordo fechado: motor **{sim.motor(game, game['motor_proxima'])['nome']}** em {game['ano'] + 1} "
                f"(o valor é debitado na virada da temporada)."
            )
        if st.button("✍️ Assinar contrato de motor", type="primary"):
            game["motor_proxima"] = escolhido["id"]
            flash(
                "success", f"Motor {escolhido['nome']} garantido para {game['ano'] + 1} — se houver caixa para pagar!"
            )
            st.rerun()
        st.caption(
            "🚨 Se na virada da temporada o caixa não cobrir o motor, entra o lendário "
            "**motor FIA compulsório (50% de potência)** — pesadelo de todo jogador de CM14."
        )


# ======================================================================
#  PATROCINADORES & FINANÇAS
# ======================================================================
def pagina_financas(game):
    eqj = sim.equipe(game, game["equipe_jogador"])
    titulo_pagina(
        "Dinheiro", "Patrocinadores & Finanças", "Quem paga a conta, para onde vai cada centavo — e o que sobra no fim."
    )
    lista_spon = game.get("patrocinadores") or db.PATROCINADORES
    spon = next((s for s in lista_spon if s["nome"] == eqj["patrocinador"]), lista_spon[-1])
    salarios = sum(p["salario_corrida"] for p in game["pilotos"] if p["equipe_id"] == eqj["id"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Caixa", sim.fmt_dinheiro_m(eqj["caixa"]))
    c2.metric("Patrocinador atual", spon["nome"])
    c3.metric("Receita fixa/corrida", sim.fmt_dinheiro_k(spon["por_corrida"]))
    saldo = spon["por_corrida"] - salarios - eqj["investimento_corrida"]
    c4.metric(
        "Saldo/corrida (sem bônus)",
        f"+ {sim.fmt_dinheiro_k(saldo)}" if saldo >= 0 else f"− {sim.fmt_dinheiro_k(-saldo)}",
    )
    if saldo < 0:
        st.warning(
            "Você gasta mais do que recebe por corrida (antes dos bônus por ponto/pódio). "
            "Ou pontua muito, ou corta salário/investimento, ou troca o patrocinador na virada."
        )

    st.subheader(f"🤝 Patrocinadores disponíveis para {game['ano'] + 1} (seu prestígio: {eqj['prestigio']})")
    linhas = [
        {
            "Patrocinador": s["nome"],
            "": "⭐ atual" if s["nome"] == eqj["patrocinador"] else "",
            "Fixo/corrida": s["por_corrida"],
            "Bônus/ponto": s["bonus_ponto"],
            "Bônus/pódio": s["bonus_podio"],
            "Bônus/vitória": s["bonus_vitoria"],
            "Prestígio mín.": s["prestigio_min"],
            "Status": "✅ assina" if eqj["prestigio"] >= s["prestigio_min"] else "🔒 prestígio insuficiente",
        }
        for s in lista_spon
    ]
    st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch", column_config=CFG_BANDEIRA)
    elegiveis = [s for s in lista_spon if eqj["prestigio"] >= s["prestigio_min"]]
    novo = st.selectbox(
        "Negociar para a próxima temporada", elegiveis, format_func=lambda s: f"{s['nome']} — {s['desc']}"
    )
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
        st.dataframe(
            pd.DataFrame(game["extrato"]).rename(
                columns={"temporada": "Ano", "etapa": "Etapa", "descricao": "Descrição", "valor": "US$ mil"}
            ),
            hide_index=True,
            width="stretch",
        )
    else:
        st.caption("Nenhum lançamento ainda. Bora correr!")


# ======================================================================
#  CAMPEONATO
# ======================================================================
def pagina_campeonato(game):
    titulo_pagina(
        "Classificação",
        f"Campeonato {game['ano']}",
        "Pilotos, construtores, evolução dos pontos e todos os resultados.",
    )
    tab1, tab2, tab3, tab4 = st.tabs(["👨‍✈️ Pilotos", "🏭 Construtores", "📈 Evolução", "🗓️ Calendário & Resultados"])

    with tab1:
        linhas = []
        for i, p in enumerate(sim.tabela_pilotos(game)):
            linhas.append(
                {
                    "Pos": i + 1,
                    "Bandeira": bnd.url_bandeira(p["bandeira"]),
                    "Piloto": p["nome"],
                    "Equipe": sim.equipe(game, p["equipe_id"])["nome"] if p["equipe_id"] else "—",
                    "": "⭐" if p["equipe_id"] == game["equipe_jogador"] else "",
                    "Pontos": p["pontos"],
                    "Vitórias": p["vitorias"],
                    "Pódios": p["podios"],
                    "Poles": p["poles"],
                    "Abandonos": p["abandonos"],
                    "Forma": p["forma"],
                }
            )
        st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch", column_config=CFG_BANDEIRA)
    with tab2:
        linhas = [
            {
                "Pos": i + 1,
                "Bandeira": bnd.url_bandeira(e["bandeira"]),
                "Equipe": e["nome"],
                "": "⭐" if e["id"] == game["equipe_jogador"] else "",
                "Pontos": e["pontos"],
                "Vitórias": e["vitorias"],
                "Pódios": e["podios"],
                "Poles": e["poles"],
            }
            for i, e in enumerate(sim.tabela_construtores(game))
        ]
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
            st.dataframe(
                pd.DataFrame(game["historico_temporadas"]).rename(
                    columns={
                        "ano": "Ano",
                        "campeao_pilotos": "Campeão (Pilotos)",
                        "equipe_campea": "Campeã (Construtores)",
                        "sua_posicao": "Sua posição",
                        "seus_pontos": "Seus pontos",
                    }
                ),
                hide_index=True,
                width="stretch",
            )
    with tab4:
        for i, etapa in enumerate(game["calendario"]):
            regs = [
                r for r in game["resultados"] if r["ano"] == game["ano"] and r["rodada"] == i + 1 and not r["sprint"]
            ]
            with st.expander(
                f"{i + 1}. [{bnd.codigo_texto(etapa['bandeira'])}] {etapa['gp']} — {etapa['circuito']} · {etapa['voltas']} voltas"
                + (f" · ⚡{rot_corrida2(game)}" if etapa["sprint"] else "")
                + (" ✅" if regs else "")
            ):
                if regs:
                    r = regs[-1]
                    st.caption("🌧️ Corrida molhada" if r["molhado"] else "☀️ Corrida seca")
                    st.dataframe(
                        df_resultado(game, r["resultado"]), hide_index=True, width="stretch", column_config=CFG_BANDEIRA
                    )
                else:
                    st.caption("Ainda não disputada.")


# ======================================================================
#  HALL DA FAMA & CONQUISTAS
# ======================================================================
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


# ======================================================================
#  SALVAR / CARREGAR
# ======================================================================
def pagina_save(game):
    titulo_pagina(
        "Sistema",
        "Salvar / Carregar",
        "Baixe o save para continuar depois ou use Novo jogo na barra lateral para começar outra carreira.",
    )
    save_json = json.dumps(game, ensure_ascii=False, indent=1)
    st.download_button(
        "⬇️ Baixar save (.json)",
        save_json,
        file_name=f"cockpit_save_{game['ano']}_etapa{game['rodada'] + 1}.json",
        mime="application/json",
        type="primary",
    )
    st.caption("Guarde o arquivo e carregue na tela inicial para continuar a carreira em qualquer lugar.")
    st.divider()
    if st.checkbox("Entendo que começar um jogo novo apaga a carreira atual desta sessão"):
        if st.button("🗑️ Abandonar carreira e voltar ao início", type="primary"):
            iniciar_novo_jogo()
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
2. **Corrida** — dispute a Sprint (se houver — com o próprio **pneu de largada**) e a classificação; depois
   confirme o **Paddock** (pneus, grid e **Perguntar em cada pit stop**) e **durante a corrida** ajuste o
   ritmo no rádio ao vivo e responda a janela do **Pit Stop** a cada parada (trocar o pneu? qual ritmo?).
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
- **Durante a corrida**: mude o **ritmo** no rádio ao vivo (afeta o tempo de volta projetado e a vida do
  pneu) e clique **Pit stop!** para abrir a janela **Pit Stop** quando quiser — piloto, **Novos pneus**
  com a durabilidade, **Ritmo do próximo stint**, volta atual, **Trocar pneu e voltar ✓** /
  **Continuar na pista ✕** (ou **Cancelar ordem ✕**, se foi você quem chamou); dá para uma parada
  extra além das planejadas. O resultado final continua sendo o do motor.
- **A janela abre em TODA parada planejada**: na volta do plano o muro chama no rádio e a prova
  **congela** até a resposta — *trocar de pneu?* (e qual composto) e *qual ritmo no próximo stint?*.
  Fechar a janela (X/ESC) equivale a **seguir na pista**; a janela que passar batido (aba em segundo
  plano) é dada como perdida e o piloto continua com o pneu velho.
- **Paddock (antes da largada)**: por piloto, **Pneus** com a durabilidade exata ("Duro (33 voltas)"),
  a posição no **Grid** e o **Perguntar em cada pit stop** — desmarque para o box executar as paradas
  planejadas sozinho, sem janela. O **Confirmar** do Paddock libera a **largada**.
- **Undercut**: rival que estava logo atrás e vai ao box aparece no rádio com o botão **⚡ Responder agora** —
  pare na volta seguinte ou aceite perder a posição. O diálogo do box mostra a **posição projetada na saída**
  ("P9 agora → P11 saindo do box"), então dá para pesar antes de confirmar.
- **Transmissão**: use **⏩ Próxima parada** para pular direto ao próximo box planejado, **⏸ Pausar** para
  pensar e **1×/2×/4×** para acelerar. A torre de tempos mostra setas de posições versus o grid, composto
  colorido e barra de diferença para o líder.
- **Overcut**: rival que estava **à frente** vai ao box e aparece o botão **🔥 Ficar e atacar** — manter o
  piloto na pista com ritmo `Atacar` devolve a posição na saída dele (o ganho aparece na torre de tempos).
  Se você parar dentro da janela, o overcut é abortado.
- **Clima ao vivo**: a tela mostra a **previsão do tempo** da prova — largada seca ou molhada e, às vezes,
  *"a chuva chega por volta de X"* ou *"a pista deve secar por volta de X"*. Durante a corrida, o chip de
  **pista** acompanha a condição real, avisa no feed quando vira e destaca no painel do piloto quando o
  composto está errado para a pista (slick na chuva, chuva no seco). **E o clima pesa no resultado de
  verdade**: talento de chuva, composto de largada certo e número de paradas contam pontos no motor —
  a previsão que você leu antes da largada decide a prova.
- **Controle da transmissão**: **⏸ Pausar / ▶ Retomar** congela a prova para pensar e **1× / 2× / 4×**
  acelera a transmissão. Atalhos de teclado: **espaço** pausa/retoma, **1/2/4** mudam a velocidade e
  **P / O** abrem o Pit Stop do 1º e do 2º piloto.
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
        st.markdown(
            '<div class="side-stats">'
            f'<div class="side-stat"><div class="lab">Caixa</div>'
            f'<div class="val">{sim.fmt_dinheiro_m(eqj["caixa"]).replace("US$ ", "$")}</div></div>'
            f'<div class="side-stat"><div class="lab">Construtores</div>'
            f'<div class="val">{sim.posicao_equipe(game, eqj["id"])}º · {eqj["pontos"]} pts</div></div></div>',
            unsafe_allow_html=True,
        )
        st.radio("Menu", MENUS, key="menu", label_visibility="collapsed")
        st.divider()
        if st.button("🆕 Novo jogo", width="stretch"):
            st.session_state.novo_jogo_pendente = True
        if st.session_state.get("novo_jogo_pendente", False):
            exibir_confirmacao_novo_jogo()
        save_json = json.dumps(game, ensure_ascii=False)
        st.download_button(
            "💾 Salvar (.json)",
            save_json,
            file_name=f"cockpit_save_{game['ano']}.json",
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
