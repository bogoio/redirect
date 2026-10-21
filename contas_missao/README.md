# contas_missao

Verificação, com dados abertos do TSE, de alegações (vídeo) sobre transferências entre campanhas ligadas ao
MBL / Partido Missão em SP. **Resultado principal:** os fatos são da eleição de **2022** (União Brasil), não de 2026.

## Estrutura
- `dados_brutos/` - arquivos de cdn.tse.jus.br (não versionados; recriar com `scripts/baixar.sh`)
- `scripts/`
  - `baixar.sh` - baixa e extrai as bases (candidatos 2020/22/24/26, contas e votação 2022/26, SP)
  - `comum.py` - leitura das bases, preservando arquivo e linha de origem
  - `01_candidatos.py` - busca inicial das pessoas na base de 2026
  - `02_fluxos.py` - pessoas (cargo, partido, votos) e fluxos entre campanhas -> `pessoas.csv`, `fluxos.csv`
  - `03_pulverizacao.py` - pagamentos a PF, cruzamentos, custo por voto
  - `04_grafo.py` - `grafo.png`
- `output/`
  - `relatorio.md` - seções A (fatos), B (irregularidades objetivas), C (indícios) e tabela alegação × dados
  - `representacao_rascunho.md` - rascunho de notícia de fato à PRE-SP
  - `fluxos.csv`, `pessoas.csv`, `pulverizacao_*.csv`, `cruzamentos.csv`, `custo_por_voto.csv`, `grafo.png`

## Rodar
```sh
cd contas_missao
sh scripts/baixar.sh          # ~1,7 GB de downloads
pip install pandas matplotlib networkx
python3 scripts/02_fluxos.py && python3 scripts/03_pulverizacao.py && python3 scripts/04_grafo.py
```

## Privacidade
Somente dados publicados pelo TSE. CPFs são usados só internamente para cruzar bases e nunca aparecem nas saídas.

## Pendências
- Julgamento (DataJud, 21/10/2026): Alex Macedo, contas **aprovadas com ressalvas** (16/10/2025) e depois
  cumprimento de sentença; Felippe Lourenço, contas **aprovadas** (19/11/2024). Ver `output/relatorio.md`.
- Falta ler o acórdão de Alex (motivo das ressalvas e valor cobrado). A `comunicaapi.pje.jus.br` bloqueia
  acessos de fora do Brasil (geobloqueio do CloudFront), e a consulta pública do PJe tem um desafio anti-robô que
  não deve ser contornado. O `dje-consulta.tse.jus.br` (tentado em 21/10/2026) só lista edições
  do DJE do próprio TSE e exige captcha (`rest/diario/captcha` = true) para pesquisar. As intimações do TRE-SP
  de 2025 saem no DJEN (CNJ), o mesmo sistema geobloqueado da comunicaapi. Falta obter o acórdão à mão.
- Res. 23.607: conferida no texto oficial (`output/res_23607_artigos.md`).
- `www.tse.jus.br` e `divulgacandcontas.tse.jus.br` só funcionam por navegador (Playwright), não por curl.
