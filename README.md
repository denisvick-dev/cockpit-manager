# 🏎️ Cockpit Manager — Edição Streamlit (DB F1 2026)

Um remake em **Python + Streamlit** do clássico brasileiro **Cockpit Manager '14**
(Cartola Games, 2014) — o "Brasfoot da Fórmula 1" — usando como base a
[**DB F1 2026 v1.0 by Jonathan Daniel**](http://cockpitmanager.blogspot.com/2026/05/db-f1-2026-v10-by-jonathan-daniel.html)
do blog *Cockpit Manager - Brasil*.

Comande equipes em **8 DBs** — F1 2026, **F1 Academy**, **F1 Legends**, **F1 Históricas (1950→2020)**,
Fórmula Indy, **Indy Legends**,
Stock Car e DTM — (ou crie a sua),
desenvolva o carro, negocie fornecedores e patrocinadores, contrate pilotos, acerte a estratégia
de pneus e paradas e jogue **temporadas sem limite**: pilotos envelhecem, evoluem, se aposentam,
jovens sobem da base e lendas entram para o Hall da Fama. Você ainda pode **criar e compartilhar
suas próprias DBs** e escolher **quantos pilotos terá o grid (a partir de 22)**.

Visual com três fontes locais aplicadas **no projeto inteiro**: **Formula1 Display** (a fonte da F1)
nos títulos, marcas e indicadores de corrida; **Manrope** na interface (botões, campos, abas, sidebar,
tabelas ao vivo e métricas); **Inter** na leitura (parágrafos, manuais e dataframes). **IBM Plex Mono**
fica nos blocos de código. Os arquivos e as licenças OFL ficam em `static/fonts/` (incluindo
`Manrope-OFL.txt`); o tema é configurado em `.streamlit/config.toml` e os tokens de fonte
(`--cm-font-brand`, `--cm-font-ui`, `--cm-font-text`, `--cm-font-mono`) no design system em `ui/tema.py`.

## ▶️ Como rodar

```bash
git clone https://github.com/denisvick-dev/cockpit-manager.git
cd cockpit-manager
pip install -r requirements.txt
streamlit run app.py
```

Abre em `http://localhost:8501`. Para publicar de graça, suba a pasta no
[Streamlit Community Cloud](https://streamlit.io/cloud) apontando para `app.py`.

### 🧪 Testes e lint

```bash
pip install -r requirements.txt -r requirements-dev.txt
ruff check .      # lint (config em pyproject.toml)
python -m pytest --cov  # 73 testes + cobertura (piso de 75%)
```

O **GitHub Actions** (`.github/workflows/ci.yml`) roda ruff + pytest em Python 3.12/3.13
e um job de *smoke* que sobe o Streamlit e checa `/_stcore/health` (as dependências fixadas
pedem **Python 3.12+**).

## 📁 Estrutura

| Arquivo | Função |
|---|---|
| `app.py` | Ponto de entrada: estado da sessão, barra lateral e roteamento entre as páginas (~250 linhas) |
| `paginas/` | Uma página por arquivo: `inicio`, `escritorio`, `corrida`, `carro`, `pilotos`, `motores`, `financas`, `campeonato`, `hall`, `save`, `ajuda` + `comum.py` com os componentes compartilhados |
| `armazenamento.py` | Saves em **slots** (`saves/`), **auto-save** a cada etapa, **migração** de saves antigos (schema versionado) e exportação CSV |
| `ui/tema.py` | **Design system**: todo o CSS do jogo (tokens `--cm-font-*`, painéis, tabelas ao vivo, cartões de undercut/overcut, barra lateral, responsivo e acessibilidade) + `aplicar()` chamado uma vez no início do app |
| `simulacao.py` | Motor do jogo: classificação, corrida, estratégia, desenvolvimento, finanças, mercado, evolução e virada de temporada |
| `dados2026.py` | A DB F1 2026: 11 equipes, 49 pilotos, 10 motores, calendário de 24 etapas |
| `dbs.py` | Sistema de DBs: **F1 2026** (corrida única por fim de semana, sem Sprint), **F1 Academy** (18 Tatuus idênticos, grade real de 2026), **F1 Legends** (Schumacher, Senna, Fangio… nos circuitos clássicos), **F1 Históricas** (8 temporadas âncora: 1950·1960·…·2020 com grids, motores e calendários reais da época), **Fórmula Indy** (25 carros, 18 etapas, Indy 500), **Indy Legends** (Foyt, Unser, Mario Andretti nos ovais históricos), **Stock Car** (34 SUVs V8, sprint+principal), **DTM** (GT3, 2 corridas/etapa) + validação de DBs personalizadas |
| `editor_db.py` | Editor de DBs na tela inicial: edite equipes/pilotos/calendário/fornecedores, valide, baixe/compartilhe o `.json` e jogue na hora |
| `bandeiras.py` + `assets/bandeiras/` | Bandeiras dos países como **imagens PNG locais** (o Windows não renderiza emoji de bandeira!) — 45 países padronizados em 96×72 px, fonte: flagcdn.com / flag-icons (domínio público) |
| `tools/padronizar_bandeiras.py` | Regenera/atualiza as bandeiras: baixa do flagcdn e encaixa todas no mesmo tamanho, sem distorcer (`python tools/padronizar_bandeiras.py`) |
| `saves/` | (criada ao salvar) Slots e o `_autosave.json` da sua carreira — fora do Git |
| `minhas_dbs/` | (criada ao salvar) Suas DBs personalizadas em `.json` viram opções permanentes na lista de DBs |
| `.streamlit/config.toml` | Tema escuro profissional (design system do jogo) |
| `tests/` | Suíte **pytest** (73 testes): determinismo e pontuação do motor, replay/pits (janela, automático, recusa, clima, undercut/overcut), tema/save em JSON e smoke test de todas as telas com `AppTest` |
| `requirements.txt` / `requirements-dev.txt` | `streamlit` + `pandas` / `pytest` + `ruff` |
| `pyproject.toml` | Configuração do **ruff** (lint) e do **pytest** |
| `.github/workflows/ci.yml` | CI: lint + testes com **cobertura (piso de 75%)** em Python 3.12/3.13 + smoke do servidor Streamlit |

## 🆕 Últimas melhorias (v3)

- **Fluxo guiado no fim de semana** — a tela de corrida virou uma sequência de passos (**Treino → Paddock →
  Corrida → Resultado**): cada etapa mostra só o que importa, o cabeçalho virou uma faixa compacta, os
  detalhes da etapa ficam num expander e a preparação sai da tela quando a transmissão começa.

- **Safety Car, Virtual Safety Car e bandeira vermelha** — a prova neutralizada junta o pelotão (as
  diferenças derretem na torre), o box fica mais barato e, na **bandeira vermelha**, a corrida para de
  verdade até você clicar em **🟥 Relargada**.
- **Volta mais rápida vale +1 ponto**, com registro no save e destaque no resultado.
- **Gráfico de stints e degradação** no pós-corrida (tempo de volta × volta, com as quedas das paradas).
- **Negociação de contratos em até 3 rodadas**, com **contraproposta** de salário/anos.
- **Comparador de carros** (radar SVG dos 6 eixos seu time × rival, sem dependências novas).
- **Linha do tempo do calendário** no Escritório (concluídas, próxima e as etapas com duas corridas).
- **⏩ Simular etapas em lote** para quem quer temporadas longas sem transmissão.
- **Exportação CSV** das tabelas (Excel pt-BR: `;` + BOM) no Campeonato, Finanças, Pilotos e resultado.
- **Tema claro** (☀️ na barra lateral) usando os mesmos tokens do design system.
- **Save em slots + auto-save a cada etapa + migração automática** de saves antigos (schema `versao`).
- **`app.py` dividido em `paginas/`** (uma por tela) e **cobertura mínima de 75%** no CI.

## 🎮 O que foi recriado do original

- **Tela-resumo ("Escritório")** no layout do original: cabeçalho com **nome do gerente**
  (ex.: "Vick 2026, 1ª etapa") + equipe em destaque, e os painéis **Carro** (6 eixos em %:
  aerodinâmica, câmbio, freio, elétrico, direção e confiabilidade), **Contratos** (motor),
  **Pilotos** (1º/2º/…/testes), **Finanças** (receitas, despesas, balanço do ano e caixa),
  **Notícias** com contador de novas e **Próxima corrida** com o botão **Continuar**
- **Investimento por corrida** no carro + comparação de nível com as rivais (menu *Campeonato → Equipes* do CM14)
- **Contratos de motor** para a próxima temporada — inclusive o lendário **motor FIA compulsório de 50%**
  de potência para quem ficar sem caixa
- **Pilotos com os 7 atributos clássicos** (Velocidade, Chuva, Concentração, Largada, Ultrapassagem,
  Acerto de carro, Físico), salários por corrida, contratos de 1º/2º piloto e piloto de testes,
  tudo negociado **para a temporada seguinte** — inclusive **pré-contrato com sinal** (fecha na
  hora, sem chance de recusa, como no original)
- **Estratégia de corrida**: número de paradas sugerido pela pista (`paradas_ideais`) e **Paddock** fiel ao
  original (pneus com durabilidade exata, posição no grid, **Perguntar em cada pit stop** e
  **Confirmar** para liberar a largada) — e **durante a prova** o ritmo ao vivo e o **Pit stop!** em
  diálogo (Novos pneus, volta atual, Cancelar/Confirmar), com clima (seco/molhado)
- **Janela de Pit Stop a cada parada**: na volta planejada (ou a qualquer momento pelo **Pit stop!**)
  abre a janela do muro — *"trocar de pneu?"* com os **novos pneus** (durabilidade de cada composto)
  e o **ritmo do próximo stint** (Conservar/Normal/Atacar). A prova **congela** enquanto a janela está
  aberta: **Trocar pneu e voltar ✓** cumpre o box naquela volta e **Continuar na pista ✕** dispensa a
  parada (o piloto segue com o pneu velho). Se o pneu chegar a 0% antes de uma parada planejada, a
  janela também abre automaticamente. Se o chefe deixar a janela passar, ela é dada como perdida
- **Tela de treino classificatório** (como no original): relógio de 60 min com barra, clima, tabela
  de Pos./Nome/Equipe/**Melhor tempo** se enchendo aos poucos e o grid final fiel ao motor;
  botões **Iniciar treino** e **Ir para corrida!**
- **Clima ao vivo com previsão (e consequência real)**: cada GP sorteia um **plano de clima** (largada
  seca/molhada e, às vezes, virada no meio da prova). A previsão aparece antes da largada ("a chuva chega por
  volta de X"), o chip de **pista** acompanha a condição real, o feed avisa quando o tempo vira e o composto
  errado é destacado no painel do piloto — e o diálogo do Pit Stop já abre com os pneus certos para aquela
  volta. **Isso agora muda o resultado do motor** (`sim.ajuste_clima`): talento de chuva pesa conforme a
  fração molhada, o composto de largada certo para a condição inicial vale posição e apostar em menos paradas
  numa prova que vira cobra caro. Quem previu o tempo errado **perde a corrida no escritório, não na tela**.
- **Transmissão controlável**: **Pausar/Retomar** (congela a prova), **1× / 2× / 4×** de velocidade e
  **atalhos de teclado** (espaço, 1/2/4, P/O para o box dos dois pilotos) via `static/atalhos.html`.
- **Torre de tempos da transmissão**: faixa na **cor da equipe** em cada linha, **setas ▲▼** de posições
  ganhas/perdidas em relação ao grid, composto como **bolinha colorida** (S/M/H/I/W), **barra de diferença**
  para o líder, cabeçalho fixo, destaque vermelho com a tag **VC** para os seus carros e badge pulsante de
  **BOX** — no treino e na corrida.
- **Overcut**: quando um rival **à frente** vai ao box, o rádio avisa e o botão **🔥 Ficar e atacar** mantém o
  piloto na pista com ritmo `Atacar` — ele recupera a posição na saída do rival, com o ganho aparecendo na torre
  de tempos. Se você parar dentro da janela, o overcut é abortado (e o feed diz isso).
- **Undercut com resposta imediata**: quando um rival que estava até 3 posições atrás vai ao box, o rádio
  avisa ("⚔️ Alonso (P10) foi ao box — undercut sobre Norris (P7)") e aparece o botão **⚡ Responder agora**,
  que abre o box na hora (a prova congela enquanto você decide).
- **Box com projeção de posição**: o diálogo do Pit Stop mostra **"P9 agora → P11 saindo do box (perde 2)"**,
  para você pesar a parada antes de confirmar.
- **Atalho de transmissão**: **⏩ Próxima parada (volta N)** salta direto para a próxima parada planejada,
  além de **⏸ Pausar/Retomar**, **1×/2×/4×** e **⏭️ Concluir corrida agora**.
- **Escritório com o campeonato à vista**: chips de **posição no construtores**, pontos, vitórias e caixa no
  cabeçalho, e o painel da próxima corrida com **clima sorteado**, **previsão do tempo** e a estratégia típica.
- **Tela de corrida ao vivo**: título do GP com "Etapa X de N", contador de **Voltas k / N**,
  tabela posição a posição (últ. volta, dif. ant., dif 1º), painel dos seus dois pilotos com
  paradas, pneu, **barra de vida**, **próxima parada** e **Pit stop!** manual (ou a janela de box
  na volta planejada), feed de quebras/boxes e botão **Dar largada!** — o resultado final continua
  sendo o do motor
- **Patrocinadores** com bônus por ponto/pódio/vitória e premiação de construtores
- **Hall da Fama** (Senna, Schumacher, Lauda, Hunt…) com indução dos seus pilotos
- **10 conquistas**, como no original
- **Importância do carro = 60%** (padrão das DBs da comunidade, ajustável na tela inicial)
- **DB 2026 fiel ao post**: Audi/Ferrari/Mercedes/Red Bull com motor próprio, Ford como fornecedora
  independente, Chevrolet rumo ao motor da Cadillac, 1 reserva por equipe, calendário original de
  24 etapas (Bahrein e Arábia Saudita podem ser removidas na criação do jogo), Bortoleto 🇧🇷 na Audi,
  Drugovich e Rafael Câmara no mercado de jovens

## 🆕 Novidades desta versão

- **Visual profissional**: nova identidade do jogo (hero com marca CM, barra lateral com cartão da
  equipe e progresso da temporada, cartões, métricas e tabelas redesenhados) e **bandeiras com
  tamanho uniforme** em todas as telas — tabelas, títulos e cartões — sem distorção.
- **Editor de DBs** (aba *Criar / editar DB*): crie categorias do zero ou modifique as existentes —
  nomes, atributos dos pilotos, calendário, pontuação… — baixe o `.json`, compartilhe com a
  comunidade e carregue DBs de outros criadores pelo upload.
- **Fórmula Indy, Stock Car e DTM** como DBs completas, cada uma com equipes, pilotos, calendário,
  fornecedores, Hall da Fama e sistema de pontuação da categoria real.
- **Três DBs novas**: **F1 Academy 2026** (grade real de 18 carros com Prema, ART, Campos, MP, Rodin e
  Hitech, regra das duas temporadas e jovens gerados só com nomes da base feminina), **F1 Legends**
  (o time dos sonhos em Monza com banking, Nordschleife, Spa original e Reims, com motores de época —
  DFV, Climax, Repco, Offy) e **Indy Legends** (as lendas da IndyCar nas 500 Milhas e nos ovais
  clássicos: Milwaukee, Pocono, Michigan e Ontario).
- **F1 Históricas**: 8 temporadas âncora — **1950, 1960, 1970, 1980, 1990, 2000, 2010 e 2020** —
  com grids, equipes, motores, Hall da Fama e calendários reais de cada época (de Farina na Alfa a
  Hamilton na Mercedes) e **a pontuação daquele ano** (8-6-4-3-2 nos anos 50/60 → 25-18-15… moderna).
  Escolha o ano no seletor 📅 da tela inicial.
- **Pré-contrato** no mercado de pilotos: pague um **sinal de 3 corridas do salário** e feche o
  acordo na hora — sem chance de recusa. Cancelar não devolve o sinal (e um piloto que se aposentar
  antes da virada deixa o acordo no vazio, com aviso no feed).
- **Polimento de interação** — cartões com hover suave, botões com leve elevação, anel de foco visível,
  barras de rolagem finas e respeito a `prefers-reduced-motion` (acessibilidade). O CSS inteiro vive em
  `ui/tema.py` e tem **layout responsivo**: abaixo de 900 px a torre de tempos esconde as colunas menos
  importantes e as barras de gap encurtam; abaixo de 760 px as abas quebram linha e as métricas reduzem.
- **Tipografia em todo o projeto** — três famílias auto-hospedadas em `static/fonts/` e aplicadas por
  componente (tokens `--cm-font-*` em `ui/tema.py` + `[[theme.fontFaces]]` no `.streamlit/config.toml`):

  | Fonte | Onde aparece |
  |---|---|
  | **Formula1 Display** | H1–H6, kickers, marcas/logo, cabeçalhos de corrida/treino, placar de voltas, título do Pit Stop, Paddock, métricas e valores de destaque |
  | **Manrope** | Interface inteira: botões, campos, selects, radios, checkboxes, sliders, abas, sidebar, tabelas ao vivo, chips de equipe, feed e rótulos — além da `font` padrão do tema (dataframes/canvas) |
  | **Inter** | Leitura: parágrafos do markdown, manuais, listas, tabelas markdown e dataframes |
  | **IBM Plex Mono** | Blocos de código e campos `code` |

  Números usam `font-variant-numeric: tabular-nums` (tabelas, voltas, métricas) e os ícones mantêm a
  fonte Material Symbols. Manrope está sob licença OFL (`static/fonts/Manrope-OFL.txt`).
- **Tamanho do grid configurável**: slider na criação do jogo, **a partir de 22 pilotos** — equipes
  podem inscrever 3º e 4º carros (grid da F1 vai até 44!), e o mercado mantém o grid cheio
  virada após virada.

## ✨ Melhorias sobre limitações conhecidas do CM14

- **Auge em platô**: no original, o "auge" era o ponto máximo e o declínio começava no dia seguinte.
  Aqui o piloto evolui até o auge, permanece anos no topo e só depois declina aos poucos.
- **Perfil "rápido e destruidor"**: Velocidade (volta rápida) e Concentração (não bater) atuam
  separadamente na simulação, permitindo equilibrar pilotos velozes mas erráticos.
- **Gráficos de evolução do campeonato e do caixa**, save/load em JSON e saves em slots com auto-save.
  A **F1 agora tem corrida única por fim de semana** (sem Sprint); Stock Car, DTM e F1 Academy mantêm as duas corridas.

## 💾 Salvando

O jogo vive na sessão do Streamlit. Use **💾 Salvar / Carregar** (ou o botão na barra lateral)
para baixar o save em `.json` e continuar depois na tela inicial.

## ⚖️ Créditos e aviso

Projeto gratuito feito por fã, sem código ou assets do jogo original e sem afiliação com
Fórmula 1, FIA, Cartola Games ou com o blog Cockpit Manager - Brasil. Nomes de equipes e
pilotos são usados apenas como referência factual à temporada 2026, no espírito das DBs
da comunidade que mantêm o CM14 vivo há mais de uma década. ❤️
