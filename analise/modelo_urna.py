# Hipótese registrada antes da coleta: se houve adulteração na compilação de algum modelo de urna, as seções desse modelo
# terão ganho de Lula (2T vs 1T, mesma seção) >= ~1 pt acima dos demais modelos, controlando 1T e UF.
# Diferença < ~0,5 pt e não significativa = hipótese não sustentada.
import csv, io, json, random, sys, time, zipfile, re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests
import bu

BASE = "https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna"
P2, P1, E2, E1 = 3221, 3220, 6258, 6257
OUT = Path(__file__).parent / "secoes_modelo.csv"
S = requests.Session()
CAMPOS = ["uf", "mun", "zona", "secao", "modelo", "l2", "f2", "v2", "l1", "f1", "v1", "fim2"]


def get(url, binario=False):
    for i in range(12):
        try:
            r = S.get(url, timeout=30)
            if r.status_code == 200:
                return r.content if binario else r.json()
            if r.status_code == 404:
                return None
        except requests.RequestException:
            pass
        time.sleep(min(60, 3 * (i + 1)))
    return None


def arquivos(pleito, uf, mun, zona, secao):
    d = f"{BASE}/{pleito}/dados/{uf}/{mun}/{zona}/{secao}"
    aux = get(f"{d}/p{pleito:06d}-{uf}-m{mun}-z{zona}-s{secao}-aux.json")
    if not aux:
        return None
    h = aux["hashes"][-1]
    return {a["tp"]: f"{d}/{h['hash']}/{a['nm']}" for a in h["arq"]}


def modelo(log_zip):
    z = zipfile.ZipFile(io.BytesIO(log_zip))
    txt = z.read(z.namelist()[0]).decode("latin1")
    m = re.search(r"Modelo de Urna: (UE\d{4})", txt)
    fim = re.findall(r"(\d\d:\d\d:\d\d)\t\w+\t\d+\tVOTA\t[^\n]*[Ee]ncerr", txt)
    return (m.group(1) if m else "?"), (fim[-1] if fim else "")


def coleta(sec):
    uf, mun, zona, secao = sec
    a2 = arquivos(P2, uf, mun, zona, secao)
    a1 = arquivos(P1, uf, mun, zona, secao)
    if not a2 or not a1 or "bu" not in a2 or "bu" not in a1 or "log" not in a2:
        return None
    b2, b1, lg = get(a2["bu"], True), get(a1["bu"], True), get(a2["log"], True)
    if not (b2 and b1 and lg):
        return None
    v2, v1 = bu.votos(b2, E2), bu.votos(b1, E1)
    mod, fim = modelo(lg)
    return dict(uf=uf, mun=mun, zona=zona, secao=secao, modelo=mod, l2=v2.get(13, 0), f2=v2.get(22, 0), v2=v2["validos"],
                l1=v1.get(13, 0), f1=v1.get(22, 0), v1=v1["validos"], fim2=fim)


def secoes():
    ufs = "ac al am ap ba ce df es go ma mg ms mt pa pb pe pi pr rj rn ro rr rs sc se sp to".split()
    todas = []
    for uf in ufs:
        cs = get(f"{BASE}/{P2}/config/{uf}/{uf}-p{P2:06d}-cs.json")
        for m in cs["abr"][0]["mu"]:
            for z in m["zon"]:
                todas += [(uf, m["cd"], z["cd"], s["ns"]) for s in z["sec"]]
    return todas


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    random.seed(20261025)
    todas = secoes()
    amostra = random.sample(todas, n)
    feitas = set()
    if OUT.exists():
        feitas = {(r["uf"], r["mun"], r["zona"], r["secao"]) for r in csv.DictReader(OUT.open())}
    pend = [s for s in amostra if s not in feitas]
    print(f"{len(todas)} seções, amostra {n}, faltam {len(pend)}", flush=True)
    novo = not OUT.exists()
    with OUT.open("a", newline="") as f, ThreadPoolExecutor(2) as ex:
        w = csv.DictWriter(f, CAMPOS)
        if novo:
            w.writeheader()
        for i, r in enumerate(ex.map(coleta, pend), 1):
            if r:
                w.writerow(r); f.flush()
            if i % 50 == 0:
                print(f"{i}/{len(pend)}", flush=True)
    print("fim", flush=True)
