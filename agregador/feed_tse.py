"""Lê a apuração ao vivo do TSE (resultados.tse.jus.br) zona a zona e roda a projeção.

Arquivos (padrão do app oficial de resultados):
  config:  oficial/ele2026/{eleicao}/config/mun-e{eleicao:06}-cm.json   (municípios e zonas)
  zona:    oficial/ele2026/{eleicao}/dados/{uf}/{uf}{mun:05}-z{zona:04}-c0001-e{eleicao:06}-u.json
Eleição presidencial de 2026: 6257 (1º turno), 6258 (2º turno).

Uso:
  python feed_tse.py                        # 2º turno: baixa as zonas, salva parcial e projeta
  python feed_tse.py --loop 3               # repete a cada 3 minutos
  python feed_tse.py --eleicao 6257         # teste com o 1º turno (já totalizado)
"""
import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

BASE = Path(__file__).parent
URL = "https://resultados.tse.jus.br/oficial/ele2026"
CACHE = BASE / "dados_tse" / "feed"      # zonas já 100% totalizadas não são baixadas de novo
NR_FLAVIO, NR_LULA = "22", "13"
MIN_FRACAO_ZONA = 0.10                     # zona entra na projeção com 10% das seções apuradas

sessao = requests.Session()


def get(url, tentativas=4):
    for i in range(tentativas):
        try:
            r = sessao.get(url, timeout=20, headers={"Cache-Control": "no-cache"})
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            time.sleep(2 ** i)
    return None


def zonas(eleicao):
    cfg = get(f"{URL}/{eleicao}/config/mun-e{eleicao:06d}-cm.json")
    return [(a["cd"], m["cd"], z) for a in cfg["abr"] if a["cd"] != "zz" for m in a["mu"] for z in m["z"]]


def ler_zona(eleicao, uf, mun, zona):
    nome = f"{uf}{mun}-z{zona}-c0001-e{eleicao:06d}-u.json"
    cache = CACHE / str(eleicao) / nome
    if cache.exists():
        d = json.loads(cache.read_text())
    else:
        d = get(f"{URL}/{eleicao}/dados/{uf}/{nome}")
        if d is None:
            return None
        if d["s"]["st"] == d["s"]["ts"]:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(d))
    votos = {c["n"]: int(c["vap"]) for a in d["carg"][0]["agr"] for p in a["par"] for c in p["cand"]}
    return dict(sg_uf=uf.upper(), cd_municipio=int(mun), nr_zona=int(zona),
                flavio=votos.get(NR_FLAVIO, 0), lula=votos.get(NR_LULA, 0),
                secoes_tot=int(d["s"]["st"]), secoes=int(d["s"]["ts"]))


def baixar(eleicao, paralelo=16):
    lista = zonas(eleicao)
    with ThreadPoolExecutor(paralelo) as ex:
        linhas = [r for r in ex.map(lambda z: ler_zona(eleicao, *z), lista) if r]
    return pd.DataFrame(linhas), len(lista)


def uma_rodada(eleicao):
    from projecao import base_r1, ler_votos, projetar
    t0 = time.time()
    df, n_zonas = baixar(eleicao)
    df["fracao"] = df.secoes_tot / df.secoes
    tot_sec = df.secoes.sum()
    apurado = df.secoes_tot.sum() / tot_sec if tot_sec else 0
    parcial_bruta = df.flavio.sum() / max(df.flavio.sum() + df.lula.sum(), 1)
    # Zona parcialmente apurada: estende os votos dela pela fração de seções (mesma divisão)
    usar = df[df.fracao >= MIN_FRACAO_ZONA].copy()
    usar["flavio"] = usar.flavio / usar.fracao
    usar["lula"] = usar.lula / usar.fracao
    saida = BASE / "output" / f"parcial_e{eleicao}.csv"
    usar[["sg_uf", "cd_municipio", "nr_zona", "flavio", "lula"]].to_csv(saida, index=False)
    b = base_r1(ler_votos(2026))
    p = usar.rename(columns={"sg_uf": "SG_UF", "cd_municipio": "CD_MUNICIPIO", "nr_zona": "NR_ZONA",
                             "flavio": "adv2", "lula": "pt2"}).set_index(["SG_UF", "CD_MUNICIPIO", "NR_ZONA"])
    r = projetar(b, p[["adv2", "pt2"]])
    print(f"[{time.strftime('%H:%M:%S')}] seções apuradas {100 * apurado:.2f}% | zonas na projeção "
          f"{r['zonas']} de {n_zonas} | parcial TSE: Flávio {100 * parcial_bruta:.2f}% | "
          f"PROJEÇÃO: Flávio {100 * r['projecao']:.2f}% (IC 90% {100 * r['ic90'][0]:.2f}-"
          f"{100 * r['ic90'][1]:.2f}; some ±0,5) | {time.time() - t0:.0f}s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eleicao", type=int, default=6258)
    ap.add_argument("--loop", type=float, help="minutos entre rodadas")
    a = ap.parse_args()
    while True:
        uma_rodada(a.eleicao)
        if not a.loop:
            break
        time.sleep(a.loop * 60)


if __name__ == "__main__":
    main()
