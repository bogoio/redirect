"""Chuva no dia da eleição x comparecimento, por município.

Pergunta: quando chove mais no 2º turno do que choveu no 1º, o comparecimento cai? Quanto
isso deslocaria a participação do Flávio em 2026 com a previsão de chuva de domingo?

Dados:
  chuva histórica: NASA POWER (PRECTOTCORR, mm/dia, grade de 0,5° x 0,625°), modo regional
  previsão 2026:   Open-Meteo (precipitation_sum do dia 25/10), por capital
  municípios:      dados_tse/chuva/municipios_ibge.csv (coordenadas) e mun-e006258-cm.json
                   (código TSE -> IBGE)

Uso:  python chuva.py
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from comparecimento import BASE, OUT, REGIAO, base_municipal, deslocamento

DIR = BASE / "dados_tse" / "chuva"
DATAS = {2014: ("20141005", "20141026"), 2018: ("20181007", "20181028"),
         2022: ("20221002", "20221030"), 2026: ("20261004", None)}
POWER = "https://power.larc.nasa.gov/api/temporal/daily/regional"
BLOCOS = [(lo, la) for lo in (-74, -64, -54, -44) for la in (-34, -24, -14, -4)]  # 10° x 10°


def grade(data):
    """Chuva do dia em toda a grade que cobre o Brasil (cache por data)."""
    arq = DIR / f"power_{data}.json"
    if arq.exists():
        return pd.read_json(arq)
    pts = []
    for lo, la in BLOCOS:
        for t in range(4):
            r = requests.get(POWER, params={"parameters": "PRECTOTCORR", "community": "AG",
                                            "longitude-min": lo, "longitude-max": lo + 10,
                                            "latitude-min": la, "latitude-max": min(la + 10, 6),
                                            "start": data, "end": data, "format": "JSON"}, timeout=120)
            if r.status_code == 200:
                break
            time.sleep(2 ** t)
        for f in r.json().get("features", []):
            lon, lat = f["geometry"]["coordinates"][:2]
            v = f["properties"]["parameter"]["PRECTOTCORR"][data]
            pts.append(dict(lon=lon, lat=lat, mm=max(v, 0) if v != -999 else np.nan))
    g = pd.DataFrame(pts).drop_duplicates(["lon", "lat"])
    g.to_json(arq)
    return g


def municipios():
    ibge = pd.read_csv(DIR / "municipios_ibge.csv")
    cfg = json.loads((DIR / "mun-e006258-cm.json").read_text())
    tse = pd.DataFrame([dict(CD_MUNICIPIO=int(m["cd"]), codigo_ibge=int(m["cdi"]))
                        for a in cfg["abr"] if a["cd"] != "zz" for m in a["mu"]])
    return tse.merge(ibge[["codigo_ibge", "latitude", "longitude"]], on="codigo_ibge")


def chuva_mun(mun, g):
    """Ponto da grade mais próximo de cada município."""
    gl = g.dropna()
    d = (mun.latitude.values[:, None] - gl.lat.values) ** 2 + \
        ((mun.longitude.values[:, None] - gl.lon.values) * np.cos(np.radians(mun.latitude.values[:, None]))) ** 2
    return gl.mm.values[d.argmin(axis=1)]


def previsao_capitais():
    """Previsão do dia 25/10 nas 27 capitais (Open-Meteo, uma chamada)."""
    ibge = pd.read_csv(DIR / "municipios_ibge.csv")
    cap = ibge[ibge.capital == 1]
    r = requests.get("https://api.open-meteo.com/v1/forecast", timeout=60, params={
        "latitude": ",".join(map(str, cap.latitude)), "longitude": ",".join(map(str, cap.longitude)),
        "daily": "precipitation_sum", "timezone": "America/Sao_Paulo",
        "start_date": "2026-10-25", "end_date": "2026-10-25"}).json()
    return pd.DataFrame(dict(lat=cap.latitude.values, lon=cap.longitude.values,
                             mm=[x["daily"]["precipitation_sum"][0] for x in r], nome=cap.nome.values))


def main():
    dados = BASE / "dados_tse"
    mun = municipios()
    hist = []
    for ano in (2014, 2018, 2022):
        d = base_municipal(dados, ano).merge(mun, on="CD_MUNICIPIO")
        d["chuva1"] = chuva_mun(d, grade(DATAS[ano][0]))
        d["chuva2"] = chuva_mun(d, grade(DATAS[ano][1]))
        hist.append(d)
    h = pd.concat(hist, ignore_index=True)
    h["dchuva"] = np.log1p(h.chuva2) - np.log1p(h.chuva1)
    h["chuva_forte"] = (h.chuva2 >= 20).astype(float) - (h.chuva1 >= 20).astype(float)

    # delta comparecimento ~ efeito de ano x UF + chuva (ponderado pelo eleitorado)
    linhas = []
    for var in ["dchuva", "chuva_forte"]:
        X = pd.get_dummies(h.ano.astype(str) + h.SG_UF, dtype=float)
        X[var] = h[var]
        w = np.sqrt(h.QT_APTOS_1.values)
        beta, *_ = np.linalg.lstsq(X.values * w[:, None], h.delta.values * w, rcond=None)
        res = h.delta.values - X.values @ beta
        # erro-padrão agrupado por UF-ano (chuva é correlacionada no espaço)
        g = (h.ano.astype(str) + h.SG_UF).values
        XtWX = np.linalg.pinv((X.values * w[:, None] ** 2).T @ X.values)
        meat = sum(np.outer(s, s) for s in (pd.DataFrame(X.values * (w ** 2 * res)[:, None]).groupby(g).sum().values))
        ep = np.sqrt((XtWX @ meat @ XtWX)[-1, -1])
        linhas.append(dict(variavel=var, coef=beta[-1], ep=ep, t=beta[-1] / ep))
    coefs = pd.DataFrame(linhas)

    # 2026: previsão por capital, aplicada a cada município pela capital mais próxima
    alvo = base_municipal(dados, 2026, precisa_r2=False).merge(mun, on="CD_MUNICIPIO")
    # A chuva da NASA para 2026 ainda é preliminar e vem com valores impossíveis (centenas de
    # mm/dia); como referência do 1º turno usa-se (a) nenhuma chuva e (b) a média dos 1º turnos
    # de 2014-2022 no município.
    media_1t = h.groupby("CD_MUNICIPIO").chuva1.mean()
    arq_prev = DIR / "previsao_25out.csv"
    prev = pd.read_csv(arq_prev) if arq_prev.exists() else previsao_capitais()
    prev.to_csv(arq_prev, index=False)
    alvo["chuva2"] = chuva_mun(alvo, prev)
    b = coefs.set_index("variavel").coef
    ep = coefs.set_index("variavel").ep["dchuva"]
    resultados = {}
    for ref, c1 in {"1º turno seco": 0.0,
                    "1º turno com chuva média de 2014-2022": alvo.CD_MUNICIPIO.map(media_1t).fillna(0)}.items():
        alvo["chuva1"] = c1
        alvo["delta_chuva"] = b["dchuva"] * (np.log1p(alvo.chuva2) - np.log1p(alvo.chuva1))
        efeito = deslocamento(alvo, alvo.delta_chuva.values)
        faixa = [deslocamento(alvo, (alvo.delta_chuva * (b["dchuva"] + k * ep) / b["dchuva"]).values)
                 for k in (-1.96, 1.96)]
        resultados[ref] = (efeito, min(faixa), max(faixa))

    OUT.mkdir(exist_ok=True)
    coefs.round(5).to_csv(OUT / "chuva_coeficientes.csv", index=False)
    prev.round(1).to_csv(OUT / "chuva_previsao_capitais.csv", index=False)
    por_reg = alvo.groupby("regiao").apply(lambda x: pd.Series({
        "chuva_1t_media_mm": np.average(x.CD_MUNICIPIO.map(media_1t).fillna(0), weights=x.QT_APTOS_1),
        "chuva_prevista_mm": np.average(x.chuva2, weights=x.QT_APTOS_1),
        "delta_comparecimento_pp_vs_seco": 100 * b["dchuva"] * np.average(np.log1p(x.chuva2), weights=x.QT_APTOS_1)}),
        include_groups=False)
    print("Coeficientes (delta comparecimento 2º-1º turno; 2014-2022, efeito fixo ano x UF):")
    print(coefs.round(5).to_string(index=False))
    print("\n2026, por região (média ponderada pelo eleitorado):\n" + por_reg.round(2).to_string())
    for ref, (e, lo, hi) in resultados.items():
        print(f"Efeito da chuva prevista na participação do Flávio ({ref}): {e:+.3f} pontos "
              f"(IC 95% {lo:+.3f} a {hi:+.3f})")


if __name__ == "__main__":
    main()
