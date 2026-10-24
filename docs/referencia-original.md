# Referência — Cockpit Manager '14 (jogo original)

Base de fidelidade do remake, extraída do vídeo
**[COCKPIT MANAGER - O BRASFOOT DA FÓRMULA 1](https://www.youtube.com/watch?v=sY3uxg0vvY0)**
(Rádio Brasfoot, 04/01/2023 — canais Rádio Brasfoot e Cockpit Manager são do mesmo dono).

O original: manager de F1 para Windows, lançado em **11/04/2014**, desenvolvido pela
**Cartola Games** (programador: Vitor Mendes) e distribuído pela SiliconAction.

## O que o original mostra no vídeo

### Novo jogo
- Escolha de **temporada de 1950 até a mais recente** (2021 no vídeo); temporadas futuras aparecem "escondidas".
- Categorias além da F1: **Fórmula Indy, Stock Car** e outros.
- Escolher uma equipe da temporada (nao vídeo: grid 2021) **ou criar uma equipe nova** no lugar de outra —
  nome, país/estado sede e **cores do carro** (ex.: laranja/branco); a equipe removida é re-editável.
- Tela inicial já com save em andamento.

### Arquivo e ritmo
- Salvar com nome de arquivo (ex.: `s14`); **autosave**: nunca / a cada corrida / a cada 3 corridas / a cada temporada.
- **Velocidade da corrida** ajustável (recomendação do vídeo: bem devagar).

### Gestão
- **Notícias**: boas-vindas, aposentadoria de pilotos, contrato de piloto, contrato de fornecedor,
  contrato de patrocínio, renovações e assinaturas.
- **Investimentos do carro** em 6 eixos: aerodinâmica, caixa de câmbio, freio, sistema elétrico,
  direção e confiabilidade — com risco de **falência** se gastar sem controle.
- **Motor**: trocar de motor e escolher já o motor da próxima temporada (no vídeo, Ferrari custa ~R$ 280 mil);
  motor próprio herda a DB.
- **Mercado de pilotos**: 1º/2º/piloto de teste, renovar, **pré-contrato**, tentar pilotos famosos
  (difícil — depende da **reputação** da equipe e do salário), pilotos intermediários para promover,
  pilotos "???" sem contrato que dá pra negociar, jovens/juniors, **proposta salarial por corrida**
  (rejeita/aceita; pode aumentar na próxima rodada).
- **Finanças**: financeiro (entradas/saídas), **banco com empréstimo e juros semanais**,
  patrocinadores que chegam de acordo com o seu nível.
- **Campeonatos**: classificação de pilotos e mundial de construtores, com pontuação real da F1 (25/18/15…).

### Corrida
- **Treino** antes da largada (quem treina melhor larga na frente).
- **Paddock** e demais telas da sessão.
- **3 pneus**: duro (~33 voltas), médio (~24), macio (~16) — macio tem a melhor rentabilidade;
  esquema de paradas **automático ou manual**.
- Grid de largada com nº de voltas, nomes dos pilotos, paradas e **pit stops**;
  durante a corrida: **pneus dos adversários** e pit stops de cada um, **quebras de carro**,
  linha do tempo de voltas. (O áudio do vídeo é edição — o jogo não tem som.)

### Pós-corrida e honras
- Classificação do campeonato após cada corrida.
- **Honras**: campeões da temporada, **Hall da Fama** e **Conquistas**.
- Tela "Sobre" com o criador.

## Mapeamento no remake (Streamlit)

| Original ('14) | No remake | Onde |
|---|---|---|
| Novo jogo + equipe criada (nome/país/cor) | ✅ | `tela_inicial()` |
| Temporadas 1950→atual | ✅ — 8 temporadas históricas (1950·1960·1970·1980·1990·2000·2010·2020) + as DBs atuais | `dbs.db_f1_historica`, seletor em `tela_inicial()` |
| Salvar/carregar arquivo, autosave | ✅ (salvo no navegador + download `.json`/zip) | `pagina_save()` |
| Velocidade da corrida | ✅ corrida ao vivo em replay volta a volta (~24 s por prova): posições, diferenças, boxes e feed de eventos — com largada, pneus e ritmo definidos antes, e o resultado final fiel ao motor | `pagina_corrida()`, `sim.montar_replay`, `sim.linhas_replay` |
| Notícias de contratos/aposentadoria | ✅ feed de notícias | `sim.noticia` |
| Investimentos (6 eixos, falência) | ✅ aero/caixa/freio/elétrico/direção/confiabilidade + alerta de caixa | `pagina_carro()` |
| Trocar motor + escolher motor do ano que vem | ✅ | `pagina_motores()` |
| Mercado (papéis, salário/corrida, famosos, teste→titular) | ✅ (1º/2º/3º/4º/teste/livre, propostas, reputação no prestígio) | `pagina_pilotos()` |
| Pré-contrato | ✅ — sinal de 3 corridas do salário fecha o acordo na hora (não reembolsável) | `sim.pre_contratar_piloto`, `pagina_pilotos()` |
| Banco (empréstimo + juros semanais) | ❌ fora de escopo nesta rodada (não priorizado) | — |
| Patrocínios por nível | ✅ (fixo/corrida + bônus/ponto) | `pagina_financas()` |
| Financeiro entradas/saídas | ✅ caixa, salários, bônus | `pagina_escritorio()`, `pagina_financas()` |
| Pontuação F1 real (25/18/15) | ✅ (cada DB usa o sistema da sua categoria) | `dbs.py`/`simulacao.py` |
| Treino → grid | ✅ tela de treino classificatório: relógio de 60 min, clima, tempos progressivos por piloto e grid final fiel ao motor (sprint quando a DB define) | `pagina_corrida()`, `sim.sessao_treino` |
| 3 pneus com durabilidade + paradas auto/manual | ✅ macio/médio/duro, paradas e ritmo antes da corrida + botão **Pit stop!** ao vivo no replay (ou parada automática na volta planejada), com barra de vida do pneu | `pagina_corrida()`, `sim.vida_pneu` |
| Pneus dos adversários, pit stops, quebras, timeline de voltas | ✅ eventos ao vivo + resumo | `simular_corrida`, `pagina_corrida()` |
| Honras: campeões, Hall da Fama, Conquistas | ✅ | `pagina_hall()` |
| Hall da Fama da própria categoria | ✅ por DB | `dbs.py` |

## Pendências sugeridas (a partir do vídeo)

1. **Banco**: empréstimo com juros semanais na tela de finanças (risco real de falência, como no original).
   — **não priorizado** nesta rodada.
2. **Pré-contrato** no mercado de pilotos. — ✅ **implementado**: na aba *Negociar*, escolha entre proposta
   comum (grátis, com chance de recusa) e **pré-contrato**, que cobra um sinal de 3 corridas do salário
   (mín. US$ 300 mil) e fecha o acordo na hora. Cancelamento não devolve o sinal; se o piloto se aposentar
   antes da virada, o acordo cai no vazio (com aviso no feed). Fonte: `sim.pre_contratar_piloto`.
3. **Temporadas históricas** (1950→…) como no original. — ✅ **implementadas**: 8 temporadas âncora
   (**1950, 1960, 1970, 1980, 1990, 2000, 2010, 2020**) na DB "F1 Históricas", com grids, equipes,
   motores, calendários reais da época e a pontuação daquele ano (8-6-4-3-2 nos anos 50/60 até os
   25-18-15… modernos). Escolha o ano no seletor **📅 Temporada histórica** da tela inicial.
   Fonte: `dbs.db_f1_historica` + `_hist_19XX`.
