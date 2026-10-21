"""Localiza as pessoas citadas na base consulta_cand_2026 (TSE), SP e BR."""
import sys, unicodedata, pandas as pd
from pathlib import Path
BASE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dados_brutos/cand2026")
NOMES = ["ALEX MACEDO", "CRISTIANO BERALDO", "RENATO BATTISTA", "KIM KATAGUIRI",
         "AMANDA VETTORAZZO", "GUTO ZACARIAS", "FELIPE LOURENCO", "SILENE",
         "CRISTIANO DA SILVA"]
def norm(s): return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().upper()
COLS = ["SG_UF","DS_CARGO","SQ_CANDIDATO","NR_CANDIDATO","NM_CANDIDATO","NM_URNA_CANDIDATO",
        "SG_PARTIDO","SG_FEDERACAO","DS_SITUACAO_CANDIDATURA","DS_SIT_TOT_TURNO","NR_TURNO"]
df = pd.concat(pd.read_csv(BASE/f"consulta_cand_2026_{uf}.csv", sep=";", encoding="latin1", dtype=str)
               for uf in ["SP","BR"])
df["_n"] = (df.NM_CANDIDATO + " | " + df.NM_URNA_CANDIDATO).map(norm)
out = []
for nome in NOMES:
    toks = nome.split()
    m = df[df._n.map(lambda s: all(t in s for t in toks))]
    if nome in ("SILENE", "CRISTIANO DA SILVA"):   # nomes genéricos: só listar contagem
        print(f"\n## {nome}: {len(m)} registros em 2026 (SP/BR)"); 
        if nome == "SILENE": m = m[m._n.str.contains("LOURENCO")]
        else: m = m.iloc[0:0]
    else: print(f"\n## {nome}: {len(m)} registro(s)")
    if len(m): print(m[COLS].to_string(index=False)); out.append(m[COLS].assign(BUSCA=nome))
pd.concat(out).to_csv("output/candidatos_2026.csv", index=False)
print("\nPartido Missão em SP:"); 
mis = df[df.SG_PARTIDO.str.upper().str.contains("MISS", na=False)]
print(mis.groupby(["SG_PARTIDO","DS_CARGO"]).size().to_string())
