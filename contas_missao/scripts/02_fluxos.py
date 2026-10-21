"""Pessoas citadas (cargo, partido, votos) e fluxos de dinheiro do grupo, 2022 e 2026.

Saídas: output/pessoas.csv, output/fluxos.csv
"""
import pandas as pd
from comum import OUT, candidatos, despesas, fonte, link_divulga, norm, originario, receitas, votos

# Nomes como constam no NM_CANDIDATO do TSE (sem acento)
NUCLEO = {
    "2022": ["KIM PATROCA KATAGUIRI", "CRISTIANO MOREIRA PINTO BERALDO", "RENATO DE SOUZA BATTISTA",
             "AUGUSTO ZACARIAS CORREA LEITE", "AMANDA VETTORAZZO CARNEIRO", "ALEX MACEDO DE SOUZA",
             "FELIPPE LOURENCO OLIVEIRA COELHO"],
    "2026": ["KIM PATROCA KATAGUIRI", "CRISTIANO MOREIRA PINTO BERALDO", "RENATO DE SOUZA BATTISTA",
             "AUGUSTO ZACARIAS CORREA LEITE"],
}


def pessoas():
    linhas = []
    for ano, nomes in NUCLEO.items():
        c = candidatos(ano)
        c = c[c.NM_CANDIDATO.map(norm).isin(nomes) & (c.DS_CARGO.str.startswith("DEPUTADO"))]
        c = c.join(votos(ano), on="SQ_CANDIDATO")
        dc = despesas(ano)
        gasto = dc.groupby("SQ_CANDIDATO").VR.sum()
        for _, x in c.iterrows():
            linhas.append(dict(ANO=ano, NOME_URNA=x.NM_URNA_CANDIDATO, NOME=x.NM_CANDIDATO, CARGO=x.DS_CARGO,
                               PARTIDO=x.SG_PARTIDO, FEDERACAO=x.SG_FEDERACAO, SITUACAO=x.DS_SIT_TOT_TURNO,
                               VOTOS=x.VOTOS, DESPESA_CONTRATADA=gasto.get(x.SQ_CANDIDATO, 0.0),
                               SQ_CANDIDATO=x.SQ_CANDIDATO, LINK=link_divulga(ano, x.SQ_CANDIDATO),
                               FONTE=fonte(x)))
    p = pd.DataFrame(linhas).sort_values(["ANO", "CARGO", "NOME"])
    p.round(2).to_csv(OUT / "pessoas.csv", index=False)
    return p


def fluxos(ano, nucleo_sq, partido_grupo=None):
    r = receitas(ano)
    o = originario(ano)
    dc = despesas(ano)
    sq_part = set(candidatos(ano).query("SG_PARTIDO == @partido_grupo").SQ_CANDIDATO) if partido_grupo else set()
    grupo = set(nucleo_sq) | sq_part

    # 1) receitas de candidato vindas de outro candidato ou de partido, quando envolve o grupo
    entre = r.DS_ORIGEM_RECEITA.str.contains("outros candidatos")
    m = r[entre & (r.SQ_CANDIDATO.isin(grupo) | r.SQ_CANDIDATO_DOADOR.isin(grupo))]
    part = r[r.DS_ORIGEM_RECEITA.str.contains("partido") & r.SQ_CANDIDATO.isin(nucleo_sq)]
    rec = pd.concat([m, part])

    # lado do doador: despesa "Doações financeiras a outros candidatos" com valor igual
    doa = dc[dc.DS_ORIGEM_DESPESA.str.startswith("Doações financeiras")]
    orig = o.groupby("SQ_RECEITA").agg(TP=("TP_DOADOR_ORIGINARIO", lambda s: "/".join(sorted(set(s)))),
                                       N=("TP_DOADOR_ORIGINARIO", "size"))
    out = []
    for _, x in rec.iterrows():
        cand_doador = x.SQ_CANDIDATO_DOADOR not in ("", "-1", "#NULO")
        mesmo_valor = doa[(abs(doa.VR - x.VR) < 0.01) & (doa.NM_FORNECEDOR.map(norm).str.contains(" ".join(norm(x.NM_CANDIDATO).split()[:2]), regex=False))]
        lado = mesmo_valor[mesmo_valor.SQ_CANDIDATO == x.SQ_CANDIDATO_DOADOR] if cand_doador else doa.iloc[0:0]
        if not len(lado):  # receita sem SQ do doador (ex.: Beraldo registrado como cargo errado): casa por nome
            lado = mesmo_valor[mesmo_valor.NM_CANDIDATO.map(norm) == norm(x.NM_DOADOR)]
        d = lado.iloc[0] if len(lado) else None
        og = orig.loc[x.SQ_RECEITA] if x.SQ_RECEITA in orig.index else None
        out.append(dict(
            ANO=ano, DATA=x.DT_RECEITA, PAGADOR=x.NM_DOADOR, PARTIDO_PAGADOR=x.SG_PARTIDO_DOADOR,
            RECEBEDOR=x.NM_CANDIDATO, PARTIDO_RECEBEDOR=x.SG_PARTIDO, CARGO_RECEBEDOR=x.DS_CARGO,
            VALOR=x.VR, TIPO_REGISTRO="doação recebida (" + x.DS_ORIGEM_RECEITA + ")",
            FONTE_RECURSO_RECEBEDOR=x.DS_FONTE_RECEITA,
            FONTE_RECURSO_PAGADOR=(d.FONTE if d is not None else ""),
            DOADOR_ORIGINARIO=(f"{og.TP} ({og.N} registros)" if og is not None else ""),
            FONTE=fonte(x) + (f"; {d._arquivo}:{d._linha}" if d is not None else ""),
            LINK=link_divulga(ano, x.SQ_CANDIDATO)))
    return pd.DataFrame(out)


def despesas_relevantes():
    """Despesas de 2022 citadas no vídeo: o aluguel de Alex Macedo a Cristiano da Silva Lourenço."""
    dc = despesas("2022")
    x = dc[dc.NM_FORNECEDOR.map(norm).str.contains("CRISTIANO DA SILVA LOURENCO")]
    return pd.DataFrame([dict(
        ANO="2022", DATA=r.DT_DESPESA, PAGADOR=r.NM_CANDIDATO, PARTIDO_PAGADOR=r.SG_PARTIDO,
        RECEBEDOR=r.NM_FORNECEDOR, PARTIDO_RECEBEDOR="", CARGO_RECEBEDOR="(pessoa física fornecedora)",
        VALOR=r.VR, TIPO_REGISTRO=f"despesa ({r.DS_ORIGEM_DESPESA}: {r.DS_DESPESA})",
        FONTE_RECURSO_RECEBEDOR="", FONTE_RECURSO_PAGADOR=r.FONTE, DOADOR_ORIGINARIO="",
        FONTE=f"{fonte(r)}; despesas_pagas_candidatos_2022_SP.csv:{int(r.LINHA_PAGA)}",
        LINK=link_divulga("2022", r.SQ_CANDIDATO)) for _, r in x.iterrows()])


if __name__ == "__main__":
    p = pessoas()
    print(p.drop(columns=["LINK", "FONTE"]).to_string(index=False))
    f = pd.concat([
        fluxos("2022", set(p[p.ANO == "2022"].SQ_CANDIDATO)),
        fluxos("2026", set(p[p.ANO == "2026"].SQ_CANDIDATO), partido_grupo="MISSÃO"),
        despesas_relevantes(),
    ]).drop_duplicates(subset=["FONTE"])
    f.to_csv(OUT / "fluxos.csv", index=False)
    print(f"\n{len(f)} fluxos -> output/fluxos.csv")
    print(f.drop(columns=["LINK", "FONTE", "CARGO_RECEBEDOR"]).to_string(index=False))
