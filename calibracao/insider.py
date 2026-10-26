"""Há dinheiro com tracking interno no Polymarket (Brasil, 2º turno de 2026)?

Baixa as negociações >= US$ 500 dos contratos do Flávio e de Lula (data-api.polymarket.com,
públicas em blockchain; guarda só carteira, lado, valor, preço e horário), separa as carteiras
direcionais grandes (>= US$ 50 mil e >= 30% do volume num lado; formadores de mercado ficam
de fora) e testa:
  (a) o fluxo delas num bloco de 6 h prevê a variação do preço nas 24 h seguintes?
  (b) elas se posicionam na direção da surpresa das pesquisas antes da divulgação
      (18 h da véspera às 18 h do dia)?
Uso:  python insider.py      (preço em ../agregador/output/polymarket_flavio_2t.csv;
                              datas de divulgação em ../agregador/output/pesquisas_divulgacao.csv)
"""
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

BASE = Path(__file__).parent
AGR = BASE.parent / "agregador" / "output"
CACHE = BASE / "cache" / "trades"
MERCADOS = {"flavio": "0x1a01bf78f56a507fcb666d564d8c8b91b0750679163ed6e96746102c9b7d285d",
            "lula": "0xdf8e2dc5860027decbe6164555c3c1c9645c3bd33e16b9dc57ca87125047d4a8"}
INICIO = pd.Timestamp("2026-10-04 20:00", tz="UTC")
TZ = "America/Sao_Paulo"


def baixar(nome, cid):
    rows, off = [], 0
    while off <= 10000:  # a API não pagina além de 10 mil; o filtro por valor cobre o período
        r = requests.get("https://data-api.polymarket.com/trades", timeout=60, params={
            "market": cid, "limit": 500, "offset": off, "takerOnly": "false",
            "filterType": "CASH", "filterAmount": 500})
        b = r.json() if r.status_code == 200 else []
        if not b:
            break
        rows += [dict(carteira=t["proxyWallet"], lado=t["side"], resultado=t["outcomeIndex"],
                      valor=float(t["size"]) * float(t["price"]), preco=float(t["price"]), ts=t["timestamp"])
                 for t in b]
        off += 500
        if b[-1]["timestamp"] < INICIO.timestamp():
            break
        time.sleep(0.2)
    d = pd.DataFrame(rows).drop_duplicates()
    d = d[d.ts >= INICIO.timestamp()].assign(mercado=nome)
    CACHE.mkdir(parents=True, exist_ok=True)
    d.to_csv(CACHE / f"{nome}_grandes.csv", index=False)
    return d


def newey_west(X, res, L=4):
    S = (X * res[:, None]).T @ (X * res[:, None])
    for k in range(1, L + 1):
        G = (X[k:] * res[k:, None]).T @ (X[:-k] * res[:-k, None])
        S += (1 - k / (L + 1)) * (G + G.T)
    Bi = np.linalg.inv(X.T @ X)
    return np.sqrt(np.diag(Bi @ S @ Bi))


def main():
    t = pd.concat([baixar(n, c) for n, c in MERCADOS.items()])
    sim, compra = t.resultado == 0, t.lado == "BUY"
    # pró-Flávio: comprar Flávio-Sim, vender Flávio-Não, comprar Lula-Não, vender Lula-Sim
    t["fluxo"] = np.where(t.mercado == "flavio", np.where(sim == compra, 1, -1), np.where(sim == compra, -1, 1)) * t.valor
    t["hora"] = pd.to_datetime(t.ts, unit="s", utc=True).dt.tz_convert(TZ)
    g = t.groupby("carteira").agg(volume=("valor", "sum"), liq=("fluxo", "sum"))
    baleias = g[(g.volume >= 50_000) & (g.liq.abs() / g.volume >= 0.3)].index
    w = t[t.carteira.isin(baleias)]
    print(f"{len(t)} negociações >= US$500, {t.carteira.nunique()} carteiras; {len(baleias)} direcionais grandes "
          f"(US$ {g.loc[baleias].volume.sum() / 1e6:.1f} mi, saldo pró-Flávio US$ {g.loc[baleias].liq.sum() / 1e6:+.2f} mi)")

    p = pd.read_csv(AGR / "polymarket_flavio_2t.csv", index_col=0).preco
    p.index = pd.to_datetime(p.index, utc=True).tz_convert(TZ)
    B = np.log(p / (1 - p)).resample("6h").last().dropna()
    fl = w.set_index("hora").fluxo.resample("6h").sum().reindex(B.index, fill_value=0) / 1e5
    dd = pd.DataFrame(dict(fut=B.shift(-4) - B, fl=fl, pas=B - B.shift(4), mesmo=B - B.shift(1))).dropna()
    X = np.column_stack([np.ones(len(dd)), dd.fl, dd.pas])
    b, *_ = np.linalg.lstsq(X, dd.fut.values, rcond=None)
    ep = newey_west(X, dd.fut.values - X @ b)
    print(f"(a) fluxo das baleias -> preço nas 24h seguintes: {b[1]:+.4f} ± {ep[1]:.4f} logit por US$100 mil "
          f"(t {b[1] / ep[1]:+.2f}); no mesmo bloco: correlação {np.corrcoef(dd.fl, dd.mesmo)[0, 1]:+.2f}")

    pq = pd.read_csv(AGR / "pesquisas_divulgacao.csv", parse_dates=["divulgacao"]).dropna(subset=["divulgacao"])
    rows = []
    for D in sorted(pq.divulgacao.unique()):
        D = pd.Timestamp(D)
        ant = pq[(pq.divulgacao < D) & (pq.divulgacao >= D - pd.Timedelta(days=7))]
        if len(ant) < 3:
            continue
        a = pd.Timestamp(D.date(), tz=TZ) - pd.Timedelta(hours=6)
        f_ = w[(w.hora >= a) & (w.hora < a + pd.Timedelta(hours=24))].fluxo.sum() / 1e5
        rows.append(dict(dia=D.date(), surpresa=pq[pq.divulgacao == D].share.mean() - ant.share.mean(), fluxo_baleias=f_))
    r = pd.DataFrame(rows)
    print("(b) antes das pesquisas:\n" + r.round(2).to_string(index=False))
    print(f"    acerto de direção {(np.sign(r.surpresa) == np.sign(r.fluxo_baleias)).mean():.0%} em {len(r)} dias; "
          f"correlação {np.corrcoef(r.surpresa, r.fluxo_baleias)[0, 1]:+.2f}")


if __name__ == "__main__":
    main()
