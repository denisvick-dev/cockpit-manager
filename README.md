# 🏎️ Cockpit Manager — Edição Streamlit (DB F1 2026)

Um remake em **Python + Streamlit** do clássico brasileiro **Cockpit Manager '14**
(Cartola Games, 2014) — o "Brasfoot da Fórmula 1" — usando como base a
[**DB F1 2026 v1.0 by Jonathan Daniel**](http://cockpitmanager.blogspot.com/2026/05/db-f1-2026-v10-by-jonathan-daniel.html)
do blog *Cockpit Manager - Brasil*.

Comande uma das 11 equipes de 2026 (ou crie a sua, como 12ª do grid), desenvolva o carro,
negocie motores e patrocinadores, contrate pilotos, acerte a estratégia de pneus e paradas
e jogue **temporadas sem limite**: pilotos envelhecem, evoluem, se aposentam, jovens da
F2/F3 sobem e lendas entram para o Hall da Fama.

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
| `dados2026.py` | A DB 2026: 11 equipes, 49 pilotos (titulares, reservas e jovens), 10 motores, 7 patrocinadores, calendário de 24 etapas |
| `.streamlit/config.toml` | Tema escuro estilo F1 |
| `requirements.txt` | `streamlit` + `pandas` |

## 🎮 O que foi recriado do original

- **Tela-resumo ("Escritório")** com nível do carro, motor, pilotos, finanças, notícias e o botão **Continuar**
- **Investimento por corrida** no carro + comparação de nível com as rivais (menu *Campeonato → Equipes* do CM14)
- **Contratos de motor** para a próxima temporada — inclusive o lendário **motor FIA compulsório de 50%**
  de potência para quem ficar sem caixa
- **Pilotos com os 7 atributos clássicos** (Velocidade, Chuva, Concentração, Largada, Ultrapassagem,
  Acerto de carro, Físico), salários por corrida, contratos de 1º/2º piloto e piloto de testes,
  tudo negociado **para a temporada seguinte**
- **Estratégia de corrida**: pneu de largada, número de paradas e ritmo, com clima (seco/molhado)
- **Patrocinadores** com bônus por ponto/pódio/vitória e premiação de construtores
- **Hall da Fama** (Senna, Schumacher, Lauda, Hunt…) com indução dos seus pilotos
- **10 conquistas**, como no original
- **Importância do carro = 60%** (padrão das DBs da comunidade, ajustável na tela inicial)
- **DB 2026 fiel ao post**: Audi/Ferrari/Mercedes/Red Bull com motor próprio, Ford como fornecedora
  independente, Chevrolet rumo ao motor da Cadillac, 1 reserva por equipe, calendário original de
  24 etapas (Bahrein e Arábia Saudita podem ser removidas na criação do jogo), Bortoleto 🇧🇷 na Audi,
  Drugovich e Rafael Câmara no mercado de jovens

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
