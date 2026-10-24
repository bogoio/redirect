"""Projeção do resultado do 2º turno durante a apuração, cruzando cada zona eleitoral já
apurada com o 1º turno da mesma zona.

Ideia: o total parcial depende da ordem em que as urnas chegam (Sul e Sudeste primeiro,
Nordeste depois). Comparar cada zona consigo mesma no 1º turno elimina esse efeito: mede-se
o deslocamento ("swing") da participação do candidato da direita entre os turnos nas zonas
já apuradas, por UF quando a UF já tem zonas suficientes, e aplica-se esse swing às zonas
que faltam.

Uso:
  python projecao.py --backtest                  # simula a apuração de 2022 (1º -> 2º turno)
  python projecao.py --parcial parcial.csv       # domingo: projeta a partir das zonas apuradas
     parcial.csv: sg_uf,cd_municipio,nr_zona,flavio,lula  (votos do 2º turno por zona)
"""
import argparse
import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from comparecimento import REGIAO

BASE = Path(__file__).parent
DADOS = BASE / "dados_tse"
OUT = BASE / "output"
CHAVE = ["SG_UF", "CD_MUNICIPIO", "NR_ZONA"]
ADVERSARIO = {2022: 22, 2026: 22}
NR_PT = 13
MIN_ZONAS_UF = 5          # swing próprio da UF a partir de 5 zonas apuradas ...
MIN_FRACAO_UF = 0.03      # ... que somem 3% dos votos da UF no 1º turno
N_BOOT = 100
SEMENTE = 2026


def ler_votos(ano):
    """Votos para presidente por zona e turno: adversário do PT, PT e total de válidos."""
    with zipfile.ZipFile(DADOS / f"votacao_candidato_munzona_{ano}.zip") as z:
        nome = next(n for n in z.namelist() if "BRASIL" in n.upper())
        cols = CHAVE + ["NR_TURNO", "CD_CARGO", "NR_CANDIDATO", "QT_VOTOS_NOMINAIS"]
        df = pd.read_csv(io.TextIOWrapper(z.open(nome), encoding="latin-1"), sep=";",
                         usecols=cols, low_memory=False)
    df = df[(df.CD_CARGO == 1) & df.SG_UF.isin(REGIAO)]
    adv = ADVERSARIO[ano]
    df["quem"] = np.select([df.NR_CANDIDATO == adv, df.NR_CANDIDATO == NR_PT], ["adv", "pt"], "outros")
    t = df.pivot_table(index=CHAVE + ["NR_TURNO"], columns="quem", values="QT_VOTOS_NOMINAIS",
                       aggfunc="sum", fill_value=0).reset_index()
    t["validos"] = t[["adv", "pt", "outros"]].sum(axis=1) if "outros" in t else t.adv + t.pt
    return t


def base_r1(votos):
    b = votos[votos.NR_TURNO == 1].set_index(CHAVE)
    out = pd.DataFrame({"adv1": b.adv, "pt1": b.pt, "validos1": b.validos})
    out["s1"] = out.adv1 / (out.adv1 + out.pt1)
    out["regiao"] = out.index.get_level_values("SG_UF").map(REGIAO)
    return out[out.adv1 + out.pt1 > 0]


def projetar(b, parcial, boot=True):
    """b: base do 1º turno por zona. parcial: zonas apuradas com adv2 e pt2 (índice CHAVE).
    Devolve participação projetada do adversário do PT, a parcial ingênua e o IC 90%."""
    p = parcial.join(b, how="inner")
    p = p[p.adv2 + p.pt2 > 0]
    if p.empty:
        return dict(ingenua=np.nan, projecao=np.nan, ic90=(np.nan, np.nan), zonas=0)
    ingenua = p.adv2.sum() / (p.adv2 + p.pt2).sum()

    tot_uf = b.groupby(level="SG_UF").validos1.sum()

    def uma(p, w=None):
        """w: pesos de reamostragem das zonas (bootstrap bayesiano); só mexem no swing."""
        p = p.assign(v2=p.adv2 + p.pt2, uf=p.index.get_level_values("SG_UF"))
        p = p.assign(swv=(p.adv2 / p.v2 - p.s1) * p.v2)  # swing ponderado pelos votos
        if w is not None:
            p = p.assign(swv=p.swv * w, v2w=p.v2 * w)
        else:
            p = p.assign(v2w=p.v2)
        nac = p.swv.sum() / p.v2w.sum()
        k_nac = p.v2.sum() / p.validos1.sum()
        g_reg = p.groupby("regiao")[["swv", "v2w"]].sum()
        reg = g_reg.swv / g_reg.v2w
        g_uf = p.groupby("uf").agg(swv=("swv", "sum"), v2=("v2", "sum"), v2w=("v2w", "sum"),
                                   val1=("validos1", "sum"), n=("v2", "size"))
        ok = (g_uf.val1 / tot_uf.reindex(g_uf.index) >= MIN_FRACAO_UF) & (g_uf.n >= MIN_ZONAS_UF)
        sw_uf = (g_uf.swv / g_uf.v2w)[ok]
        k_uf = g_uf.v2 / g_uf.val1
        falta = b.drop(p.index, errors="ignore")
        uf = pd.Series(falta.index.get_level_values("SG_UF"), index=falta.index)
        sw = uf.map(sw_uf).fillna(falta.regiao.map(reg)).fillna(nac)
        k = uf.map(k_uf).fillna(k_nac)
        v = falta.validos1 * k
        adv = p.adv2.sum() + (v * (falta.s1 + sw).clip(0, 1)).sum()
        return adv / (p.v2.sum() + v.sum())

    proj = uma(p)
    ic = (np.nan, np.nan)
    if boot:
        rng = np.random.default_rng(SEMENTE)
        sims = [uma(p, rng.dirichlet(np.ones(len(p))) * len(p)) for _ in range(N_BOOT)]
        ic = tuple(np.percentile(sims, [5, 95]))
    return dict(ingenua=ingenua, projecao=proj, ic90=ic, zonas=len(p))


# ---------- backtest em 2022 ----------

ORDENS = {
    # Sul, Sudeste e Centro-Oeste apuram primeiro, Norte e Nordeste depois (com ruído)
    "realista": {"S": 0, "SE": 0.5, "CO": 0.7, "N": 1.6, "NE": 2.0},
    "aleatória": None,
    "Nordeste primeiro": {"NE": 0, "N": 0.4, "CO": 1.2, "SE": 1.6, "S": 2.0},
}
MARCOS = [0.01, 0.02, 0.05, 0.10, 0.20, 0.50]


def backtest():
    votos = ler_votos(2022)
    b = base_r1(votos)
    r2 = votos[votos.NR_TURNO == 2].set_index(CHAVE)
    r2 = pd.DataFrame({"adv2": r2.adv, "pt2": r2.pt}).reindex(b.index).dropna()
    final = r2.adv2.sum() / (r2.adv2 + r2.pt2).sum()
    rng = np.random.default_rng(SEMENTE)
    linhas = []
    for nome, pesos in ORDENS.items():
        ruido = rng.random(len(r2))
        chave = ruido if pesos is None else r2.index.get_level_values("SG_UF").map(REGIAO).map(pesos) + ruido
        ordem = r2.iloc[np.argsort(np.asarray(chave, float))]
        acum = (ordem.adv2 + ordem.pt2).cumsum() / (ordem.adv2 + ordem.pt2).sum()
        for marco in MARCOS:
            parcial = ordem[acum.values <= marco]
            r = projetar(b, parcial)
            linhas.append(dict(ordem=nome, apurado=f"{marco:.0%}", zonas=r["zonas"],
                               parcial_ingenua=100 * r["ingenua"], projecao=100 * r["projecao"],
                               ic90_inf=100 * r["ic90"][0], ic90_sup=100 * r["ic90"][1],
                               final=100 * final, erro_ingenua=100 * (r["ingenua"] - final),
                               erro_projecao=100 * (r["projecao"] - final)))
    t = pd.DataFrame(linhas).round(2)
    OUT.mkdir(exist_ok=True)
    t.to_csv(OUT / "projecao_backtest_2022.csv", index=False)
    print("Backtest 2022 (participação de Bolsonaro entre os dois; final real "
          f"{100 * final:.2f}%):\n" + t.drop(columns="final").to_string(index=False))


def ao_vivo(arq):
    b = base_r1(ler_votos(2026))
    p = pd.read_csv(arq).rename(columns={"sg_uf": "SG_UF", "cd_municipio": "CD_MUNICIPIO", "nr_zona": "NR_ZONA",
                                         "flavio": "adv2", "lula": "pt2"}).set_index(CHAVE)
    r = projetar(b, p)
    print(f"Zonas apuradas: {r['zonas']} de {len(b)}")
    print(f"Parcial (só zonas apuradas): Flávio {100 * r['ingenua']:.2f}%")
    print(f"Projeção (swing por zona sobre o 1º turno): Flávio {100 * r['projecao']:.2f}% "
          f"(IC 90% {100 * r['ic90'][0]:.2f}-{100 * r['ic90'][1]:.2f})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backtest", action="store_true")
    ap.add_argument("--parcial")
    a = ap.parse_args()
    if a.backtest:
        backtest()
    if a.parcial:
        ao_vivo(a.parcial)


if __name__ == "__main__":
    main()
