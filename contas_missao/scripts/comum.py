"""Leitura das bases do TSE e utilidades comuns.

Todos os arquivos vêm de https://cdn.tse.jus.br/estatistica/sead/odsele/ (ver baixar.sh).
Separador ';', codificação latin1, valores com vírgula decimal.
"""
import unicodedata
from pathlib import Path
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = RAIZ / "dados_brutos"
OUT = RAIZ / "output"
CDN = "https://cdn.tse.jus.br/estatistica/sead/odsele"

# id da eleição usado pelo DivulgaCandContas (2022 = eleição geral federal)
DIVULGA_ID = {"2022": "2040602022"}


def norm(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper().strip()


def ler(caminho_rel):
    """Lê CSV do TSE preservando o número da linha no arquivo (cabeçalho = linha 1)."""
    df = pd.read_csv(BRUTOS / caminho_rel, sep=";", encoding="latin1", dtype=str, keep_default_na=False)
    df["_arquivo"] = Path(caminho_rel).name
    df["_linha"] = df.index + 2
    return df


def valor(serie):
    return serie.str.replace(",", ".", regex=False).astype(float)


def fonte(row):
    return f"{row['_arquivo']}:{row['_linha']}"


def link_divulga(ano, sq):
    if ano in DIVULGA_ID:
        return f"https://divulgacandcontas.tse.jus.br/divulga/#/candidato/{ano}/{DIVULGA_ID[ano]}/SP/{sq}"
    return ""


def candidatos(ano):
    return ler(f"cand{ano}/consulta_cand_{ano}_SP.csv")


def votos(ano):
    v = ler(f"votacao{ano}/votacao_candidato_munzona_{ano}_SP.csv")
    v = v[v.NR_TURNO == "1"]
    v["QT"] = v.QT_VOTOS_NOMINAIS_VALIDOS.astype(int)
    return v.groupby("SQ_CANDIDATO").QT.sum().rename("VOTOS")


def receitas(ano):
    r = ler(f"contas{ano}/receitas_candidatos_{ano}_SP.csv")
    r["VR"] = valor(r.VR_RECEITA)
    return r


def originario(ano):
    o = ler(f"contas{ano}/receitas_candidatos_doador_originario_{ano}_SP.csv")
    o["VR"] = valor(o.VR_RECEITA)
    return o


def despesas(ano):
    """Despesas contratadas, com a fonte do recurso vinda das despesas pagas.

    Uma despesa (SQ_PRESTADOR_CONTAS + SQ_DESPESA) pode ter vários itens nas contratadas,
    então VR_PAGO repete em cada item: não somar VR_PAGO depois do merge; usar VR (item).
    """
    dc = ler(f"contas{ano}/despesas_contratadas_candidatos_{ano}_SP.csv")
    dc["VR"] = valor(dc.VR_DESPESA_CONTRATADA)
    dp = ler(f"contas{ano}/despesas_pagas_candidatos_{ano}_SP.csv")
    dp["VR_PAGO"] = valor(dp.VR_PAGTO_DESPESA)
    pagas = (dp.groupby(["SQ_PRESTADOR_CONTAS", "SQ_DESPESA"])
               .agg(VR_PAGO=("VR_PAGO", "sum"),
                    FONTE=("DS_FONTE_DESPESA", lambda s: " + ".join(sorted(set(s)))),
                    DT_PAGTO=("DT_PAGTO_DESPESA", "min"),
                    LINHA_PAGA=("_linha", "first"))
               .reset_index())
    return dc.merge(pagas, on=["SQ_PRESTADOR_CONTAS", "SQ_DESPESA"], how="left")
