# -*- coding: utf-8 -*-
"""Armazenamento das carreiras: slots locais, auto-save, migração e exportação.

- **Slots**: cada carreira é um `.json` em `saves/` (uma pasta por máquina, fora
  do Git). O jogador pode salvar com nome, carregar e apagar pela tela
  *Salvar / Carregar*.
- **Auto-save**: a cada etapa concluída o jogo grava `saves/_autosave.json`, então
  fechar o navegador não custa a temporada.
- **Migração**: todo save carrega `versao`. `migrar_save()` completa campos que
  não existiam nas versões anteriores e avisa o que foi ajustado — carreiras
  antigas continuam abrindo.
- **CSV**: `csv_bytes()` gera CSV com `;` e BOM (abre certo no Excel em pt-BR).
"""

from __future__ import annotations

import json
import os
import re
import time

VERSAO_SAVE = 3
PASTA_SAVES = "saves"
NOME_AUTOSAVE = "_autosave"


# ------------------------------------------------------------------ caminhos
def pasta_saves(criar: bool = True) -> str:
    """Pasta onde os slots ficam (ao lado do app, ignorada pelo Git)."""
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), PASTA_SAVES)
    if criar:
        os.makedirs(base, exist_ok=True)
    return base


def nome_seguro(nome: str) -> str:
    """Transforma o nome digitado num nome de arquivo previsível."""
    limpo = re.sub(r"[^0-9A-Za-zÀ-ÿ _.-]", "", (nome or "").strip())
    limpo = re.sub(r"\s+", "_", limpo).strip("._-")
    return (limpo or f"save_{time.strftime('%Y%m%d_%H%M')}")[:60]


def caminho_slot(nome: str) -> str:
    # o auto-save tem nome reservado (o "_" inicial identifica o slot automático)
    if nome == NOME_AUTOSAVE:
        return os.path.join(pasta_saves(), f"{NOME_AUTOSAVE}.json")
    return os.path.join(pasta_saves(), f"{nome_seguro(nome)}.json")


# ------------------------------------------------------------------ migração
def _padroes() -> dict:
    """Campos obrigatórios de um save na versão atual (e seus valores padrão)."""
    import dados2026 as db

    meta_padrao = {
        "nome": "Save (F1 2026)",
        "categoria": "Fórmula 1",
        "rotulo_fornecedor": "Motor",
        "rotulo_corrida2": "Sprint",
        "pontos_corrida": list(db.PONTOS_CORRIDA),
        "pontos_corrida2": list(db.PONTOS_SPRINT),
        "fator_pontos_bonus": 1.0,
        "pontua_abandono": False,
    }
    return {
        "rodada": 0,
        "calendario": [],
        "resultados": [],
        "historico_pontos": [],
        "historico_caixa": [],
        "historico_temporadas": [],
        "noticias": [],
        "extrato": [],
        "contratos_proxima": {},
        "negociacoes": {},
        "motor_proxima": None,
        "patrocinador_proxima": None,
        "hall_da_fama": [],
        "conquistas": [],
        "temporadas_completas": 0,
        "regen_usados": 0,
        "importancia_carro": 0.6,
        "incluir_canceladas": False,
        "meta": meta_padrao,
    }


def migrar_save(dados: dict) -> tuple[dict, list[str]]:
    """Deixa um save de qualquer versão no formato atual.

    Devolve `(save, avisos)`; `avisos` é a lista do que precisou ser ajustado
    (mostrada ao jogador na tela de carregar).
    """
    if not isinstance(dados, dict):
        raise ValueError("O arquivo não parece um save do Cockpit Manager.")
    for chave in ("equipes", "pilotos", "ano"):
        if chave not in dados:
            raise ValueError(f"Save incompleto: falta o campo '{chave}'.")

    avisos: list[str] = []
    versao = int(dados.get("versao") or 1)
    if versao > VERSAO_SAVE:
        avisos.append(
            f"Este save foi criado numa versão mais nova do jogo (v{versao}); "
            "os campos desconhecidos foram preservados."
        )
    elif versao < VERSAO_SAVE:
        avisos.append(f"Save migrado da versão {versao} para a {VERSAO_SAVE}.")

    # v1 -> v2: histórico de temporadas, caixa e conquistas
    if versao < 2:
        dados.setdefault("historico_temporadas", [])
        dados.setdefault("historico_caixa", [])
        dados.setdefault("conquistas", [])
        dados.setdefault("temporadas_completas", 0)
    # v2 -> v3: negociações em rodadas e voltas rápidas
    if versao < 3:
        dados.setdefault("negociacoes", {})

    padroes = _padroes()
    faltando = []
    for chave, valor in padroes.items():
        if chave not in dados:
            dados[chave] = valor
            faltando.append(chave)
    if faltando:
        avisos.append("Campos novos preenchidos com o padrão: " + ", ".join(faltando) + ".")

    meta = dict(padroes["meta"])
    meta.update(dados.get("meta") or {})
    dados["meta"] = meta
    if not dados.get("calendario"):
        dados["calendario"] = dados.get("calendario_base") or []
    dados.setdefault("calendario_base", dados["calendario"])
    if dados.get("patrocinadores") is None:
        import dados2026 as db

        dados["patrocinadores"] = db.PATROCINADORES

    for p in dados["pilotos"]:
        p["voltas_rapidas"] = int(p.get("voltas_rapidas") or 0)
        p.setdefault("aposentado", False)
    dados["versao"] = VERSAO_SAVE
    return dados, avisos


# ------------------------------------------------------- (de)serialização
def serializar(game: dict, identado: bool = False) -> str:
    """JSON pronto para gravar/baixar (sempre com a versão atual do schema)."""
    game["versao"] = VERSAO_SAVE
    return json.dumps(game, ensure_ascii=False, indent=1 if identado else None)


def desserializar(texto) -> tuple[dict, list[str]]:
    """Lê o JSON (texto ou bytes) e devolve `(save migrado, avisos)`."""
    if isinstance(texto, bytes):
        texto = texto.decode("utf-8-sig")
    return migrar_save(json.loads(texto))


# ------------------------------------------------------------------- slots
def salvar(game: dict, nome: str) -> str:
    """Grava o save num slot e devolve o caminho do arquivo."""
    caminho = caminho_slot(nome)
    with open(caminho, "w", encoding="utf-8") as fh:
        fh.write(serializar(game, identado=True))
    return caminho


def carregar(nome: str) -> tuple[dict, list[str]]:
    with open(caminho_slot(nome), encoding="utf-8") as fh:
        return desserializar(fh.read())


def apagar(nome: str) -> bool:
    caminho = caminho_slot(nome)
    if os.path.exists(caminho):
        os.remove(caminho)
        return True
    return False


def listar_saves() -> list[dict]:
    """Slots disponíveis, do mais recente para o mais antigo."""
    pasta = pasta_saves()
    itens = []
    for arq in os.listdir(pasta):
        if not arq.endswith(".json"):
            continue
        caminho = os.path.join(pasta, arq)
        nome = arq[:-5]
        info = {
            "nome": nome,
            "arquivo": arq,
            "caminho": caminho,
            "mtime": os.path.getmtime(caminho),
            "modificado": time.strftime("%d/%m %H:%M", time.localtime(os.path.getmtime(caminho))),
            "tamanho_kb": round(os.path.getsize(caminho) / 1024, 1),
            "ano": "—",
            "rodada": "—",
            "equipe": "—",
            "auto": nome == NOME_AUTOSAVE,
            "versao": 1,
        }
        try:
            with open(caminho, encoding="utf-8") as fh:
                dados = json.load(fh)
            info["ano"] = dados.get("ano", "—")
            info["rodada"] = int(dados.get("rodada", 0)) + 1
            eq_id = dados.get("equipe_jogador")
            info["equipe"] = next(
                (e.get("nome", "—") for e in dados.get("equipes", []) if e.get("id") == eq_id), "—"
            )
            info["versao"] = dados.get("versao", 1)
        except (OSError, ValueError):
            info["equipe"] = "arquivo ilegível"
        itens.append(info)
    return sorted(itens, key=lambda x: x["mtime"], reverse=True)


# ---------------------------------------------------------------- auto-save
def auto_salvar(game: dict) -> str:
    """Grava o auto-save (silencioso: nunca derruba o jogo por erro de disco)."""
    try:
        return salvar(game, NOME_AUTOSAVE)
    except OSError:
        return ""


def auto_save_info() -> dict | None:
    """Metadados do auto-save, se existir (usado na barra lateral).

    Lê só o arquivo do auto-save: a barra lateral roda em toda interação e não
    pode varrer a pasta inteira de slots.
    """
    caminho = caminho_slot(NOME_AUTOSAVE)
    if not os.path.exists(caminho):
        return None
    info = {"nome": NOME_AUTOSAVE, "caminho": caminho, "auto": True, "ano": "—", "rodada": "—",
            "equipe": "—", "versao": 1}
    try:
        with open(caminho, encoding="utf-8") as fh:
            dados = json.load(fh)
        info["ano"] = dados.get("ano", "—")
        info["rodada"] = int(dados.get("rodada", 0)) + 1
        info["equipe"] = next(
            (e.get("nome", "—") for e in dados.get("equipes", []) if e.get("id") == dados.get("equipe_jogador")),
            "—",
        )
        info["versao"] = dados.get("versao", 1)
    except (OSError, ValueError):
        return None
    info["modificado"] = time.strftime("%d/%m %H:%M", time.localtime(os.path.getmtime(caminho)))
    return info


# --------------------------------------------------------------------- CSV
def csv_bytes(df, separador: str = ";") -> bytes:
    """CSV compatível com o Excel em português (BOM + ponto e vírgula)."""
    return df.to_csv(index=False, sep=separador).encode("utf-8-sig")
