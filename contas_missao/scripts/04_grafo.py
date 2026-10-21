"""Grafo dos fluxos de output/fluxos.csv (2022 e 2026). Saída: output/grafo.png

Camadas da esquerda para a direita: partido -> candidatos que repassaram -> candidatos que receberam -> fornecedor.
Espessura proporcional ao valor; cor pela fonte do recurso. Arestas abaixo de R$ 5 mil omitidas.
"""
import re
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from comum import OUT

COR = {"FEFC": "#eb6834", "Fundo Partidário": "#8a5cc2", "Outros recursos": "#2a78d6"}
TINTA, TINTA2, FUNDO = "#0b0b0b", "#52514e", "#fcfcfb"
MINIMO = 5000


def rotulo(nome):
    nome = re.sub(r"^ELEI[CÇ][AÃ]O 2022 | DEPUTADO (FEDERAL|ESTADUAL)$", "", nome)
    nome = nome.replace("CORREIA", "CORREA")
    curtos = {"KIM PATROCA KATAGUIRI": "Kim Kataguiri", "AUGUSTO ZACARIAS CORREA LEITE": "Guto Zacarias",
              "GUTO ZACARIAS": "Guto Zacarias", "RENATO DE SOUZA BATTISTA": "Renato Battista",
              "CRISTIANO MOREIRA PINTO BERALDO": "Cristiano Beraldo", "AMANDA VETTORAZZO CARNEIRO": "Amanda Vettorazzo",
              "ALEX MACEDO DE SOUZA": "Alex Macedo", "FELIPPE LOURENCO OLIVEIRA COELHO": "Felippe Lourenço"}
    if nome in curtos:
        return curtos[nome]
    if nome.startswith("Direção"):
        return nome.split(" - ")[0].replace("/Comissão Provisória", "").replace("/Distrital", "")
    return nome.title()


def fonte(row):
    f = str(row.FONTE_RECURSO_PAGADOR) if pd.notna(row.FONTE_RECURSO_PAGADOR) else str(row.FONTE_RECURSO_RECEBEDOR)
    f = f.upper()
    return "FEFC" if ("ESPECIAL" in f) else "Fundo Partidário" if "PARTID" in f else "Outros recursos"


def painel(ax, f, titulo):
    f = f.assign(DE=f.PAGADOR.map(rotulo), PARA=f.RECEBEDOR.map(rotulo), F=f.apply(fonte, axis=1))
    partido = f.TIPO_REGISTRO.str.contains("partido")
    f.loc[partido, "DE"] = f.loc[partido, "DE"] + " (" + f.loc[partido, "PARTIDO_PAGADOR"].fillna("") + ")"
    e = f.groupby(["DE", "PARA", "F"]).VALOR.sum().reset_index()
    e = e[e.VALOR >= MINIMO]
    g = nx.MultiDiGraph()
    for _, x in e.iterrows():
        g.add_edge(x.DE, x.PARA, valor=x.VALOR, fonte=x.F)
    pagadores = set(e.DE); recebedores = set(e.PARA)
    camada = {}
    for n in g.nodes:
        if n.startswith("Direção"):
            camada[n] = 0
        elif n in pagadores and n in recebedores and any(e[(e.DE == n)].PARA.isin(recebedores & pagadores) == False):
            camada[n] = 1
        elif n in pagadores:
            camada[n] = 1 if not n.startswith("Direção") else 0
        else:
            camada[n] = 2
    camada["Cristiano Da Silva Lourenço"] = 3 if "Cristiano Da Silva Lourenço" in camada else None
    camada = {k: v for k, v in camada.items() if v is not None}
    # quem recebe de candidato e paga fornecedor fica na camada 2
    for n in ["Alex Macedo", "Felippe Lourenço"]:
        if n in camada:
            camada[n] = 2
    pos = {}
    for c in range(4):
        ns = sorted([n for n, k in camada.items() if k == c],
                    key=lambda n: -e[(e.DE == n) | (e.PARA == n)].VALOR.sum())
        for i, n in enumerate(ns):
            pos[n] = (c, -(i - (len(ns) - 1) / 2) * 1.0)
    vmax = e.VALOR.max()
    for (u, v, d) in g.edges(data=True):
        ax.annotate("", xy=pos[v], xytext=pos[u],
                    arrowprops=dict(arrowstyle="-|>", color=COR[d["fonte"]], lw=0.8 + 6 * d["valor"] / vmax,
                                    alpha=0.85, shrinkA=14, shrinkB=14, mutation_scale=12,
                                    connectionstyle="arc3,rad=0.06"))
        mx, my = pos[u][0] * 0.45 + pos[v][0] * 0.55, pos[u][1] * 0.45 + pos[v][1] * 0.55
        if d["valor"] >= 30000:
            ax.text(mx, my, f"R$ {d['valor']/1000:,.0f} mil".replace(",", "."), fontsize=7, color=TINTA2,
                    ha="center", va="center", bbox=dict(fc=FUNDO, ec="none", pad=0.6))
    for n, (x, y) in pos.items():
        ax.scatter([x], [y], s=60, color=TINTA, zorder=3)
        ax.text(x, y + 0.22, n, fontsize=8, color=TINTA, ha="center", va="bottom", zorder=4)
    topo = max(y for _, y in pos.values())
    ax.text(-0.6, topo + 1.5, titulo, fontsize=11, color=TINTA, ha="left")
    for c, nome in enumerate(["Partido", "Candidatos que repassam", "Candidatos que recebem", "Fornecedor PF"]):
        if any(k == c for k in camada.values()):
            ax.text(c, topo + 0.8, nome, fontsize=8, color=TINTA2, ha="center")
    ax.set_xlim(-0.6, 3.6); ax.set_ylim(min(y for _, y in pos.values()) - 0.5, topo + 1.9); ax.axis("off")


if __name__ == "__main__":
    f = pd.read_csv(OUT / "fluxos.csv", dtype=str)
    f["VALOR"] = f.VALOR.astype(float)
    fig, axes = plt.subplots(2, 1, figsize=(13, 15), gridspec_kw=dict(height_ratios=[3, 1]), facecolor=FUNDO)
    painel(axes[0], f[f.ANO == "2022"], "2022 - União Brasil (SP): fluxos para Kim, Renato, Guto, Amanda, Beraldo, Alex e Felippe")
    painel(axes[1], f[f.ANO == "2026"], "2026 - Missão (SP) e Cristiano Beraldo (PP), prestações ainda parciais")
    handles = [plt.Line2D([0], [0], color=c, lw=3, label=k) for k, c in COR.items()]
    fig.legend(handles=handles, loc="upper right", frameon=False, title="Fonte do recurso")
    fig.text(0.01, 0.005, f"Fonte: TSE, dados abertos de prestação de contas (receitas e despesas de candidatos, SP). "
             "Espessura proporcional ao valor; fluxos abaixo de R$ 5.000 omitidos (ver output/fluxos.csv).",
             fontsize=7, color=TINTA2)
    fig.tight_layout(rect=(0, 0.02, 1, 0.97))
    fig.savefig(OUT / "grafo.png", dpi=150, facecolor=FUNDO)
    print("output/grafo.png")
