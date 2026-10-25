# -*- coding: utf-8 -*-
"""
Bandeiras como IMAGENS (e não emoji).

Por quê? O Windows não renderiza emojis de bandeira de país — mostra apenas
as letrinhas ("GB", "AU", "MX"...). Então o jogo usa arquivos PNG locais
(pasta assets/bandeiras/, fonte: flagcdn.com — bandeiras de domínio público),
convertendo o emoji guardado nas DBs (par de indicadores regionais) em
código ISO do país e daí para a imagem.
"""

import base64
import re
from functools import lru_cache
from pathlib import Path

PASTA = Path(__file__).resolve().parent / "assets" / "bandeiras"
_RE_BANDEIRA = re.compile(r"[\U0001F1E6-\U0001F1FF]{2}")


def codigo_bandeira(emoji):
    """'🇧🇷' -> 'br' | '🏁'/texto qualquer -> None"""
    if not emoji:
        return None
    m = _RE_BANDEIRA.search(str(emoji))
    if not m:
        return None
    return "".join(chr(ord(c) - 0x1F1E6 + ord("A")) for c in m.group(0)).lower()


@lru_cache(maxsize=256)
def _data_uri(codigo):
    arq = PASTA / f"{codigo}.png"
    try:
        return "data:image/png;base64," + base64.b64encode(arq.read_bytes()).decode()
    except Exception:
        return None


def url_bandeira(emoji):
    """URL (data URI local, ou flagcdn se não houver arquivo) para colunas de imagem."""
    codigo = codigo_bandeira(emoji)
    if not codigo:
        return ""
    return _data_uri(codigo) or f"https://flagcdn.com/w80/{codigo}.png"


TAMANHOS = {"mini": 13, "padrao": 15, "destaque": 20, "titulo": 26, "hero": 36}


def img_bandeira(emoji, altura=15):
    """Tag <img> HTML da bandeira. altura em px ou nome: mini/padrao/destaque/titulo/hero."""
    codigo = codigo_bandeira(emoji)
    if not codigo:
        return str(emoji or "")
    if isinstance(altura, str):
        altura = TAMANHOS.get(altura, 15)
    src = url_bandeira(emoji)
    return f'<img class="flag-img" src="{src}" alt="{codigo.upper()}" style="height:{int(altura)}px;width:auto;">'


def com_bandeira(emoji, texto, altura=15):
    img = img_bandeira(emoji, altura)
    return f"{img} {texto}" if img else str(texto)


def substituir_emojis(texto, altura=14):
    """Troca todos os emojis de bandeira dentro de um texto por <img>."""
    if not texto:
        return texto
    return _RE_BANDEIRA.sub(lambda m: img_bandeira(m.group(0), altura), str(texto))


def codigo_texto(emoji):
    """'GB' — para seletores (selectbox não aceita imagem, só texto)."""
    codigo = codigo_bandeira(emoji)
    return codigo.upper() if codigo else str(emoji or "")
