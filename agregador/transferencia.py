"""Transferência de votos do 1º para o 2º turno, por município (dados abertos do TSE).

Pergunta: para onde vão os votos dos candidatos eliminados no 1º turno? Regressão
ecológica por eleição (2014, 2018, 2022): o ganho de votos de cada finalista entre
os turnos, município a município, contra os votos que cada eliminado teve ali.
O coeficiente de um eliminado é a fração dos votos dele que foi para o adversário
do PT. Depois aplica faixas dessas taxas aos eliminados de 2026.

Uso:  python transferencia.py [--dados dados_tse]
Saídas em output/transferencia_*.csv.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import lsq_linear

from comparecimento import ADVERSARIO, ANOS_HIST, BASE, NR_PT, OUT, REGIAO, ler_zip

# Eliminados com voto próprio relevante em cada ano; o resto vira "outros".
# Classificação: esquerda, centro, direita (em relação ao PT x adversário).
ELIMINADOS = {
    2014: {40: ("Marina", "centro"), 50: ("Luciana Genro", "esquerda"), 20: ("Pastor Everaldo", "direita")},
    2018: {12: ("Ciro", "esquerda"), 45: ("Alckmin", "centro"), 30: ("Amoêdo", "direita"),
           51: ("Daciolo", "direita"), 15: ("Meirelles", "centro"), 18: ("Marina", "centro"),
           19: ("Alvaro Dias", "direita"), 50: ("Boulos", "esquerda")},
    2022: {15: ("Tebet", "centro"), 12: ("Ciro", "esquerda"), 44: ("Soraya", "direita"),
           30: ("Felipe D'Avila", "direita")},
}
ELIMINADOS_2026 = {70: ("Augusto Cury", "centro"), 14: ("Renan Santos", "direita"),
                   55: ("Caiado", "direita"), 30: ("Zema", "direita")}


def votos_mun(dados, ano):
    cols = {"NR_TURNO", "SG_UF", "CD_MUNICIPIO", "CD_CARGO", "NR_CANDIDATO", "QT_VOTOS_NOMINAIS"}
    df = ler_zip(dados / f"votacao_candidato_munzona_{ano}.zip", cols)
    df = df[(df.CD_CARGO == 1) & df.SG_UF.isin(REGIAO)]
    return df.pivot_table(index=["CD_MUNICIPIO", "NR_TURNO"], columns="NR_CANDIDATO",
                          values="QT_VOTOS_NOMINAIS", aggfunc="sum").fillna(0)


def ajustar_ano(dados, ano):
    v = votos_mun(dados, ano)
    r1, r2 = v.xs(1, level="NR_TURNO"), v.xs(2, level="NR_TURNO")
    r1, r2 = r1.align(r2, join="inner", axis=0)
    adv, elim = ADVERSARIO[ano], ELIMINADOS[ano]
    X = pd.DataFrame({nome: r1[nr] for nr, (nome, _) in elim.items()})
    outros = [c for c in r1.columns if c not in (NR_PT, adv, *elim)]
    X["outros"] = r1[outros].sum(axis=1)
    finalistas_r2 = r2[NR_PT] + r2[adv]
    finalistas_r1 = r1[NR_PT] + r1[adv]
    # Saldo de eleitores novos/voltando (comparecimento, brancos e nulos) não explicado pelos eliminados
    X["saldo_novos"] = finalistas_r2 - finalistas_r1 - X.sum(axis=1)
    y = r2[adv] - r1[adv]
    # Taxas restritas a [0, 1]; ponderado por 1/sqrt(eleitores) para as capitais
    # não dominarem (a variância do saldo cresce com o tamanho do município)
    w = 1 / np.sqrt(finalistas_r2.clip(lower=1).values)
    beta = lsq_linear(X.values * w[:, None], y.values * w, bounds=(0, 1)).x
    beta = pd.Series(beta, index=X.columns)
    tot = X.sum()
    linhas = [dict(ano=ano, eliminado=c, campo=next((g for n, g in elim.values() if n == c), "-"),
                   votos_r1=int(tot[c]), pct_validos_r1=round(100 * tot[c] / r1.values.sum(), 2),
                   taxa_para_adversario=round(beta[c], 3)) for c in X.columns]
    resumo = dict(ano=ano,
                  bip_adv_r1=round(100 * r1[adv].sum() / finalistas_r1.sum(), 2),
                  bip_adv_r2=round(100 * r2[adv].sum() / finalistas_r2.sum(), 2),
                  ganho_adv_pct_do_ganho_total=round(100 * y.sum() / (finalistas_r2 - finalistas_r1).sum(), 1),
                  r2_previsto_pelo_modelo=round(100 * (r1[adv].sum() + (X * beta).values.sum())
                                                / finalistas_r2.sum(), 2))
    return pd.DataFrame(linhas), resumo


def cenario_2026(dados, taxas):
    v = votos_mun(dados, 2026).xs(1, level="NR_TURNO").sum()
    fl, lu = v[22], v[NR_PT]
    elim = {nome: v[nr] for nr, (nome, _) in ELIMINADOS_2026.items()}
    outros = v.drop([22, NR_PT, *ELIMINADOS_2026]).sum()
    linhas = []
    for nome_cen, t in taxas.items():
        ganho = sum(elim[n] * t[ELIMINADOS_2026[nr][1]] for nr, (n, _) in ELIMINADOS_2026.items())
        ganho += outros * t["esquerda"]  # os demais 2026 são da esquerda pequena
        total = fl + lu + sum(elim.values()) + outros
        linhas.append(dict(cenario=nome_cen, **{f"taxa_{k}": v_ for k, v_ in t.items()},
                           flavio_bip=round(100 * (fl + ganho) / total, 2)))
    return pd.DataFrame(linhas), round(100 * fl / (fl + lu), 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dados", default=str(BASE / "dados_tse"))
    dados = Path(ap.parse_args().dados)
    OUT.mkdir(exist_ok=True)

    partes, resumos = zip(*(ajustar_ano(dados, a) for a in ANOS_HIST))
    tab = pd.concat(partes, ignore_index=True)
    res = pd.DataFrame(resumos)
    tab.to_csv(OUT / "transferencia_historico.csv", index=False)
    res.to_csv(OUT / "transferencia_resumo.csv", index=False)

    # Taxa média ponderada por votos, por campo (só eliminados com >= 1% dos válidos)
    rel = tab[(tab.campo != "-") & (tab.pct_validos_r1 >= 1)]
    por_campo = rel.groupby("campo").apply(
        lambda g: np.average(g.taxa_para_adversario, weights=g.votos_r1)).round(3)
    faixa = rel.groupby("campo").taxa_para_adversario.agg(["min", "max"]).round(3)
    taxas = {"historico_medio": por_campo.to_dict(),
             "pessimista_flavio": faixa["min"].to_dict(),
             "otimista_flavio": faixa["max"].to_dict()}
    cen, bip_r1 = cenario_2026(dados, taxas)
    cen.to_csv(OUT / "transferencia_2026.csv", index=False)

    print(tab.to_string(index=False))
    print("\nResumo por ano:\n" + res.to_string(index=False))
    print("\nTaxas por campo (média ponderada; min-max):\n" + pd.concat([por_campo.rename("media"), faixa], axis=1).to_string())
    print(f"\n2026: Flávio no 1º turno (bipartidário) = {bip_r1}%")
    print(cen.to_string(index=False))


if __name__ == "__main__":
    main()
