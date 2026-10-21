# Calibração do Polymarket

Testa duas hipóteses com mercados já resolvidos:

1. **Viés favorito-azarão**: favoritos em faixas altas de preço vencem mais do que o preço indica.
2. **Volume e prazo**: mercados com mais volume e mais perto do evento são mais bem calibrados.

## Rodar

```bash
pip install requests pandas numpy matplotlib
python coleta.py --amostra 200   # amostra + esquema real dos dados
python coleta.py --so-lista      # só a lista de mercados (metadados)
python coleta.py                 # coleta completa: lista + históricos (retoma do cache)
python analise.py                # gera output/
```

Cache em `cache/` (fora do git): `cache/mercados/pagina_NNNNNN.json` (100 mercados por página, com o cursor seguinte) e `cache/historico/<token_id>.json`. Apagar um arquivo força baixar de novo só aquele pedaço.

## Coleta (`coleta.py`)

- **Mercados**: `GET https://gamma-api.polymarket.com/markets/keyset` com `closed=true`, `end_date_min=2023-02-01`, `volume_num_min=1000`, `include_tag=true`, paginando por `after_cursor` (máximo de 100 por página). `/markets` com `offset` recusa offsets altos (erro 422 "use /markets/keyset").
- Campos guardados: `id`, `question`, `slug`, `conditionId`, `category`, `volumeNum`, `startDate`, `createdAt`, `endDate`, `closedTime`, `umaResolutionStatus`, `outcomes`, `outcomePrices`, `clobTokenIds`, `negRisk`, `groupItemTitle`, `events` (id, slug, título, negRisk) e `tags` (rótulos). `outcomes`, `outcomePrices` e `clobTokenIds` vêm como texto JSON; os tokens seguem a ordem de `outcomes`.
- **Histórico**: `GET https://clob.polymarket.com/prices-history` com `market=<token do 1º resultado>` e `fidelity=60` (de hora em hora). Para mercado encerrado, `interval=max` volta vazio; a API só aceita janelas `startTs`/`endTs` curtas (15 dias passam, 30 não). Por isso são 3 janelas de 14 dias contadas para trás a partir de `closedTime`, cobrindo 42 dias.
- Mercados de 2022 não têm histórico na CLOB (todos vieram vazios na amostra); daí o corte em fevereiro de 2023.
- Pausa de 0,25 s entre chamadas; em erro 429/5xx ou de rede, novas tentativas com espera crescente (2 s, 4 s, ..., até 60 s).

## Análise (`analise.py`)

**Limpeza**
- Binário: exatamente 2 resultados. Inclui pares que não são Yes/No (por exemplo, dois times); o 1º resultado faz o papel do "Yes".
- Resolução clara: preço final acima de 0,99 de um lado e abaixo de 0,01 do outro (a API às vezes traz 0,99999...). Descarta 0/0, 50/50 e preços intermediários.
- Descarta histórico com menos de 5 pontos.

**Momento do evento**: primeiro instante em que o preço passa de 0,98 (ou fica abaixo de 0,02) e se mantém assim, do mesmo lado, por 12 horas; ou a data de fim (`endDate`), o que vier primeiro. Todos os instantâneos são medidos antes desse momento.

**Instantâneos**: preço 24 horas, 3 dias, 7 dias e 30 dias antes do momento do evento. Usa o último ponto até o instante, e só se ele tiver no máximo 48 horas de defasagem.

**Favorito**
- *Todos os contratos*: cada mercado conta; o favorito é o lado acima de 50%.
- *Favorito por evento* (padrão dos cortes): em eventos com vários candidatos mutuamente exclusivos (`negRisk`), o favorito é o contrato com o maior preço do Yes no instante, e o volume é a soma do evento. Em outros grupos com vários mercados (por exemplo, faixas de preço de cripto), fica só o mercado de maior volume do evento.

**Faixas**: 50-60, 60-70, 70-80, 80-85, 85-90, 90-95 e 95-99 (preço acima de 99% fica de fora). Em cada faixa: casos, acerto, preço médio, intervalo de Wilson a 95% e diferença acerto - preço em pontos percentuais.

**Cortes**: volume (abaixo de 100 mil, 100 mil a 1 milhão, 1 a 10 milhões, acima de 10 milhões de dólares), prazo (24 h, 3, 7 e 30 dias), categoria e período (momento do evento antes de 2024 ou de 2024 em diante).

**Categoria "política"**: o mercado tem uma tag entre Politics, Elections, Election, U.S. Politics, Global Elections, World Elections, US Election, Geopolitics, Trump, Biden, Congress e Senate, **ou** a pergunta contém uma destas palavras: election, elected, president, presidential, senate, governor, prime minister, parliament, congress, nominee, nomination, primary, vote, mayor, chancellor, trump, biden, harris, democrat, republican, minister, referendum, cabinet. O resto é "outros".

**Métricas**: Brier score e log loss do preço do favorito (preço limitado a [0,0001; 0,9999]) por grupo de cada corte.

**Teste do viés favorito-azarão**: nas faixas de 80% para cima, z = (vitórias − soma dos preços) / √(soma de p(1−p)), unilateral (H1: o favorito vence mais do que o preço indica). Mostra o efeito em pontos percentuais por faixa e agregado.

## Saídas (`output/`)

| Arquivo | Conteúdo |
|---|---|
| `calibracao_geral.csv` | faixas nas duas versões (todos os contratos e favorito por evento), prazos somados |
| `calibracao_por_volume.csv`, `_por_prazo.csv`, `_por_categoria.csv`, `_por_periodo.csv` | faixas por corte (favorito por evento) |
| `metricas_brier_logloss.csv` | Brier e log loss por grupo de cada corte |
| `vies_favorito_azarao.csv` | teste nas faixas de 80% para cima |
| `resposta_alto_volume_24h_7d.csv` | favorito a 80-90, 90-95 e 95-99%, volume acima de 10 milhões, 24 h a 7 dias antes: acerto e intervalo |
| `maiores_erros.csv` | favoritos acima de 80% que perderam, do maior volume para o menor |
| `curva_*.png` | curvas de calibração com a diagonal de referência |

## Limitações

- **Amostra pequena nas faixas altas**: perto de 95-99%, poucos favoritos perdem. Diferenças de 1 ou 2 pontos ficam dentro do intervalo de confiança mesmo com milhares de casos.
- **Dependência entre mercados**: a versão "favorito por evento" reduz o problema, mas cada evento ainda entra até 4 vezes (um por prazo) quando os prazos são somados. Eventos diferentes também podem ser correlacionados (vários mercados sobre a mesma eleição em eventos separados). Os intervalos de confiança supõem independência e, por isso, são otimistas.
- **Viés de seleção da plataforma**: só entram mercados que o Polymarket criou e que foram resolvidos. Mercados cancelados ou resolvidos como inválidos ficam de fora, e a mistura de temas (esporte, cripto, política) muda ao longo do tempo.
- **Momento do evento** é uma heurística: um mercado que oscila perto de 98% sem que o fato tenha acontecido pode ter o momento marcado cedo demais.
- **Volume** é o volume total do mercado (ou a soma do evento), não o volume no momento do instantâneo.
- **Preço do histórico** é o preço da série da CLOB (ponto médio/último negócio), não o preço executável com o spread.
