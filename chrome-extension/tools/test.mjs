// Testes das partes puras da extensao (parsing de playlist e classificacao de URL).
// Uso: node tools/test.mjs

import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
  bestVariant,
  fetchSegments,
  isMasterPlaylist,
  parseAttributes,
  resolveMediaPlaylist,
  segmentsFrom
} from '../src/hls.js';

import { classify, formatBytes, formatDuration, suggestFilename } from '../src/shared.js';

const MASTER = `#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360
360/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2400000,RESOLUTION=1280x720
720/index.m3u8`;

const MEDIA = `#EXTM3U
#EXT-X-TARGETDURATION:6
#EXT-X-MAP:URI="init.mp4"
#EXTINF:6.0,
seg0.m4s
#EXTINF:6.0,
seg1.m4s
#EXT-X-ENDLIST`;

const ENCRYPTED = `#EXTM3U
#EXT-X-KEY:METHOD=AES-128,URI="key.bin"
#EXTINF:6.0,
seg0.ts`;

test('reconhece master playlist e escolhe a maior bandwidth', () => {
  const lines = MASTER.split('\n');
  assert.equal(isMasterPlaylist(lines), true);
  const best = bestVariant('https://cdn.example.com/v/master.m3u8', lines);
  assert.equal(best.url, 'https://cdn.example.com/v/720/index.m3u8');
  assert.equal(best.resolution, '1280x720');
});

test('segue o master ate o playlist de midia', async () => {
  const responses = {
    'https://cdn.example.com/v/master.m3u8': MASTER,
    'https://cdn.example.com/v/720/index.m3u8': MEDIA
  };
  const playlist = await resolveMediaPlaylist(
    'https://cdn.example.com/v/master.m3u8',
    async (url) => responses[url]
  );
  assert.equal(playlist.url, 'https://cdn.example.com/v/720/index.m3u8');
});

test('extrai segmentos com o init na frente', () => {
  const segments = segmentsFrom(
    'https://cdn.example.com/v/720/index.m3u8',
    MEDIA.split('\n')
  );
  assert.deepEqual(segments, [
    'https://cdn.example.com/v/720/init.mp4',
    'https://cdn.example.com/v/720/seg0.m4s',
    'https://cdn.example.com/v/720/seg1.m4s'
  ]);
});

test('recusa playlist criptografado', () => {
  assert.throws(
    () => segmentsFrom('https://cdn.example.com/v/index.m3u8', ENCRYPTED.split('\n')),
    /criptografado/
  );
});

test('parseAttributes le valores com e sem aspas', () => {
  const attrs = parseAttributes('#EXT-X-KEY:METHOD=AES-128,URI="https://x/y?a=1",IV=0x00');
  assert.equal(attrs.METHOD, 'AES-128');
  assert.equal(attrs.URI, 'https://x/y?a=1');
});

test('fetchSegments preserva a ordem mesmo em paralelo', async () => {
  const segments = Array.from({ length: 12 }, (_, i) => `s${i}`);
  const buffers = await fetchSegments(
    segments,
    async (url) => {
      await new Promise((r) => setTimeout(r, Math.random() * 5));
      return url;
    },
    null,
    4
  );
  assert.deepEqual(buffers, segments);
});

test('classify separa playlist, segmento e arquivo', () => {
  assert.equal(classify('https://x/y/index.m3u8'), 'hls');
  assert.equal(classify('https://x/y/manifest.mpd'), 'dash');
  assert.equal(classify('https://x/y/seg1.ts'), 'segment');
  assert.equal(classify('https://x/y/filme.mp4'), 'video');
  assert.equal(classify('https://x/y/stream', 'video/mp4'), 'video');
  assert.equal(classify('blob:https://x/abc'), 'blob');
  assert.equal(classify('https://x/y/pagina.html'), null);
});

test('suggestFilename limpa o titulo e usa a extensao certa', () => {
  assert.equal(
    suggestFilename({ url: 'https://x/y/a.mp4', title: 'Meu: vídeo / teste' }),
    'Meu vídeo teste.mp4'
  );
  assert.equal(suggestFilename({ url: 'https://x/y/index.m3u8', kind: 'hls', title: 'Aula 1' }), 'Aula 1.ts');
});

test('formatadores', () => {
  assert.equal(formatBytes(1536), '1.5 KB');
  assert.equal(formatDuration(3725), '1:02:05');
  assert.equal(formatDuration(95), '1:35');
});
