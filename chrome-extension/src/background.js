// Service worker: fareja requisicoes de midia, guarda por aba e coordena os downloads.

import { classify, suggestFilename } from './shared.js';

const MAX_ITEMS_PER_TAB = 60;
const STORAGE_KEY = 'tabs';

// { [tabId]: { url: item } }
let store = null;
let loading = null;
let saveTimer = null;

function loadStore() {
  if (store) return Promise.resolve(store);
  if (!loading) {
    loading = chrome.storage.session.get(STORAGE_KEY).then((data) => {
      store = data[STORAGE_KEY] || {};
      return store;
    });
  }
  return loading;
}

function scheduleSave() {
  if (saveTimer) return;
  saveTimer = setTimeout(() => {
    saveTimer = null;
    chrome.storage.session.set({ [STORAGE_KEY]: store }).catch(() => {});
  }, 400);
}

function tabBucket(tabId) {
  if (!store[tabId]) store[tabId] = {};
  return store[tabId];
}

function updateBadge(tabId) {
  const count = Object.keys(store[tabId] || {}).length;
  const text = count ? String(count) : '';
  chrome.action.setBadgeText({ tabId, text }).catch(() => {});
  chrome.action.setBadgeBackgroundColor({ tabId, color: '#e8542f' }).catch(() => {});
}

function addItem(tabId, item) {
  const bucket = tabBucket(tabId);
  const existing = bucket[item.url];

  if (existing) {
    // Mantem o que ja sabemos e completa com o que chegou agora.
    bucket[item.url] = {
      ...existing,
      ...Object.fromEntries(Object.entries(item).filter(([, v]) => v !== undefined && v !== '')),
      size: Math.max(existing.size || 0, item.size || 0),
      seenAt: existing.seenAt
    };
  } else {
    const keys = Object.keys(bucket);
    if (keys.length >= MAX_ITEMS_PER_TAB) {
      // Descarta o mais antigo para nao crescer sem limite.
      let oldest = keys[0];
      for (const key of keys) {
        if ((bucket[key].seenAt || 0) < (bucket[oldest].seenAt || 0)) oldest = key;
      }
      delete bucket[oldest];
    }
    bucket[item.url] = { ...item, seenAt: Date.now() };
  }

  scheduleSave();
  updateBadge(tabId);
}

function clearTab(tabId) {
  if (store && store[tabId]) {
    delete store[tabId];
    scheduleSave();
  }
  updateBadge(tabId);
}

// --- Sniffer de rede -------------------------------------------------------

chrome.webRequest.onBeforeRequest.addListener(
  (details) => {
    if (details.tabId < 0 || details.frameId !== 0) return;
    loadStore().then(() => clearTab(details.tabId));
  },
  { urls: ['<all_urls>'], types: ['main_frame'] }
);

chrome.webRequest.onHeadersReceived.addListener(
  (details) => {
    if (details.tabId < 0) return;
    const headers = details.responseHeaders || [];
    const header = (name) => {
      const found = headers.find((h) => h.name.toLowerCase() === name);
      return found ? found.value || '' : '';
    };

    const contentType = header('content-type');
    const kind = classify(details.url, contentType);
    if (!kind || kind === 'segment' || kind === 'blob') return;

    // Um MP4 pedido em Range costuma vir em pedacos: guarda o tamanho total.
    const range = header('content-range');
    const totalFromRange = range ? Number((range.split('/')[1] || '').trim()) : 0;
    const size = totalFromRange || Number(header('content-length')) || 0;

    loadStore().then(() => {
      addItem(details.tabId, {
        url: details.url,
        kind,
        contentType,
        size,
        source: 'network'
      });
    });
  },
  { urls: ['<all_urls>'], types: ['media', 'xmlhttprequest', 'object', 'other'] },
  ['responseHeaders']
);

chrome.tabs.onRemoved.addListener((tabId) => {
  loadStore().then(() => clearTab(tabId));
});

// --- Offscreen (montagem de HLS e criacao de blob URL) ---------------------

let offscreenReady = null;

async function ensureOffscreen() {
  if (await chrome.offscreen.hasDocument()) return;
  if (!offscreenReady) {
    offscreenReady = chrome.offscreen
      .createDocument({
        url: 'src/offscreen.html',
        reasons: ['BLOBS'],
        justification: 'Baixar e juntar os segmentos de um stream HLS antes de salvar o arquivo.'
      })
      .catch((err) => {
        // Corrida entre dois pedidos simultaneos: o documento ja existe.
        if (!String(err).includes('Only a single offscreen')) throw err;
      })
      .finally(() => {
        offscreenReady = null;
      });
  }
  await offscreenReady;
}

async function downloadDirect(item, filename) {
  const id = await chrome.downloads.download({
    url: item.url,
    filename,
    saveAs: false
  });
  return { ok: true, downloadId: id };
}

async function downloadStream(item, filename) {
  await ensureOffscreen();
  const result = await chrome.runtime.sendMessage({
    target: 'offscreen',
    type: 'BUILD_STREAM',
    url: item.url,
    kind: item.kind
  });

  if (!result || !result.ok) {
    return { ok: false, error: (result && result.error) || 'Falha ao montar o stream.' };
  }

  const downloadId = await chrome.downloads.download({
    url: result.blobUrl,
    filename,
    saveAs: false
  });

  const onChanged = (delta) => {
    if (delta.id !== downloadId) return;
    const done = delta.state && (delta.state.current === 'complete' || delta.state.current === 'interrupted');
    if (!done) return;
    chrome.downloads.onChanged.removeListener(onChanged);
    chrome.runtime
      .sendMessage({ target: 'offscreen', type: 'REVOKE', blobUrl: result.blobUrl })
      .catch(() => {});
  };
  chrome.downloads.onChanged.addListener(onChanged);

  return { ok: true, downloadId };
}

// --- Mensagens -------------------------------------------------------------

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!msg || msg.target === 'offscreen' || msg.type === 'STREAM_PROGRESS') return;

  (async () => {
    await loadStore();

    switch (msg.type) {
      case 'PAGE_ITEMS': {
        const tabId = sender.tab && sender.tab.id;
        if (typeof tabId === 'number') {
          for (const item of msg.items || []) {
            const kind = classify(item.url);
            if (!kind || kind === 'segment') continue;
            addItem(tabId, { ...item, kind, source: 'page' });
          }
        }
        sendResponse({ ok: true });
        break;
      }

      case 'GET_ITEMS': {
        const bucket = store[msg.tabId] || {};
        const items = Object.values(bucket).sort((a, b) => (b.size || 0) - (a.size || 0));
        sendResponse({ ok: true, items });
        break;
      }

      case 'CLEAR': {
        clearTab(msg.tabId);
        sendResponse({ ok: true });
        break;
      }

      case 'DOWNLOAD': {
        const item = msg.item;
        const filename = msg.filename || suggestFilename(item);
        try {
          const result = item.kind === 'hls' || item.kind === 'dash'
            ? await downloadStream(item, filename)
            : await downloadDirect(item, filename);
          sendResponse(result);
        } catch (err) {
          sendResponse({ ok: false, error: String((err && err.message) || err) });
        }
        break;
      }

      default:
        sendResponse({ ok: false, error: `Mensagem desconhecida: ${msg.type}` });
    }
  })();

  return true; // resposta assincrona
});
