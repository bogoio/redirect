// Helpers compartilhados entre o service worker e o popup.

export const VIDEO_EXTS = [
  'mp4', 'm4v', 'webm', 'mov', 'mkv', 'avi', 'flv', 'ogv', 'ogg', 'mpg', 'mpeg', '3gp'
];
export const AUDIO_EXTS = ['mp3', 'm4a', 'aac', 'wav', 'flac', 'opus'];
export const SEGMENT_EXTS = ['ts', 'm4s', 'cmfv', 'cmfa'];

export function pathExtension(url) {
  try {
    const { pathname } = new URL(url);
    const last = pathname.split('/').pop() || '';
    const dot = last.lastIndexOf('.');
    return dot === -1 ? '' : last.slice(dot + 1).toLowerCase();
  } catch {
    return '';
  }
}

// Retorna 'hls' | 'dash' | 'video' | 'audio' | 'segment' | 'blob' | null
export function classify(url, contentType = '') {
  if (!url || url.startsWith('data:')) return null;
  if (url.startsWith('blob:')) return 'blob';

  const ext = pathExtension(url);
  const ct = (contentType || '').split(';')[0].trim().toLowerCase();

  if (ext === 'm3u8' || ct === 'application/vnd.apple.mpegurl' || ct === 'application/x-mpegurl' ||
      ct === 'audio/mpegurl' || ct === 'audio/x-mpegurl') return 'hls';
  if (ext === 'mpd' || ct === 'application/dash+xml') return 'dash';

  if (SEGMENT_EXTS.includes(ext) || ct === 'video/mp2t') return 'segment';

  if (VIDEO_EXTS.includes(ext)) return 'video';
  if (AUDIO_EXTS.includes(ext)) return 'audio';

  if (ct.startsWith('video/')) return 'video';
  if (ct.startsWith('audio/')) return 'audio';

  return null;
}

export const KIND_LABEL = {
  hls: 'HLS',
  dash: 'DASH',
  video: 'VIDEO',
  audio: 'AUDIO',
  blob: 'BLOB'
};

export function formatBytes(bytes) {
  if (!bytes || bytes < 0) return '';
  const units = ['B', 'KB', 'MB', 'GB'];
  let value = bytes;
  let i = 0;
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i += 1;
  }
  return `${value >= 10 || i === 0 ? Math.round(value) : value.toFixed(1)} ${units[i]}`;
}

export function formatDuration(seconds) {
  if (!seconds || !isFinite(seconds)) return '';
  const total = Math.round(seconds);
  const h = Math.floor(total / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  const pad = (n) => String(n).padStart(2, '0');
  return h > 0 ? `${h}:${pad(m)}:${pad(s)}` : `${m}:${pad(s)}`;
}

export function sanitizeFilename(name, fallback = 'video') {
  const clean = (name || '')
    .replace(/[\\/:*?"<>|]/g, ' ')
    .split('')
    .filter((ch) => ch.charCodeAt(0) > 31)
    .join('')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 120);
  return clean || fallback;
}

export function urlBasename(url) {
  try {
    const { pathname } = new URL(url);
    const last = decodeURIComponent(pathname.split('/').filter(Boolean).pop() || '');
    return last.replace(/\.[a-z0-9]{1,5}$/i, '') || 'video';
  } catch {
    return 'video';
  }
}

export function downloadExtension(item) {
  if (item.kind === 'hls' || item.kind === 'dash') return 'ts';
  const ext = pathExtension(item.url);
  if (VIDEO_EXTS.includes(ext) || AUDIO_EXTS.includes(ext)) return ext;
  if ((item.contentType || '').includes('webm')) return 'webm';
  if ((item.contentType || '').startsWith('audio/')) return 'm4a';
  return 'mp4';
}

// Nome de arquivo sugerido a partir do item detectado.
export function suggestFilename(item) {
  const base = sanitizeFilename(item.title || urlBasename(item.url));
  const ext = downloadExtension(item);
  return base.toLowerCase().endsWith(`.${ext}`) ? base : `${base}.${ext}`;
}

export function shortenUrl(url, max = 76) {
  if (url.length <= max) return url;
  return `${url.slice(0, max - 20)}...${url.slice(-17)}`;
}
