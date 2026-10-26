import pickle, numpy as np, pandas as pd
import statsmodels.formula.api as smf
from benford import ler_presidente

K = ["SG_UF", "CD_MUNICIPIO", "NR_ZONA"]


def base_2022():
    d = ler_presidente("dados_tse/votacao_candidato_munzona_2022.zip", ["votacao_candidato_munzona_2022_BRASIL.csv"])
    t1 = d[d.NR_TURNO == 1]
    v1 = t1.groupby(K).QT_VOTOS_NOMINAIS.sum().rename("validos1")
    p = t1.pivot_table(index=K, columns="NR_CANDIDATO", values="QT_VOTOS_NOMINAIS", aggfunc="sum").fillna(0)
    b = pd.concat([p[22].rename("adv1"), p[13].rename("pt1"), v1], axis=1)
    t2 = d[d.NR_TURNO == 2].pivot_table(index=K, columns="NR_CANDIDATO", values="QT_VOTOS_NOMINAIS", aggfunc="sum").fillna(0)
    f = pd.concat([t2[22].rename("flavio"), t2[13].rename("lula")], axis=1)
    return b.join(f, how="inner").reset_index()


def base_2026():
    b = pickle.load(open("dados_tse/feed/base_r1_2026.pkl", "rb")).reset_index()
    b.columns = K + list(b.columns[3:])
    f = pd.read_csv("output/final_e6258_zonas.csv").rename(columns={"sg_uf": "SG_UF", "cd_municipio": "CD_MUNICIPIO", "nr_zona": "NR_ZONA"})
    return b.merge(f, on=K)


def ajusta(m):
    m = m[(m.validos1 > 0) & (m.lula + m.flavio > 0)].copy()
    m["v2"] = m.lula + m.flavio
    m["l2"] = m.lula / m.v2
    m["pt1s"] = m.pt1 / m.validos1
    m["out1s"] = (m.validos1 - m.pt1 - m.adv1) / m.validos1
    m["comp"] = np.log(m.v2 / m.validos1)
    m["tam"] = np.log(m.validos1)
    r = smf.wls("l2 ~ pt1s + out1s + I(pt1s**2) + comp + tam + C(SG_UF)", m, weights=m.v2).fit()
    m["pred"] = r.fittedvalues
    m["res"] = m.l2 - m.pred
    mad = 1.4826 * np.median(np.abs(m.res - m.res.median()))
    m["z"] = (m.res - m.res.median()) / mad
    m["votos_extra_lula"] = m.res * m.v2
    return m, r.rsquared


def resumo(nome, m, r2):
    n = len(m)
    out = {"serie": nome, "zonas": n, "R2": round(r2, 4), "desvio_tipico_pt": round(100 * 1.4826 * np.median(np.abs(m.res - m.res.median())), 2)}
    for c in (3, 4, 5):
        s = m[np.abs(m.z) > c]
        out[f">{c}dp"] = len(s)
        out[f">{c}dp pró-Lula"] = int((s.z > 0).sum())
    s4 = m[np.abs(m.z) > 4]
    out["saldo_votos_>4dp"] = int(s4.votos_extra_lula.sum())
    return out


if __name__ == "__main__":
    m26, r26 = ajusta(base_2026())
    m22, r22 = ajusta(base_2022())
    pd.set_option("display.width", 220)
    print(pd.DataFrame([resumo("2022 1T→2T", m22, r22), resumo("2026 1T→2T", m26, r26)]).to_string(index=False))
    print("\nsaldo total líquido de Lula vs previsão, zonas >4dp em 2026:", int(m26.loc[np.abs(m26.z) > 4, "votos_extra_lula"].sum()))
    print("margem final Lula:", int(m26.lula.sum() - m26.flavio.sum()))
    cols = K + ["validos1", "v2", "pt1s", "l2", "pred", "z", "votos_extra_lula"]
    top = m26.reindex(m26.z.abs().sort_values(ascending=False).index).head(20)[cols]
    print("\n20 zonas mais fora do padrão em 2026:")
    print(top.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print("\npor UF, zonas >4dp em 2026:")
    print(m26[np.abs(m26.z) > 4].groupby("SG_UF").agg(n=("z", "size"), pro_lula=("z", lambda s: (s > 0).sum()), votos=("votos_extra_lula", "sum")).sort_values("n", ascending=False).to_string())
    m26.sort_values("z").to_csv("output/zonas_residuos_2026.csv", index=False)
