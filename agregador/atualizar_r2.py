"""Reconstrói polls_r2.csv a partir da tabela de 2º turno (Lula x Flávio) da página
"Pesquisas de opinião para a eleição presidencial no Brasil em 2026" da Wikipedia.

Uso:  python atualizar_r2.py <arquivo_wikitext>
      (curl "https://pt.wikipedia.org/w/index.php?title=Pesquisas_de_opini%C3%A3o_para_a_elei%C3%A7%C3%A3o_presidencial_no_Brasil_em_2026&action=raw")
Entra só pesquisa com resultado divulgado e meio do campo depois do 1º turno (04/out).
"""
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE / "historico"))
from wiki_parse import linhas  # noqa: E402

DIA_R1 = date(2026, 10, 4)
MESES = {"set": 9, "out": 10}
NOMES = {"poderdata": "PoderData", "datafolha": "Datafolha", "nexus": "BTG/Nexus", "vox": "Vox Brasil",
         "verit": "Veritá", "atlas": "AtlasIntel", "real time": "Real Time Big Data",
         "alfa": "Alfa Inteligência", "mda": "CNT/MDA", "ideia": "Ideia"}
DATA = re.compile(r"(\d{1,2})\s*([a-z]{3})?\s*[–-]\s*(\d{1,2})\s*([a-z]{3})|^(\d{1,2})\s*([a-z]{3})$", re.I)


def nome(s):
    low = s.lower()
    return next((v for k, v in NOMES.items() if k in low), s.strip())


def datas(s):
    m = DATA.search(s.strip())
    if not m:
        return None
    if m.group(5):
        mes = MESES.get(m.group(6).lower())
        return (date(2026, mes, int(m.group(5))),) * 2 if mes else None
    fim_mes = MESES.get(m.group(4).lower())
    ini_mes = MESES.get((m.group(2) or m.group(4)).lower())
    if not fim_mes or not ini_mes:
        return None
    return date(2026, ini_mes, int(m.group(1))), date(2026, fim_mes, int(m.group(3)))


def pct(s):
    m = re.search(r"\d+(?:,\d+)?", s)
    return float(m.group(0).replace(",", ".")) if m and "%" in s else None


def main():
    texto = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
    ini = next(i for i, l in enumerate(texto) if l.startswith("=== Lula e Flávio Bolsonaro"))
    fim = next(i for i, l in enumerate(texto[ini + 1:], ini + 1) if l.startswith("==== 2025"))
    out = []
    for r in linhas("\n".join(texto), ini + 1, fim):
        i = next((k for k, c in enumerate(r) if datas(c)), None)
        if i is None or len(r) < i + 5:
            continue
        di, df = datas(r[i])
        lula, flavio, nv = pct(r[i + 3]), pct(r[i + 4]), pct(r[i + 5]) if len(r) > i + 5 else None
        if di + (df - di) / 2 <= DIA_R1 or lula is None or flavio is None:
            continue
        n = int(re.sub(r"\D", "", r[i + 1])) if re.search(r"\d", r[i + 1]) else None
        validos = abs(lula + flavio - 100) < 0.6
        out.append(dict(instituto=nome(r[0]), campo_inicio=di, campo_fim=df, n=n, flavio=flavio,
                        lula=lula, base="validos" if validos else "totais",
                        nao_validos=None if validos else nv, confianca_dado="alta",
                        observacao="fonte: Wikipedia (pt), tabela de 2º turno"))
    d = pd.DataFrame(out).drop_duplicates().sort_values("campo_fim", ascending=False)
    d.to_csv(BASE / "polls_r2.csv", index=False)
    print(d.to_string(index=False))


if __name__ == "__main__":
    main()
