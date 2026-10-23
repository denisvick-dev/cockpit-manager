# -*- coding: utf-8 -*-
"""
Padroniza as bandeiras de assets/bandeiras/:
- baixa a versão maior (flagcdn w160, domínio público)
- encaixa cada bandeira, sem distorcer, num canvas uniforme 96x72 (4:3)
  com fundo transparente e uma bordinha sutil — assim TODAS as bandeiras
  têm exatamente o mesmo tamanho na tela (tabelas e títulos alinhados).

Uso:  python tools/padronizar_bandeiras.py
"""
import sys
import urllib.request
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "assets" / "bandeiras"
LARGURA, ALTURA = 96, 72          # canvas final (4:3)
MARGEM = 4                        # respiro em volta da bandeira


def padronizar(img):
    img = img.convert("RGBA")
    img.thumbnail((LARGURA - 2 * MARGEM, ALTURA - 2 * MARGEM), Image.LANCZOS)
    canvas = Image.new("RGBA", (LARGURA, ALTURA), (0, 0, 0, 0))
    x = (LARGURA - img.width) // 2
    y = (ALTURA - img.height) // 2
    canvas.paste(img, (x, y), img)
    borda = ImageDraw.Draw(canvas)
    borda.rectangle([x, y, x + img.width - 1, y + img.height - 1],
                    outline=(255, 255, 255, 64), width=2)
    return canvas


def main():
    sys.path.insert(0, str(RAIZ))
    PASTA.mkdir(parents=True, exist_ok=True)
    arquivos = sorted(PASTA.glob("*.png"))
    if not arquivos:
        print("Nenhuma bandeira em assets/bandeiras/.")
        return
    for arq in arquivos:
        codigo = arq.stem
        try:
            req = urllib.request.Request(f"https://flagcdn.com/w160/{codigo}.png",
                                         headers={"User-Agent": "cockpit-manager-streamlit"})
            bruto = urllib.request.urlopen(req, timeout=20).read()
            img = Image.open(BytesIO(bruto))
        except Exception:
            img = Image.open(arq)  # mantém a atual em caso de falha de rede
        padronizar(img).save(arq, optimize=True)
        print(f"ok {codigo}")
    print(f"{len(arquivos)} bandeiras padronizadas em {LARGURA}x{ALTURA}px.")


if __name__ == "__main__":
    main()
