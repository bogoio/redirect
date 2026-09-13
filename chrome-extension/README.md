# Pega Vídeo

Extensão de Chrome (Manifest V3) que detecta as mídias da aba atual e baixa com um clique.

## Como funciona

Duas fontes de detecção, que se complementam:

1. **Sniffer de rede** (`src/background.js`): escuta `webRequest.onHeadersReceived` e guarda tudo que
   volta como vídeo/áudio ou como playlist (`.m3u8`, `.mpd`). Segmentos soltos (`.ts`, `.m4s`) são
   ignorados, senão a lista viraria uma enxurrada.
2. **Varredura do DOM** (`src/content.js`): procura `<video>`, `<audio>` e `<source>` na página,
   inclusive dentro de shadow DOM aberto, e manda duração e resolução junto.

O que foi detectado fica por aba em `chrome.storage.session` e some quando a aba navega ou fecha.
O contador no ícone mostra quantas mídias há na aba.

## Instalação

1. `chrome://extensions`
2. Ligue o **Modo do desenvolvedor**
3. **Carregar sem compactação** e aponte para a pasta `chrome-extension/`

## Uso

Dê play no vídeo por alguns segundos (é o play que dispara as requisições), abra o popup e clique em
**Baixar**.

- **MP4/WebM e afins**: download direto pela API `chrome.downloads`, com os cookies da sessão.
- **HLS (`.m3u8`)**: a extensão resolve o master playlist, escolhe a variante de maior bandwidth,
  baixa os segmentos (5 em paralelo, ordem preservada) e junta num `.ts` único. A montagem roda num
  documento offscreen porque o service worker do MV3 não tem `URL.createObjectURL`. Para converter
  depois: `ffmpeg -i saida.ts -c copy saida.mp4`.
- **DASH (`.mpd`)**: não é montado aqui. O botão **ffmpeg** copia a linha de comando pronta.
- **`blob:`**: esse URL só existe dentro da página, não dá para baixar de fora. Reescaneie depois de
  dar play e pegue o stream real que o sniffer detectou.

## Limites conhecidos

- **DRM não passa.** Widevine, PlayReady e FairPlay entregam mídia criptografada; a extensão para com
  um aviso em vez de fingir que deu certo. Vale para os serviços de streaming por assinatura.
- **HLS com `#EXT-X-KEY`** (AES-128/SAMPLE-AES) também é recusado.
- Alguns CDNs exigem `Referer` na requisição. A API de downloads não deixa mandar cabeçalho próprio,
  então esses casos falham; o botão **ffmpeg** existe justamente como saída.
- A montagem de HLS acontece na memória, então arquivos muito longos podem pesar.
- Quando o HLS separa vídeo e áudio em renditions diferentes (`#EXT-X-MEDIA`), a extensão pega só a
  variante de vídeo. Nesse caso o `.ts` sai mudo e o caminho é o ffmpeg com as duas faixas.
- Só baixe o que você tem direito de baixar.

## Desenvolvimento

```bash
node tools/test.mjs        # testes das partes puras (parsing de playlist, classificação, nomes)
python3 tools/make_icons.py  # regera os PNGs de icons/
```

Estrutura:

```
manifest.json
src/background.js   service worker: sniffer, estado por aba, downloads
src/content.js      varredura do DOM
src/hls.js          parsing de playlist e download ordenado dos segmentos (testável)
src/offscreen.js    monta o HLS e cria o blob URL
src/popup.*         interface
src/shared.js       classificação de URL, formatação, nome de arquivo
tools/              testes e gerador de ícones
```
