# Relatório final - 2º turno 2026 (Flávio Bolsonaro x Lula)

Data de referência: 19/10/2026. Votação: 25/10/2026.

## Estimativa final

**Flávio Bolsonaro: cerca de 84% de chance de vitória** (faixa plausível de 79% a 88%).
Participação bipartidária esperada: **~52,1%** (intervalo de 80%: 49,4% a 54,9%).

## Como chegamos lá

| Camada | Participação do Flávio | P(Flávio vence) |
|---|---|---|
| Agregador de pesquisas, cenário A (bruto) | 51,66% | 79,2% |
| Agregador, cenário B (ajuste de casa) | 51,68% | 79,6% |
| Só Veritá + Gerp | 52,25% | 86% |
| Transferência dos votos do 1º turno (central) | 52,5% | - |
| **Combinação pesquisas + transferência** | **~52,1%** | **~84%** |
| Polymarket (19/10, normalizado) | - | 78,2% |

## 1. Agregador de pesquisas

- 17 pesquisas de 2º turno, 11 institutos, conferidas contra a lista original.
- Peso = desempenho no 1º turno × recência (meia-vida 4 dias) × amostra.
- O 1º turno separou os institutos em dois grupos: Veritá, Gerp, Futura e Vox erraram menos de 0,6 ponto; os tradicionais (Datafolha, Quaest, AtlasIntel, PoderData, CNT/MDA, BTG) subestimaram o Flávio em 1,6 a 4,2 pontos.
- Resultado: os quatro que acertaram ficam com ~95% do peso. Veritá (12-16/out) sozinha responde por 29% da média.
- Incerteza: erro de eleição t de Student (5 g.l., dp 2,0) + dispersão entre pesquisas (1,37) = dp total 2,42.

## 2. Sensibilidade

- Na grade completa, P(Flávio) varia de 75% a 86%.
- A premissa que mais mexe é o tamanho do erro de eleição: dp 1,5 → ~83%; dp 2,5 → ~76%.
- Meia-vida, versão da Veritá, ajuste de casa e "só top-4" mexem 1 ponto ou menos, porque o peso já está concentrado nos institutos que acertaram.

## 3. Sinais fora das pesquisas

- **Transferência:** sobraram 7,8% no 1º turno, sendo 4,7% de direita antipetista (Renan Santos, Caiado, Zema) e 2,9% do Cury. Flávio precisa de 38% desses votos; Lula, de 62%. Em hipóteses razoáveis de divisão, Flávio fica entre 51,6% e 53,1%.
- **Histórico:** desde 1989, quem liderou o 1º turno sempre venceu o 2º.
- **Mercado:** Polymarket em ~78%, com US$ 187 milhões negociados; o preço implica erro de eleição de ~2,1 pontos, compatível com a premissa do modelo.
- **Mobilização:** o ato na Paulista em 18/10 reduz o risco de desmobilização da base do Flávio.

## 4. Riscos (o caminho do Lula)

- Erro sistemático de ~2 pontos nas pesquisas a favor do Flávio (já aconteceu na direção oposta no 1º turno).
- Comparecimento maior de quem se absteve no 1º turno, sobretudo no Nordeste.
- Fato novo na última semana (debate, escândalo).
- Mudança de locais de votação (4.352 seções, ~0,4% do eleitorado): efeito estimado em décimos de ponto, sem direção partidária clara.

## Conclusão

Flávio é favorito claro, mas não certo: aproximadamente **5 em 6**. Uma vitória do Lula exigiria um erro de pesquisa de cerca de 2 pontos, algo dentro do histórico brasileiro.

## Limitações

- Um único 1º turno é amostra pequena para medir qualidade de instituto.
- As divisões de transferência são premissas, não dados medidos.
- Algumas pesquisas têm data ou amostra aproximadas (marcadas como `baixa` em `polls_r2.csv`).
- Resultado do 1º turno conferido via CartaCapital, não diretamente no portal do TSE.
