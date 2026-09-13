import {
  KIND_LABEL,
  classify,
  formatBytes,
  formatDuration,
  shortenUrl,
  suggestFilename,
  urlBasename
} from './shared.js';

const listEl = document.getElementById('list');
const statusEl = document.getElementById('status');
const template = document.getElementById('item-template');

const progressBars = new Map(); // url -> elemento .bar

async function activeTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function rescanPage(tabId) {
  try {
    await chrome.tabs.sendMessage(tabId, { type: 'RESCAN' });
  } catch {
    // Sem content script na aba (chrome://, Web Store, PDF...): so o sniffer de rede vale.
  }
}

async function getItems(tabId) {
  const res = await chrome.runtime.sendMessage({ type: 'GET_ITEMS', tabId });
  return (res && res.items) || [];
}

function itemKind(item) {
  return item.kind || classify(item.url) || 'video';
}

function metaLine(item) {
  const parts = [];
  if (item.width && item.height) parts.push(`${item.width}x${item.height}`);
  if (item.duration) parts.push(formatDuration(item.duration));
  if (item.size) parts.push(formatBytes(item.size));
  parts.push(item.source === 'page' ? 'da página' : 'da rede');
  return parts.join(' · ');
}

function ffmpegCommand(item) {
  return `ffmpeg -i "${item.url}" -c copy "${suggestFilename(item).replace(/\.ts$/, '.mp4')}"`;
}

async function copy(text, button) {
  await navigator.clipboard.writeText(text);
  const original = button.textContent;
  button.textContent = 'Copiado';
  setTimeout(() => {
    button.textContent = original;
  }, 1200);
}

function render(items, pageTitle) {
  listEl.replaceChildren();
  progressBars.clear();

  if (!items.length) {
    statusEl.textContent =
      'Nada detectado ainda. Dê play no vídeo por alguns segundos e clique em Reescanear.';
    return;
  }

  statusEl.textContent = `${items.length} ${items.length === 1 ? 'mídia detectada' : 'mídias detectadas'} nesta aba.`;

  for (const raw of items) {
    const item = { ...raw, kind: itemKind(raw), title: raw.title || pageTitle };
    const node = template.content.firstElementChild.cloneNode(true);

    const badge = node.querySelector('.badge');
    badge.textContent = KIND_LABEL[item.kind] || 'MÍDIA';
    badge.classList.add(item.kind);

    node.querySelector('.meta').textContent = metaLine(item);
    node.querySelector('.title').textContent = item.title || urlBasename(item.url);
    node.querySelector('.url').textContent = shortenUrl(item.url);

    const downloadBtn = node.querySelector('.download');
    const copyBtn = node.querySelector('.copy');
    const ffmpegBtn = node.querySelector('.ffmpeg');
    const note = node.querySelector('.note');
    const progress = node.querySelector('.progress');

    copyBtn.addEventListener('click', () => copy(item.url, copyBtn));
    ffmpegBtn.addEventListener('click', () => copy(ffmpegCommand(item), ffmpegBtn));

    if (item.kind === 'blob') {
      downloadBtn.disabled = true;
      ffmpegBtn.disabled = true;
      note.hidden = false;
      note.textContent =
        'URL blob: existe só dentro da página. Dê play no vídeo e reescaneie para o sniffer pegar o stream real.';
    } else if (item.kind === 'dash') {
      downloadBtn.disabled = true;
      note.hidden = false;
      note.textContent = 'DASH (.mpd): use o comando ffmpeg ao lado.';
    } else {
      downloadBtn.addEventListener('click', async () => {
        downloadBtn.disabled = true;
        downloadBtn.textContent = item.kind === 'hls' ? 'Montando...' : 'Baixando...';
        note.hidden = true;

        if (item.kind === 'hls') {
          progress.hidden = false;
          progressBars.set(item.url, progress.querySelector('.bar'));
        }

        const res = await chrome.runtime.sendMessage({
          type: 'DOWNLOAD',
          item,
          filename: suggestFilename(item)
        });

        progress.hidden = true;
        if (res && res.ok) {
          downloadBtn.textContent = 'Baixado';
        } else {
          downloadBtn.textContent = 'Tentar de novo';
          downloadBtn.disabled = false;
          note.hidden = false;
          note.textContent = (res && res.error) || 'Falhou. Tente o comando ffmpeg.';
        }
      });
    }

    listEl.append(node);
  }
}

chrome.runtime.onMessage.addListener((msg) => {
  if (!msg || msg.type !== 'STREAM_PROGRESS') return;
  const bar = progressBars.get(msg.url);
  if (bar && msg.total) bar.style.width = `${Math.round((msg.done / msg.total) * 100)}%`;
});

async function refresh({ rescan } = { rescan: true }) {
  const tab = await activeTab();
  if (!tab || typeof tab.id !== 'number') {
    statusEl.textContent = 'Nenhuma aba ativa.';
    return;
  }

  if (rescan) {
    await rescanPage(tab.id);
    await new Promise((r) => setTimeout(r, 250));
  }

  render(await getItems(tab.id), tab.title || '');
}

document.getElementById('rescan').addEventListener('click', () => refresh({ rescan: true }));
document.getElementById('clear').addEventListener('click', async () => {
  const tab = await activeTab();
  if (tab) await chrome.runtime.sendMessage({ type: 'CLEAR', tabId: tab.id });
  refresh({ rescan: false });
});

refresh({ rescan: true });
