# Verificação de alegações sobre transferências entre campanhas ligadas ao MBL (SP)

Base: dados abertos do TSE (cdn.tse.jus.br), arquivos baixados em 21/10/2026. Cada número tem a fonte em
`output/fluxos.csv`, `output/pessoas.csv` e nos demais CSVs de `output/`, no formato `arquivo:linha`.
Os scripts que geram tudo estão em `scripts/`.

**Premissa corrigida.** O vídeo situa os fatos em 2026, mas eles são da **eleição de 2022**. Em 2022 todos os
envolvidos concorreram pelo **União Brasil**. Alex Macedo, Amanda Vettorazzo e Felippe Lourenço não foram
candidatos em 2026. Os votos citados no vídeo (1.619 e 712) batem exatamente com 2022.

**Limitações.**
- O DivulgaCandContas e os portais `*.jus.br` estavam bloqueados pela rede deste ambiente. Por isso **a
  situação do julgamento das contas não foi verificada**, e o texto das resoluções vem de fontes secundárias
  (ver seção "Regras").
- As prestações de 2026 ainda são majoritariamente parciais: 18.157 linhas de relatório financeiro, 7.201
  parciais e 1.511 finais na base de receitas de SP.

---

## A) Fatos confirmados nos dados do TSE

### A.1 Candidaturas

| Ano | Candidato | Cargo | Partido / federação | Votos | Resultado | Despesa contratada |
|---|---|---|---|---:|---|---:|
| 2022 | Kim Kataguiri | Dep. federal | União | 295.460 | Eleito por QP | R$ 1.623.079 |
| 2022 | Cristiano Beraldo | Dep. federal | União | 43.460 | Suplente | R$ 1.369.724 |
| 2022 | Alex Macedo de Souza | Dep. federal | União | **1.619** | Suplente | R$ 735.025 |
| 2022 | Guto Zacarias | Dep. estadual | União | 152.481 | Eleito por QP | R$ 738.706 |
| 2022 | Renato Battista | Dep. estadual | União | 54.551 | Suplente | R$ 738.567 |
| 2022 | Amanda Vettorazzo | Dep. estadual | União | 54.720 | Suplente | R$ 567.545 |
| 2022 | Felippe Lourenço Oliveira Coelho | Dep. estadual | União | **712** | Suplente | R$ 199.960 |
| 2026 | Kim Kataguiri | Dep. federal | Missão | 520.071 | Eleito por QP | R$ 488.212 (parcial) |
| 2026 | Guto Zacarias | Dep. federal | Missão | 41.423 | Suplente | R$ 209.095 (parcial) |
| 2026 | Renato Battista | Dep. estadual | Missão | 89.489 | Suplente | R$ 146.567 (parcial) |
| 2026 | Cristiano Beraldo | Dep. federal | **PP** (fed. União/PP) | 13.858 | Suplente | R$ 927.740 (parcial) |

O nome correto é "Felippe" (com dois "p"). A busca por "Felipe Lourenço de Oliveira" não encontra o candidato.

Em 2022, Beraldo tem também um registro como deputado estadual (nº 44555) com situação `#NULO`. A doação a
Alex foi registrada na receita de Alex como vinda desse registro estadual, sem SQ do doador. A despesa
correspondente saiu da campanha federal de Beraldo.

### A.2 Doações recebidas por Alex Macedo (2022)

Todas foram feitas em **14/09/2022** e registradas como "Recursos de outros candidatos". Do lado do doador,
estão como despesa "Doações financeiras a outros candidatos/partidos", paga com a fonte **"Outros
Recursos"**, ou seja, **não** é FEFC nem Fundo Partidário. No arquivo de doador originário, todas essas
doações remontam a **pessoas físicas** (entre 7 e 41 registros cada).

| Doador | Valor no TSE | Fonte (lado doador) | Fonte |
|---|---:|---|---|
| Cristiano Beraldo | R$ 208.765,00 | Outros Recursos | receitas_candidatos_2022_SP.csv:32260 |
| Renato Battista | R$ 136.600,00 | Outros Recursos | receitas…:26103; despesas_contratadas…:119163 |
| Kim Kataguiri | R$ 121.435,00 | Outros Recursos | receitas…:22092; despesas_contratadas…:35020 |
| Amanda Vettorazzo | R$ 36.600,00 | Outros Recursos | receitas…:18117; despesas_contratadas…:122861 |
| Guto Zacarias | R$ 36.600,00 | Outros Recursos | receitas…:27941; despesas_contratadas…:274019 |
| **Total** | **R$ 540.000,00** | | |

Os cinco doadores receberam, entre agosto e setembro de 2022, a maior parte de seus recursos da **Direção
Municipal do União Brasil em São Paulo**, como "Outros Recursos": Kim R$ 1,10 mi, Beraldo R$ 902 mil,
Renato R$ 689 mil, Guto R$ 688 mil e Amanda R$ 468 mil.

Alex também recebeu do partido:
- R$ 180.000 de FEFC em dinheiro, da Direção Nacional (19/08/2022);
- R$ 48.624,53 de FEFC e R$ 11.907,42 de Fundo Partidário, da Direção Estadual, **todos em bens estimáveis**
  (material impresso conjunto, assessoria contábil e jurídica, programas de rádio e TV).

No total, Alex recebeu R$ 785.882,27. Pelo arquivo de despesas pagas, ele gastou R$ 180.000,00 com FEFC e
R$ 540.000,00 com Outros Recursos. Os R$ 180 mil de FEFC em dinheiro foram integralmente gastos.

### A.3 Doações recebidas por Felippe Lourenço (2022)

| Doador | Valor | Data | Fonte (lado doador) |
|---|---:|---|---|
| Renato Battista | R$ 100.000,00 | 16/09/2022 | Outros Recursos |
| Guto Zacarias | R$ 50.000,00 | 16/09/2022 | Outros Recursos |

Felippe também recebeu R$ 50.000 de FEFC da Direção Nacional (31/08/2022), além de estimáveis da Direção
Estadual. Ele gastou R$ 49.960,06 com FEFC e R$ 149.999,83 com Outros Recursos.

### A.4 Pagamento de Alex Macedo a Cristiano da Silva Lourenço

- **R$ 30.000,00**, despesa "Locação/cessão de bens imóveis", com a descrição "ALUGUEL DE IMOVEL PARA COMITÊ
  POLITICO". Contratada em 16/08/2022 e paga em 23/08/2022 por transferência eletrônica.
- Fonte: **FEFC**. Documento informado: tipo "Outro", nº "CONTRATO".
- Fonte: despesas_contratadas_candidatos_2022_SP.csv:43881; despesas_pagas_candidatos_2022_SP.csv:166952.
- O recebedor foi **candidato a vereador em Embu das Artes em 2020** (Solidariedade, não eleito). O CPF do
  fornecedor coincide com o do candidato em consulta_cand_2020_SP.csv:59563.
- Em 2024, há um candidato a vereador em Embu das Artes (PSB, suplente) com o mesmo nome completo. Nessa base
  o CPF não é divulgado, então a identidade de 2024 é só por nome.

### A.5 Pagamentos a pessoas físicas

| | Alex Macedo | Felippe Lourenço |
|---|---:|---:|
| Pagamentos a PF | 161 (161 pessoas) | 32 (32 pessoas) |
| Total a PF | R$ 445.179 (**61%** do gasto) | R$ 56.825 (28%) |
| Mediana / mínimo / máximo | R$ 1.500 / 280 / 30.000 | R$ 750 / 225 / 6.000 |
| Valores múltiplos de R$ 100 | 68% | 28% |
| Valores mais repetidos | R$ 1.500 (31×), R$ 1.220 (30×), R$ 600 (22×) | R$ 650 (10×), R$ 750 (9×), R$ 6.000 (5×) |
| Concentração de datas | 56 contratos em 18/08/2022; 12 datas no total | 9 em 01/09/2022; 10 datas no total |
| Descrições | "Equipe de rua" (73), "Cabo eleitoral" (44), coordenadores | "Cabo eleitoral" (23), coordenadores |

Detalhes em `pulverizacao_*.csv`.

### A.6 Custo por voto (despesa contratada ÷ votos nominais)

| Candidato (2022) | R$/voto | Mediana do cargo em SP | Vezes a mediana | Percentil |
|---|---:|---:|---:|---:|
| Alex Macedo (fed.) | **454,00** | 38,31 | **11,9×** | 97º |
| Felippe Lourenço (est.) | **280,84** | 23,24 | **12,1×** | 97º |
| Beraldo (fed.) | 31,52 | 38,31 | 0,8× | 43º |
| Renato Battista (est.) | 13,54 | 23,24 | 0,6× | 34º |
| Amanda Vettorazzo (est.) | 10,37 | 23,24 | 0,4× | 27º |
| Kim Kataguiri (fed.) | 5,49 | 38,31 | 0,1× | 7º |
| Guto Zacarias (est.) | 4,84 | 23,24 | 0,2× | 11º |

A comparação considera 1.197 candidatos a deputado federal e 1.286 a deputado estadual em SP, com voto e
gasto maiores que zero.

### A.7 Cruzamentos de recebedores PF com outras bases do TSE (`cruzamentos.csv`)

**Confirmados por CPF** (candidatos de 2020):
- pagos por Alex: Geizo Marques Alves (vereador, Embu das Artes, PL, R$ 10.000), Danilo Freitas de Barros
  (vereador, Embu das Artes, Solidariedade, R$ 3.500) e Cristiano da Silva Lourenço (A.4);
- pago por Felippe: Margareth Gonzaga da Silva Santos (vereadora, Santa Cruz da Conceição, DEM, R$ 650).

**Doadores que também receberam:** duas pessoas contratadas por Felippe como coordenadores (R$ 6.000 cada,
contratadas em 16/08/2022) aparecem como doadoras de R$ 2.500 cada à mesma campanha (17/08/2022). Essas
doações são **estimáveis**, não em dinheiro.

Nenhum recebedor PF de Alex ou Felippe aparece como fornecedor das campanhas de Kim, Beraldo, Renato, Guto ou
Amanda.

### A.8 Rede do grupo (`fluxos.csv`, `grafo.png`)

**2022.** Além das doações a Alex e Felippe:
- Kim doou a Ronaldo Formigão (R$ 150.000), Augusto Cesar Correa Neto (R$ 100.000) e Luis Antonio de Lima
  Clemente (R$ 24.997);
- Guto doou a Sergio de Paula Reis Filho (R$ 62.500), Juan Ramon Soto (R$ 32.500), Walter Martins Junior
  (R$ 30.000) e Cesar Rocha Andrade da Silva (R$ 25.000), e R$ 18.000 a Kim.

Todos os recebedores são do União Brasil. Todas as doações saíram como "Outros Recursos". Não há transferência
do grupo para candidatos de outros partidos.

**2026 (parcial).** A única transferência entre candidatos envolvendo o Missão em SP foi de Kim Kataguiri para
Rafael Francisco Ferraz Minatogawa (Missão, dep. estadual): R$ 64.898,50 em sete parcelas, como Outros
Recursos. Beraldo (PP) recebeu R$ 1.000.000 de FEFC da Direção Nacional do **PP** e R$ 24.000 da Direção
Estadual do PP. Não há repasse do Missão nem de candidatos do Missão para Beraldo.

---

## B) Irregularidades objetivas, com a regra violada

**Nenhuma irregularidade objetiva pôde ser demonstrada só com os dados abertos.** Item por item:

| Item | Regra | Conclusão |
|---|---|---|
| Doações de Kim, Renato, Guto, Amanda e Beraldo a Alex e Felippe (2022) | Res. TSE 23.607/2019, art. 17, § 2º (FEFC) e art. 19, § 7º (Fundo Partidário): vedam repasse a candidato de partido não coligado. | **Não se aplica.** Todos eram do mesmo partido, e a fonte registrada é "Outros Recursos", com doador originário pessoa física. A doação entre candidatos do mesmo partido com recursos próprios da campanha é permitida. |
| R$ 30.000 de FEFC por aluguel a Cristiano da Silva Lourenço | Res. 23.607, art. 60 (comprovação de gastos por documento fiscal idôneo ou outro meio idôneo de prova) | **Depende do julgamento.** Os dados mostram a despesa e o documento informado ("CONTRATO"), mas não se a locação foi comprovada. Ser ex-candidato de outro partido não torna o pagamento ilegal. |
| Pagamento de R$ 112.000 à mãe de Felippe | (pagamento a parente) | **Não existe nos dados.** Não há pagamento a "Silene" nem a nenhum fornecedor com sobrenome "Lourenço" nas despesas de Felippe, e nenhum fornecedor dele soma R$ 112 mil. |
| Contas de Alex "reprovadas" | Res. 23.607, art. 74 | **Não verificado.** A situação do julgamento não está nas bases abertas, e o DivulgaCandContas estava inacessível. A base registra a última versão da prestação final de Alex em **03/06/2025**, compatível com retificação durante o julgamento. |

---

## C) Indícios que merecem investigação (não são afirmação de crime)

1. **Concentração e simultaneidade.** Cinco candidatos transferiram exatamente R$ 540.000,00 a uma única
   campanha de deputado federal no mesmo dia (14/09/2022). Dois dias depois, dois deles transferiram
   R$ 150.000 a outra campanha. Essas duas campanhas tiveram custo por voto cerca de 12 vezes a mediana do
   cargo (97º percentil). Não é ilegal, mas pode valer apurar a finalidade eleitoral real.
2. **Origem em cadeia.** Pessoas físicas doaram ao Diretório Municipal do União Brasil em SP; o diretório
   repassou como "Outros Recursos" aos candidatos do grupo; esses candidatos repassaram a Alex e Felippe; Alex e
   Felippe pagaram centenas de pessoas físicas. O doador originário está identificado nos dados, mas não há
   explicação pública para a cadeia.
3. **Pulverização em Alex Macedo.** 161 pagamentos a pessoas físicas (61% do gasto). 56 contratos foram
   assinados no mesmo dia, e valores se repetem (R$ 1.500 × 31; R$ 1.220 × 30). Vários recebedores foram
   candidatos a vereador em Embu das Artes em 2020 ou 2024. A apuração possível é verificar se os serviços
   foram prestados (art. 60, § 3º, permite exigir documentação complementar).
4. **Aluguel de comitê de R$ 30.000 (FEFC)** pago a um ex-candidato a vereador de Embu das Artes. Cabe verificar
   a propriedade do imóvel, o contrato e o uso efetivo como comitê.
5. **Coordenadores de Felippe que doaram serviços estimáveis à campanha** um dia depois de serem contratados.
   O ponto é verificar se a mesma atividade foi declarada duas vezes (paga e doada).
6. **Inconsistência de registro** na doação de Beraldo a Alex: na receita de Alex, o doador aparece como
   candidato a deputado estadual (nº 44555, registro `#NULO`); na despesa de Beraldo, a doação saiu da campanha
   federal.

---

## Alegação do vídeo × o que os dados mostram

| Alegação | O que os dados do TSE mostram | Situação |
|---|---|---|
| Eleições de 2026 | Os fatos são de 2022 (União Brasil) | **Incorreta** |
| Alex Macedo, dep. federal, 1.619 votos | Confirmado (2022) | **Confirmada** |
| Beraldo → Alex R$ 208.765 | R$ 208.765,00, 14/09/2022, Outros Recursos | **Confirmada** |
| Renato → Alex R$ 136.600 | R$ 136.600,00, 14/09/2022, Outros Recursos | **Confirmada** |
| Kim → Alex R$ 121.435 | R$ 121.435,00, 14/09/2022, Outros Recursos | **Confirmada** |
| Amanda → Alex R$ 36.000 | **R$ 36.600,00** | Confirmada com valor diferente |
| Guto → Alex R$ 36.000 | **R$ 36.600,00** | Confirmada com valor diferente |
| Total ~R$ 539.999,99 | R$ 540.000,00 | Confirmada |
| Contas de Alex reprovadas por não comprovar aluguel | Não verificável nesta coleta. Existe um aluguel de R$ 30 mil pago com FEFC. | **Não verificada** |
| Pulverização em pagamentos pequenos a PF | 161 pagamentos a PF, 61% do gasto, mediana de R$ 1.500 | **Confirmada** (fato, não ilícito) |
| R$ 30.000 do fundo eleitoral a "Cristiano da Silva", ligado a candidatura em Embu das Artes | R$ 30.000 de FEFC a Cristiano da Silva Lourenço, candidato a vereador em Embu das Artes em 2020 (CPF) e homônimo em 2024 | **Confirmada** |
| Felipe Lourenço de Oliveira, dep. estadual, 712 votos | Felippe Lourenço Oliveira Coelho, 712 votos (2022) | **Confirmada** (nome diferente) |
| Renato → Felipe R$ 110.000 | **R$ 100.000,00** | Confirmada com valor diferente |
| Guto → Felipe R$ 50.000 | R$ 50.000,00 | **Confirmada** |
| Felipe repassou R$ 112.000 à mãe, Silene Aparecida Lourenço | Nenhum pagamento a ela nos dados. Nenhuma "Silene Aparecida Lourenço" candidata em SP em 2020, 2022, 2024 ou 2026. | **Não confirmada** |
| Silene, vereadora eleita pelo PL | Não encontrada nas bases de candidatos de SP | **Não confirmada** |
| Recursos eram do fundo eleitoral | Os repasses entre candidatos foram "Outros Recursos" (doador originário PF). O FEFC aparece só no aluguel de R$ 30 mil e nos gastos diretos de Alex e Felippe. | **Incorreta** quanto aos repasses |

---

## Regras (Res. TSE 23.607/2019)

O site do TSE estava inacessível deste ambiente. Os trechos abaixo vêm de **transcrições secundárias**
(acórdãos de TREs e material técnico) e **precisam ser conferidos** no texto compilado oficial antes de
qualquer uso:
https://www.tse.jus.br/legislacao/compilada/res/2019/resolucao-no-23-607-de-17-de-dezembro-de-2019

- **Art. 17, § 2º** (redação da Res. 23.665/2021): "É vedado o repasse de recursos do FEFC, dentro ou fora da
  circunscrição, por partidos políticos ou candidatas ou candidatos: I - não pertencentes à mesma coligação;
  e/ou II - não coligados." O STF declarou o dispositivo constitucional na ADI 7214 (30/09/2022).
- **Art. 19, § 7º:** regra equivalente para o Fundo Partidário (também mantida na ADI 7214).
- **Art. 60, § 1º e § 3º:** admitem qualquer meio idôneo de prova dos gastos e permitem à Justiça Eleitoral
  exigir documentação complementar quando houver dúvida sobre a execução do objeto. Há precedente do TSE
  admitindo exigir prova da propriedade de imóvel locado de pessoa física quando a despesa é paga com recurso
  público.
- **Pagamento a parentes:** não localizei vedação expressa na resolução. A questão é de comprovação da
  efetiva prestação (art. 60).
- **Eleições 2026:** a Res. 23.607 foi alterada pelas Res. 23.752 (fev/2026) e 23.770 (2026). As mudanças
  identificadas tratam dos prazos de distribuição do FEFC (art. 17, §§ 9º a 9º-B) e não afetam as regras
  acima. Para os fatos de 2022 vale a redação vigente naquela eleição.
