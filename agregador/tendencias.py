"""Google Trends: parte do candidato da direita nas buscas (Flávio x Lula), por dia.
Termômetro de momento, não estimativa de voto (ver README).

Uso:  python tendencias.py [--inicio 2026-10-07] [--fim 2026-10-25]
"""
import argparse

from pytrends.request import TrendReq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inicio", default="2026-10-07")
    ap.add_argument("--fim", default="2026-10-25")
    a = ap.parse_args()
    termos = ["Flávio Bolsonaro", "Lula"]
    pt = TrendReq(hl="pt-BR", tz=180, timeout=(10, 30))
    pt.build_payload(termos, geo="BR", timeframe=f"{a.inicio} {a.fim}")
    d = pt.interest_over_time()
    d["parte_flavio"] = (100 * d[termos[0]] / (d[termos[0]] + d[termos[1]])).round(1)
    print(d[termos + ["parte_flavio"]].to_string())


if __name__ == "__main__":
    main()
