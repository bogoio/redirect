# Pesquisa de candidatos - fase 1 (concorrência oficial e IP)

Data: 2026-10-27. Status: **parcial**. A coluna de demanda (vendidos) depende do Terapeak, porque o eBay bloqueia o acesso automatizado a partir da nuvem (HTTP 403) e a API do usuário não tem o escopo Marketplace Insights. Ranking final e Top 10 só depois da demanda.

Dados completos: `candidatos.csv`.

## O que os dados já mostram

| Candidato | Oficial concorrente | Preço oficial | Risco IP | Leitura |
|---|---|---|---|---|
| Scarface | Blitzway 1/4 | ~€666 | ALTO | Terapeak: média $63, 54 vendedores, 3 dos 6 top removidos por violação |
| Taxi Driver | sem estátua, só 1/6 Present Toys | ~$190 revenda | médio | lacuna de estátua |
| Godfather | Blitzway 1/4 Vito | $499 | médio | você já converte aqui |
| Clint Eastwood | Sideshow Legacy | $420 / $640 | médio-alto | oficial ativo no seu preço |
| Bruce Lee | Blitzway, Star Ace | $499 | ALTO | espólio processa uso de imagem |
| Rocky | Sideshow / Sly Shop 1:10 | $140 / $349 | médio-alto | oficial barato |
| Breaking Bad | Supacraft 1/4, threezero 1/6 | $499 / $155 | médio-alto | saturado |
| Goodfellas, Pulp Fiction, Lebowski, Rambo | não encontrado | - | médio | possíveis lacunas, falta demanda |
| Flintstones | Iron Studios 1/10 | $130 | médio-alto | oficial barato limita peça avulsa |
| Wacky Races | só Bearbrick/Funko | $20-675 | médio-alto | lacuna de estátua |
| Space Ghost / Jonny Quest | nada encontrado | - | médio-alto | lacuna; HQ nova em 2025-26 |
| Pink Panther | HCG 16" | $605 | médio-alto | bom para FDM |
| Popeye 1929 | não pesquisado | - | baixo-médio | domínio público nos EUA desde 2025 (marca não) |
| Chaves/Chapolin | só Funko/Little People | - | médio | sem estátua oficial |
| Asterix | Pixi, Plastoy | €130-250 | médio-alto | demanda europeia, escapa da tarifa |
| Tintin | Pixi/Moulinsart | - | MUITO ALTO | descartar |

## Primeiras conclusões (sem demanda ainda)
1. **Descartar:** Tintin (há condenação contra esculturas de resina) e Bruce Lee.
2. **Scarface:** o mercado de custom é barato e sofre takedown. Fica fora do tier premium.
3. **Lacunas de estátua oficial:** Taxi Driver, Goodfellas, Pulp Fiction, Lebowski, Wacky Races, Space Ghost/Jonny Quest e Chaves. Esses são os primeiros a validar no Terapeak.
4. **Oficial barato ($130-155):** Flintstones, Rocky e Heisenberg 1/6 tiram espaço de peça avulsa. Só o diorama diferencia.

## Próximo passo
Rodar a coleta de vendidos (Terapeak) no computador do usuário, nos termos do CSV e nos sites .com, .co.uk, .de, .ca e .com.au.

## Fontes
- [Blitzway Scarface 1/4](https://www.1001hobbies.co.uk/statues/727201-blitzway-99375-scarface-1-4-superb-scale-statue-8809321472273.html)
- [Present Toys Taxi Driver 1/6 (eBay.de)](https://www.ebay.de/itm/156785389243)
- [Blitzway Vito Corleone (Sideshow)](https://www.sideshow.com/collectibles/the-godfather-vito-corleone-blitzway-903718/)
- [Sideshow Man with No Name](https://www.sideshow.com/collectibles/clint-eastwood-the-man-with-no-name-faux-bronze-sideshow-collectibles-200710)
- [Blitzway Bruce Lee](https://news.toyark.com/2019/10/25/bruce-lee-tribute-statue-by-blitzway-368891) · [processo Bruce Lee Enterprises](https://hongkongfp.com/2019/12/26/bruce-lees-daughter-sues-fast-food-chain-using-fathers-image/)
- [Rocky Gonna Fly Now](https://www.sideshow.com/collectibles/rocky-gonna-fly-now-sly-stallone-shop-915643) · [Rocky Over Drago](https://www.sideshow.com/collectibles/rocky-over-drago-through-the-ropes-sly-stallone-shop-915694)
- [Supacraft Walter White](https://www.sideshow.com/collectibles/breaking-bad-walter-white-supacraft-903147) · [threezero Heisenberg](https://www.sideshow.com/collectibles/breaking-bad-heisenberg-threezero-902349)
- [Iron Studios Fred Flintstone](https://www.sideshow.com/collectibles/the-flintstones-fred-flintstone-iron-studios-910753)
- [Bearbrick Muttley](https://www.sideshow.com/collectibles/wacky-races-bearbrick-muttley-100-400-medicom-toy-910258)
- [Space Ghost/Jonny Quest HQ](https://graphicpolicy.com/2025/05/06/preview-space-ghost-jonny-quest-space-quest-1/)
- [Pink Panther HCG](https://www.sideshow.com/collectibles/pink-panther-and-the-inspector-hollywood-collectibles-group-908302)
- [Popeye em domínio público (NPR)](https://www.npr.org/2024/12/26/nx-s1-5231543)
- [Funko Chaves (Xataka)](https://www.xataka.com.mx/cine-y-tv/oficial-primeros-funko-pop-chavo-chapulin-colorado-llegaran-diciembre)
- [Pixi Asterix (eBay.de)](https://www.ebay.de/itm/256867733249)
- [Caso das esculturas de Tintin](https://globalfreedomofexpression.columbia.edu/cases/the-case-of-the-tintin-sculptures/)
- [Lei de direito de imagem da Califórnia](https://en.wikipedia.org/wiki/California_Celebrities_Rights_Act)
