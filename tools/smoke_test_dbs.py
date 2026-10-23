# -*- coding: utf-8 -*-
"""
Smoke test das DBs embutidas: valida, cria um jogo, simula a 1ª etapa
e vira a temporada de cada DB. Uso:  python tools/smoke_test_dbs.py
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import dbs
import simulacao as sim


def main():
    falhas = 0
    for key, dbd in dbs.dbs_embutidas().items():
        nome = dbd["meta"]["nome"]
        norm, erros, avisos = dbs.validar_e_normalizar(dbd)
        print(f"[{key}] {nome} — {len(dbd['equipes'])} equipes / {len(dbd['pilotos'])} pilotos / "
              f"grid {dbs.grid_natural(dbd)} (máx {dbs.grid_maximo(dbd)}) / {len(dbd['calendario'])} etapas")
        for e in erros:
            print("   ERRO:", e)
            falhas += 1
        for a in avisos:
            print("   aviso:", a)
        if norm is None:
            falhas += 1
            continue
        try:
            g = sim.criar_novo_jogo(norm["equipes"][0]["id"], 2026, True, 0.5,
                                    db_dados=norm, qtd_pilotos=dbs.grid_natural(norm))
            et = g["calendario"][0]
            grid = sim.simular_classificacao(g, et, False)
            estr = {p["id"]: {"pneu": "Médio", "paradas": 2, "ritmo": "Normal"}
                    for p in sim.titulares(g)}
            res, ev = sim.simular_corrida(g, et, grid, estr, False, sprint=bool(et["sprint"]))
            sim.aplicar_resultado(g, et, grid, res, False, sprint=bool(et["sprint"]), eventos=ev)
            if et["sprint"] and g["rodada"] == 0:
                g["rodada"] += 1
            r = sim.virar_temporada(g)
            jovem = sim._gerar_jovem(g, random.Random(7))
            print(f"   jogo OK — temporada {g['ano']} | novo jovem: {jovem['nome']} | "
                  f"campeões 2026: {r['campeao_pilotos']} / {r['campea_construtores']}")
        except Exception as exc:
            print("   ERRO no jogo:", type(exc).__name__, exc)
            falhas += 1
    print("FALHAS:", falhas)
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
