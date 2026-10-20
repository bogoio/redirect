"""Coleta de mercados encerrados do Polymarket (Gamma API) e do histórico de preços
de cada token (CLOB API), com cache local em JSON.

Uso:
  python coleta.py --amostra 200     # baixa só 200 mercados e mostra o esquema real
  python coleta.py --esquema         # só mostra o esquema do que já está em cache
  python coleta.py                   # coleta completa (retoma de onde parou)
"""
import argparse
import json
import time
from pathlib import Path

import requests

BASE = Path(__file__).parent
CACHE_MERC = BASE / "cache" / "mercados"
CACHE_HIST = BASE / "cache" / "historico"
GAMMA = "https://gamma-api.polymarket.com/markets"
CLOB = "https://clob.polymarket.com/prices-history"
LIMITE_PAGINA = 500
FIDELIDADE_MIN = 60  # pontos de hora em hora
PAUSA = 0.25

sessao = requests.Session()


def get(url, params, tentativas=6):
    """GET com pausa e novas tentativas (backoff exponencial em 429/5xx/rede)."""
    espera = 2
    for _ in range(tentativas):
        try:
            r = sessao.get(url, params=params, timeout=30)
            if r.status_code == 200:
                time.sleep(PAUSA)
                return r.json()
            if r.status_code not in (429, 500, 502, 503, 504):
                r.raise_for_status()
        except requests.RequestException as e:
            print(f"  erro de rede: {e}")
        time.sleep(espera)
        espera = min(espera * 2, 60)
    raise RuntimeError(f"falhou depois de {tentativas} tentativas: {url} {params}")


def listar_mercados(maximo=None):
    """Pagina /markets?closed=true e guarda uma página por arquivo (retomável)."""
    offset, total = 0, 0
    while maximo is None or total < maximo:
        arq = CACHE_MERC / f"pagina_{offset:07d}.json"
        if arq.exists():
            pag = json.loads(arq.read_text())
        else:
            lim = LIMITE_PAGINA if maximo is None else min(LIMITE_PAGINA, maximo - total)
            pag = get(GAMMA, {"closed": "true", "limit": lim, "offset": offset,
                              "order": "id", "ascending": "true"})
            arq.write_text(json.dumps(pag))
        if not pag:
            break
        total += len(pag)
        offset += len(pag)
        print(f"mercados: {total}")
    return mercados_em_cache()


def mercados_em_cache():
    out = []
    for arq in sorted(CACHE_MERC.glob("pagina_*.json")):
        out.extend(json.loads(arq.read_text()))
    return out


def tokens(m):
    t = m.get("clobTokenIds")
    return json.loads(t) if isinstance(t, str) else (t or [])


def baixar_historico(token_id):
    arq = CACHE_HIST / f"{token_id}.json"
    if arq.exists():
        return json.loads(arq.read_text())
    h = get(CLOB, {"market": token_id, "interval": "max", "fidelity": FIDELIDADE_MIN})
    arq.write_text(json.dumps(h))
    return h


def mostrar_esquema(mercados):
    from collections import Counter
    campos = Counter(k for m in mercados for k in m)
    print(f"\n{len(mercados)} mercados em cache. Campos (presença):")
    for k, c in campos.most_common():
        exemplo = next((m[k] for m in mercados if m.get(k) not in (None, "", [])), None)
        print(f"  {k:28s} {c:6d}  ex.: {str(exemplo)[:90]}")
    hs = list(CACHE_HIST.glob("*.json"))[:1]
    if hs:
        h = json.loads(hs[0].read_text())
        print(f"\nHistórico (exemplo {hs[0].name[:20]}...): chaves {list(h)[:5]}; "
              f"primeiros pontos {str(h.get('history', h))[:200]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--amostra", type=int)
    ap.add_argument("--esquema", action="store_true")
    a = ap.parse_args()
    for d in (CACHE_MERC, CACHE_HIST):
        d.mkdir(parents=True, exist_ok=True)
    if a.esquema:
        return mostrar_esquema(mercados_em_cache())
    mercados = listar_mercados(a.amostra)
    if a.amostra:
        mercados = mercados[:a.amostra]
    for i, m in enumerate(mercados):
        tk = tokens(m)
        if tk:
            baixar_historico(tk[0])  # o primeiro token é o "Yes" (conferir no esquema)
        if i % 100 == 0:
            print(f"históricos: {i}/{len(mercados)}")
    mostrar_esquema(mercados)


if __name__ == "__main__":
    main()
