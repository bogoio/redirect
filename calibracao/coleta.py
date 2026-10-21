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
GAMMA_KEYSET = "https://gamma-api.polymarket.com/markets/keyset"
CLOB = "https://clob.polymarket.com/prices-history"
LIMITE_PAGINA = 100  # máximo aceito pelo keyset
FIDELIDADE_MIN = 60  # pontos de hora em hora
PAUSA = 0.25
# A CLOB só tem histórico de mercados da era do livro de ofertas (mercados de 2022 voltam vazios; corte em fev/2023);
# mercados abaixo de US$ 1 mil de volume quase não têm negociação.
FILTRO = {"closed": "true", "end_date_min": "2023-02-01T00:00:00Z", "volume_num_min": 1000,
          "include_tag": "true"}
# A CLOB recusa janelas startTs/endTs longas (15 dias passa, 30 não): 3 janelas de 14 dias
# contadas para trás a partir do fechamento cobrem 42 dias, o bastante para o instantâneo de 30.
JANELA_DIAS, N_JANELAS = 14, 3
CAMPOS = ["id", "question", "slug", "conditionId", "category", "volumeNum", "startDate", "createdAt",
          "endDate", "closedTime", "umaResolutionStatus", "outcomes", "outcomePrices",
          "clobTokenIds", "negRisk", "groupItemTitle"]

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
    """Pagina /markets/keyset (offset é limitado a <5000; keyset usa after_cursor) e guarda
    uma página por arquivo junto com o cursor seguinte, para retomar de onde parou."""
    n, total, cursor = 0, 0, None
    while maximo is None or total < maximo:
        arq = CACHE_MERC / f"pagina_{n:06d}.json"
        if arq.exists():
            pag = json.loads(arq.read_text())
        else:
            params = {**FILTRO, "limit": LIMITE_PAGINA}
            if cursor:
                params["after_cursor"] = cursor
            r = get(GAMMA_KEYSET, params)
            pag = {"markets": [enxugar(m) for m in r.get("markets", [])], "next_cursor": r.get("next_cursor")}
            arq.write_text(json.dumps(pag))
        total += len(pag["markets"])
        n += 1
        if n % 20 == 0:
            print(f"mercados: {total}", flush=True)
        cursor = pag.get("next_cursor")
        if not pag["markets"] or not cursor:
            break
    return mercados_em_cache()


def enxugar(m):
    """Guarda só o necessário (o registro completo tem ~90 campos)."""
    d = {k: m.get(k) for k in CAMPOS}
    d["events"] = [{k: e.get(k) for k in ("id", "slug", "title", "negRisk")} for e in m.get("events") or []]
    d["tags"] = sorted({t.get("label") for t in m.get("tags") or [] if t.get("label")})
    return d


def mercados_em_cache():
    out = []
    for arq in sorted(CACHE_MERC.glob("pagina_*.json")):
        out.extend(json.loads(arq.read_text())["markets"])
    return out


def tokens(m):
    t = m.get("clobTokenIds")
    return json.loads(t) if isinstance(t, str) else (t or [])


def fim_ts(m):
    from datetime import datetime
    for k in ("closedTime", "endDate"):
        v = m.get(k)
        if v:
            v = v.replace(" ", "T").replace("+00", "+00:00") if "+00:" not in v and v.endswith("+00") else v
            return int(datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp())
    return None


def baixar_historico(m, token_id):
    """interval=max volta vazio para mercado encerrado; junta janelas de 14 dias."""
    arq = CACHE_HIST / f"{token_id}.json"
    if arq.exists():
        return json.loads(arq.read_text())
    fim = fim_ts(m)
    pontos = {}
    if fim:
        for j in range(N_JANELAS):
            b = fim + 3600 - j * JANELA_DIAS * 86400
            h = get(CLOB, {"market": token_id, "startTs": b - JANELA_DIAS * 86400, "endTs": b,
                           "fidelity": FIDELIDADE_MIN})
            for p in h.get("history", []):
                pontos[p["t"]] = p["p"]
            if j == 0 and not pontos:
                break  # sem negociação perto do fim: não insiste
    h = {"history": [{"t": t, "p": pontos[t]} for t in sorted(pontos)]}
    arq.write_text(json.dumps(h))
    return h


def priorizar(mercados, amostra_baixo, semente=2026):
    """Baixa históricos do maior volume para o menor; abaixo de US$ 100 mil (a maioria),
    só uma amostra aleatória de `amostra_baixo` mercados (semente fixa)."""
    import random
    alto = sorted((m for m in mercados if (m.get("volumeNum") or 0) >= 1e5),
                  key=lambda m: -(m.get("volumeNum") or 0))
    baixo = [m for m in mercados if (m.get("volumeNum") or 0) < 1e5]
    if amostra_baixo is not None and len(baixo) > amostra_baixo:
        baixo = random.Random(semente).sample(baixo, amostra_baixo)
    return alto + baixo


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
    ap.add_argument("--so-lista", action="store_true", help="só lista os mercados, sem históricos")
    ap.add_argument("--amostra-baixo", type=int, default=10000,
                    help="quantos mercados abaixo de US$ 100 mil baixar (amostra aleatória)")
    a = ap.parse_args()
    for d in (CACHE_MERC, CACHE_HIST):
        d.mkdir(parents=True, exist_ok=True)
    if a.esquema:
        return mostrar_esquema(mercados_em_cache())
    mercados = listar_mercados(a.amostra)
    if a.amostra:
        mercados = mercados[:a.amostra]
    if a.so_lista:
        return print(f"{len(mercados)} mercados listados")
    mercados = priorizar(mercados, a.amostra_baixo)
    for i, m in enumerate(mercados):
        tk = tokens(m)
        if tk:
            baixar_historico(m, tk[0])  # tokens seguem a ordem de outcomes; o 1º é "Yes"
        if i % 500 == 0:
            print(f"históricos: {i}/{len(mercados)} (volume atual US$ {m.get('volumeNum') or 0:,.0f})", flush=True)
    mostrar_esquema(mercados)


if __name__ == "__main__":
    main()
