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
(`--cm-font-brand`, `--cm-font-ui`, `--cm-font-text`, `--cm-font-mono`) no `<style>` do `app.py`.

## ▶️ Como rodar

```bash
git clone https://github.com/denisvick-dev/cockpit-manager.git
cd cockpit-manager
pip install -r requirements.txt
streamlit run app.py
```

Abre em `http://localhost:8501`. Para publicar de graça, suba a pasta no
[Streamlit Community Cloud](https://streamlit.io/cloud) apontando para `app.py`.

## 📁 Estrutura

| Arquivo | Função |
|---|---|
| `app.py` | Interface Streamlit (telas: Escritório, Corrida, Carro, Pilotos, Motores, Finanças, Campeonato, Hall da Fama…) |
| `simulacao.py` | Motor do jogo: classificação, corrida, estratégia, desenvolvimento, finanças, mercado, evolução e virada de temporada |
| `dados2026.py` | A DB F1 2026: 11 equipes, 49 pilotos, 10 motores, calendário de 24 etapas |
| `dbs.py` | Sistema de DBs: **F1 2026**, **F1 Academy** (18 Tatuus idênticos, grade real de 2026), **F1 Legends** (Schumacher, Senna, Fangio… nos circuitos clássicos), **F1 Históricas** (8 temporadas âncora: 1950·1960·…·2020 com grids, motores e calendários reais da época), **Fórmula Indy** (25 carros, 18 etapas, Indy 500), **Indy Legends** (Foyt, Unser, Mario Andretti nos ovais históricos), **Stock Car** (34 SUVs V8, sprint+principal), **DTM** (GT3, 2 corridas/etapa) + validação de DBs personalizadas |
| `editor_db.py` | Editor de DBs na tela inicial: edite equipes/pilotos/calendário/fornecedores, valide, baixe/compartilhe o `.json` e jogue na hora |
| `bandeiras.py` + `assets/bandeiras/` | Bandeiras dos países como **imagens PNG locais** (o Windows não renderiza emoji de bandeira!) — 45 países padronizados em 96×72 px, fonte: flagcdn.com / flag-icons (domínio público) |
| `tools/padronizar_bandeiras.py` | Regenera/atualiza as bandeiras: baixa do flagcdn e encaixa todas no mesmo tamanho, sem distorcer (`python tools/padronizar_bandeiras.py`) |
| `minhas_dbs/` | (criada ao salvar) Suas DBs personalizadas em `.json` viram opções permanentes na lista de DBs |
| `.streamlit/config.toml` | Tema escuro profissional (design system do jogo) |
| `requirements.txt` | `streamlit` + `pandas` |

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
- **Estratégia de corrida**: paradas e ritmo escolhidos **antes** da corrida + **Paddock** fiel ao
  original (pneus com durabilidade exata, posição no grid, **Perguntar em cada pit stop** e
  **Confirmar** para liberar a largada) — e **durante a prova** o ritmo ao vivo e o **Pit stop!** em
  diálogo (Novos pneus, volta atual, Cancelar/Confirmar), com clima (seco/molhado)
- **Janela de Pit Stop a cada parada**: na volta planejada (ou a qualquer momento pelo **Pit stop!**)
  abre a janela do muro — *"trocar de pneu?"* com os **novos pneus** (durabilidade de cada composto)
  e o **ritmo do próximo stint** (Conservar/Normal/Atacar). A prova **congela** enquanto a janela está
  aberta: **Trocar pneu e voltar ✓** cumpre o box naquela volta e **Continuar na pista ✕** dispensa a
  parada (o piloto segue com o pneu velho). Se o chefe deixar a janela passar, ela é dada como perdida
- **Tela de treino classificatório** (como no original): relógio de 60 min com barra, clima, tabela
  de Pos./Nome/Equipe/**Melhor tempo** se enchendo aos poucos e o grid final fiel ao motor;
  botões **Iniciar treino** e **Ir para corrida!**
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
- **Tipografia em todo o projeto** — três famílias auto-hospedadas em `static/fonts/` e aplicadas por
  componente (tokens `--cm-font-*` no `app.py` + `[[theme.fontFaces]]` no `.streamlit/config.toml`):

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
- **Fins de semana Sprint**, gráficos de evolução do campeonato e do caixa, save/load em JSON.

## 💾 Salvando

O jogo vive na sessão do Streamlit. Use **💾 Salvar / Carregar** (ou o botão na barra lateral)
para baixar o save em `.json` e continuar depois na tela inicial.

## ⚖️ Créditos e aviso

Projeto gratuito feito por fã, sem código ou assets do jogo original e sem afiliação com
Fórmula 1, FIA, Cartola Games ou com o blog Cockpit Manager - Brasil. Nomes de equipes e
pilotos são usados apenas como referência factual à temporada 2026, no espírito das DBs
da comunidade que mantêm o CM14 vivo há mais de uma década. ❤️
