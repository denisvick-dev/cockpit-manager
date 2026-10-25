# -*- coding: utf-8 -*-
"""Como Jogar: manual rápido e atalhos."""

import streamlit as st


from .comum import titulo_pagina

def pagina_ajuda():
    titulo_pagina("Manual", "Como Jogar", "Tudo o que um chefe de equipe precisa saber antes da primeira largada.")
    st.markdown("""
Comande uma equipe de F1 temporada após temporada, **sem limite de anos** — exatamente como o original de 2014.

### 🔁 O ciclo do jogo
1. **Escritório** — confira caixa, carro, pilotos, notícias, a **linha do tempo do calendário** e a próxima
   corrida. Sem tempo para transmitir? Use **⏩ Simular etapas em lote** para rodar várias etapas de uma vez.
   Clique em **Continuar** para a próxima prova.
2. **Corrida** — a tela é **um passo por vez** (a trilha no topo mostra onde você está):
   **1 Treino** → **2 Paddock** → **3 Corrida** → **4 Resultado**. Na F1 é **uma corrida por fim de semana**
   (sem Sprint): treino classificatório, **Paddock** (pneus, grid e **Perguntar em cada pit stop**) e, **durante
   a corrida**, ritmo no rádio ao vivo e a janela do **Pit Stop** a cada parada (trocar o pneu? qual ritmo?).
   Dá para voltar ao treino pelo **← Revisar treino** sem perder a grade — e nada da preparação fica na tela
   durante a transmissão. Nas DBs com **duas corridas por etapa**
   (Stock Car, DTM e F1 Academy) a primeira delas abre o fim de semana, com o próprio **pneu de largada**.
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
- **Safety Car, VSC e bandeira vermelha**: quando a prova é neutralizada o pelotão se junta na torre de
  tempos (as diferenças derretem) e o box fica mais barato. Na **bandeira vermelha** (só com pista
  alagada) a corrida **para de verdade** até você clicar em **🟥 Relargada**.
- **Volta mais rápida**: vale **+1 ponto** para quem marcar — aparece na classificação final com ⚡ e entra
  na conta do campeonato.
- **Pós-corrida**: além do resultado, você vê os **stints e a degradação** dos seus pilotos (tempo de volta
  volta a volta, com as quedas das paradas) e pode **exportar o resultado em CSV**.
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
A negociação é **em rodadas**: se a oferta não convencer, o estafe responde com uma **contraproposta**
(salário e anos pedidos). Você pode aceitar, cobrir com menos ou encerrar a conversa — e ele só volta a
negociar na próxima temporada depois de duas recusas.

### 💾 Save, auto-save e temas
- **Auto-save**: ao fim de cada etapa o jogo grava `saves/_autosave.json` sozinho — fechar o navegador não
  custa a temporada.
- **Slots**: em *Salvar / Carregar* você salva com nome, carrega e apaga slots, além de baixar o `.json`.
  Saves antigos são **migrados automaticamente** ao abrir.
- **Tema claro**: o interruptor ☀️ na barra lateral troca o visual noturno pelo claro.
- **CSV**: as tabelas principais têm botão de exportar (Excel pt-BR, com `;`).

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
