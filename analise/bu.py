def tlv(b, i):
    t = b[i]; i += 1
    if t & 0x1F == 0x1F:
        n = 0
        while True:
            x = b[i]; i += 1; n = (n << 7) | (x & 0x7F)
            if not x & 0x80:
                break
        tag = n
    else:
        tag = t & 0x1F
    ln = b[i]; i += 1
    if ln & 0x80:
        k = ln & 0x7F; ln = int.from_bytes(b[i:i + k], "big"); i += k
    return t, tag, bool(t & 0x20), i, i + ln


def arvore(b, ini=0, fim=None):
    fim = len(b) if fim is None else fim
    out, i = [], ini
    while i < fim:
        t, tag, cons, s, e = tlv(b, i)
        out.append((t, tag, arvore(b, s, e) if cons else b[s:e]))
        i = e
    return out


def _int(v):
    return int.from_bytes(v, "big", signed=True)


def votos(raw, eleicao):
    """{numero_candidato: votos} do cargo de presidente; chave 'validos' soma os votos nominais."""
    inner = [v for t, _, v in arvore(raw)[0][2] if t == 0x04][0]
    res = {}

    def entradas(nos):
        for t, _, v in nos:
            if not isinstance(v, list):
                continue
            d = {x[0]: x[2] for x in v}
            if 0x81 in d and 0x82 in d and not isinstance(d[0x81], list):
                if _int(d[0x81]) == 1 and isinstance(d.get(0xA3), list):
                    nr = _int(d[0xA3][1][2])
                    res[nr] = res.get(nr, 0) + _int(d[0x82])
            else:
                entradas(v)

    def busca(nos):
        for t, _, v in nos:
            if isinstance(v, list):
                if v and v[0][0] == 0x02 and _int(v[0][2]) == eleicao:
                    entradas(v)
                else:
                    busca(v)

    busca(arvore(inner))
    res["validos"] = sum(n for k, n in res.items() if k != "validos")
    return res
