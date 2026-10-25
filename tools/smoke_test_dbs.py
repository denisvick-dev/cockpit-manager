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
    banco = list(dbs.dbs_embutidas().items())
    # demais temporadas históricas (a de 1950 já vem embutida)
    for ano in dbs.HIST_ANOS:
        if ano != 1950:
            banco.append((f"hist_{ano}", dbs.db_f1_historica(ano)))
    for key, dbd in banco:
        nome = dbd["meta"]["nome"]
        norm, erros, avisos = dbs.validar_e_normalizar(dbd)
        print(
            f"[{key}] {nome} — {len(dbd['equipes'])} equipes / {len(dbd['pilotos'])} pilotos / "
            f"grid {dbs.grid_natural(dbd)} (máx {dbs.grid_maximo(dbd)}) / {len(dbd['calendario'])} etapas"
        )
        for e in erros:
            print("   ERRO:", e)
            falhas += 1
        for a in avisos:
            print("   aviso:", a)
        if norm is None:
            falhas += 1
            continue
        try:
            ano_jogo = int(norm["meta"].get("ano", 2026))
            g = sim.criar_novo_jogo(
                norm["equipes"][0]["id"], ano_jogo, True, 0.5, db_dados=norm, qtd_pilotos=dbs.grid_natural(norm)
            )
            # pré-contrato: fecha na hora e é consumido na virada
            livres = [p for p in norm["pilotos"] if p["papel"] == "livre"]
            if livres:
                eqj = sim.equipe(g, g["equipe_jogador"])
                taxa = sim.taxa_sinal(400)
                if eqj["caixa"] >= taxa / 1000.0:
                    ok, msg = sim.pre_contratar_piloto(g, livres[0]["id"], "P1", 400, 2)
                    if not ok:
                        print("   ERRO no pré-contrato:", msg)
                        falhas += 1
                    elif g["contratos_proxima"].get(livres[0]["id"], {}).get("sinal") != taxa:
                        print("   ERRO: pré-contrato não gravado com sinal")
                        falhas += 1
            et = g["calendario"][0]
            grid = sim.simular_classificacao(g, et, False)
            estr = {p["id"]: {"pneu": "Médio", "paradas": 2, "ritmo": "Normal"} for p in sim.titulares(g)}
            res, ev = sim.simular_corrida(g, et, grid, estr, False, sprint=bool(et["sprint"]))
            sim.aplicar_resultado(g, et, grid, res, False, sprint=bool(et["sprint"]), eventos=ev)
            if et["sprint"] and g["rodada"] == 0:
                g["rodada"] += 1
            r = sim.virar_temporada(g)
            jovem = sim._gerar_jovem(g, random.Random(7))
            print(
                f"   jogo OK — temporada {g['ano']} | novo jovem: {jovem['nome']} | "
                f"campeões {ano_jogo}: {r['campeao_pilotos']} / {r['campea_construtores']}"
            )
        except Exception as exc:
            print("   ERRO no jogo:", type(exc).__name__, exc)
            falhas += 1
    print("FALHAS:", falhas)
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
