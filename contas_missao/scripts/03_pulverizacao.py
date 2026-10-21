"""Pagamentos a pessoas físicas de Alex Macedo e Felipe Lourenço (2022), cruzamentos e custo por voto.

Saídas: output/pulverizacao_resumo.csv, output/pulverizacao_faixas.csv, output/pulverizacao_valores_repetidos.csv,
        output/cruzamentos.csv, output/custo_por_voto.csv
Pessoas físicas não candidatas aparecem só agregadas ou com o nome como está na base, nunca com CPF.
"""
import pandas as pd
from comum import OUT, candidatos, despesas, ler, norm, receitas, votos

ALVOS = {"250001602051": "ALEX MACEDO", "250001602115": "FELIPPE LOURENÇO"}
NUCLEO_2022 = ["KIM PATROCA KATAGUIRI", "CRISTIANO MOREIRA PINTO BERALDO", "RENATO DE SOUZA BATTISTA",
               "AUGUSTO ZACARIAS CORREA LEITE", "AMANDA VETTORAZZO CARNEIRO"]
FAIXAS = [0, 500, 1000, 1500, 2000, 3000, 5000, 10000, 1e9]


def pagamentos_pf(dc):
    pf = dc[dc.SQ_CANDIDATO.isin(ALVOS) & (dc.DS_TIPO_FORNECEDOR == "PESSOA FÍSICA")].copy()
    pf["CAMPANHA"] = pf.SQ_CANDIDATO.map(ALVOS)
    pf["DATA"] = pd.to_datetime(pf.DT_DESPESA, dayfirst=True)
    return pf


def resumo(pf, dc):
    linhas = []
    for camp, g in pf.groupby("CAMPANHA"):
        tot = dc[dc.SQ_CANDIDATO == g.SQ_CANDIDATO.iloc[0]].VR.sum()
        linhas.append(dict(
            CAMPANHA=camp, N_PAGAMENTOS_PF=len(g), N_PESSOAS=g.NR_CPF_CNPJ_FORNECEDOR.nunique(),
            TOTAL_PF=g.VR.sum(), PCT_DO_GASTO=g.VR.sum() / tot, MIN=g.VR.min(), MEDIANA=g.VR.median(),
            MAX=g.VR.max(), PCT_MULTIPLO_100=(g.VR % 100 == 0).mean(), PCT_MULTIPLO_500=(g.VR % 500 == 0).mean(),
            DATAS_DISTINTAS=g.DT_DESPESA.nunique(),
            DATA_MAIS_COMUM=g.DT_DESPESA.value_counts().index[0],
            N_NA_DATA_MAIS_COMUM=g.DT_DESPESA.value_counts().iloc[0],
            DESCRICOES_MAIS_COMUNS="; ".join(f"{k} ({v})" for k, v in g.DS_DESPESA.str.upper().value_counts().head(5).items()),
            ORIGENS="; ".join(f"{k} ({v})" for k, v in g.DS_ORIGEM_DESPESA.value_counts().items()),
            FONTES_RECURSO="; ".join(f"{k} ({v})" for k, v in g.FONTE.value_counts().items())))
    return pd.DataFrame(linhas)


def faixas(pf):
    pf = pf.assign(FAIXA=pd.cut(pf.VR, FAIXAS, right=True).astype(str))
    return pf.groupby(["CAMPANHA", "FAIXA"]).VR.agg(N="size", TOTAL="sum").reset_index()


def repetidos(pf):
    v = pf.groupby(["CAMPANHA", "VR"]).size().rename("N").reset_index()
    return v[v.N >= 3].sort_values(["CAMPANHA", "N"], ascending=[True, False])


def cruzamentos(pf, dc):
    """Recebedor PF que também é candidato (2020/2022/2024), doador em 2022 ou fornecedor do núcleo."""
    cpfs = set(pf.NR_CPF_CNPJ_FORNECEDOR)
    nomes = dict(zip(pf.NR_CPF_CNPJ_FORNECEDOR, pf.NM_FORNECEDOR))
    camp = pf.groupby("NR_CPF_CNPJ_FORNECEDOR").CAMPANHA.agg(lambda s: "/".join(sorted(set(s))))
    valor = pf.groupby("NR_CPF_CNPJ_FORNECEDOR").VR.sum()
    achados = []

    def add(cpf, tipo, detalhe, fonte):
        achados.append(dict(RECEBEDOR=nomes[cpf], CAMPANHA_PAGADORA=camp[cpf], VALOR_RECEBIDO=valor[cpf],
                            CRUZAMENTO=tipo, DETALHE=detalhe, FONTE=fonte))

    for ano in ["2020", "2022"]:  # nessas bases o CPF do candidato é público
        c = candidatos(ano)
        for _, x in c[c.NR_CPF_CANDIDATO.isin(cpfs)].iterrows():
            add(x.NR_CPF_CANDIDATO, f"candidato {ano} (CPF)",
                f"{x.DS_CARGO} {x.NM_UE} {x.SG_PARTIDO} '{x.NM_URNA_CANDIDATO}' {x.DS_SIT_TOT_TURNO}",
                f"{x._arquivo}:{x._linha}")
    c24 = candidatos("2024")  # CPF não divulgado em 2024: só nome completo idêntico
    n24 = c24.assign(_n=c24.NM_CANDIDATO.map(norm))
    for cpf, nome in nomes.items():
        for _, x in n24[n24._n == norm(nome)].iterrows():
            add(cpf, "candidato 2024 (só nome; CPF não divulgado)",
                f"{x.DS_CARGO} {x.NM_UE} {x.SG_PARTIDO} '{x.NM_URNA_CANDIDATO}' {x.DS_SIT_TOT_TURNO}",
                f"{x._arquivo}:{x._linha}")
    r = receitas("2022")
    for _, x in r[r.NR_CPF_CNPJ_DOADOR.isin(cpfs)].iterrows():
        add(x.NR_CPF_CNPJ_DOADOR, "doador 2022", f"doou {x.VR:.2f} a {x.NM_CANDIDATO} ({x.SG_PARTIDO})",
            f"{x._arquivo}:{x._linha}")
    outros = dc[dc.NM_CANDIDATO.map(norm).isin(NUCLEO_2022) | (dc.SQ_CANDIDATO.isin(ALVOS))]
    for _, x in outros[outros.NR_CPF_CNPJ_FORNECEDOR.isin(cpfs)].iterrows():
        if ALVOS.get(x.SQ_CANDIDATO) in camp[x.NR_CPF_CNPJ_FORNECEDOR].split("/"):
            continue
        add(x.NR_CPF_CNPJ_FORNECEDOR, "fornecedor de outra campanha do grupo",
            f"recebeu {x.VR:.2f} de {x.NM_CANDIDATO} ({x.DS_DESPESA})", f"{x._arquivo}:{x._linha}")
    return pd.DataFrame(achados).drop_duplicates()


def custo_por_voto():
    linhas = []
    for ano in ["2022", "2026"]:
        c = candidatos(ano)
        c = c[c.DS_CARGO.isin(["DEPUTADO FEDERAL", "DEPUTADO ESTADUAL"])]
        g = despesas(ano).groupby("SQ_CANDIDATO").VR.sum().rename("GASTO")
        t = c.join(votos(ano), on="SQ_CANDIDATO").join(g, on="SQ_CANDIDATO")
        t = t[(t.VOTOS > 0) & (t.GASTO > 0)].assign(CPV=lambda d: d.GASTO / d.VOTOS)
        med = t.groupby("DS_CARGO").CPV.median()
        alvo = t[t.NM_CANDIDATO.map(norm).isin(NUCLEO_2022 + ["ALEX MACEDO DE SOUZA", "FELIPPE LOURENCO OLIVEIRA COELHO"])]
        for _, x in alvo.iterrows():
            linhas.append(dict(ANO=ano, CANDIDATO=x.NM_URNA_CANDIDATO, CARGO=x.DS_CARGO, PARTIDO=x.SG_PARTIDO,
                               VOTOS=x.VOTOS, GASTO=x.GASTO, CUSTO_POR_VOTO=x.CPV,
                               MEDIANA_CARGO_SP=med[x.DS_CARGO], VEZES_A_MEDIANA=x.CPV / med[x.DS_CARGO],
                               PERCENTIL_NO_CARGO=(t[t.DS_CARGO == x.DS_CARGO].CPV < x.CPV).mean(),
                               N_CANDIDATOS_COMPARADOS=(t.DS_CARGO == x.DS_CARGO).sum()))
    return pd.DataFrame(linhas).sort_values(["ANO", "CUSTO_POR_VOTO"], ascending=[True, False])


if __name__ == "__main__":
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 120)
    dc = despesas("2022")
    pf = pagamentos_pf(dc)
    for nome, df in [("pulverizacao_resumo", resumo(pf, dc)), ("pulverizacao_faixas", faixas(pf)),
                     ("pulverizacao_valores_repetidos", repetidos(pf)), ("cruzamentos", cruzamentos(pf, dc)),
                     ("custo_por_voto", custo_por_voto())]:
        df.round(4).to_csv(OUT / f"{nome}.csv", index=False)
        print(f"\n### {nome}\n{df.T.to_string() if nome.endswith('resumo') else df.to_string(index=False)}")
