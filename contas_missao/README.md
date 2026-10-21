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
- Situação do julgamento das contas de Alex Macedo (SQ 250001602051) e Felippe Lourenço (SQ 250001602115), 2022.
- Conferir o texto oficial da Res. TSE 23.607/2019, arts. 17 § 2º, 19 § 7º, 60 e 74 (as transcrições do relatório são de fontes secundárias).
- Tentativa de 21/10/2026: a rede do ambiente recusa divulgacandcontas.tse.jus.br, www.tse.jus.br, www.tre-sp.jus.br,
  consultaunificadapje.tse.jus.br e planalto.gov.br (só cdn.tse.jus.br responde). Buscas na web não acharam notícia
  sobre o julgamento dessas duas contas. Para concluir: liberar esses domínios na configuração de rede do ambiente.
