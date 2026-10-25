# -*- coding: utf-8 -*-
"""Tema visual do Cockpit Manager.

O CSS do jogo mora aqui (e não no app.py) para manter a interface legível:
- tokens de fonte (`--cm-font-*`) e cores da marca;
- componentes do escritório, da torre de tempos, do Paddock e do box;
- polimento de interação e acessibilidade (foco visível, scrollbars, reduced motion).

Uso: `from ui import tema` e `tema.aplicar()` uma vez por execução.
"""
import streamlit as st

CSS = """
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
  .side-next{display:flex; gap:9px; align-items:center; margin:8px 0 10px; padding:8px 10px;
    border:1px solid rgba(224,36,68,.4); border-radius:12px;
    background:linear-gradient(120deg, rgba(200,16,46,.16), rgba(13,17,26,.7));}
  .side-next .sn-gp{font-size:.84rem; font-weight:700; color:#F8FAFC; line-height:1.2;}
  .side-next .sn-meta{font-size:.7rem; color:#94A3B8; margin-top:2px;}
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

  /* ---------- bandeira vermelha (corrida interrompida) ---------- */
  .bandeira-vermelha{display:flex; gap:8px; align-items:center; margin:.45rem 0 .5rem;
    padding:10px 13px; border-radius:12px; font-size:.86rem; color:#FFE4E6;
    background:linear-gradient(100deg, rgba(190,18,60,.55), rgba(120,10,30,.35));
    border:1px solid rgba(255,99,132,.55); animation:pulsa 1.4s ease-in-out infinite;}

  /* ---------- comparador de carros (radar SVG) ---------- */
  .radar-wrap{display:flex; flex-wrap:wrap; gap:14px; align-items:center; justify-content:center;
    border:1px solid var(--cm-border); border-radius:16px; padding:10px 14px; margin:.2rem 0 .8rem;
    background:linear-gradient(160deg, rgba(255,255,255,.035), rgba(255,255,255,.01));}
  .radar{width:300px; max-width:100%; height:auto;}
  .radar-grade{fill:none; stroke:rgba(148,163,184,.18); stroke-width:1;}
  .radar-eixo{stroke:rgba(148,163,184,.14); stroke-width:1;}
  .radar-serie{fill-opacity:.16; stroke-width:2; stroke-linejoin:round;}
  .radar-rotulo{fill:#94A3B8; font-family:var(--cm-font-ui); font-size:9px; font-weight:700;
    letter-spacing:.06em; text-transform:uppercase;}
  .radar-legenda{display:flex; flex-direction:column; gap:6px; font-family:var(--cm-font-ui); font-size:.78rem;}
  .radar-leg{display:flex; align-items:center; gap:7px; color:#CBD5E1;}
  .radar-leg i{width:11px; height:11px; border-radius:3px; display:inline-block;}

  /* ---------- fluxo da corrida (treino → paddock → corrida) ---------- */
  .wizard{display:flex; align-items:center; gap:6px; flex-wrap:wrap;
    border:1px solid var(--cm-border); border-radius:14px; padding:7px 10px; margin:0 0 14px;
    background:linear-gradient(100deg, rgba(255,255,255,.035), rgba(255,255,255,.008));}
  .wz-step{display:flex; align-items:center; gap:7px; padding:4px 10px 4px 6px; border-radius:10px;
    font-family:var(--cm-font-ui); font-size:.78rem; font-weight:700; color:#7C8AA0; white-space:nowrap;}
  .wz-step .wz-n{display:inline-flex; align-items:center; justify-content:center; width:21px; height:21px;
    border-radius:50%; font-size:.7rem; background:rgba(148,163,184,.14); color:#94A3B8;
    border:1px solid rgba(148,163,184,.28); font-variant-numeric:tabular-nums;}
  .wz-step.done{color:#BBF7D0;} .wz-step.done .wz-n{background:rgba(22,101,52,.55);
    border-color:rgba(74,222,128,.55); color:#DCFCE7;}
  .wz-step.agora{color:#F8FAFC; background:rgba(200,16,46,.20); box-shadow:inset 0 0 0 1px rgba(224,36,68,.45);}
  .wz-step.agora .wz-n{background:var(--cm-red); border-color:#FF8FA0; color:#fff;}
  .wz-trilha{flex:1 1 18px; min-width:14px; height:2px; border-radius:2px; background:rgba(148,163,184,.20);}
  .wz-trilha.done{background:rgba(74,222,128,.45);}
  .race-hero.compacto{padding:13px 16px; margin-bottom:10px; border-radius:16px;}
  .race-hero.compacto h1{font-size:1.42rem; margin:.05rem 0 .1rem;}
  .race-hero .migalha{display:flex; flex-wrap:wrap; gap:6px; margin-top:7px;}
  .race-hero .migalha span{font-family:var(--cm-font-ui); font-size:.72rem; font-weight:700;
    letter-spacing:.02em; padding:2px 9px; border-radius:999px; color:#CBD5E1;
    background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.12);}
  .race-hero .migalha span.destaque{background:rgba(200,16,46,.22); border-color:rgba(224,36,68,.45); color:#FFE4E6;}

  /* ---------- calendário (timeline do escritório) ---------- */
  .timeline-wrap{overflow-x:auto; padding:2px 0 6px; margin-bottom:4px;}
  .timeline{display:flex; gap:0; min-width:max-content; align-items:flex-start;}
  .tl-item{display:flex; flex-direction:column; align-items:center; width:82px; position:relative;}
  .tl-item::before{content:""; position:absolute; top:13px; left:0; right:0; height:2px;
    background:rgba(148,163,184,.22); z-index:0;}
  .tl-item:first-child::before{left:50%;} .tl-item:last-child::before{right:50%;}
  .tl-item.done::before{background:rgba(74,222,128,.55);}
  .tl-item.agora::before{background:linear-gradient(90deg, rgba(74,222,128,.55), rgba(224,36,68,.75));}
  .tl-dot{position:relative; z-index:1; width:26px; height:26px; border-radius:50%;
    display:flex; align-items:center; justify-content:center; font-size:.7rem; font-weight:700;
    font-family:var(--cm-font-ui); background:#111827; color:#94A3B8;
    border:1px solid rgba(148,163,184,.35); font-variant-numeric:tabular-nums;}
  .tl-item.done .tl-dot{background:#14532D; border-color:rgba(74,222,128,.7); color:#BBF7D0;}
  .tl-item.agora .tl-dot{background:var(--cm-red); border-color:#FF8FA0; color:#fff;
    box-shadow:0 0 0 4px rgba(200,16,46,.20); animation:pulsa 1.6s ease-in-out infinite;}
  .tl-gp{margin-top:6px; font-size:.62rem; line-height:1.15; text-align:center; color:#94A3B8;
    max-width:78px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}
  .tl-item.agora .tl-gp{color:#F8FAFC; font-weight:700;}
  .tl-item.done .tl-gp{color:#CBD5E1;}
  .tl-sprint{color:#FACC15; margin-left:2px;}

  /* ---------- responsivo (mobile / tablet) ---------- */
  @media (max-width:900px){
    .office-head .time{font-size:1.6rem;}
    .office-meta{gap:6px;}
    .office-meta .om{padding:2px 8px; font-size:.7rem;}
    .race-titulo{font-size:1.1rem;}
    .tbl-viva th,.tbl-viva td{padding:5px 6px; font-size:.8rem;}
    /* colunas menos importantes somem da torre de tempos no celular */
    .tbl-viva th:nth-child(5),.tbl-viva td:nth-child(5),
    .tbl-viva th:nth-child(3),.tbl-viva td:nth-child(3){display:none;}
    .gap-bar{width:38px;}
    .eq-chip{min-width:auto; padding:2px 6px; font-size:.72rem;}
    .voltas-box .n{font-size:1.35rem;}
    .paddock-gp{font-size:.98rem;}
  }
  @media (max-width:760px){
    .stTabs [data-baseweb="tab-list"]{flex-wrap:wrap; gap:4px;}
    .stTabs [data-baseweb="tab"]{padding:6px 10px; font-size:.82rem;}
    .side-next{display:none;}
    .painel h4{font-size:.68rem; letter-spacing:.12em;}
    div[data-testid="stMetricValue"]{font-size:1.25rem !important;}
  }
</style>
"""

# Tema claro: o jogo nasce escuro (padrão da F1 noturna). Este bloco reescreve as
# superfícies e os textos principais quando o jogador escolhe o modo claro na
# barra lateral — a estrutura e as fontes continuam as mesmas.
CSS_CLARO = """
<style>
  :root{
    --cm-bg:#F4F6FA; --cm-panel:#FFFFFF; --cm-text:#0F172A; --cm-muted:#5A6779;
    --cm-border:rgba(15,23,42,.12);
  }
  .stApp{
    background:
      radial-gradient(1100px 520px at 85% -10%, rgba(200,16,46,.08), transparent 60%),
      radial-gradient(900px 480px at -10% 0%, rgba(31,78,121,.10), transparent 55%),
      linear-gradient(180deg,#F7F9FC 0%, #EDF1F7 100%);
    color:#0F172A;
  }
  .stApp h1,.stApp h2{color:#0B1220;} .stApp h3,.stApp h4,.stApp h5{color:#1E293B;}
  .stApp p,.stApp li,.stApp label,.stApp [data-testid="stMarkdownContainer"]{color:#1F2937;}
  .stApp [data-testid="stCaptionContainer"],.stApp [data-testid="stCaptionContainer"] p,
  .stApp caption,.stApp small{color:#5A6779;}
  .stApp a{color:#B3122C !important;}
  .hero{background:linear-gradient(115deg, rgba(200,16,46,.14), rgba(255,255,255,.96) 46%, #FFFFFF);}
  .hero p{color:#334155;} .kicker{color:#B3122C;}
  .chip{background:rgba(15,23,42,.05); border-color:rgba(15,23,42,.14); color:#1F2937;}
  .chip.hot{background:rgba(200,16,46,.10); border-color:rgba(200,16,46,.35); color:#8C0E24;}
  .page-head{border-bottom-color:var(--cm-border);} .page-head p{color:#5A6779;}
  .painel,.news-card,.sessao-card,.race-hero,.previsao-tempo,.box-piloto,.undercut-card,
  .overcut-card,.side-next,.proj-box,.radio-box,.badge-box,.painel-fim{
    background:linear-gradient(165deg,#FFFFFF,#F8FAFC) !important;
    border-color:var(--cm-border) !important; color:#1F2937 !important;
    box-shadow:0 8px 22px rgba(15,23,42,.07) !important;
  }
  .painel h4,.sessao-titulo,.paddock-gp,.race-titulo,.sn-gp{color:#0B1220 !important;}
  div[data-testid="stMetric"]{background:linear-gradient(160deg,#FFFFFF,#F6F8FC);
    border-color:var(--cm-border); box-shadow:0 8px 20px rgba(15,23,42,.06);}
  div[data-testid="stMetricValue"]{color:#0B1220 !important;}
  div[data-testid="stMetric"] label{color:#5A6779 !important;}
  div[data-testid="stExpander"]{background:#FFFFFF; border-color:var(--cm-border);}
  div[data-testid="stDataFrame"],div[data-testid="stDataEditor"]{border-color:var(--cm-border);}
  section[data-testid="stSidebar"]{background:linear-gradient(180deg,#FFFFFF 0%,#EEF2F8 100%);
    border-right:1px solid var(--cm-border);}
  section[data-testid="stSidebar"] .side-brand .b1{color:#0B1220;}
  section[data-testid="stSidebar"] div[role="radiogroup"] label{color:#1F2937;}
  section[data-testid="stSidebar"] div[role="radiogroup"] label:hover{background:rgba(15,23,42,.05);}
  section[data-testid="stSidebar"] div[role="radiogroup"] label[aria-checked="true"],
  section[data-testid="stSidebar"] div[role="radiogroup"] [data-checked="true"]{
    background:linear-gradient(90deg, rgba(200,16,46,.14), rgba(200,16,46,.04));
    border-color:rgba(200,16,46,.30);}
  .side-stats .side-stat{background:#FFFFFF; border-color:var(--cm-border);}
  .side-stat .val{color:#0B1220;} .side-stat .lab{color:#5A6779;}
  .side-next .sn-gp{color:#0B1220;} .side-next .sn-meta{color:#5A6779;}
  .office-meta .om{background:rgba(15,23,42,.05); border-color:rgba(15,23,42,.12); color:#1F2937;}
  .office-head .time{color:#0B1220;}
  .stat-top{color:#334155;} .stat-top strong{color:#0B1220;}
  .stat-track,.gap-bar{background:rgba(15,23,42,.10); border-color:rgba(15,23,42,.10);}
  .gap-txt{color:#5A6779;} .gap-lider{color:#8A6100;}
  .sessao-circuito{color:#475569;} .sessao-linha{color:#334155;}
  .tbl-viva th{background:#EEF2F8; color:#334155;}
  .tbl-viva td{color:#1F2937; border-bottom-color:rgba(15,23,42,.08);}
  .tbl-viva tr.meu td{background:rgba(200,16,46,.10);}
  .tbl-viva tr.fora td{color:#8492A6;}
  .tbl-viva tbody tr:hover td{background:rgba(15,23,42,.04);}
  .tbl-viva td.p1{color:#8A6100;} .tbl-viva td.p2{color:#475569;} .tbl-viva td.p3{color:#8A5A2B;}
  .tbl-viva td.mono{color:#334155;} .feed-race,.race-sub{color:#334155;}
  .sessao-card .sessao-gp{color:#0B1220;}
  .pausa-chip{background:#8C0E24; color:#fff;}
  .tag-vc{background:#B3122C;}
  ::selection{background:rgba(200,16,46,.22); color:#0B1220;}
  ::-webkit-scrollbar-thumb{background:rgba(15,23,42,.22);}
  .pin{filter:none;}
  input,textarea,select,[data-baseweb="select"] div,[data-baseweb="input"] input{
    background:#FFFFFF !important; color:#0F172A !important; border-color:rgba(15,23,42,.16) !important;}
  [data-baseweb="tab-list"]{border-bottom-color:var(--cm-border);}
  .stTabs [aria-selected="true"]{background:rgba(200,16,46,.10); color:#8C0E24 !important;}
  .stButton > button{background:#FFFFFF; color:#1F2937; border:1px solid rgba(15,23,42,.16);}
  .stButton > button[kind="primary"],.stButton > button[data-testid="stBaseButton-primary"]{
    background:linear-gradient(135deg,#D61437,#93021C); color:#fff; border-color:transparent;}
  hr{border-color:var(--cm-border);}
  .wizard{background:linear-gradient(100deg,#FFFFFF,#F7F9FC); border-color:var(--cm-border);}
  .wz-step{color:#5A6779;} .wz-step.agora{color:#0B1220; background:rgba(200,16,46,.10);}
  .wz-step.done{color:#14532D;}
  .race-hero .migalha span{color:#334155; background:rgba(15,23,42,.05); border-color:rgba(15,23,42,.12);}
  .race-hero .migalha span.destaque{background:rgba(200,16,46,.12); border-color:rgba(200,16,46,.35); color:#8C0E24;}
  .bandeira-vermelha{color:#7F1023; background:linear-gradient(100deg, rgba(255,205,214,.95), rgba(255,235,238,.85));
    border-color:rgba(190,18,60,.35);}
  .radar-wrap{background:linear-gradient(165deg,#FFFFFF,#F7F9FC); border-color:var(--cm-border);}
  .radar-grade{stroke:rgba(15,23,42,.14);} .radar-eixo{stroke:rgba(15,23,42,.10);}
  .radar-rotulo{fill:#5A6779;} .radar-leg{color:#334155;}
  .tl-item::before{background:rgba(15,23,42,.14);}
  .tl-dot{background:#FFFFFF; color:#5A6779; border-color:rgba(15,23,42,.2);}
  .tl-item.done .tl-dot{background:#DCFCE7; border-color:#16A34A; color:#14532D;}
  .tl-item.done .tl-gp{color:#334155;} .tl-gp{color:#5A6779;}
  .tl-item.agora .tl-gp{color:#8C0E24;}
</style>
"""


def aplicar(claro: bool = False) -> None:
    """Injeta o CSS do jogo na página (idempotente: o Streamlit só re-renderiza).

    `claro=True` adiciona o bloco do tema claro depois do CSS base, então as
    regras de cor do modo claro vencem por ordem de cascata.
    """
    st.markdown(CSS + (CSS_CLARO if claro else ""), unsafe_allow_html=True)
