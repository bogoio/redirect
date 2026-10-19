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
