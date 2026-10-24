"""Testes de teoria sobre as pesquisas de véspera (pesquisas_vespera.csv), 2014-2022.

1. Voto envergonhado (espiral do silêncio): pesquisa remota (telefone/internet, sem
   entrevistador) erra menos com a direita que a presencial, dentro da mesma eleição?
2. Indecisos: nos 2º turnos com presidente candidato (2014: Dilma; 2022: Bolsonaro), institutos
   com mais indecisos superestimaram o governo? Inclinação s do erro a favor do governo por
   ponto de indeciso => fração dos indecisos que foi para o governo ≈ 0,5 - s.

Uso:  python historico/testes_teoria.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

MODO = {"Datafolha": "presencial", "Ibope/Ipec": "presencial", "Quaest": "presencial", "CNT/MDA": "presencial",
        "Vox Populi": "presencial", "PoderData": "remoto", "Ipespe": "remoto", "AtlasIntel": "remoto",
        "Real Time Big Data": "remoto", "Gerp": "remoto", "BTG/Nexus": "remoto"}  # só modos conhecidos


def inclinacao(df, x, y, grupo):
    s = df.assign(e=df[y] - df.groupby(grupo)[y].transform("mean"), u=df[x] - df.groupby(grupo)[x].transform("mean"))
    b = (s.u * s.e).sum() / (s.u ** 2).sum()
    res = s.e - b * s.u
    return b, np.sqrt((res ** 2).sum() / (len(s) - 1 - s[grupo].nunique()) / (s.u ** 2).sum())


def main():
    h = pd.read_csv(Path(__file__).parent / "pesquisas_vespera.csv")
    h["eleicao"] = h.ano.astype(str) + " T" + h.turno.astype(str)
    h["erro_rel"] = h.erro - h.groupby("eleicao").erro.transform("mean")
    d = h.assign(modo=h.instituto.map(MODO)).dropna(subset=["modo"])
    print("1. Erro na participação da direita por modo (pesquisa - resultado):")
    print(d.pivot_table(index="eleicao", columns="modo", values="erro", aggfunc="mean").round(2).to_string())
    for nome, s in [("todas", d), ("2º turnos", d[d.turno == 2])]:
        a, b = s[s.modo == "remoto"].erro_rel, s[s.modo == "presencial"].erro_rel
        dif, ep = a.mean() - b.mean(), np.sqrt(a.var() / len(a) + b.var() / len(b))
        print(f"   remoto - presencial ({nome}, dentro da eleição): {dif:+.2f} ± {ep:.2f} (n {len(a)}/{len(b)})")

    t = h.assign(u=100 - h.pt - h.adversario)
    t = t[(t.turno == 2) & (t.u >= 1.5) & t.ano.isin([2014, 2022])].copy()
    t["erro_gov"] = np.where(t.ano == 2022, t.erro, -t.erro)
    print("\n2. Indecisos nos 2º turnos com presidente candidato:")
    for nome, s in [("todos", t), ("sem Gerp, Brasmarket e Veritá", t[~t.instituto.isin(["Gerp", "Brasmarket", "Veritá"])])]:
        b, ep = inclinacao(s, "u", "erro_gov", "ano")
        print(f"   {nome}: n={len(s)} inclinação {b:+.3f} ± {ep:.3f} (t {b / ep:.2f}) -> "
              f"fração dos indecisos para o governo ≈ {0.5 - b:.2f}")


if __name__ == "__main__":
    main()
