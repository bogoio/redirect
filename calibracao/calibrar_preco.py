"""Converte um preço do Polymarket em probabilidade calibrada, usando os mercados já
resolvidos do cache: taxa de acerto de favoritos com preço perto do informado, no mesmo
prazo e categoria.

Uso:  python calibrar_preco.py --preco 0.795 --dias 4 --categoria política [--janela 0.05]
"""
import argparse

import numpy as np

import analise as a


def calibrar(preco, dias, categoria, janela=0.05, ev=None):
    if ev is None:
        linhas, _ = a.carregar()
        ev = a.favorito_por_evento(a.instantaneos(linhas))
    # prazos vizinhos ao número de dias até o evento
    prazos = [p for p, d in a.PRAZOS.items() if d <= 2 * dias and d >= dias / 2] or ["7d"]
    linhas = []
    for cat in [categoria, None]:
        g = ev[ev.prazo.isin(prazos) & ev.preco_fav.between(preco - janela, preco + janela)]
        if cat:
            g = g[g.categoria == cat]
        k, n = int(g.fav_venceu.sum()), len(g)
        lo, hi = a.wilson(k, n)
        linhas.append(dict(categoria=cat or "todas", prazos="+".join(prazos), n=n,
                           eventos=g.evento.nunique(), preco_medio=g.preco_fav.mean(),
                           acerto=k / n if n else np.nan, ic95_inf=lo, ic95_sup=hi))
    return linhas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preco", type=float, required=True)
    ap.add_argument("--dias", type=float, required=True)
    ap.add_argument("--categoria", default="política")
    ap.add_argument("--janela", type=float, default=0.05)
    x = ap.parse_args()
    for r in calibrar(x.preco, x.dias, x.categoria, x.janela):
        print(f"{r['categoria']:9s} prazos {r['prazos']:7s} n={r['n']:5d} ({r['eventos']} eventos) "
              f"preço médio {r['preco_medio']:.3f} -> acerto {r['acerto']:.3f} "
              f"[IC95 {r['ic95_inf']:.3f}-{r['ic95_sup']:.3f}]")


if __name__ == "__main__":
    main()
