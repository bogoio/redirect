"""Calibração do Polymarket a partir do cache de coleta.py.

Uso:  python analise.py
Saídas em output/.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from math import erf, sqrt

from coleta import CACHE_HIST, fim_ts, mercados_em_cache, tokens

BASE = Path(__file__).parent
OUT = BASE / "output"

MIN_PONTOS = 5
LIMIAR = 0.98            # "momento do evento": preço > 0,98 ou < 0,02 ...
SUSTENTADO_H = 12        # ... por pelo menos 12 horas seguidas
DEFASAGEM_MAX_H = 48     # instantâneo vale só se houver ponto até 48 h antes do instante
PRAZOS = {"24h": 1, "3d": 3, "7d": 7, "30d": 30}
FAIXAS = [0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95, 0.99]
ROTULOS = ["50-60", "60-70", "70-80", "80-85", "85-90", "90-95", "95-99"]
VOLUMES = [0, 1e5, 1e6, 1e7, np.inf]
ROT_VOL = ["<100 mil", "100 mil-1 mi", "1-10 mi", ">10 mi"]
# Política: tag com estes rótulos ou palavra-chave na pergunta
TAGS_POL = {"politics", "elections", "election", "u.s. politics", "global elections", "world elections",
            "us election", "geopolitics", "trump", "biden", "congress", "senate"}
PALAVRAS_POL = ["election", "elected", "president", "presidential", "senate", "governor", "prime minister",
                "parliament", "congress", "nominee", "nomination", "primary", "vote", "mayor", "chancellor",
                "trump", "biden", "harris", "democrat", "republican", "minister", "referendum", "cabinet"]


# ---------- carga e limpeza ----------

def parse(v):
    return json.loads(v) if isinstance(v, str) else v


def carregar():
    linhas, motivos = [], {}

    def descarta(m):
        motivos[m] = motivos.get(m, 0) + 1

    for m in mercados_em_cache():
        out, pr, tk = parse(m["outcomes"]), parse(m["outcomePrices"]), tokens(m)
        # Binário = 2 resultados (Yes/No ou dois lados, ex. times); o 1º token faz o papel do "Yes"
        if not out or len(out) != 2 or not tk:
            descarta("não binário"); continue
        pr = [float(x) for x in pr]
        if not (max(pr) > 0.99 and min(pr) < 0.01):  # preço final pode vir 0,99999...
            descarta("resolução não 1/0 (inválido, 50/50, cancelado)"); continue
        arq = CACHE_HIST / f"{tk[0]}.json"
        if not arq.exists():
            descarta("histórico não baixado (fora da amostra < US$ 100 mil)"); continue
        h = json.loads(arq.read_text())["history"]
        if len(h) < MIN_PONTOS:
            descarta(f"histórico com menos de {MIN_PONTOS} pontos"); continue
        ev = (m.get("events") or [{}])[0]
        tags = {t.lower() for t in m.get("tags") or []}
        q = m["question"].lower()
        politica = bool(tags & TAGS_POL) or any(p in q for p in PALAVRAS_POL)
        fim = fim_ts({"endDate": m.get("endDate")}) or fim_ts(m)
        linhas.append(dict(id=m["id"], question=m["question"], evento=ev.get("id") or f"m{m['id']}",
                           evento_titulo=ev.get("title"), neg_risk=bool(ev.get("negRisk") or m.get("negRisk")),
                           volume=float(m.get("volumeNum") or 0), yes_venceu=pr[0] > 0.99,
                           fim=fim, categoria="política" if politica else "outros",
                           t=np.array([p["t"] for p in h]), p=np.array([p["p"] for p in h])))
    return linhas, motivos


def momento_evento(t, p, fim):
    """Primeiro instante em que o preço passa de 0,98 (ou fica abaixo de 0,02) e fica
    assim por SUSTENTADO_H horas; ou a data de fim, o que vier primeiro."""
    fora = (p > LIMIAR) | (p < 1 - LIMIAR)
    lado = np.sign(p - 0.5)
    for i in np.flatnonzero(fora):
        j = (t >= t[i]) & (t <= t[i] + SUSTENTADO_H * 3600)
        if t[j][-1] - t[i] >= (SUSTENTADO_H - 2) * 3600 and fora[j].all() and (lado[j] == lado[i]).all():
            return min(t[i], fim) if fim else t[i]
    return fim if fim else t[-1]


def preco_em(t, p, instante):
    k = np.searchsorted(t, instante, side="right") - 1
    if k < 0 or instante - t[k] > DEFASAGEM_MAX_H * 3600:
        return np.nan
    return p[k]


# ---------- instantâneos ----------

def instantaneos(linhas):
    """Uma linha por mercado e prazo: preço do Yes no instante."""
    reg = []
    for m in linhas:
        ev_ts = momento_evento(m["t"], m["p"], m["fim"])
        for nome, dias in PRAZOS.items():
            inst = ev_ts - dias * 86400
            px = preco_em(m["t"], m["p"], inst)
            if not np.isnan(px):
                # Atividade antes do instante (proxy de liquidez sem olhar o futuro): horas
                # com mudança de preço nos 7 dias anteriores
                j = (m["t"] > inst - 7 * 86400) & (m["t"] <= inst)
                atividade = int((np.diff(m["p"][j]) != 0).sum()) if j.sum() > 1 else 0
                reg.append(dict(id=m["id"], question=m["question"], evento=m["evento"], neg_risk=m["neg_risk"],
                                volume=m["volume"], categoria=m["categoria"], yes_venceu=m["yes_venceu"],
                                prazo=nome, momento=pd.to_datetime(ev_ts, unit="s"), p_yes=px,
                                atividade=atividade))
    return pd.DataFrame(reg)


def favorito_por_mercado(s):
    """Versão 'todos os contratos': em cada mercado, o favorito é o lado acima de 50%."""
    d = s[s.p_yes != 0.5].copy()
    yes_fav = d.p_yes > 0.5
    d["preco_fav"] = np.where(yes_fav, d.p_yes, 1 - d.p_yes)
    d["fav_venceu"] = np.where(yes_fav, d.yes_venceu, ~d.yes_venceu)
    return d


def favorito_por_evento(s):
    """Versão por evento: com vários candidatos (negRisk), o favorito é o contrato de maior
    preço do Yes no instante; nos demais grupos, fica um mercado por evento (o de maior
    volume) com o favorito binário."""
    linhas = []
    for (ev, prazo), g in s.groupby(["evento", "prazo"]):
        if g.neg_risk.iloc[0] and len(g) > 1:
            r = g.loc[g.p_yes.idxmax()].copy()
            r["preco_fav"], r["fav_venceu"] = r.p_yes, r.yes_venceu
            r["volume"] = g.volume.sum()
            linhas.append(r)
        else:
            r = favorito_por_mercado(g.loc[[g.volume.idxmax()]])
            if len(r):
                linhas.append(r.iloc[0])
    return pd.DataFrame(linhas)


# ---------- estatística ----------

def wilson(k, n, z=1.96):
    if n == 0:
        return np.nan, np.nan
    f = k / n
    c = (f + z * z / (2 * n)) / (1 + z * z / n)
    m = z * sqrt(f * (1 - f) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - m, c + m


def faixa(preco):
    return pd.cut(preco, FAIXAS, labels=ROTULOS, right=False, include_lowest=True)


def tabela_faixas(d, por=()):
    d = d.assign(faixa=faixa(d.preco_fav)).dropna(subset=["faixa"])
    linhas = []
    for chave, g in d.groupby(list(por) + ["faixa"], observed=True):
        n, k = len(g), int(g.fav_venceu.sum())
        lo, hi = wilson(k, n)
        chave = chave if isinstance(chave, tuple) else (chave,)
        linhas.append({**dict(zip(list(por) + ["faixa"], chave)), "n": n, "acerto": k / n,
                       "preco_medio": g.preco_fav.mean(), "ic95_inf": lo, "ic95_sup": hi,
                       "dif_pp": 100 * (k / n - g.preco_fav.mean())})
    return pd.DataFrame(linhas).round(4)


def metricas(d, por):
    linhas = []
    for chave, g in d.groupby(por, observed=True):
        p = g.preco_fav.clip(1e-4, 1 - 1e-4)
        y = g.fav_venceu.astype(float)
        linhas.append({por: chave, "n": len(g), "brier": ((p - y) ** 2).mean(),
                       "log_loss": -(y * np.log(p) + (1 - y) * np.log(1 - p)).mean()})
    return pd.DataFrame(linhas).round(4)


def teste_vies(d, minimo=0.80):
    """Acerto x preço acima de 80%: z = (vitórias - soma dos preços) / sqrt(soma p(1-p)),
    unilateral (H1: favorito vence mais que o preço). Por faixa e agregado."""
    d = d[d.preco_fav >= minimo].assign(faixa=lambda x: faixa(x.preco_fav)).dropna(subset=["faixa"])
    linhas = []
    for nome, g in list(d.groupby("faixa", observed=True)) + [("80-99 (todas)", d)]:
        k, esp, var = g.fav_venceu.sum(), g.preco_fav.sum(), (g.preco_fav * (1 - g.preco_fav)).sum()
        z = (k - esp) / sqrt(var) if var > 0 else np.nan
        linhas.append(dict(faixa=nome, n=len(g), acerto=k / len(g), preco_medio=esp / len(g),
                           efeito_pp=100 * (k - esp) / len(g), z=z,
                           p_valor_unilateral=0.5 * (1 - erf(z / sqrt(2))) if not np.isnan(z) else np.nan))
    return pd.DataFrame(linhas).round(4)


# ---------- gráficos ----------

def curva(tab, coluna, titulo, arq):
    fig, ax = plt.subplots(figsize=(6.5, 6))
    ax.plot([0.5, 1], [0.5, 1], color="#888", ls="--", lw=1, label="calibração perfeita")
    for nome, g in tab.groupby(coluna, observed=True):
        g = g[g.n >= 5]
        ax.errorbar(g.preco_medio, g.acerto, yerr=[g.acerto - g.ic95_inf, g.ic95_sup - g.acerto],
                    marker="o", ms=4, capsize=2, lw=1.2, label=f"{nome} (n={g.n.sum()})")
    ax.set_xlim(0.5, 1); ax.set_ylim(0.3, 1.02)
    ax.set_xlabel("Preço médio do favorito"); ax.set_ylabel("Taxa de acerto do favorito")
    ax.set_title(titulo); ax.legend(fontsize=8, loc="upper left"); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(arq, dpi=130); plt.close(fig)


# ---------- principal ----------

def main():
    OUT.mkdir(exist_ok=True)
    linhas, motivos = carregar()
    s = instantaneos(linhas)
    todos = favorito_por_mercado(s).assign(versao="todos os contratos")
    ev = favorito_por_evento(s).assign(versao="favorito por evento")
    for d in (todos, ev):
        d["volume_faixa"] = pd.cut(d.volume, VOLUMES, labels=ROT_VOL, right=False)
        d["periodo"] = np.where(d.momento.dt.year < 2024, "antes de 2024", "2024 em diante")
        d["atividade_faixa"] = pd.cut(d.atividade, [-1, 10, 40, 100, 10**6],
                                      labels=["0-10 h", "11-40 h", "41-100 h", ">100 h"])

    geral = tabela_faixas(pd.concat([todos, ev]), ["versao"])
    geral.to_csv(OUT / "calibracao_geral.csv", index=False)
    cortes = {"volume": "volume_faixa", "prazo": "prazo", "categoria": "categoria", "periodo": "periodo",
              "atividade": "atividade_faixa"}
    tabs = {}
    for nome, col in cortes.items():
        tabs[nome] = tabela_faixas(ev, [col])
        tabs[nome].to_csv(OUT / f"calibracao_por_{nome}.csv", index=False)
    pd.concat([metricas(ev, col).rename(columns={col: "grupo"}).assign(corte=nome)
               for nome, col in cortes.items()]).to_csv(OUT / "metricas_brier_logloss.csv", index=False)
    vies = teste_vies(ev)
    vies.to_csv(OUT / "vies_favorito_azarao.csv", index=False)

    # Pergunta direta: volume > 10 mi, 24 h a 7 dias
    alvo = ev[(ev.volume_faixa == ">10 mi") & ev.prazo.isin(["24h", "3d", "7d"])]
    alvo = alvo.assign(f=pd.cut(alvo.preco_fav, [0.8, 0.9, 0.95, 0.99], labels=["80-90", "90-95", "95-99"],
                                right=False))
    resp = []
    for f, g in alvo.groupby("f", observed=False):
        k, n = int(g.fav_venceu.sum()), len(g)
        lo, hi = wilson(k, n)
        resp.append(dict(faixa=f, n=n, eventos=g.evento.nunique(), acerto=k / n if n else np.nan,
                         preco_medio=g.preco_fav.mean() if n else np.nan, ic95_inf=lo, ic95_sup=hi))
    resp = pd.DataFrame(resp).round(4)
    resp.to_csv(OUT / "resposta_alto_volume_24h_7d.csv", index=False)

    erros = (todos[(todos.preco_fav >= 0.8) & ~todos.fav_venceu.astype(bool)]
             .sort_values(["volume", "preco_fav"], ascending=False)
             .drop_duplicates("id")[["question", "momento", "prazo", "preco_fav", "volume", "categoria"]])
    erros.head(50).round({"preco_fav": 3, "volume": 0}).to_csv(OUT / "maiores_erros.csv", index=False)

    curva(tabs["volume"], "volume_faixa", "Calibração por volume (favorito por evento)", OUT / "curva_volume.png")
    curva(tabs["prazo"], "prazo", "Calibração por prazo antes do evento", OUT / "curva_prazo.png")
    curva(tabs["atividade"], "atividade_faixa", "Por atividade nos 7 dias antes (horas com negócio)",
          OUT / "curva_atividade.png")
    curva(tabs["categoria"], "categoria", "Política x outros", OUT / "curva_categoria.png")
    curva(geral, "versao", "Todos os contratos x favorito por evento", OUT / "curva_geral.png")

    print(f"Mercados válidos: {len(linhas)}; descartados: {motivos}")
    print(f"Instantâneos: todos os contratos {len(todos)}, por evento {len(ev)} ({ev.evento.nunique()} eventos)")
    print("\nGeral:\n" + geral.to_string(index=False))
    print("\nViés favorito-azarão (por evento, faixas >= 80%):\n" + vies.to_string(index=False))
    print("\nVolume > US$ 10 mi, 24 h a 7 dias:\n" + resp.to_string(index=False))


if __name__ == "__main__":
    main()
