from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.formula.api as smf

d = pd.read_csv(Path(__file__).parent / "secoes_modelo.csv")
d = d[(d.v1 > 20) & (d.l2 + d.f2 > 20) & (d.modelo != "?")].copy()
d["s2"] = d.l2 / (d.l2 + d.f2)
d["l1s"] = d.l1 / d.v1
d["f1s"] = d.f1 / d.v1
d["ganho"] = 100 * (d.s2 - d.l1s / (d.l1s + d.f1s))
pd.set_option("display.width", 200)
print(f"{len(d)} seções válidas\n")
print(d.groupby("modelo").agg(secoes=("s2", "size"), lula_1T=("l1s", lambda s: round(100 * s.mean(), 1)),
                              lula_2T=("s2", lambda s: round(100 * s.mean(), 1)), ganho_bruto=("ganho", lambda s: round(s.mean(), 2))).to_string())
base = sorted(d.modelo.unique())[-1]
r = smf.wls(f"s2 ~ l1s + f1s + I(l1s**2) + C(uf) + C(modelo, Treatment('{base}'))", d, weights=d.l2 + d.f2).fit(cov_type="HC1")
print(f"\nEfeito do modelo (pts de Lula no 2T, vs {base}, controlando 1T da seção e UF):")
for k in r.params.index:
    if "modelo" in k:
        lo, hi = r.conf_int().loc[k]
        print(f"  {k.split('T.')[-1].rstrip(']')}: {100 * r.params[k]:+.2f} pt  (IC95 {100 * lo:+.2f} a {100 * hi:+.2f}, p={r.pvalues[k]:.3f})")
print(f"\nR2 = {r.rsquared:.4f}, erro típico por seção = {100 * np.sqrt(r.mse_resid / (d.l2 + d.f2).mean()):.2f} pt")
f = r.f_test(" = ".join([k for k in r.params.index if "modelo" in k]) + " = 0") if sum("modelo" in k for k in r.params.index) > 1 else None
if f is not None:
    print(f"teste conjunto (todos os modelos iguais): p={float(f.pvalue):.3f}")
