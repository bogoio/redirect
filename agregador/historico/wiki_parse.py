"""Extrai linhas de tabelas wikitext (Wikipedia) como listas de células limpas."""
import re, sys


def limpar(c):
    c = re.sub(r"<ref[^>]*/>", "", c)
    c = re.sub(r"<ref.*?</ref>", "", c, flags=re.S)
    c = re.sub(r"<ref.*", "", c)
    c = re.sub(r"\{\{(?:yes\d?|no\d?|small|nowrap|right|left|Sort\|[^|{}]*)\|?([^{}]*)\}\}", r"\1", c)
    c = re.sub(r"\{\{(?:efn|Efn|refn)[^{}]*\}\}", "", c)
    c = re.sub(r"\{\{[^{}]*\}\}", "", c)
    c = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", c)
    if "|" in c and not c.startswith("[["):  # atributos tipo style=...|valor
        partes = c.split("|")
        if re.search(r"(style|rowspan|colspan|class)\s*=", partes[0]):
            c = "|".join(partes[1:])
    c = re.sub(r"\[https?://\S+ ([^\]]*)\]", r"\1", c)
    c = re.sub(r"<[^>]+>", " ", c).replace("'''", "").replace("''", "")
    return " ".join(c.split())


def linhas(texto, ini, fim):
    seg = texto.splitlines()[ini - 1:fim]
    rows, cur = [], None
    for l in seg:
        if l.startswith("|-") or l.startswith("|}"):
            if cur:
                rows.append(cur)
            cur = []
            continue
        if cur is None:
            continue
        if l.startswith("|") or l.startswith("!"):
            for c in re.split(r"\|\||!!", l[1:]):
                cur.append(limpar(c))
        elif cur:
            cur[-1] += " " + limpar(l)
    if cur:
        rows.append(cur)
    return rows


if __name__ == "__main__":
    f, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    for r in linhas(open(f, encoding="utf-8").read(), a, b)[: int(sys.argv[4]) if len(sys.argv) > 4 else 15]:
        print(r)
