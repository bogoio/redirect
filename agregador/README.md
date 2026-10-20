# Agregador de pesquisas - 2º turno 2026 (Flávio Bolsonaro x Lula)

Votação em 25/10/2026. Média ponderada das pesquisas + Monte Carlo para P(Flávio vence).

## Rodar

```bash
pip install pandas numpy matplotlib
python model.py                    # usa a data de hoje
python model.py --hoje 2026-10-19  # fixa a data de referência
```

Saídas em `output/`:
- `pesquisas_cenario_A.csv`, `pesquisas_cenario_B.csv` - cada pesquisa: participação bipartidária, pesos, peso final normalizado e contribuição para a média
- `house_errors_r1.csv` - erro de casa de cada instituto no 1º turno
- `sensibilidade_grade.csv` (pivot) e `sensibilidade_longa.csv` - P(Flávio vence) em cada célula
- `grafico_pesquisas.png` - pesquisas (tamanho = peso), média ponderada e faixa de 80%
- `resumo.txt` - resumo em 5 linhas

## Acrescentar uma pesquisa nova

Adicione uma linha em `polls_r2.csv`:

```
instituto,campo_inicio,campo_fim,n,flavio,lula,base,nao_validos,confianca_dado,observacao
Quaest,2026-10-20,2026-10-22,2000,47,45,totais,8,alta,
```

- `instituto`: use exatamente o mesmo nome de `polls_r1.csv` para herdar o erro de casa (ex.: `PoderData`, não `PoderData/Aya`).
- `base`: `validos` ou `totais`. A conversão é sempre `flavio / (flavio + lula)`, então os não válidos não alteram a participação bipartidária; `nao_validos` é só registro.
- `n` vazio: o modelo usa a mediana dos demais.
- Sem data de campo: use a data de divulgação menos 2 dias em início e fim, marque `confianca_dado` como `media`/`baixa` e explique em `observacao`.
- Atualize `esperado_r2` em `check_inputs()` (conferência de quantidade de linhas).

Depois rode `python model.py` de novo.

## Premissas

- **Calibração**: resultado oficial do 1º turno, Flávio 47,03 x Lula 45,16 → participação bipartidária 51,01%. Erro de casa = participação na pesquisa da véspera - 51,01 (negativo = subestimou o Flávio). A Veritá tem duas versões (47x45 padrão; 45,14x44,65 alternativa, testada na sensibilidade).
- **Peso** = desempenho × recência × amostra
  - desempenho = 1 / (erro_casa² + 0,5²). Sem 1º turno (Ipespe, DataTrends): erro mediano dos institutos tradicionais (Quaest, PoderData, Real Time Big Data, AtlasIntel, Datafolha, CNT/MDA, BTG/Nexus) = -2,61. PoderData/Aya herda o erro da PoderData.
  - recência = exp(-ln2 × idade / meia_vida), meia-vida 4 dias, idade do meio do campo até a data de referência. Rodadas antigas do mesmo instituto entram com o peso reduzido, não são descartadas.
  - amostra = sqrt(min(n, 5000) / 1000).
- **Cenário A**: média ponderada bruta. **Cenário B**: cada estimativa menos metade do erro de casa do instituto.
- **Incerteza**: erro de eleição t de Student (5 g.l.) reescalada para dp 2,0 pontos, somado em quadratura com o dp ponderado entre as estimativas. 100.000 simulações por cenário (semente fixa).
- **Sensibilidade**: dp 1,5/2,0/2,5 × meia-vida 3/4/7 × A/B × Veritá padrão/alternativa × todas vs. só top-4 (Veritá, Gerp, Futura, Vox Brasil - erro na diferença do 1º turno < 2 pontos).

## Limitações conhecidas

- O peso de desempenho é muito agressivo: com erro de casa perto de zero, Veritá/Gerp/Futura/Vox ficam com ~95% do peso e os institutos tradicionais com ~1% cada. Por isso o cenário B e o cenário "só top-4" quase não diferem do A. Um único 1º turno é uma amostra pequena para medir qualidade de instituto.
- Dados de confiança `baixa`: Vox Brasil recente (data e n supostos), PoderData/Aya e BTG/Nexus (datas aproximadas, n imputado).
- O dp do erro de eleição (2,0) é premissa externa e é o fator que mais mexe em P.

## Cenário de malícia estrutural

Fatores que as pesquisas não medem ficam em `estrutural.csv` (`efeito` em pontos da participação do Flávio, `dp` = incerteza do fator, `lado` = direita ou governo). O modelo aplica sobre o cenário A quatro combinações (`CENARIOS_ESTRUTURAIS` em `model.py`): neutro, equilibrado, direita forte (direita ×1,5, governo ×0,5) e governo forte (o inverso). Cada cenário desloca a média pela soma dos efeitos e soma a incerteza dos fatores ao erro total. Saída: `output/cenarios_estruturais.csv`. Os efeitos são julgamento, não dado: edite o CSV para testar outras leituras.

## Estudo de comparecimento (`comparecimento.py`)

Estima se o comparecimento cresce mais do 1º para o 2º turno onde o PT é forte, e quanto isso deslocaria a participação do Flávio em 2026.

1. Baixe de https://dadosabertos.tse.jus.br, para 2014, 2018, 2022 e 2026, os arquivos `detalhe_votacao_munzona_AAAA.zip` e `votacao_candidato_munzona_AAAA.zip`, e coloque em `agregador/dados_tse/` (pasta ignorada pelo git).
2. Rode `python comparecimento.py`.

Método: regressão por município, ponderada pelo eleitorado, da variação do comparecimento (2º - 1º turno) contra voto do PT no 1º turno, abstenção no 1º turno, tamanho do município, região e efeito de ano. Os novos eleitores previstos votam como o próprio município votou no 1º turno. Inclui backtest (ajusta sem um ano e prevê esse ano). O script imprime uma linha pronta para substituir `comparecimento_nordeste` em `estrutural.csv`.

Limitação: os novos eleitores do 2º turno podem votar diferente da média do município; o resultado deve ser lido como deslocamento mínimo esperado.

## Histórico dos institutos (`historico/`)

`historico/pesquisas_vespera.csv`: última pesquisa de cada instituto nos 10 dias antes de cada turno de 2014, 2018 e 2022 (54 pesquisas, 19 institutos), extraída do wikitext da Wikipedia em português por `historico/extrair.py` (`python -I historico/extrair.py <pasta_com_wikitext>`), com o erro na participação do adversário do PT contra o resultado do TSE. Em 2014 a Wikipedia só lista Ibope, Datafolha, Vox Populi e CNT/MDA, sem tamanho de amostra.

Com `historico=True` (padrão), `model.py` usa esse histórico mais o 1º turno de 2026: viés do instituto = média dos erros encolhida para 0, desempenho = erro quadrático médio encolhido para o geral (`K_ENCOLHIMENTO` = 2 pseudo-observações). Instituto sem histórico recebe o erro geral. A grade de sensibilidade compara com o critério antigo (`pesos = so_r1_2026`).

## Transferência de votos (`transferencia.py`)

Regressão ecológica por município (2014-2022): fração dos votos de cada eliminado do 1º turno que foi para o adversário do PT, aplicada aos eliminados de 2026. Os coeficientes por candidato são instáveis (falácia ecológica); vale o agregado.
