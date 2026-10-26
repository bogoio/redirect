"""Lê a apuração ao vivo do TSE (resultados.tse.jus.br) zona a zona e roda a projeção.

Arquivos (padrão do app oficial de resultados):
  config:  oficial/ele2026/{eleicao}/config/mun-e{eleicao:06}-cm.json   (municípios e zonas)
  zona:    oficial/ele2026/{eleicao}/dados/{uf}/{uf}{mun:05}-z{zona:04}-c0001-e{eleicao:06}-u.json
Eleição presidencial de 2026: 6257 (1º turno), 6258 (2º turno).

Uso:
  python feed_tse.py                        # 2º turno: baixa as zonas, salva parcial e projeta
  python feed_tse.py --loop 0               # repete sem pausa (cada rodada ~ tempo do download)
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


from requests.adapters import HTTPAdapter
sessao.mount("https://", HTTPAdapter(pool_connections=128, pool_maxsize=128))


def get(url, tentativas=3):
    for i in range(tentativas):
        try:
            r = sessao.get(url, timeout=8, headers={"Cache-Control": "no-cache"})
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            time.sleep(0.5 * (i + 1))
    return None


def zonas(eleicao):
    cfg = get(f"{URL}/{eleicao}/config/mun-e{eleicao:06d}-cm.json")
    return [(a["cd"], m["cd"], z) for a in cfg["abr"] if a["cd"] != "zz" for m in a["mu"] for z in m["z"]]


def ler_zona(eleicao, uf, mun, zona, usar_cache=True):
    nome = f"{uf}{mun}-z{zona}-c0001-e{eleicao:06d}-u.json"
    cache = CACHE / str(eleicao) / nome
    if usar_cache and cache.exists():
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


_LISTA = {}


def baixar(eleicao, paralelo=48, usar_cache=True):
    if eleicao not in _LISTA:
        _LISTA[eleicao] = zonas(eleicao)
    lista = _LISTA[eleicao]
    with ThreadPoolExecutor(paralelo) as ex:
        linhas = [r for r in ex.map(lambda z: ler_zona(eleicao, *z, usar_cache=usar_cache), lista) if r]
    return pd.DataFrame(linhas), len(lista)


_BASE = {}


def base_1t():
    """Base do 1º turno de 2026 por zona, lida do ZIP do TSE uma vez e guardada em pickle."""
    if "b" not in _BASE:
        from projecao import base_r1, ler_votos
        arq = CACHE / "base_r1_2026.pkl"
        if arq.exists():
            _BASE["b"] = pd.read_pickle(arq)
        else:
            _BASE["b"] = base_r1(ler_votos(2026))
            arq.parent.mkdir(parents=True, exist_ok=True)
            _BASE["b"].to_pickle(arq)
    return _BASE["b"]


def sinal(proj, zonas_proj, apurado):
    """Regra de decisão combinada antes da apuração (participação do Flávio, %)."""
    dist = abs(proj - 50)
    if zonas_proj < 300:
        return "POUCAS ZONAS - espere"
    if apurado >= 0.05:
        return ("QUASE CERTO" if dist >= 1.5 else "FORTE" if dist >= 0.5 else "INDEFINIDO") + \
            (" Flávio" if proj > 50 else " Lula") * bool(dist >= 0.5)
    return ("FORTE" if dist >= 1.5 else "INDICA" if dist >= 0.5 else "INDEFINIDO") + \
        (" Flávio" if proj > 50 else " Lula") * bool(dist >= 0.5)


_HIST = []


def uma_rodada(eleicao, usar_cache=True, intervalo=False):
    from projecao import projetar
    t0 = time.time()
    df, n_zonas = baixar(eleicao, usar_cache=usar_cache)
    t_baixa = time.time() - t0
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
    b = base_1t()
    p = usar.rename(columns={"sg_uf": "SG_UF", "cd_municipio": "CD_MUNICIPIO", "nr_zona": "NR_ZONA",
                             "flavio": "adv2", "lula": "pt2"}).set_index(["SG_UF", "CD_MUNICIPIO", "NR_ZONA"])
    if p.empty:
        print(f"[{time.strftime('%H:%M:%S')}] nenhuma zona apurada ainda ({t_baixa:.0f}s)", flush=True)
        return
    r = projetar(b, p[["adv2", "pt2"]], boot=intervalo)
    proj = 100 * r["projecao"]
    _HIST.append(proj)
    var = f"{proj - _HIST[-2]:+.2f}" if len(_HIST) > 1 else "-"
    ic = f" IC90 {100 * r['ic90'][0]:.2f}-{100 * r['ic90'][1]:.2f}" if intervalo else ""
    print(f"[{time.strftime('%H:%M:%S')}] SINAL: {sinal(proj, r['zonas'], apurado)} | PROJEÇÃO Flávio "
          f"{proj:.2f}% (var {var}{ic}) | apurado {100 * apurado:.2f}% | zonas {r['zonas']}/{n_zonas} | "
          f"parcial TSE {100 * parcial_bruta:.2f}% | {t_baixa:.0f}s download, {time.time() - t0:.0f}s total",
          flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eleicao", type=int, default=6258)
    ap.add_argument("--loop", type=float, help="minutos entre rodadas (0 = sem pausa)")
    ap.add_argument("--sem-cache", action="store_true", help="baixa tudo de novo (teste de velocidade)")
    ap.add_argument("--intervalo", action="store_true", help="calcula o IC 90% (mais lento)")
    a = ap.parse_args()
    base_1t()
    while True:
        try:
            uma_rodada(a.eleicao, usar_cache=not a.sem_cache, intervalo=a.intervalo)
        except Exception as e:  # rodada com erro de rede não derruba o laço
            print(f"[{time.strftime('%H:%M:%S')}] erro na rodada: {e}", flush=True)
        if a.loop is None:
            break
        time.sleep(a.loop * 60)


if __name__ == "__main__":
    main()
