// Parsing e montagem de playlists HLS. Sem dependencia de APIs de extensao,
// pra poder rodar em teste (tools/test-hls.mjs).

const MAX_PLAYLIST_DEPTH = 3;
const DEFAULT_CONCURRENCY = 5;

export function resolveUrl(base, uri) {
  return new URL(uri, base).href;
}

export function parseAttributes(line) {
  const attrs = {};
  const re = /([A-Z0-9-]+)=("[^"]*"|[^,]*)/g;
  let match;
  while ((match = re.exec(line))) {
    attrs[match[1]] = match[2].replace(/^"|"$/g, '');
  }
  return attrs;
}

export function isMasterPlaylist(lines) {
  return lines.some((line) => line.startsWith('#EXT-X-STREAM-INF'));
}

// Escolhe a variante de maior bandwidth de um master playlist.
export function bestVariant(playlistUrl, lines) {
  let best = null;
  for (let i = 0; i < lines.length; i += 1) {
    if (!lines[i].startsWith('#EXT-X-STREAM-INF')) continue;
    const attrs = parseAttributes(lines[i]);
    const bandwidth = Number(attrs.BANDWIDTH || attrs['AVERAGE-BANDWIDTH'] || 0);
    const target = lines.slice(i + 1).find((line) => line && !line.startsWith('#'));
    if (!target) continue;
    if (!best || bandwidth > best.bandwidth) {
      best = { bandwidth, resolution: attrs.RESOLUTION || '', url: resolveUrl(playlistUrl, target) };
    }
  }
  return best;
}

// Extrai os segmentos de um playlist de midia (o EXT-X-MAP vem primeiro).
export function segmentsFrom(playlistUrl, lines) {
  const segments = [];
  let init = null;

  for (const line of lines) {
    if (line.startsWith('#EXT-X-KEY')) {
      const attrs = parseAttributes(line);
      if (attrs.METHOD && attrs.METHOD !== 'NONE') {
        throw new Error(`Stream criptografado (${attrs.METHOD}): a extensao nao monta esse arquivo.`);
      }
      continue;
    }
    if (line.startsWith('#EXT-X-MAP')) {
      const attrs = parseAttributes(line);
      if (attrs.URI) init = resolveUrl(playlistUrl, attrs.URI);
      continue;
    }
    if (!line || line.startsWith('#')) continue;
    segments.push(resolveUrl(playlistUrl, line));
  }

  return init ? [init, ...segments] : segments;
}

function splitLines(text) {
  return text.split(/\r?\n/).map((line) => line.trim());
}

// Segue master playlists ate achar o playlist de midia.
export async function resolveMediaPlaylist(url, fetchText, depth = 0) {
  const lines = splitLines(await fetchText(url));
  if (!isMasterPlaylist(lines)) return { url, lines };
  if (depth >= MAX_PLAYLIST_DEPTH) throw new Error('Playlist aninhado demais.');

  const variant = bestVariant(url, lines);
  if (!variant) throw new Error('Nenhuma variante encontrada no playlist.');
  return resolveMediaPlaylist(variant.url, fetchText, depth + 1);
}

// Baixa os segmentos em paralelo mantendo a ordem original.
export async function fetchSegments(segments, fetchBuffer, onProgress, concurrency = DEFAULT_CONCURRENCY) {
  const buffers = new Array(segments.length);
  let cursor = 0;
  let done = 0;

  async function worker() {
    while (cursor < segments.length) {
      const index = cursor;
      cursor += 1;
      buffers[index] = await fetchBuffer(segments[index], index);
      done += 1;
      if (onProgress) onProgress(done, segments.length);
    }
  }

  const workers = Math.max(1, Math.min(concurrency, segments.length));
  await Promise.all(Array.from({ length: workers }, worker));
  return buffers;
}
