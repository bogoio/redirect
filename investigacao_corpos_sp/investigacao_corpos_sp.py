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

# Casos conhecidos ate 23/10/2026. Lista incompleta (faltam ~10 dos 20).
CASOS = [
    dict(data=date(2026, 9, 5), local="Jabaquara (R. Contos Gauchescos)", municipio="Sao Paulo",
         zona="Sul", metodo="amarrado, saco plastico, posicao fetal",
         vitima="Jose Zito da Conceicao, 55", oficial=True, obs=None),
    dict(data=date(2026, 9, 10), local="Via publica", municipio="Sao Paulo",
         zona=None, metodo="amarrada, saco plastico + cobertor",
         vitima="mulher nao identificada", oficial=True, obs="unica mulher na conta oficial"),
    dict(data=date(2026, 9, 10), local="Colonia", municipio="Sao Paulo",
         zona="Leste", metodo="amarrado, cobertor, cabeca em sacos",
         vitima=None, oficial=True, obs=None),
    dict(data=date(2026, 9, 19), local="Jacana (R. Antonio Nascente)", municipio="Sao Paulo",
         zona="Norte", metodo="esquartejado em sacolas",
         vitima="Murilo Sanches dos Santos, 26", oficial=True, obs=None),
    dict(data=date(2026, 9, 21), local="Jardim Celeste", municipio="Sao Paulo",
         zona="Sul", metodo="porta-malas de veiculo",
         vitima=None, oficial=True, obs=None),
    dict(data=date(2026, 9, 25), local="Vila Andrade", municipio="Sao Paulo",
         zona="Sul", metodo="enrolado em lencol",
         vitima=None, oficial=True, obs=None),
    dict(data=date(2026, 9, 27), local="Jardim Sao Luis (Av. Guido Caloi)", municipio="Sao Paulo",
         zona="Sul", metodo="decapitacao; cabeca separada",
         vitima=None, oficial=True, obs="corpo a ~21 km, em Itapecerica da Serra, enrolado em lencol"),
    dict(data=date(2026, 10, 2), local="Ciclovia Parque Ecologico do Tiete", municipio="Sao Paulo",
         zona="Leste", metodo="saco plastico preto",
         vitima=None, oficial=True, obs="perto do CT do Corinthians"),
    dict(data=date(2026, 10, 13), local="Belenzinho", municipio="Sao Paulo",
         zona="Leste", metodo=None, vitima=None, oficial=True, obs=None),
    dict(data=date(2026, 10, 13), local="Represa Billings, Riacho Grande (Anchieta km 29)",
         municipio="Sao Bernardo do Campo", zona=None, metodo="na agua",
         vitima=None, oficial=None, obs=None),
    dict(data=date(2026, 10, 21), local="Estrada Borba Gato", municipio="Itapecerica da Serra",
         zona=None, metodo="porta-malas de carro abandonado no mato",
         vitima="homem, nao divulgado", oficial=None,
         obs="20o corpo; RG e boletim de ocorrencia dentro do carro"),
]


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


if __name__ == "__main__":
    print("CSV salvo em", salvar_csv())
    resumo()
