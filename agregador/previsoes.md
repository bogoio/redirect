# Previsões registradas antes do 2º turno (25/10/2026)

Registradas em 24/10/2026, antes das pesquisas finais de sábado. Participação do Flávio nos votos válidos.

| Fonte | Vencedor | Placar | Chance do Flávio | P(Flávio ≥ 52,5%) |
|---|---|---|---|---|
| Modelo (base, `model.py`) | Flávio | 51,2% (80%: 48,7–53,8) | 74% | 25% |
| Modelo, cenário indecisos contra o governo | Flávio | 52,5% | 89% | 50% |
| Modelo + mercados calibrados | Flávio | — | 73% | — |
| Kalshi (escada de votos, 21/10) | Flávio | mediana ~52% | 78,5% (bruto) | ~42% |
| Usuário (heurística) | Flávio | **≥ 52,5%** | 96% | — |

Balanço depois do resultado: comparar cada linha com o resultado oficial do TSE e rodar o balanço por zona (`projecao.py`, `feed_tse.py`).

## Previsão final (25/10/2026, 13h, antes do fechamento das urnas)

60 pesquisas (últimas: Quaest, AtlasIntel, Futura e PoderData de 23-24/out), `python model.py --hoje 2026-10-25`.

| Fonte | Flávio | Faixa de 80% | Chance do Flávio |
|---|---|---|---|
| Modelo A (pesquisas) | 50,9% | 48,4–53,5 | 69% |
| Modelo B (ajuste de casa) | 51,1% | — | 72% |
| Polymarket 79,9% / Kalshi 80,5%, calibrados | — | — | ~72,5% |
| **Aposta final (modelo A + mercados)** | **50,9%** | | **~71%** |
| Usuário | ≥ 52,5% | | 96% |

## Resultado (TSE, 99,8% das seções, 25/10/2026 21:19)

Lula 64.102.155 (51,76%) × Flávio 59.741.925 (**48,24%**). Lula vence por ~4,4 milhões de votos.

| Fonte | Flávio previsto | Erro | Vencedor |
|---|---|---|---|
| Modelo A (pesquisas) | 50,9% | -2,7 pt | errado (dava 69% Flávio) |
| Modelo B (ajuste de casa) | 51,1% | -2,9 pt | errado |
| Mercados calibrados | — | — | errado (~72,5% Flávio) |
| Usuário | ≥ 52,5% | ≥ -4,3 pt | errado |
| Projeção da apuração (`feed_tse.py`) | 47,6–48,8% desde 300 zonas | ≤ 0,6 pt | certo (FORTE Lula desde 1,5% apurado) |

Leitura: erro das pesquisas de ~2,7 pt contra Flávio, na mesma direção em todas as regiões; Lula ficou com a maior parte do saldo dos eliminados no 1º turno e com o aumento de votos válidos, concentrado no Nordeste (dia da prorrogação até 19h). Análise de zonas anômalas pendente.
