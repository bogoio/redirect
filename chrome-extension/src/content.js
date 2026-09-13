// Content script: varre o DOM atras de <video>/<audio> e manda o que achar pro service worker.

(() => {
  const seen = new Map();
  let scanTimer = null;

  function pageTitle() {
    const og = document.querySelector('meta[property="og:title"]');
    const title = (og && og.content) || document.title || '';
    return title.trim().slice(0, 120);
  }

  function collectRoots(root, out) {
    out.push(root);
    const walker = root.querySelectorAll ? root.querySelectorAll('*') : [];
    for (const el of walker) {
      if (el.shadowRoot) collectRoots(el.shadowRoot, out);
    }
    return out;
  }

  function mediaElements() {
    const roots = collectRoots(document, []);
    const found = [];
    for (const root of roots) {
      if (!root.querySelectorAll) continue;
      found.push(...root.querySelectorAll('video, audio'));
    }
    return found;
  }

  function describe(el, url) {
    const isVideo = el.tagName === 'VIDEO';
    const kind = url.startsWith('blob:') ? 'blob' : undefined; // o worker reclassifica pelo URL
    return {
      url,
      kind,
      title: pageTitle(),
      duration: isFinite(el.duration) ? el.duration : 0,
      width: isVideo ? el.videoWidth || 0 : 0,
      height: isVideo ? el.videoHeight || 0 : 0,
      poster: isVideo ? el.poster || '' : ''
    };
  }

  function scan() {
    const items = [];

    for (const el of mediaElements()) {
      const urls = new Set();
      if (el.currentSrc) urls.add(el.currentSrc);
      if (el.src) urls.add(el.src);
      for (const source of el.querySelectorAll('source')) {
        if (source.src) urls.add(source.src);
      }

      for (const url of urls) {
        if (!url || url.startsWith('data:')) continue;
        const item = describe(el, url);
        const signature = `${url}|${item.width}x${item.height}|${Math.round(item.duration)}`;
        if (seen.get(url) === signature) continue;
        seen.set(url, signature);
        items.push(item);
      }
    }

    if (!items.length) return;
    chrome.runtime.sendMessage({ type: 'PAGE_ITEMS', items }).catch(() => {});
  }

  function scheduleScan() {
    clearTimeout(scanTimer);
    scanTimer = setTimeout(scan, 500);
  }

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg && msg.type === 'RESCAN') {
      seen.clear();
      scan();
      sendResponse({ ok: true });
    }
    return false;
  });

  document.addEventListener('loadedmetadata', scheduleScan, true);
  document.addEventListener('play', scheduleScan, true);
  document.addEventListener('durationchange', scheduleScan, true);

  new MutationObserver(scheduleScan).observe(document.documentElement, {
    childList: true,
    subtree: true
  });

  scheduleScan();
})();
