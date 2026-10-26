import zipfile, io, numpy as np, pandas as pd
from scipy.stats import chisquare

COLS = ["NR_TURNO", "SG_UF", "CD_MUNICIPIO", "NR_ZONA", "CD_CARGO", "NR_CANDIDATO", "QT_VOTOS_NOMINAIS"]


def ler_presidente(zip_path, membros):
    out = []
    with zipfile.ZipFile(zip_path) as z:
        for m in membros:
            for ch in pd.read_csv(z.open(m), sep=";", encoding="latin1", usecols=COLS, chunksize=2_000_000):
                out.append(ch[ch.CD_CARGO == 1])
    d = pd.concat(out)
    return d.groupby(["NR_TURNO", "SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_CANDIDATO"]).QT_VOTOS_NOMINAIS.sum().reset_index()


def dig(x, pos):
    s = x.astype(int).astype(str)
    s = s[s.str.len() > pos]
    return s.str[pos].astype(int)


B1 = np.log10(1 + 1 / np.arange(1, 10))
B2 = np.array([sum(np.log10(1 + 1 / (10 * k + d)) for k in range(1, 10)) for d in range(10)])


def testes(v):
    v = v[v >= 10]
    d1, d2, dl = dig(v, 0), dig(v, 1), v.astype(int) % 10
    o1 = np.bincount(d1, minlength=10)[1:]
    o2 = np.bincount(d2, minlength=10)
    ol = np.bincount(dl, minlength=10)
    p1 = chisquare(o1, B1 * o1.sum()).pvalue
    p2 = chisquare(o2, B2 * o2.sum()).pvalue
    pl = chisquare(ol).pvalue
    return dict(n=len(v), media2=round(d2.mean(), 3), p_1o_dig=p1, p_2o_dig=p2, p_ult_dig=pl)


if __name__ == "__main__":
    d22 = ler_presidente("dados_tse/votacao_candidato_munzona_2022.zip", ["votacao_candidato_munzona_2022_BRASIL.csv"])
    d26 = ler_presidente("dados_tse/votacao_candidato_munzona_2026.zip", ["votacao_candidato_munzona_2026_BRASIL.csv"])
    fin = pd.read_csv("output/final_e6258_zonas.csv")
    d26_1 = d26[d26.NR_TURNO == 1]
    top2_26 = d26_1.groupby("NR_CANDIDATO").QT_VOTOS_NOMINAIS.sum().nlargest(2).index
    linhas = []
    for nome, v in [
        ("2026 2T Lula", fin.lula), ("2026 2T Flávio", fin.flavio),
        *[(f"2026 1T cand {c}", d26_1[d26_1.NR_CANDIDATO == c].QT_VOTOS_NOMINAIS) for c in top2_26],
        *[(f"2022 2T cand {c}", d22[(d22.NR_TURNO == 2) & (d22.NR_CANDIDATO == c)].QT_VOTOS_NOMINAIS) for c in (13, 22)],
        *[(f"2022 1T cand {c}", d22[(d22.NR_TURNO == 1) & (d22.NR_CANDIDATO == c)].QT_VOTOS_NOMINAIS) for c in (13, 22)],
    ]:
        linhas.append(dict(serie=nome, **testes(v.reset_index(drop=True))))
    r = pd.DataFrame(linhas)
    pd.set_option("display.width", 200)
    print(r.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print("média esperada do 2º dígito por Benford:", round((B2 * np.arange(10)).sum(), 3))
