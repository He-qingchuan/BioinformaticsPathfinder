'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const lessons = window.LESSONS;
  const lessonDialog = $('lesson-dialog');
  const imageDialog = $('image-dialog');
  const glossaryDialog = $('glossary-dialog');
  const key = 'scrna-islands-read-v4';
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
    $('lesson-documents').innerHTML = '<p class="eyebrow">本地脚本 · 延伸阅读</p>' + (next.documents.length ? next.documents.map(d => `<a href="${encodeURI(d.url)}" target="_blank" rel="noopener">${escape(d.title)} ↗</a>`).join('') : '<a href="library/脚本与资料目录.html" target="_blank" rel="noopener">研究背景与样本范围 ↗</a>');
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

  // 功能：把控件绑定到随包数据；目的：让学员观察规则影响，不写回分析。
  // 功能：把控件绑定到随包数据；目的：让学员观察规则影响，不写回分析。
  function bindLabs() {
    if ($('qc-slider')) {
      const update=()=>{const limit=+$('qc-slider').value; $('qc-value').textContent=limit;
        const groups={}; window.CASE.qc.forEach(([mt,sample])=>{groups[sample]??={all:0,keep:0};groups[sample].all++;if(mt<=limit)groups[sample].keep++;});
        $('qc-count').textContent=Object.entries(groups).map(([k,v])=>`${k}：${v.keep.toLocaleString()} / ${v.all.toLocaleString()}（${(v.keep/v.all*100).toFixed(1)}%）`).join('；');};
      $('qc-slider').oninput=update; update();
    }
    if ($('dot-fraction')) {
      const update=()=>{const f=+$('dot-fraction').value,m=+$('dot-mean').value;
        $('dot-demo').setAttribute('r',40*Math.sqrt(f/100));$('dot-demo').setAttribute('fill',`hsl(3 43% ${94-m*.62}%)`);
        $('dot-output').textContent=`比例 ${f}%；缩放颜色值 ${(m/100).toFixed(2)}。两种编码可以独立变化。`;};
      $('dot-fraction').oninput=update;$('dot-mean').oninput=update;update();
    }
    if ($('route-image')) $('route-image').onchange=()=>{$('route-preview').src=$('route-image').value;};
    if ($('resolution-select')) {const update=()=>{
      const v=$('resolution-select').value, key='leiden_res_'+v.replace('.','_');
      $('resolution-result').textContent=`分辨率 ${v}：${window.CASE.facts['06'].clusters[key]} 个历史簇。查看上方同坐标对照图，再结合 marker 解释。`;};
      $('resolution-select').onchange=update;update();}
  }
  refreshProgress();
  restoreLocation();
})();
