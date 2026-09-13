// Documento offscreen: baixa e junta os segmentos de um playlist HLS e devolve um blob URL.
// Precisa rodar aqui porque o service worker do MV3 nao tem URL.createObjectURL.

import { fetchSegments, resolveMediaPlaylist, segmentsFrom } from './hls.js';

async function fetchText(url) {
  const res = await fetch(url, { credentials: 'include' });
  if (!res.ok) throw new Error(`HTTP ${res.status} ao ler o playlist.`);
  return res.text();
}

async function fetchBuffer(url, index) {
  const res = await fetch(url, { credentials: 'include' });
  if (!res.ok) throw new Error(`HTTP ${res.status} no segmento ${index + 1}.`);
  return res.arrayBuffer();
}

async function buildStream(url, kind) {
  if (kind === 'dash') {
    throw new Error('DASH (.mpd) nao e montado pela extensao. Use o comando ffmpeg.');
  }

  const playlist = await resolveMediaPlaylist(url, fetchText);
  const segments = segmentsFrom(playlist.url, playlist.lines);
  if (!segments.length) throw new Error('Playlist sem segmentos.');

  const report = (done, total) => {
    chrome.runtime.sendMessage({ type: 'STREAM_PROGRESS', url, done, total }).catch(() => {});
  };
  report(0, segments.length);

  const buffers = await fetchSegments(segments, fetchBuffer, report);
  const blob = new Blob(buffers, { type: 'video/mp2t' });
  return URL.createObjectURL(blob);
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (!msg || msg.target !== 'offscreen') return false;

  if (msg.type === 'REVOKE') {
    URL.revokeObjectURL(msg.blobUrl);
    sendResponse({ ok: true });
    return false;
  }

  if (msg.type === 'BUILD_STREAM') {
    buildStream(msg.url, msg.kind)
      .then((blobUrl) => sendResponse({ ok: true, blobUrl }))
      .catch((err) => sendResponse({ ok: false, error: String((err && err.message) || err) }));
    return true;
  }

  return false;
});
