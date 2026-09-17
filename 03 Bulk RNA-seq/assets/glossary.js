'use strict';
(() => {
  const data = window.GLOSSARY;
  const dialog = document.getElementById('glossary-dialog');
  if (!data || !dialog || typeof dialog.showModal !== 'function') return;
  const $ = id => document.getElementById(id);
  const query = $('glossary-query');
  const category = $('glossary-category');
  const container = $('glossary-entries');
  const status = $('glossary-status');
  const byId = new Map(data.entries.map(e => [e.id, e]));
  const normalized = value => value.normalize('NFKC').toLowerCase().replace(/\s+/g, '').replace(/[–−]/g, '-');
  const names = entry => [entry.zh, entry.en, entry.abbr, entry.legacy_name || '', ...entry.aliases].filter(Boolean);
  const searchable = new Map(data.entries.map(e => [e.id, normalized([
    ...names(e), e.category, e.summary, e.example, e.in_course, e.pitfall
  ].join(' '))]));
  let origin = null;
  let positions = [];
  let directId = null;
  let lastResults = [];
  for (const label of data.categories) category.add(new Option(label, label));

  function syncBody() {
    document.body.classList.toggle('modal-open', !!document.querySelector('dialog[open]'));
  }
  function findEntries() {
    if (directId && byId.has(directId)) return [byId.get(directId)];
    const pool = data.entries.filter(e => !category.value || e.category === category.value);
    const text = query.value.trim();
    if (!text) return pool;
    // Exact spelling first keeps BP (ontology) separate from bp (sequence unit).
    const spelled = pool.filter(e => names(e).includes(text));
    if (spelled.length) return spelled;
    const q = normalized(text);
    const exact = pool.filter(e => names(e).some(n => normalized(n) === q));
    if (exact.length) return exact;
    const named = pool.filter(e => names(e).some(n => normalized(n).includes(q)));
    const namedIds = new Set(named.map(e => e.id));
    const mentioned = pool.filter(e => !namedIds.has(e.id) && searchable.get(e.id).includes(q));
    return [...named, ...mentioned];
  }
  function render() {
    lastResults = findEntries();
    container.innerHTML = lastResults.length
      ? lastResults.map(e => e.html).join('')
      : '<p class="glossary-empty">还没有找到这个词。可以试试英文名、缩写，或点击“查看全部术语”。</p>';
    container.scrollTop = 0;
    status.textContent = directId
      ? `正在解释：${byId.get(directId).zh} · 全部 ${data.entries.length} 项`
      : `找到 ${lastResults.length} 项 · 全部 ${data.entries.length} 项`;
  }
  function rememberPosition(element) {
    const elements = new Set([document.scrollingElement]);
    for (let node = element; node; node = node.parentElement) {
      if (node.scrollHeight > node.clientHeight || node.scrollWidth > node.clientWidth) elements.add(node);
    }
    positions = [...elements].filter(Boolean).map(el => [el, el.scrollLeft, el.scrollTop]);
  }
  function focusEntry() {
    const heading = container.querySelector('.glossary-entry h3');
    if (!heading) return;
    heading.tabIndex = -1;
    heading.focus({preventScroll: true});
  }
  function open(id, trigger) {
    if (!dialog.open) {
      origin = trigger || document.activeElement;
      rememberPosition(origin);
    }
    directId = byId.has(id) ? id : null;
    category.value = '';
    query.value = directId ? (byId.get(directId).abbr || byId.get(directId).zh) : '';
    render();
    if (!dialog.open) dialog.showModal();
    syncBody();
    if (directId) focusEntry();
    else query.focus({preventScroll: true});
  }
  document.addEventListener('click', event => {
    const link = event.target.closest('[data-term]');
    if (!link || !byId.has(link.dataset.term)) return;
    // Modified link clicks retain the normal printable-page fallback.
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    open(link.dataset.term, link);
  });
  for (const id of ['open-glossary', 'lesson-glossary', 'reading-glossary']) {
    const opener = $(id);
    if (opener) opener.addEventListener('click', () => open(null, opener));
  }
  query.addEventListener('input', () => { directId = null; render(); });
  category.addEventListener('change', () => { directId = null; render(); });
  $('glossary-all').addEventListener('click', () => {
    directId = null;
    query.value = '';
    category.value = '';
    render();
    query.focus({preventScroll: true});
  });
  $('close-glossary').addEventListener('click', () => dialog.close());
  dialog.addEventListener('keydown', event => {
    if (event.key === 'Tab') {
      const controls = [...dialog.querySelectorAll('a[href],button,input,select,textarea,[tabindex]')]
        .filter(el => !el.disabled && el.tabIndex >= 0 && el.getClientRects().length);
      const first = controls[0], last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault(); last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault(); first?.focus();
      }
    }
    if (event.key === 'Escape') {
      event.preventDefault();
      event.stopPropagation();
      dialog.close();
    }
  });
  dialog.addEventListener('cancel', event => { event.preventDefault(); dialog.close(); });
  dialog.addEventListener('close', () => {
    syncBody();
    const owner = origin && origin.closest('dialog');
    if (origin && origin.isConnected && (!owner || owner.open)) {
      origin.focus({preventScroll: true});
      for (const [el, left, top] of positions) {
        if (el.isConnected) el.scrollTo({left, top, behavior: 'instant'});
      }
    }
    origin = null;
    positions = [];
  });
  document.body.classList.add('glossary-ready');
})();
