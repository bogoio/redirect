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
- Resultado do julgamento das contas de 2022. O DivulgaCandContas (consultado em 21/10/2026) não traz o
  resultado. Ele informa os processos no PJe do TRE-SP: Alex Macedo **0605945-18.2022.6.26.0000** (retificadora
  entregue em 03/06/2025) e Felippe Lourenço **0607025-17.2022.6.26.0000** (só a entrega final de 01/11/2022).
  Para consultar: a consulta pública unificada do PJe exige captcha (fazer à mão). Outra opção é liberar na rede
  do ambiente `comunicaapi.pje.jus.br` ou `api-publica.datajud.cnj.jus.br`.
- Res. 23.607: conferida no texto oficial (`output/res_23607_artigos.md`).
- Acesso ao TSE: `www.tse.jus.br` e `divulgacandcontas.tse.jus.br` respondem 403 (Akamai) ao curl e só
  funcionam por navegador (Playwright/Chromium).
