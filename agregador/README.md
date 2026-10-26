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

`python atualizar_r2.py <wikitext>` reconstrói `polls_r2.csv` inteiro a partir da Wikipedia (instruções no topo do script). Pesquisa que ainda não está na Wikipedia vai em `polls_r2_manual.csv` (mesmo formato), que não é sobrescrito; linha da Wikipedia errada ou duplicada vai em `polls_r2_excluir.csv` (instituto, campo_inicio, campo_fim, motivo). Formato:

Adicione uma linha em `polls_r2.csv`:

```
instituto,campo_inicio,campo_fim,n,flavio,lula,base,nao_validos,confianca_dado,observacao
Quaest,2026-10-20,2026-10-22,2000,47,45,totais,8,alta,
```

- `instituto`: use exatamente o mesmo nome de `polls_r1.csv` para herdar o erro de casa (ex.: `PoderData`, não `PoderData/Aya`).
- `base`: `validos` ou `totais`. A conversão é sempre `flavio / (flavio + lula)`, então os não válidos não alteram a participação bipartidária; `nao_validos` é só registro.
- `n` vazio: o modelo usa a mediana dos demais.
- Sem data de campo: use a data de divulgação menos 2 dias em início e fim, marque `confianca_dado` como `media`/`baixa` e explique em `observacao`.

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

## Mercado de previsão calibrado (`mercado.csv`)

O preço do Polymarket entra como segunda estimativa, mas corrigido pela calibração histórica da plataforma (`calibracao/`): em vez do preço, usa a taxa com que favoritos de preço parecido, no mesmo prazo e em mercados de eleição, venceram de fato. Para atualizar, rode `python ../calibracao/calibrar_preco.py --preco <preço> --dias <dias até a eleição>` e acrescente uma linha. O resumo mostra a probabilidade do modelo A, a do mercado calibrado e a média simples das duas.

## Projeção durante a apuração (`projecao.py`)

Cruza cada zona já apurada no 2º turno com a mesma zona no 1º turno, mede o deslocamento ("swing") da participação do Flávio (por UF quando a UF tem pelo menos 5 zonas e 3% dos votos apurados; senão pela região; senão nacional) e aplica esse swing às zonas que faltam. Assim a projeção não depende da ordem em que as urnas chegam.

- `python projecao.py --backtest`: simula a apuração de 2022 (1º -> 2º turno) em três ordens de chegada (Sul/Sudeste primeiro, aleatória, Nordeste primeiro). Saída em `output/projecao_backtest_2022.csv`. Com 1% das zonas, a projeção errou no máximo 0,45 ponto; o total parcial errou de 2 a 18 pontos.
- `python projecao.py --parcial parcial.csv`: projeção a partir de um CSV (`sg_uf,cd_municipio,nr_zona,flavio,lula`).
- **Domingo: `python feed_tse.py --loop 3`** baixa do TSE as ~6.100 zonas (arquivo por município e zona, `resultados.tse.jus.br/oficial/ele2026/6258/dados/...`), estende zonas parcialmente apuradas pela fração de seções (a partir de 10%) e imprime a parcial do TSE e a projeção a cada 3 minutos. Testado no 1º turno (eleição 6257): todas as zonas casam com a base e a projeção reproduz o resultado. Primeira rodada ~3 min; zonas 100% apuradas ficam em cache.
- O intervalo de 90% vem de um bootstrap bayesiano das zonas e mede só o sorteio: não capta que as primeiras zonas podem diferir das demais. Na prática, some ±0,5 ponto.

## Buscas no Google (`tendencias.py`)

Parte do Flávio nas buscas (Google Trends, "Flávio Bolsonaro" x "Lula"). Não entra no modelo: o nível não diz nada ("Lula" é nome curto de presidente no cargo; a direita teve 22% das buscas no 1º turno de 2026 e 51% dos votos) e a variação nas duas semanas finais acompanhou o movimento das pesquisas em 2018, mas não o erro delas em 2022 (busca da direita estável ou caindo, e Bolsonaro acima das pesquisas nos dois turnos). Serve como termômetro de momento.

## Chuva x comparecimento (`chuva.py`)

Chuva no dia de cada turno (NASA POWER, grade de 0,5°; 2014, 2018 e 2022) cruzada com a variação do comparecimento do 1º para o 2º turno em cada município, com efeito fixo de ano x UF e erro-padrão agrupado por UF-ano. Coeficiente: -0,135 ponto de comparecimento por unidade de log(1 + mm) a mais no 2º turno (t = -3,4); 20 mm ou mais no 2º turno e não no 1º: -0,29 ponto. Aplicado à previsão de 25/10 (Open-Meteo, por capital, cada município herda a capital mais próxima): comparecimento cai até 0,44 ponto no Sudeste, mas o efeito na participação do Flávio é de -0,01 a -0,02 ponto, porque quem deixa de votar vota como o próprio município. Não entra no modelo. Os dados da NASA para 2026 ainda são preliminares e vêm com valores impossíveis; por isso o 1º turno de 2026 entra como "seco" ou com a chuva média dos 1º turnos anteriores.

## Cenário: indecisos contra o governo (`indecisos()` em `model.py`)

Teste em `historico/testes_teoria.py`: nos 2º turnos com presidente candidato (2014 e 2022), institutos com mais indecisos superestimaram o governo; a fração dos indecisos que foi para o governo fica entre 0,07 (todas as pesquisas) e 0,28 (sem Gerp, Brasmarket e Veritá), contra 0,5 da divisão proporcional, com evidência fraca (t de 1,0 a 1,8). O cenário redistribui os indecisos de cada pesquisa (100 - Flávio - Lula nos votos totais; pesquisa só em válidos recebe a mediana) com 28% para Lula e 72% para o Flávio, e soma ao erro a incerteza da fração (de 0,07 a 0,5). Aparece no resumo; não altera a estimativa base. O mesmo arquivo testa o voto envergonhado (modo remoto x presencial) e não acha efeito.

## Revisão de outubro (pesos e incerteza)

- **Piso de erro no peso de desempenho (`tau_prior`, padrão 1,25):** `peso_desempenho = 1 / (erro_típico² + tau_prior²)`; antes o piso era 0,5. Entra na grade de sensibilidade (0,5 / 1,25 / 2,0).
- **Repetição do mesmo instituto:** a k-ésima rodada mais recente de cada instituto entra com peso dividido por √k (`peso_repeticao`), porque os erros de método de um instituto são correlacionados entre rodadas.
- **Pesos do cenário B:** calculados sobre o erro que sobra depois de descontar metade do viés (parte não-viés + metade do viés) mais a incerteza do próprio viés (`INCERTEZA_VIES` = 1,25).
- **Deriva até a eleição:** `sd_total` soma `sd_drift = 0,25 × √(idade efetiva)`, em que a idade efetiva é a média, ponderada pelos pesos, de dias entre o meio do campo e `--hoje`. Use `--hoje` = data da eleição para a previsão final.
- **Diagnóstico no resumo:** N efetivo de Kish (1 / Σ peso²) e participação dos 4 institutos de maior peso.
