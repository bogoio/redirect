#!/bin/sh
# Baixa as bases usadas. Rodar a partir de contas_missao/.
set -e
CDN=https://cdn.tse.jus.br/estatistica/sead/odsele
for y in 2020 2022 2024 2026; do
  mkdir -p dados_brutos/cand$y && (cd dados_brutos/cand$y && curl -sSO $CDN/consulta_cand/consulta_cand_$y.zip && unzip -oq consulta_cand_$y.zip '*_SP.csv' 'leiame*')
done
for y in 2022 2026; do
  mkdir -p dados_brutos/contas$y dados_brutos/votacao$y
  (cd dados_brutos/contas$y && for k in candidatos orgaos_partidarios; do curl -sSO $CDN/prestacao_contas/prestacao_de_contas_eleitorais_${k}_$y.zip; unzip -oq prestacao_de_contas_eleitorais_${k}_$y.zip '*_SP.csv' 'leiame*'; done)
  (cd dados_brutos/votacao$y && curl -sSO $CDN/votacao_candidato_munzona/votacao_candidato_munzona_$y.zip && unzip -oq votacao_candidato_munzona_$y.zip '*_SP.csv' leiame.pdf)
done
