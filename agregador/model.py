"""Agregador ponderado de pesquisas - 2º turno 2026 (Flávio Bolsonaro x Lula).

Uso:  python model.py [--hoje AAAA-MM-DD]
Saídas em output/.
"""
import argparse
import itertools
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = Path(__file__).parent
OUT = BASE / "output"

# Resultado oficial do 1º turno (votos válidos)
R1_FLAVIO, R1_LULA = 47.03, 45.16
R1_SHARE = 100 * R1_FLAVIO / (R1_FLAVIO + R1_LULA)  # ~51,01

DEFAULTS = dict(sd_eleicao=2.0, meia_vida=4.0, cenario="A", verita="padrao", so_top4=False,
                historico=True)
# Pseudo-observações que puxam o erro de cada instituto para a média geral (histórico)
K_ENCOLHIMENTO = 2
TOP4 = ["Veritá", "Gerp", "Futura", "Vox Brasil"]
N_SIM = 100_000
DF_T = 5
SEED = 2026


def share(f, l):
    return 100 * f / (f + l)


def house_errors(verita="padrao"):
    r1 = pd.read_csv(BASE / "polls_r1.csv")
    r1 = r1[(r1.instituto != "Veritá") | (r1.versao == verita)].copy()
    r1["share"] = share(r1.flavio, r1.lula)
    r1["house_error"] = r1.share - R1_SHARE
    r1["erro_margem"] = (r1.flavio - r1.lula) - (R1_FLAVIO - R1_LULA)
    return r1


def erros_historicos(r1):
    """Erro de cada instituto somando as pesquisas de véspera de 2014-2022
    (historico/pesquisas_vespera.csv) ao 1º turno de 2026. Viés = média encolhida
    para 0; desempenho = erro quadrático médio encolhido para o geral."""
    h = pd.read_csv(BASE / "historico" / "pesquisas_vespera.csv")[["instituto", "erro"]]
    e = pd.concat([h, r1[["instituto", "house_error"]].rename(columns={"house_error": "erro"})])
    rms_geral = np.sqrt((e.erro ** 2).mean())
    g = e.groupby("instituto").erro
    n = g.count()
    vies = g.sum() / (n + K_ENCOLHIMENTO)
    rms = np.sqrt(((e.erro ** 2).groupby(e.instituto).sum() + K_ENCOLHIMENTO * rms_geral ** 2)
                  / (n + K_ENCOLHIMENTO))
    return pd.DataFrame({"n_eleicoes": n, "vies": vies, "rms": rms}), rms_geral


def load_r2():
    r2 = pd.read_csv(BASE / "polls_r2.csv", parse_dates=["campo_inicio", "campo_fim"])
    r2["share"] = share(r2.flavio, r2.lula)
    r2["n_imputado"] = r2.n.isna()
    r2["n"] = r2.n.fillna(r2.n.median())
    r2["meio_campo"] = (r2.campo_inicio + (r2.campo_fim - r2.campo_inicio) / 2).dt.floor("h")
    return r2


def weigh(r2, r1, hoje, meia_vida, cenario, historico=False):
    he = r1.set_index("instituto").house_error
    he_default = r1.loc[r1.tradicional == 1, "house_error"].median()
    d = r2.copy()
    d["tem_r1"] = d.instituto.isin(he.index)
    d["idade_dias"] = (hoje - d.meio_campo).dt.total_seconds() / 86400
    if historico:
        hist, rms_geral = erros_historicos(r1)
        d["house_error"] = d.instituto.map(hist.vies).fillna(0.0)
        erro_tipico = d.instituto.map(hist.rms).fillna(rms_geral)
    else:
        d["house_error"] = d.instituto.map(he).fillna(he_default)
        erro_tipico = d.house_error.abs()
    d["peso_desempenho"] = 1 / (erro_tipico ** 2 + 0.5 ** 2)
    d["peso_recencia"] = np.exp(-np.log(2) * d.idade_dias / meia_vida)
    d["peso_amostra"] = np.sqrt(np.minimum(d.n, 5000) / 1000)
    d["peso"] = d.peso_desempenho * d.peso_recencia * d.peso_amostra
    d["peso_norm"] = d.peso / d.peso.sum()
    d["estimativa"] = d.share - (0.5 * d.house_error if cenario == "B" else 0)
    d["contribuicao"] = d.peso_norm * d.estimativa
    return d


def simulate(d, sd_eleicao, rng, desvio=0.0, sd_extra=0.0):
    media_pesq = (d.peso_norm * d.estimativa).sum()
    disp = np.sqrt((d.peso_norm * (d.estimativa - media_pesq) ** 2).sum())
    media = media_pesq + desvio
    sd_total = np.sqrt(sd_eleicao ** 2 + disp ** 2 + sd_extra ** 2)
    t = rng.standard_t(DF_T, N_SIM) / np.sqrt(DF_T / (DF_T - 2))  # t com dp = 1
    sims = media + sd_total * t
    q = np.percentile(sims, [2.5, 10, 50, 90, 97.5])
    return dict(media=media, dispersao=disp, sd_total=sd_total,
                p_flavio=(sims > 50).mean(), mediana=q[2],
                ic80=(q[1], q[3]), ic95=(q[0], q[4]), sims=sims)


def run(hoje, sd_eleicao, meia_vida, cenario, verita, so_top4, rng, historico=True):
    r1 = house_errors(verita)
    r2 = load_r2()
    if so_top4:
        r2 = r2[r2.instituto.isin(TOP4)]
    d = weigh(r2, r1, hoje, meia_vida, cenario, historico)
    return d, simulate(d, sd_eleicao, rng), r1


# Multiplicadores de cada lado da "malícia estrutural" (efeitos em estrutural.csv)
CENARIOS_ESTRUTURAIS = {
    "neutro": dict(direita=0.0, governo=0.0),
    "equilibrado": dict(direita=1.0, governo=1.0),
    "direita_forte": dict(direita=1.5, governo=0.5),
    "governo_forte": dict(direita=0.5, governo=1.5),
}


def estrutural(d, rng):
    """Desloca a média pelos fatores estruturais e soma a incerteza deles."""
    f = pd.read_csv(BASE / "estrutural.csv")
    linhas = []
    for nome, mult in CENARIOS_ESTRUTURAIS.items():
        m = f.lado.map(mult)
        desvio = (f.efeito * m).sum()
        sd_extra = np.sqrt(((f.dp * m) ** 2).sum())
        res = simulate(d, DEFAULTS["sd_eleicao"], rng, desvio, sd_extra)
        linhas.append(dict(cenario=nome, desvio=round(desvio, 2), sd_extra=round(sd_extra, 2),
                           media=round(res["media"], 2), ic80_inf=round(res["ic80"][0], 2),
                           ic80_sup=round(res["ic80"][1], 2), p_flavio=round(res["p_flavio"], 3)))
    return pd.DataFrame(linhas)


def mercado():
    """Última linha de mercado.csv: preço de mercado e a probabilidade calibrada pelo
    histórico de mercados resolvidos (pasta calibracao/)."""
    arq = BASE / "mercado.csv"
    if not arq.exists():
        return None
    return pd.read_csv(arq).iloc[-1]


def check_inputs(r1, r2):
    """Confere os números de entrada contra a lista do pedido."""
    assert len(r2) > 0 and r2.share.between(30, 70).all(), "polls_r2.csv vazio ou com valor fora de faixa"
    assert abs(R1_SHARE - 51.01) < 0.01
    v = r1[r1.instituto == "Veritá"].iloc[0]
    assert (v.flavio, v.lula) == (47, 45)
    print(f"Entrada OK: {len(r2)} pesquisas de 2º turno, {len(r1)} institutos no 1º turno, "
          f"participação real do Flávio no 1º turno = {R1_SHARE:.2f}%")


def plot(d, res, path):
    d = d.sort_values("meio_campo")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.axhspan(*res["ic80"], color="#4C78A8", alpha=0.15, label="Faixa de 80% (simulação)")
    ax.axhline(res["media"], color="#4C78A8", lw=2, label=f"Média ponderada {res['media']:.2f}%")
    ax.axhline(50, color="0.4", lw=1, ls="--")
    ax.scatter(d.meio_campo, d.estimativa, s=40 + 1500 * d.peso_norm,
               color="#E45756", alpha=0.6, edgecolor="k", lw=0.5)
    for _, r in d.iterrows():
        ax.annotate(r.instituto, (r.meio_campo, r.estimativa), fontsize=7,
                    xytext=(4, 4), textcoords="offset points")
    ax.set_ylabel("Participação bipartidária do Flávio (%)")
    ax.set_title("2º turno 2026 - pesquisas (tamanho = peso) e média ponderada (cenário A)")
    ax.legend(loc="lower left")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(path, dpi=150)


def fmt(res):
    return (f"{res['mediana']:.2f}% (80%: {res['ic80'][0]:.2f}-{res['ic80'][1]:.2f}; "
            f"95%: {res['ic95'][0]:.2f}-{res['ic95'][1]:.2f}) | P(Flávio>50%) = {res['p_flavio']:.1%}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hoje", default=pd.Timestamp.today().strftime("%Y-%m-%d"))
    hoje = pd.Timestamp(ap.parse_args().hoje)
    OUT.mkdir(exist_ok=True)
    rng = np.random.default_rng(SEED)

    check_inputs(house_errors(), load_r2())
    house_errors().drop(columns="versao").round(3).to_csv(OUT / "house_errors_r1.csv", index=False)

    resultados = {}
    for cen in "AB":
        d, res, _ = run(hoje, **{**DEFAULTS, "cenario": cen}, rng=rng)
        resultados[cen] = res
        cols = ["instituto", "meio_campo", "n", "n_imputado", "share", "house_error", "estimativa",
                "idade_dias", "peso_desempenho", "peso_recencia", "peso_amostra", "peso",
                "peso_norm", "contribuicao", "confianca_dado", "observacao"]
        d.sort_values("peso_norm", ascending=False)[cols].assign(meio_campo=lambda x: x.meio_campo.dt.date).round(4).to_csv(
            OUT / f"pesquisas_cenario_{cen}.csv", index=False)
        if cen == "A":
            plot(d, res, OUT / "grafico_pesquisas.png")
            estr = estrutural(d, rng)
            estr.to_csv(OUT / "cenarios_estruturais.csv", index=False)

    # Grade de sensibilidade
    linhas = []
    grade = itertools.product([1.5, 2.0, 2.5], [3, 4, 7], "AB", ["padrao", "alternativa"],
                              [False, True], [True, False])
    for sd, mv, cen, ver, top4, hist in grade:
        _, res, _ = run(hoje, sd, mv, cen, ver, top4, rng, hist)
        linhas.append(dict(sd_eleicao=sd, meia_vida=mv, cenario=cen, verita=ver,
                           amostra="só top-4" if top4 else "todas",
                           pesos="historico" if hist else "so_r1_2026",
                           media=round(res["media"], 2), p_flavio=round(res["p_flavio"], 3)))
    sens = pd.DataFrame(linhas)
    sens.to_csv(OUT / "sensibilidade_longa.csv", index=False)
    piv = sens.pivot_table(index=["pesos", "amostra", "cenario", "verita", "meia_vida"],
                           columns="sd_eleicao", values="p_flavio")
    piv.to_csv(OUT / "sensibilidade_grade.csv")

    # Qual premissa mexe mais: amplitude de P ao variar cada fator, demais no padrão
    base = sens[(sens.sd_eleicao == 2.0) & (sens.meia_vida == 4) & (sens.cenario == "A")
                & (sens.verita == "padrao") & (sens.amostra == "todas") & (sens.pesos == "historico")]
    fatores = {"sd_eleicao": [1.5, 2.0, 2.5], "meia_vida": [3, 4, 7], "cenario": ["A", "B"],
               "verita": ["padrao", "alternativa"], "amostra": ["todas", "só top-4"],
               "pesos": ["historico", "so_r1_2026"]}
    padrao = base.iloc[0]
    amp = {}
    for f, vals in fatores.items():
        m = np.ones(len(sens), bool)
        for g in fatores:
            if g != f:
                m &= sens[g] == padrao[g]
        sub = sens[m]
        amp[f] = sub.p_flavio.max() - sub.p_flavio.min()
    mais = max(amp, key=amp.get)

    a, b = resultados["A"], resultados["B"]
    resumo = [
        f"Estimativa central (A, bruto): {a['mediana']:.2f}% para Flávio na participação bipartidária; com ajuste de casa (B): {b['mediana']:.2f}%.",
        f"Intervalo A: 80% {a['ic80'][0]:.2f}-{a['ic80'][1]:.2f} | 95% {a['ic95'][0]:.2f}-{a['ic95'][1]:.2f} (dp total {a['sd_total']:.2f}, dispersão entre pesquisas {a['dispersao']:.2f}).",
        f"Intervalo B: 80% {b['ic80'][0]:.2f}-{b['ic80'][1]:.2f} | 95% {b['ic95'][0]:.2f}-{b['ic95'][1]:.2f}.",
        f"P(Flávio vence): A = {a['p_flavio']:.1%} | B = {b['p_flavio']:.1%}; na grade varia de {sens.p_flavio.min():.1%} a {sens.p_flavio.max():.1%}.",
        f"Premissa que mais mexe (variando uma de cada vez): {mais} (amplitude de {amp[mais]:.1%} em P); "
        + ", ".join(f"{k} {v:.1%}" for k, v in amp.items() if k != mais) + ".",
        "Malícia estrutural (sobre A): " + " | ".join(
            f"{r.cenario} {r.media:.2f}% / P {r.p_flavio:.1%}" for r in estr.itertuples()) + ".",
    ]
    m = mercado()
    if m is not None:
        comb = (a["p_flavio"] + m.p_calibrada) / 2
        resumo.append(
            f"Mercado ({m.fonte}, {m.data}): preço {m.preco:.1%} -> calibrado {m.p_calibrada:.1%} "
            f"(IC95 {m.ic95_inf:.1%}-{m.ic95_sup:.1%}, {m.eventos} eventos); "
            f"média modelo A + mercado calibrado = {comb:.1%}.")
    (OUT / "resumo.txt").write_text("\n".join(resumo) + "\n", encoding="utf-8")
    print(f"Data de referência: {hoje.date()}")
    print("\n".join(resumo))


if __name__ == "__main__":
    main()
