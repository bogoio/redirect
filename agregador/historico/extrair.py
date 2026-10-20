"""Monta a tabela de pesquisas de véspera (2014, 2018, 2022) a partir do wikitext da
Wikipedia e calcula o erro de cada instituto contra o resultado oficial.

Uso:  python -I extrair.py <pasta_com_wikitext>
Saída: pesquisas_vespera.csv (nesta pasta).
"""
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from wiki_parse import linhas  # noqa: E402

# Participação do adversário do PT entre os dois finalistas (TSE, votos válidos)
RESULTADO = {(2014, 1): 33.55 / (33.55 + 41.59) * 100, (2014, 2): 48.36,
             (2018, 1): 46.03 / (46.03 + 29.28) * 100, (2018, 2): 55.13,
             (2022, 1): 43.20 / (43.20 + 48.43) * 100, (2022, 2): 49.10}
ELEICAO = {(2014, 1): date(2014, 10, 5), (2014, 2): date(2014, 10, 26),
           (2018, 1): date(2018, 10, 7), (2018, 2): date(2018, 10, 28),
           (2022, 1): date(2022, 10, 2), (2022, 2): date(2022, 10, 30)}
# arquivo, linhas, tamanhos de linha aceitos, índices (instituto, data, n, pt, adversário)
TABELAS = {
    (2014, 1): ("pt_2014_t1.txt", (1, 10**6), None, (2, 1, None, 4, 6)),
    (2014, 2): ("pt_2014_t2.txt", (1, 10**6), None, (2, 1, None, 4, 5)),
    (2018, 1): ("en_2018.txt", (11, 626), (13, 14), (0, 1, 2, 3, 10)),
    (2018, 2): ("en_2018.txt", (4687, 4861), (6,), (0, 1, 2, 3, 4)),
    (2022, 1): ("en_2022.txt", (117, 867), (10,), (0, 1, 2, 4, 3)),
    (2022, 2): ("en_2022.txt", (1977, 2322), (7,), (0, 1, 2, 4, 3)),
}
MESES = {"jan": 1, "fev": 2, "feb": 2, "mar": 3, "abr": 4, "apr": 4, "mai": 5, "may": 5,
         "jun": 6, "jul": 7, "ago": 8, "aug": 8, "set": 9, "sep": 9, "out": 10, "oct": 10,
         "nov": 11, "dez": 12, "dec": 12}
NOMES = [("ibope", "Ibope/Ipec"), ("ipec", "Ibope/Ipec"), ("datafolha", "Datafolha"),
         ("quaest", "Quaest"), ("atlas", "AtlasIntel"), ("poder", "PoderData"),
         ("mda", "CNT/MDA"), ("real ?time", "Real Time Big Data"), ("ipespe", "Ipespe"),
         ("paran", "Paraná Pesquisas"), ("vox populi", "Vox Populi"), ("verit", "Veritá"),
         ("futura", "Futura"), ("gerp", "Gerp"), ("sensus", "Sensus"), ("ideia", "Ideia"),
         ("btg|nexus|fsb", "BTG/Nexus"), ("brasmarket", "Brasmarket"), ("mdb", None)]


def instituto(s):
    low = s.lower()
    for pad, nome in NOMES:
        if re.search(pad, low):
            return nome
    return s.strip()


def fim_campo(s, ano):
    s = s.lower()
    meses = [MESES[m[:3]] for m in re.findall(r"[a-zç]{3,}", s) if m[:3] in MESES]
    dias = [int(d) for d in re.findall(r"\b(\d{1,2})\b", s)]
    if not meses or not dias:
        return None
    try:
        return date(ano, meses[-1], dias[-1])
    except ValueError:
        return None


def num(s):
    m = re.search(r"(\d+(?:[.,]\d+)?)", s.replace(",", ".") if "%" in s else s)
    return float(m.group(1)) if m else None


def extrair(pasta, chave):
    arq, (a, b), tam, (ii, idt, inn, ipt, iadv) = TABELAS[chave]
    ano, turno = chave
    out = []
    for r in linhas((pasta / arq).read_text(encoding="utf-8"), a, b):
        if (tam and len(r) not in tam) or len(r) <= max(ipt, iadv, ii) or r[ii].startswith("Result") or not r[ipt].strip().endswith("%"):
            continue
        fim = fim_campo(r[idt], ano)
        if fim is None or not (0 <= (ELEICAO[chave] - fim).days <= 10):
            continue
        n = int(re.sub(r"\D", "", r[inn])) if inn is not None and re.search(r"\d", r[inn]) else None
        pt, adv = num(r[ipt]), num(r[iadv])
        if not pt or not adv:
            continue
        out.append(dict(ano=ano, turno=turno, instituto=instituto(r[ii]), campo_fim=fim, n=n,
                        pt=pt, adversario=adv, fonte=r[ii][:60]))
    d = pd.DataFrame(out).dropna(subset=["instituto"])
    d = d.sort_values("campo_fim", ascending=False).drop_duplicates("instituto")  # última de cada
    d["share"] = 100 * d.adversario / (d.adversario + d.pt)
    d["resultado"] = RESULTADO[chave]
    d["erro"] = d.share - d.resultado
    return d


def main():
    pasta = Path(sys.argv[1])
    tab = pd.concat([extrair(pasta, k) for k in TABELAS], ignore_index=True)
    tab = tab.round({"share": 2, "resultado": 2, "erro": 2})
    tab.to_csv(Path(__file__).parent / "pesquisas_vespera.csv", index=False)
    print(tab.drop(columns="fonte").to_string(index=False))


if __name__ == "__main__":
    main()
