'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const lessons = window.LESSONS;
  const lessonDialog = $('lesson-dialog');
  const imageDialog = $('image-dialog');
  const glossaryDialog = $('glossary-dialog');
  const key = 'rnaseq-islands-read-v1';
  let current = null;
  let trigger = null;
  let read = new Set();
  let storageWorks = true;
  let toastTimer;
  const escape = value => String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));

  try {
    const stored = JSON.parse(localStorage.getItem(key) || '[]');
    if (Array.isArray(stored)) read = new Set(stored.filter(id => lessons.some(l => l.id === id)));
  } catch (_) { storageWorks = false; }

  function notify(message) {
    $('toast').textContent = message;
    $('toast').classList.add('visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => $('toast').classList.remove('visible'), 2800);
  }
  function saveRead() {
    try { localStorage.setItem(key, JSON.stringify([...read])); }
    catch (_) { storageWorks = false; }
    refreshProgress();
  }
  function refreshProgress() {
    $('progress-label').textContent = `已读 ${read.size} / ${lessons.length}`;
    document.querySelectorAll('.station-node,.station-card').forEach(el => {
      el.classList.toggle('is-read', read.has(el.dataset.station));
      const lesson = lessons.find(l => l.id === el.dataset.station);
      el.setAttribute('aria-label', `${lesson.badge} ${lesson.title}：${lesson.subtitle}${read.has(lesson.id) ? '，已读' : ''}`);
    });
    if (current) {
      $('mark-read').textContent = read.has(current.id) ? '本站已读 ✓' : '标记本站已读';
      $('mark-read').setAttribute('aria-pressed', String(read.has(current.id)));
    }
  }
  function syncBody() { document.body.classList.toggle('modal-open', !!document.querySelector('dialog[open]')); }
  function setHash(hash, replace = false) {
    try { history[replace ? 'replaceState' : 'pushState'](null, '', hash); }
    catch (_) { location.hash = hash; }
  }
  function openLesson(id, addHistory = true, origin = null) {
    const next = lessons.find(s => s.id === id);
    if (!next) return;
    current = next;
    if (origin) trigger = origin;
    $('lesson-eyebrow').textContent = `${next.badge} · ${next.subtitle} · 约 ${next.minutes} 分钟`;
    $('lesson-title').textContent = next.title;
    $('lesson-question').textContent = next.question;
    $('lesson-content').innerHTML = next.html;
    $('lesson-toc').innerHTML = [...$('lesson-content').querySelectorAll('h2')].map(h => `<a href="#${h.id}">${escape(h.textContent)}</a>`).join('');
    $('lesson-documents').innerHTML = '<p class="eyebrow">本地脚本 · 延伸阅读</p>' + (next.documents.length ? next.documents.map(d => `<a href="${encodeURI(d.url)}" target="_blank" rel="noopener">${escape(d.title)} ↗</a>`).join('') : '<a href="library/附1%20研究背景与样本范围.html" target="_blank" rel="noopener">研究背景与样本范围 ↗</a>');
    const index = lessons.indexOf(next);
    $('previous-station').disabled = index === 0;
    $('next-station').textContent = index === lessons.length - 1 ? '回到地图 →' : '下一站 →';
    bindLabs();
    if (!lessonDialog.open) lessonDialog.showModal();
    syncBody();
    $('lesson-scroll').scrollTop = 0;
    lessonDialog.querySelector('.lesson-shell').scrollTop = 0;
    $('lesson-toc').scrollLeft = 0;
    refreshProgress();
    if (addHistory) setHash('#station/' + id);
    $('close-lesson').focus({preventScroll:true});
  }
  function closeLesson(addHistory = true) {
    if (imageDialog.open) imageDialog.close();
    if (glossaryDialog.open) glossaryDialog.close();
    lessonDialog.close();
    syncBody();
    if (addHistory) setHash('#world');
    if (trigger && trigger.isConnected) trigger.focus({preventScroll:true});
  }
  function restoreLocation() {
    const match = /^#station\/([a-z]+)$/.exec(location.hash);
    if (match && lessons.some(s => s.id === match[1])) openLesson(match[1], false);
    else if (lessonDialog.open) closeLesson(false);
  }
  window.addEventListener('popstate', restoreLocation);
  window.addEventListener('hashchange', restoreLocation);

  document.addEventListener('click', event => {
    const station = event.target.closest('[data-station]');
    if (station) { event.preventDefault(); openLesson(station.dataset.station, true, station); return; }
    const check = event.target.closest('[data-check-answer]');
    if (check) {
      const quiz = check.closest('.quiz');
      const selected = quiz.querySelector('input:checked');
      const feedback = quiz.querySelector('.quiz-feedback');
      if (!selected) { feedback.textContent = '先选一个答案，也可以直接展开下方解析。'; return; }
      feedback.textContent = selected.value === quiz.dataset.answer ? '答对了。你已经抓住这一站的关键。' : '再想一步：看看下方解析，分清这个问题涉及的概念。';
      quiz.querySelector('details').open = true;
    }
  });
  $('lesson-toc').addEventListener('click', event => {
    const a = event.target.closest('a');
    if (!a) return;
    event.preventDefault();
    document.getElementById(a.hash.slice(1)).scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
  });
  $('close-lesson').onclick = () => closeLesson();
  lessonDialog.addEventListener('cancel', event => { event.preventDefault(); closeLesson(); });
  $('previous-station').onclick = () => { const i = lessons.indexOf(current); if (i > 0) openLesson(lessons[i - 1].id); };
  $('next-station').onclick = () => { const i = lessons.indexOf(current); if (i < lessons.length - 1) openLesson(lessons[i + 1].id); else closeLesson(); };
  $('mark-read').onclick = () => {
    if (!current) return;
    if (read.has(current.id)) read.delete(current.id); else read.add(current.id);
    saveRead();
    if (!storageWorks) notify('本次阅读中已记录；浏览器限制了本地保存。');
  };
  $('lesson-fullscreen').onclick = () => {
    const active = lessonDialog.classList.toggle('lecture-mode');
    $('lesson-fullscreen').textContent = active ? '退出讲课模式' : '全屏讲课';
    $('lesson-fullscreen').setAttribute('aria-pressed', String(active));
  };
  $('reset-progress').onclick = () => { read.clear();saveRead();notify('已读记录已重置，课程仍全部开放。'); };
  $('show-routes').onchange = () => document.querySelector('.world-map').classList.toggle('show-routes', $('show-routes').checked);
  function setView(list) {
    document.querySelector('.map-scroller').hidden = list;
    $('station-list').hidden = !list;
    $('map-view').setAttribute('aria-pressed', String(!list));
    $('list-view').setAttribute('aria-pressed', String(list));
    $('show-routes').disabled = list;
  }
  $('map-view').onclick = () => setView(false);
  $('list-view').onclick = () => setView(true);

  function bindLabs() {
    if ($('other-rna')) $('other-rna').oninput = event => {
      const other = Number(event.target.value), pct = 50 / (50 + other) * 100;
      $('other-value').textContent = String(other);
      $('target-bar').style.width = pct + '%';
      $('target-bar').textContent = pct >= 20 ? '目标 RNA' : '目标';
      $('composition-output').textContent = pct.toFixed(1) + '%';
    };
    if ($('swap-direction')) {
      let swapped = false;
      $('swap-direction').onclick = () => {
        swapped = !swapped;
        $('direction-formula').textContent = swapped ? 'log₂(5 / 20)' : 'log₂(20 / 5)';
        $('direction-value').textContent = swapped ? '−2' : '+2';
        $('direction-meaning').textContent = swapped ? 'B 相对 A 是 1/4，log₂FC 为 −2。' : 'A 相对 B 是 4 倍，log₂FC 为 +2。';
      };
    }
    if ($('fdr')) {
      const classify = r => {
        const p = Number(r.padj), fc = Number(r.fc);
        if (!Number.isFinite(p) || !Number.isFinite(fc) || p > Number($('fdr').value) || Math.abs(fc) < Number($('fc-threshold').value)) return 'ns';
        return fc > 0 ? 'up' : 'down';
      };
      const updateGene = () => {
        const id = $('gene-query').value.trim().toUpperCase();
        const r = window.DE.find(r => r.id === id);
        if (!r) { $('gene-answer').textContent = id ? '这一比较的已保存结果中没有找到该 ID。请使用完整基因 ID；缺少记录不等于基因不表达。' : '输入基因 ID，可以核对它的幅度、padj 和当前筛选状态。'; return; }
        const p = Number(r.padj);
        const shownP = Number.isFinite(p) ? (p === 0 ? '0（源表数值表示）' : p.toPrecision(4)) : r.padj;
        $('gene-answer').textContent = `${r.id}：log₂FC = ${Number(r.fc).toFixed(3)}，padj = ${shownP}；当前筛选：${{up:'上调候选',down:'下调候选',ns:'未达到候选阈值'}[classify(r)]}。`;
      };
      const update = () => {
        const counts = {up:0,down:0,ns:0};
        window.DE.forEach(r => counts[classify(r)]++);
        $('fc-value').textContent = Number($('fc-threshold').value).toFixed(1);
        for (const type of ['up','down','ns']) $(type + '-count').textContent = counts[type].toLocaleString('en-US');
        updateGene();
      };
      $('fdr').onchange = update;
      $('fc-threshold').oninput = update;
      $('gene-query').oninput = updateGene;
      $('reset-threshold').onclick = () => { $('fdr').value = '0.05';$('fc-threshold').value = '1';update(); };
      update();
    }
    if ($('shuffle-rank')) {
      let scattered = false;
      $('shuffle-rank').onclick = () => {
        scattered = !scattered;
        const positions = scattered ? [1,5,9,13,17,21] : [0,1,3,4,5,8];
        document.querySelectorAll('.rank-gene').forEach((el,i) => el.classList.toggle('hit',positions.includes(i)));
        $('shuffle-rank').textContent = scattered ? '改为前端集中' : '改为分散分布';
        $('rank-explanation').textContent = scattered ? '现在 6 名成员分布在整条队伍里，没有明显集中在一端。成员数量没变，位置变了；真实结果还需要权重和检验来判断。' : '同一功能的成员聚在上调端，提示整体偏向。这只是直觉示意，真实 GSEA 还会考虑排序权重、集合大小和统计检验。';
      };
    }
  }
  refreshProgress();
  restoreLocation();
})();
