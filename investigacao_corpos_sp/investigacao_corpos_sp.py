#!/usr/bin/env python3
"""
INVESTIGACAO: CORPOS ABANDONADOS NA GRANDE SP (set-out 2026)
=============================================================
Handoff de uma sessao no Claude.ai para continuar no Claude Code.

CONTEXTO
--------
Em 22/10/2026 o g1 SP noticiou o 20o corpo abandonado na Grande SP desde
setembro, com a suspeita de "serial killer" descartada pela policia.
Raciocinio estrutural/falsificacionista: testar hipoteses contra os dados,
nao acumular confirmacao.

Hipotese oficial (DHPP / SSP): execucoes do "tribunal do crime" do PCC,
autores diferentes, motivacoes especificas. Um caso avancado indicaria
retaliacao por suspeita de estupro.

Pontos levantados:
1. Eixo Itapecerica - Embu - Taboao: ja em ago/2026 havia forca-tarefa
   porque 18 corpos foram achados em Embu das Artes desde o inicio do
   ano (seccional de Taboao da Serra). Local de desova regional com
   vitimas de varias cidades -> logistica de grupo, nao individuo.
2. Dispersao na capital: 4 ZL, 3 ZS, 1 ZN, 1 ZO, metodos variados
   (ensacado, esquartejado, queimado). Contra autor unico.
3. 20o caso: corpo em porta-malas de carro abandonado na Estrada Borba
   Gato, Itapecerica, com RG e um boletim de ocorrencia dentro do carro.
   Pergunta aberta: BO de roubo do carro (vitima = ladrao punido?) ou BO
   feito pela vitima (procurou a policia = motivo de "julgamento")?
4. A contagem de 20 e da imprensa; a conta oficial "forte" e ~9 casos
   com perfil de execucao (5/set a 13/out). Inclui casos heterogeneos
   (ex.: Lapa, sem sinais de violencia).
5. Pergunta central: por que o pico em setembro e por que deixar corpos
   visiveis (recado)? O que mudou no territorio/faccao?

PROXIMOS PASSOS
---------------
- Completar a tabela CASOS (os 20) com buscas em g1, SBT News, Estadao,
  Folha, DGABC, TMC. Campos vazios = None.
- Marcar quais entram na contagem oficial vs. so na da imprensa.
- Agrupar por municipio/seccional, metodo e intervalo entre casos.
- Plotar no mapa (folium) para ver clusters.
- Comparar com base historica de homicidios/encontros de cadaver da SSP-SP
  (dados abertos) para checar se o volume e anomalo ou so o metodo.

FONTES JA USADAS
----------------
- https://tmc.com.br/brasil/corpos-abandonados-grande-sp-pcc-tribunal-crime-itapecerica/
- https://sbtnews.sbt.com.br/noticia/brasil/corpos-encontrados-em-sp-ainda-sao-misterio
- https://sbtnews.sbt.com.br/noticia/brasil/serial-killer-o-que-se-sabe-sobre-os-corpos-achados-em-sp
- https://www.gazetasp.com.br/policia/fim-do-misterio-do-suposto-serial-killer-em-sp-policia-identifica-3-suspeitos-e-descarta-hipotese-de-assassino-em-serie/
- https://www.dgabc.com.br/Noticia/4351536/policia-investiga-mortes-em-serie-em-sp-mas-descarta-acao-de-serial-killer
- https://www.dgabc.com.br/Noticia/4351589/
- https://www.bnewssaopaulo.com.br/noticias/policia/sp-policia-descarta-serial-killer-apos-corpos-serem-achados-em-sacos-de-lixo.html
- https://www.maisgoias.com.br/brasil/policia-cria-forca-tarefa-para-investigar-desova-de-corpos-na-grande-sp/

Uso: python investigacao_corpos_sp.py  -> gera casos.csv e imprime resumo
"""

import csv
from collections import Counter
from datetime import date

# Casos conhecidos ate 23/10/2026. Lista ainda incompleta.
# fonte: m = Metropoles (mapa dos 12), s = SBT News (9 oficiais), t = TMC, a = ABCD Jornal
# lat/lon = centro aproximado do bairro, NAO o endereco exato.
def caso(d, local, municipio, zona, metodo, vitima, oficial, obs, fonte, lat, lon):
    return dict(data=d, local=local, municipio=municipio, zona=zona, metodo=metodo,
                vitima=vitima, oficial=oficial, obs=obs, fonte=fonte, lat=lat, lon=lon)


CASOS = [
    caso(date(2026, 9, 5), "Jabaquara (R. Contos Gauchescos)", "Sao Paulo", "Sul",
         "amarrado, saco plastico, posicao fetal", "Jose Zito da Conceicao, 55", True, None,
         "m,s", -23.646, -46.641),
    caso(date(2026, 9, 10), "Vila Chuca (R. Osmano Ungaretti, 146)", "Sao Paulo", None,
         "cobertor dentro de saco plastico; tiros no rosto e cabeca",
         "Yasmin Dandara Silveira Brisola, 32", True, "unica mulher na conta oficial",
         "m,s", None, None),
    caso(date(2026, 9, 10), "Colonia (R. Zenichi Sato, 9)", "Sao Paulo", "Leste",
         "amarrado, cobertor, saco plastico", "Filipe de Carvalho Cabral, 34", True,
         "desaparecido desde 6/9", "m,s", -23.553, -46.437),
    caso(date(2026, 9, 13), "Cidade Nitro Quimica, Sao Miguel Paulista (Av. Eduardo Sabino de Oliveira)",
         "Sao Paulo", "Leste", "corrego; queimado, amarrado, saco plastico",
         "Rodrigo Machado de Albuquerque, 35", None, None, "m", -23.505, -46.428),
    caso(date(2026, 9, 19), "Jacana (R. Antonio Nascentes, 385)", "Sao Paulo", "Norte",
         "esquartejado em sacolas", "Murilo Sanches dos Santos, 26", True,
         "desaparecido ha ~10 dias", "m", -23.457, -46.582),
    caso(date(2026, 9, 21), "Jardim Celeste (R. Herbert Smith, 56)", "Sao Paulo", "Sul",
         "porta-malas; lencol + saco plastico; decomposicao avancada",
         "Rafael Zimbarg Francez, 25, motorista de app", True, None, "m", -23.661, -46.617),
    caso(date(2026, 9, 25), "Vila Andrade (R. Sao Joao do Pernambuco, 37)", "Sao Paulo", "Sul",
         "lencol, maos e pes amarrados", "homem branco nao identificado", True, None,
         "m", -23.629, -46.737),
    caso(date(2026, 9, 27), "Jardim Sao Luis (Av. Guido Caloi, 900)", "Sao Paulo", "Sul",
         "decapitacao; cabeca numa praca", None, True,
         "corpo a ~21 km, em Itapecerica da Serra, enrolado em lencol", "m,s", -23.655, -46.733),
    caso(date(2026, 9, 30), "Colonia (R. Tadao Inoue, 1.200), sob o Rodoanel", "Sao Paulo", "Leste",
         "cobertor; pulsos amarrados com fio; tiro na cabeca", None, None, None,
         "m", -23.560, -46.430),
    caso(date(2026, 10, 2), "Ciclovia Parque Ecologico do Tiete", "Sao Paulo", "Leste",
         "saco plastico preto; bracos e pernas com fita", "homem nao identificado", True,
         "perto do CT do Corinthians", "m,s", -23.493, -46.523),
    caso(date(2026, 10, 8), "Grajau (Av. Paulo Guilguer Reimberg, perto da estacao Varginha)",
         "Sao Paulo", "Sul", None, "homem", True, None, "s", -23.776, -46.697),
    caso(date(2026, 10, 8), "Eldorado (R. Botocudos)", "Diadema", None,
         None, None, None, "'provavel corpo', area de dificil acesso; nao confirmado na serie",
         "a", -23.708, -46.623),
    caso(date(2026, 10, 9), "Jardim Lourdes (R. Filinto Elisio)", "Sao Paulo", None, None,
         "homem nao identificado, 20-25", True, None, "s", None, None),
    caso(date(2026, 10, 13), "Belenzinho", "Sao Paulo", "Leste", None, None, True,
         "denuncia de disparos na noite anterior", "s", -23.541, -46.590),
    caso(date(2026, 10, 13), "Represa Billings, Riacho Grande (Anchieta km 28-29)",
         "Sao Bernardo do Campo", None, "na agua, 'pacote' boiando", None, True, None,
         "s", -23.773, -46.537),
    caso(date(2026, 10, 21), "Vila Guilherme (Marginal Tiete)", "Sao Paulo", "Norte",
         "esquartejado em 4 sacos", "Lucimara Garcia do Nascimento de Freitas, 35", None,
         "PM flagrou 2 homens com os sacos; um suspeito morreu no confronto", "m", -23.510, -46.606),
    caso(date(2026, 10, 21), "Tremembe (Av. Cel. Sezefredo Fagundes, 25.555), mata", "Sao Paulo", "Norte",
         "trauma na cabeca; sacos plasticos", "Milber Conceicao Paiva, 43", None,
         "desaparecido desde 19/10", "m", -23.415, -46.596),
    caso(date(2026, 10, 21), "Estrada Borba Gato", "Itapecerica da Serra", None,
         "porta-malas de carro abandonado no mato", "homem, nao divulgado", None,
         "20o corpo; RG e boletim de ocorrencia dentro do carro", "t", -23.718, -46.849),
    caso(date(2026, 10, 22), "Marginal Tiete (via)", "Sao Paulo", None, None, "homem", None,
         "~5h30; trecho nao informado", "correiodamanha", None, None),
]

# Na contagem da imprensa, mas ainda sem caso individual achado:
# Lapa / 2a da Zona Oeste, Barueri (1), Santana de Parnaiba (1),
# Embu das Artes (1), ABC alem de SBC (Santo Andre / Sao Caetano).


def salvar_csv(caminho="casos.csv"):
    campos = list(CASOS[0].keys())
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for c in sorted(CASOS, key=lambda x: x["data"]):
            w.writerow({k: ("" if v is None else v) for k, v in c.items()})
    return caminho


def resumo():
    casos = sorted(CASOS, key=lambda x: x["data"])
    print(f"Casos catalogados: {len(casos)} de 20 noticiados\n")
    print("Linha do tempo:")
    anterior = None
    for c in casos:
        gap = f"(+{(c['data'] - anterior).days}d)" if anterior else ""
        print(f"  {c['data']} {gap:>7}  {c['municipio']:<22} {c['local']}")
        anterior = c["data"]
    print("\nPor municipio:", dict(Counter(c["municipio"] for c in casos)))
    print("Por zona (capital):", dict(Counter(c["zona"] for c in casos if c["zona"])))
    ligados_itapecerica = [c for c in casos if "Itapecerica" in (c["municipio"] + (c["obs"] or ""))]
    print(f"Casos ligados a Itapecerica: {len(ligados_itapecerica)}")
    print("Por mes:", dict(Counter(c["data"].strftime("%Y-%m") for c in casos)))


def mapa(caminho="mapa.html"):
    try:
        import folium
    except ImportError:
        print("folium nao instalado; mapa pulado")
        return None
    m = folium.Map(location=[-23.6, -46.65], zoom_start=10, tiles="OpenStreetMap")
    for c in sorted(CASOS, key=lambda x: x["data"]):
        if c["lat"] is None:
            continue
        cor = "red" if c["oficial"] else "gray"
        folium.CircleMarker(
            [c["lat"], c["lon"]], radius=7, color=cor, fill=True, fill_opacity=0.8,
            popup=f"{c['data']} - {c['local']}<br>{c['metodo'] or ''}<br>{c['vitima'] or ''}",
        ).add_to(m)
    # ligacao cabeca/corpo do caso de 27/9
    folium.PolyLine([[-23.655, -46.733], [-23.716, -46.849]], color="red", dash_array="5").add_to(m)
    m.save(caminho)
    return caminho


if __name__ == "__main__":
    print("CSV salvo em", salvar_csv())
    resumo()
    print("Mapa salvo em", mapa())
