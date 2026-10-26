"""Estudo de comparecimento entre 1º e 2º turno, por município (dados abertos do TSE).

Pergunta: o comparecimento do 2º turno cresce mais onde o PT é forte? Se sim,
quanto isso desloca a participação bipartidária do Flávio em 2026?

Dados (baixar de https://dadosabertos.tse.jus.br e colocar em agregador/dados_tse/):
  detalhe_votacao_munzona_AAAA.zip      (comparecimento por município/zona)
  votacao_candidato_munzona_AAAA.zip    (votos por candidato por município/zona)
para AAAA = 2014, 2018, 2022 e 2026.

Uso:  python comparecimento.py [--dados dados_tse]
Saídas em output/comparecimento_*.csv e uma sugestão de linha para estrutural.csv.
"""
import argparse
import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).parent
OUT = BASE / "output"

ANOS_HIST = [2014, 2018, 2022]
ANO_ALVO = 2026
CARGO_PRESIDENTE = 1
NR_PT = 13
# Número do adversário do PT em cada 2º turno
ADVERSARIO = {2014: 45, 2018: 17, 2022: 22, 2026: 22}
REGIAO = {
    **dict.fromkeys(["AC", "AM", "AP", "PA", "RO", "RR", "TO"], "N"),
    **dict.fromkeys(["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"], "NE"),
    **dict.fromkeys(["DF", "GO", "MS", "MT"], "CO"),
    **dict.fromkeys(["ES", "MG", "RJ", "SP"], "SE"),
    **dict.fromkeys(["PR", "RS", "SC"], "S"),
}


def ler_zip(path, colunas):
    """Lê o CSV nacional do zip do TSE (ou concatena os por UF)."""
    with zipfile.ZipFile(path) as z:
        nomes = [n for n in z.namelist() if n.lower().endswith(".csv")]
        brasil = [n for n in nomes if "BRASIL" in n.upper()]
        alvo = brasil or nomes
        partes = []
        for n in alvo:
            with z.open(n) as f:
                df = pd.read_csv(io.TextIOWrapper(f, encoding="latin-1"), sep=";",
                                 usecols=lambda c: c in colunas, low_memory=False)
                partes.append(df)
    return pd.concat(partes, ignore_index=True)


def comparecimento(dados, ano):
    cols = {"NR_TURNO", "SG_UF", "CD_MUNICIPIO", "CD_CARGO", "QT_APTOS", "QT_COMPARECIMENTO"}
    df = ler_zip(dados / f"detalhe_votacao_munzona_{ano}.zip", cols)
    df = df[(df.CD_CARGO == CARGO_PRESIDENTE) & df.SG_UF.isin(REGIAO)]
    g = df.groupby(["CD_MUNICIPIO", "SG_UF", "NR_TURNO"], as_index=False)[["QT_APTOS", "QT_COMPARECIMENTO"]].sum()
    g["taxa"] = g.QT_COMPARECIMENTO / g.QT_APTOS
    return g.pivot_table(index=["CD_MUNICIPIO", "SG_UF"], columns="NR_TURNO",
                         values=["QT_APTOS", "taxa"]).pipe(_achatar)


def votos(dados, ano):
    cols = {"NR_TURNO", "SG_UF", "CD_MUNICIPIO", "CD_CARGO", "NR_CANDIDATO",
            "QT_VOTOS_NOMINAIS", "QT_VOTOS_NOMINAIS_VALIDOS"}
    df = ler_zip(dados / f"votacao_candidato_munzona_{ano}.zip", cols)
    col = "QT_VOTOS_NOMINAIS_VALIDOS" if "QT_VOTOS_NOMINAIS_VALIDOS" in df else "QT_VOTOS_NOMINAIS"
    df = df[(df.CD_CARGO == CARGO_PRESIDENTE) & (df.NR_TURNO == 1)
            & df.NR_CANDIDATO.isin([NR_PT, ADVERSARIO[ano]])]
    g = df.pivot_table(index="CD_MUNICIPIO", columns="NR_CANDIDATO", values=col, aggfunc="sum").fillna(0)
    return pd.DataFrame({"pt_r1": g[NR_PT] / (g[NR_PT] + g[ADVERSARIO[ano]]),
                         "votos_finalistas_r1": g[NR_PT] + g[ADVERSARIO[ano]]})


def _achatar(p):
    p.columns = [f"{a}_{b}" for a, b in p.columns]
    return p.reset_index()


def base_municipal(dados, ano, precisa_r2=True):
    c = comparecimento(dados, ano)
    d = c.merge(votos(dados, ano), left_on="CD_MUNICIPIO", right_index=True)
    d["ano"] = ano
    d["regiao"] = d.SG_UF.map(REGIAO)
    d["abst_r1"] = 1 - d.taxa_1
    d["log_aptos"] = np.log(d.QT_APTOS_1)
    if precisa_r2:
        d["delta"] = d.taxa_2 - d.taxa_1
    return d.dropna(subset=["pt_r1", "taxa_1"])


def matriz(d, anos_fe):
    X = pd.DataFrame({"const": 1.0, "pt_r1": d.pt_r1 - 0.5, "abst_r1": d.abst_r1,
                      "log_aptos": d.log_aptos}, index=d.index)
    for r in ["N", "NE", "CO", "S"]:  # SE é a referência
        X[f"reg_{r}"] = (d.regiao == r).astype(float)
    for a in anos_fe[1:]:
        X[f"ano_{a}"] = (d.ano == a).astype(float)
    return X


def ajustar(hist):
    anos = sorted(hist.ano.unique())
    X = matriz(hist, anos)
    w = np.sqrt(hist.QT_APTOS_1.values)
    beta, *_ = np.linalg.lstsq(X.values * w[:, None], hist.delta.values * w, rcond=None)
    return pd.Series(beta, index=X.columns), anos


def prever(alvo, beta, anos, efeito_ano=None):
    """Prevê delta por município. efeito_ano escolhe o nível de um ano histórico
    (None = média dos efeitos de ano)."""
    X = matriz(alvo.assign(ano=anos[0]), anos)
    fe = [0.0] + [beta[f"ano_{a}"] for a in anos[1:]]
    nivel = np.mean(fe) if efeito_ano is None else fe[anos.index(efeito_ano)]
    cols = [c for c in X.columns if not c.startswith("ano_")]
    return X[cols].values @ beta[cols].values + nivel


def deslocamento(alvo, delta):
    """Variação da participação bipartidária do adversário do PT (Flávio) causada
    pelo comparecimento extra, supondo que os novos eleitores votam como o município."""
    taxa_r1 = alvo.taxa_1.values
    validos_por_comp = alvo.votos_finalistas_r1.values / (alvo.QT_APTOS_1.values * taxa_r1)
    extra = alvo.QT_APTOS_1.values * delta * validos_por_comp
    pt0 = (alvo.pt_r1 * alvo.votos_finalistas_r1).sum()
    tot0 = alvo.votos_finalistas_r1.sum()
    pt1 = pt0 + (alvo.pt_r1.values * extra).sum()
    tot1 = tot0 + extra.sum()
    return 100 * ((1 - pt1 / tot1) - (1 - pt0 / tot0))


def backtest(hist):
    """Ajusta sem um ano e prevê o deslocamento dele; compara com o observado."""
    linhas = []
    for a in sorted(hist.ano.unique()):
        treino, teste = hist[hist.ano != a], hist[hist.ano == a]
        beta, anos = ajustar(treino)
        prev = deslocamento(teste, prever(teste, beta, anos))
        obs = deslocamento(teste, teste.delta.values)
        linhas.append(dict(ano_testado=a, deslocamento_previsto=round(prev, 3),
                           deslocamento_observado=round(obs, 3)))
    return pd.DataFrame(linhas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dados", default=str(BASE / "dados_tse"))
    dados = Path(ap.parse_args().dados)
    faltando = [f"{p}_{a}.zip" for a in ANOS_HIST + [ANO_ALVO]
                for p in ("detalhe_votacao_munzona", "votacao_candidato_munzona")
                if not (dados / f"{p}_{a}.zip").exists()]
    if faltando:
        raise SystemExit(f"Arquivos ausentes em {dados}:\n  " + "\n  ".join(faltando))
    OUT.mkdir(exist_ok=True)

    hist = pd.concat([base_municipal(dados, a) for a in ANOS_HIST], ignore_index=True)
    alvo = base_municipal(dados, ANO_ALVO, precisa_r2=False)

    beta, anos = ajustar(hist)
    beta.round(5).to_csv(OUT / "comparecimento_coeficientes.csv", header=["coef"])
    bt = backtest(hist)
    bt.to_csv(OUT / "comparecimento_backtest.csv", index=False)

    # Um cenário por nível histórico de comparecimento + a média
    cenarios = {f"nivel_{a}": a for a in anos} | {"media": None}
    res = pd.DataFrame([dict(cenario=k, deslocamento_flavio=round(
        deslocamento(alvo, prever(alvo, beta, anos, v)), 3)) for k, v in cenarios.items()])
    res.to_csv(OUT / "comparecimento_2026.csv", index=False)

    # Previsão por município (nível médio dos anos)
    mun = alvo[["CD_MUNICIPIO", "SG_UF", "regiao", "QT_APTOS_1", "taxa_1", "pt_r1"]].copy()
    mun["delta_previsto"] = prever(alvo, beta, anos)
    mun["comparecimento_r2_previsto"] = mun.taxa_1 + mun.delta_previsto
    mun.round(4).sort_values("QT_APTOS_1", ascending=False).to_csv(
        OUT / "comparecimento_municipios_2026.csv", index=False)

    central = res.loc[res.cenario == "media", "deslocamento_flavio"].item()
    erro_bt = (bt.deslocamento_previsto - bt.deslocamento_observado).abs().mean()
    dp = float(np.hypot(res.deslocamento_flavio.std(ddof=0), erro_bt))

    print("Coeficiente de pt_r1 (delta de comparecimento por 100% de PT):", round(beta.pt_r1, 4))
    print("Backtest:\n" + bt.to_string(index=False))
    print("Cenários 2026:\n" + res.to_string(index=False))
    print(f"\nSugestão para estrutural.csv (substitui comparecimento_nordeste):\n"
          f"comparecimento_estimado,{'direita' if central > 0 else 'governo'},{central:.2f},{dp:.2f},"
          f"estimado por comparecimento.py (média dos níveis {anos[0]}-{anos[-1]})")


if __name__ == "__main__":
    main()
